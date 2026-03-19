"""Sandbox runner — launches the filter agent inside a Docker container.

The CLI calls `run_filter_sandbox(query, ...)` which:
1. Ensures Docker is available and the image exists (auto-builds if needed)
2. Runs `docker run --rm` with the query + env vars
3. Captures stdout (filtered output) and streams stderr (agent logs)
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

_log = logging.getLogger("tvly.sandbox")

IMAGE_NAME = "tvly-filter-sandbox"
SANDBOX_DIR = "sandbox"  # relative to repo root

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
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
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

    # Verify daemon is running
    result = subprocess.run(
        [docker, "info"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Docker daemon is not running.\n"
            f"  stderr: {result.stderr.strip()[:200]}"
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
    """Build the filter sandbox Docker image from sandbox/."""
    repo_root = Path(__file__).resolve().parent.parent
    sandbox_dir = repo_root / SANDBOX_DIR

    if not (sandbox_dir / "Dockerfile").exists():
        raise FileNotFoundError(
            f"Dockerfile not found at {sandbox_dir / 'Dockerfile'}.\n"
            f"Build manually:  docker build -t {IMAGE_NAME} {SANDBOX_DIR}/"
        )

    _log.info("Building filter sandbox image...")
    from tavily_cli.theme import AQUA, err_console
    err_console.print(f"  [{AQUA}]Building filter sandbox image (first run only)...[/{AQUA}]")

    result = subprocess.run(
        [docker, "build", "-t", IMAGE_NAME, str(sandbox_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to build Docker image '{IMAGE_NAME}':\n{result.stderr[-500:]}"
        )

    _log.info("Image built: %s", IMAGE_NAME)
    err_console.print(f"  [{AQUA}]Image built: {IMAGE_NAME}[/{AQUA}]")


def run_filter_sandbox(
    query: str,
    *,
    instructions: str | None = None,
    model: str | None = None,
    verbose: bool = False,
    timeout: int = 300,
) -> str:
    """Run the filter agent inside Docker and return its output.

    Args:
        query: The search/filter query.
        instructions: Optional additional filtering instructions.
        model: LLM model identifier override.
        verbose: Forward --verbose to the agent (debug logging to stderr).
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

    # Load .env for API keys
    _load_env()

    # Build docker run command
    cmd: list[str] = [
        docker, "run", "--rm",
        "--network=host",  # agent needs outbound for LLM + Tavily API calls
        "--memory=512m",
        "--cpus=1.0",
    ]

    # Forward env vars into the container
    for var in _ENV_VARS:
        val = os.environ.get(var)
        if val:
            cmd.extend(["-e", f"{var}={val}"])

    cmd.append(IMAGE_NAME)

    # ENTRYPOINT args: tvly-filter "query" [--instructions ...] [--model ...] [--verbose]
    cmd.append(query)
    if instructions:
        cmd.extend(["--instructions", instructions])
    if model:
        cmd.extend(["--model", model])
    if verbose:
        cmd.append("--verbose")

    _log.info("Running filter agent in sandbox (timeout=%ds)", timeout)
    _log.debug("Docker command: %s", " ".join(cmd[:8]) + " ...")

    # Run with stderr streaming to our stderr (so user sees agent logs in real time)
    result = subprocess.run(
        cmd,
        capture_output=False,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Filter agent exited with code {result.returncode}"
        )

    output = (result.stdout or "").strip()
    if not output:
        raise RuntimeError("Filter agent produced no output")

    _log.info("Filter agent returned %d chars", len(output))
    return output
