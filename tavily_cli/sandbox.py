"""Sandbox runner — launches the filter agent inside a Docker container.

The CLI calls `run_filter_sandbox(query, ...)` which:
1. Ensures the Docker image exists (builds if needed)
2. Runs `docker run --rm` with the query + env vars
3. Captures and returns stdout (the filtered output)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

IMAGE_NAME = "tvly-filter-sandbox"
DOCKERFILE = "Dockerfile.filter"

# Env vars to forward into the container
_ENV_VARS = [
    "TAVILY_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "FILTER_MODEL",
    "LANGSMITH_TRACING",
    "LANGSMITH_ENDPOINT",
    "LANGSMITH_API_KEY",
    "LANGSMITH_PROJECT",
]


def _load_env() -> None:
    """Load .env file from the repo root into os.environ (no-op if missing)."""
    from dotenv import load_dotenv

    env_file = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_file, override=False)


def _docker_bin() -> str:
    """Find docker binary or fail with a clear message."""
    docker = shutil.which("docker")
    if not docker:
        raise RuntimeError(
            "Docker is required for --filter but was not found on PATH.\n"
            "Install Docker: https://docs.docker.com/get-docker/"
        )
    return docker


def _image_exists(docker: str) -> bool:
    """Check if the filter sandbox image is already built."""
    result = subprocess.run(
        [docker, "image", "inspect", IMAGE_NAME],
        capture_output=True,
    )
    return result.returncode == 0


def _build_image(docker: str) -> None:
    """Build the filter sandbox Docker image."""
    # Find the Dockerfile relative to this package
    pkg_dir = Path(__file__).resolve().parent.parent
    dockerfile = pkg_dir / DOCKERFILE

    if not dockerfile.exists():
        raise FileNotFoundError(
            f"Dockerfile not found at {dockerfile}.\n"
            f"Run from the skills repo root, or build manually:\n"
            f"  docker build -t {IMAGE_NAME} -f Dockerfile.filter ."
        )

    from tavily_cli.theme import AQUA, err_console
    err_console.print(f"  [{AQUA}]Building filter sandbox image...[/{AQUA}]")

    result = subprocess.run(
        [docker, "build", "-t", IMAGE_NAME, "-f", str(dockerfile), str(pkg_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to build Docker image:\n{result.stderr}"
        )

    err_console.print(f"  [{AQUA}]Image built: {IMAGE_NAME}[/{AQUA}]")


def _build_docker_cmd(
    docker: str,
    query: str,
    *,
    instructions: str | None = None,
    model: str | None = None,
    timeout: int = 120,
) -> list[str]:
    """Assemble the `docker run` command."""
    cmd = [
        docker, "run", "--rm",
        "--network=host",  # agent needs outbound for LLM + Tavily API calls
    ]

    # Load .env into the process env, then forward known vars into the container
    _load_env()
    for var in _ENV_VARS:
        val = os.environ.get(var)
        if val:
            cmd.extend(["-e", f"{var}={val}"])

    # Resource limits
    cmd.extend([
        "--memory=512m",
        "--cpus=1.0",
    ])

    cmd.append(IMAGE_NAME)

    # Args to filter_agent.py (ENTRYPOINT)
    cmd.append(query)
    if instructions:
        cmd.extend(["--instructions", instructions])
    if model:
        cmd.extend(["--model", model])

    return cmd


def run_filter_sandbox(
    query: str,
    *,
    instructions: str | None = None,
    model: str | None = None,
    timeout: int = 120,
) -> str:
    """Run the filter agent inside Docker and return its output.

    Args:
        query: The search/filter query.
        instructions: Optional additional filtering instructions.
        model: LLM model identifier override.
        timeout: Max seconds to wait for the container.

    Returns:
        The filtered output from the agent (stdout).

    Raises:
        RuntimeError: If Docker is missing, image build fails, or container errors.
        subprocess.TimeoutExpired: If the container exceeds the timeout.
    """
    docker = _docker_bin()

    # Auto-build image if it doesn't exist
    if not _image_exists(docker):
        _build_image(docker)

    cmd = _build_docker_cmd(
        docker,
        query,
        instructions=instructions,
        model=model,
        timeout=timeout,
    )

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if stderr:
            raise RuntimeError(f"Filter agent failed:\n{stderr}")
        raise RuntimeError(f"Filter agent exited with code {result.returncode}")

    return result.stdout.strip()
