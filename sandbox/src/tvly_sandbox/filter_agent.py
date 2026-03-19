#!/usr/bin/env python3
"""Filter agent — runs entirely inside a Docker container.

This script is the ENTRYPOINT of the tvly-filter-sandbox Docker image.
Everything happens in-container: LLM calls, Tavily API calls, and the
Python scripts the agent writes and executes.

The agent has a persistent bash/Python shell (via ShellToolMiddleware +
HostExecutionPolicy).  Inside the shell, scripts can call:

    from tvly_sandbox.tavily_tools import search, extract

to fetch web content, then filter/process it programmatically and print()
only the relevant signal.  Raw content never enters the LLM context window.

This mirrors Anthropic's Dynamic Filtering / Programmatic Tool Calling:
  LLM writes code → code calls search() → code filters → print()

Usage (inside container):
    tvly-filter "query" [--instructions "..."] [--model "..."] [--verbose]
    echo "query" | tvly-filter - [--instructions "..."]

Usage (from host via sandbox.py):
    The host calls `docker run --rm tvly-filter-sandbox "query" --instructions "..."`.
    Stdout contains the filtered output. Logs go to stderr.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time

# ---------------------------------------------------------------------------
# Logging — all agent logs go to stderr, stdout reserved for filtered output
# ---------------------------------------------------------------------------

_log = logging.getLogger("tvly.filter")


def _setup_logging(verbose: bool = False) -> None:
    """Configure hierarchical logging for the filter agent."""
    level = logging.DEBUG if verbose else logging.INFO

    root = logging.getLogger("tvly")
    root.setLevel(level)

    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)-7s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root.addHandler(handler)

    # Quiet down noisy libraries
    for name in ("httpx", "httpcore", "openai", "anthropic"):
        logging.getLogger(name).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a web research agent with dynamic filtering capabilities. Your job is
to find, fetch, and **programmatically filter** web content to extract only the
information that answers the user's query.

## Your tool

You have ONE tool: a persistent bash/Python **shell** running in a sandboxed
container.

Inside the shell, you can write and run Python scripts that call:
- `from tvly_sandbox.tavily_tools import search, extract`
- `search(query, max_results=5, ...)` → list of dicts with keys:
  title, url, content (snippet), score, raw_content (full page markdown)
- `extract(urls, ...)` → list of dicts with keys: url, raw_content

## Your workflow

1. **Search**: Write a Python script that calls `search()` with a good query.
2. **Inspect**: In the SAME script, iterate over results and print a compact
   summary — titles, URLs, and short content previews. Do NOT print raw_content
   in full. Just check what you got.
3. **Filter with code**: Write a follow-up script that:
   - Calls `search()` or `extract()` to get raw content
   - Uses string ops, regex, or BeautifulSoup to extract relevant passages
   - Cross-references across sources if needed
   - Prints ONLY the filtered, relevant information
4. **Iterate**: If the first search didn't cover everything, do more targeted
   searches and filter those too.
5. **Synthesize**: After all filtering is done, provide a clean final answer
   with citations as [Title](url).

## Critical rules

- **ALL data retrieval and filtering happens in Python code via the shell tool.**
- Never ask for search results as a separate tool call. Write code that calls
  `search()` and processes the results in the same script.
- The raw_content can be 50K+ chars per page. NEVER print it in full. Always
  filter in code and print only relevant excerpts.
- For scripts longer than 3-4 lines, write to a file and execute it:
  ```
  cat > /tmp/filter.py << 'PYEOF'
  from tvly_sandbox.tavily_tools import search
  results = search("your query", max_results=8)
  for r in results:
      # filter logic here
      print(relevant_excerpt)
  PYEOF
  python /tmp/filter.py
  ```
- Available packages: tavily-python, beautifulsoup4, lxml, json, re, csv, httpx.
- Keep your final output focused and concise — high signal, zero noise.
- Always cite sources as [Title](url).
"""


# ---------------------------------------------------------------------------
# Agent construction
# ---------------------------------------------------------------------------


def build_agent(model: str):
    """Build the filter agent with a host-executed shell (already inside Docker)."""
    from langchain.agents import create_agent
    from langchain.agents.middleware import (
        HostExecutionPolicy,
        ModelCallLimitMiddleware,
        ShellToolMiddleware,
    )

    # Forward API keys into the shell session so agent-written scripts can
    # import tavily_tools and call the Tavily API
    shell_env: dict[str, str] = {}
    for var in ("TAVILY_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        val = os.environ.get(var)
        if val:
            shell_env[var] = val

    # Verbose flag for tavily_tools logging inside scripts
    if _log.isEnabledFor(logging.DEBUG):
        shell_env["TVLY_FILTER_VERBOSE"] = "1"

    execution_policy = HostExecutionPolicy(
        command_timeout=60.0,
        max_output_lines=500,
    )

    _log.debug(
        "Execution policy: HostExecutionPolicy(timeout=60s, max_lines=500)"
    )

    middleware = [
        ShellToolMiddleware(
            workspace_root="/workspace",
            execution_policy=execution_policy,
            startup_commands=[
                "export PYTHONDONTWRITEBYTECODE=1",
            ],
            env=shell_env,
        ),
        ModelCallLimitMiddleware(run_limit=25, exit_behavior="end"),
    ]

    agent = create_agent(
        model=model,
        tools=[],  # No separate tools — everything through the shell
        system_prompt=SYSTEM_PROMPT,
        middleware=middleware,
    )

    _log.info("Agent built (model=%s, run_limit=25)", model)
    return agent


# ---------------------------------------------------------------------------
# run_filter() — main entry point
# ---------------------------------------------------------------------------


def run_filter(
    query: str,
    *,
    instructions: str | None = None,
    model: str = "anthropic:claude-sonnet-4-20250514",
    verbose: bool = False,
) -> dict:
    """Run the filter agent and return structured results.

    Args:
        query: The search/filter query.
        instructions: Optional additional filtering instructions.
        model: LLM model identifier string.
        verbose: Enable debug-level logging.

    Returns:
        dict with keys:
            output (str): The final filtered content.
            steps (int): Number of agent steps (LLM calls).
            elapsed (float): Total wall-clock time in seconds.
    """
    _setup_logging(verbose)
    _log.info("Filter agent starting for query: %r", query)

    # Verify the package is importable
    try:
        from tvly_sandbox import tavily_tools  # noqa: F401
        _log.debug("tvly_sandbox.tavily_tools found at %s", tavily_tools.__file__)
    except ImportError:
        _log.error("tvly_sandbox.tavily_tools not importable — is the package installed?")
        raise RuntimeError("tvly_sandbox.tavily_tools not importable")

    # Build agent
    agent = build_agent(model)

    # Compose user message
    user_message = query
    if instructions:
        user_message = f"{query}\n\nAdditional filtering instructions: {instructions}"
        _log.info("Custom instructions: %s", instructions[:200])

    # Invoke
    t0 = time.monotonic()
    _log.info("Invoking agent...")

    result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})

    elapsed = time.monotonic() - t0
    messages = result.get("messages", [])
    _log.info("Agent finished in %.1fs (%d messages)", elapsed, len(messages))

    # Log step-by-step summary
    step_count = _log_steps(messages)

    # Extract final AI message
    output = _extract_final_output(messages)
    _log.info("Final output: %d chars", len(output))

    return {
        "output": output,
        "steps": step_count,
        "elapsed": round(elapsed, 2),
    }


def _log_steps(messages: list) -> int:
    """Log a summary of each agent step. Returns the step count."""
    step = 0
    for msg in messages:
        msg_type = getattr(msg, "type", None)
        if msg_type is None and isinstance(msg, dict):
            msg_type = msg.get("role")

        if msg_type == "ai":
            step += 1
            tool_calls = getattr(msg, "tool_calls", None) or []
            if tool_calls:
                for tc in tool_calls:
                    name = tc.get("name", "?") if isinstance(tc, dict) else getattr(tc, "name", "?")
                    args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {})
                    cmd_preview = ""
                    if isinstance(args, dict):
                        cmd_text = args.get("command", args.get("shell", ""))
                        if cmd_text:
                            cmd_preview = f" → {cmd_text[:120]}"
                    _log.debug("  step %d: tool=%s%s", step, name, cmd_preview)
            else:
                content = getattr(msg, "content", "") or ""
                if isinstance(content, list):
                    content = " ".join(
                        b.get("text", "") if isinstance(b, dict) else str(b)
                        for b in content
                    )
                _log.debug("  step %d: response (%d chars)", step, len(content))

        elif msg_type == "tool":
            content = getattr(msg, "content", "") or ""
            if isinstance(content, str):
                lines = content.count("\n") + 1
                _log.debug("  tool output: %d lines, %d chars", lines, len(content))

    return step


def _extract_final_output(messages: list) -> str:
    """Extract the last AI message content from the agent's message list."""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "ai":
            content = getattr(msg, "content", None)
            if not content:
                continue

            if isinstance(content, str) and content.strip():
                return content

            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        text_parts.append(block)
                combined = "\n".join(t for t in text_parts if t.strip())
                if combined:
                    return combined

        if isinstance(msg, dict) and msg.get("role") == "assistant":
            content = msg.get("content", "")
            if content and isinstance(content, str) and content.strip():
                return content

    return "No response generated."


# ---------------------------------------------------------------------------
# CLI entry point (ENTRYPOINT of the Docker image)
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Filter agent — search, extract, and filter web content in a sandbox.",
    )
    parser.add_argument(
        "query",
        help='Search query. Use "-" to read from stdin.',
    )
    parser.add_argument(
        "--instructions",
        default=None,
        help="Additional filtering instructions for the agent.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("FILTER_MODEL", "anthropic:claude-sonnet-4-20250514"),
        help="LLM model identifier (default: anthropic:claude-sonnet-4-20250514).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable debug-level logging (logs to stderr).",
    )

    args = parser.parse_args()

    query = args.query
    if query == "-":
        query = sys.stdin.read(100_000).strip()
    if not query:
        print("Error: empty query", file=sys.stderr)
        sys.exit(1)

    import warnings
    warnings.filterwarnings("ignore")

    try:
        result = run_filter(
            query,
            instructions=args.instructions,
            model=args.model,
            verbose=args.verbose,
        )
        print(result["output"])
    except KeyboardInterrupt:
        sys.exit(130)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        _log.exception("Unhandled error")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
