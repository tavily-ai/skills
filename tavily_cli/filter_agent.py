#!/usr/bin/env python3
"""Filter agent — runs entirely inside a Docker container.

Receives a query (+ optional instructions) via CLI args or stdin.
Has access to:
  - Persistent bash/Python shell (via ShellToolMiddleware + HostExecutionPolicy)
  - tavily_search() and tavily_extract() callable from within Python scripts

The agent writes Python code that calls search/extract, processes the raw
results programmatically, and prints only filtered signal to stdout.
Raw content never enters the LLM's context window — it stays in the code
execution environment.

This mirrors Anthropic's Dynamic Filtering / Programmatic Tool Calling pattern:
  LLM writes code → code calls web_search() → code filters results → print()

Usage:
    python filter_agent.py "query" [--instructions "..."] [--model "..."]
    echo "query" | python filter_agent.py - [--instructions "..."]
"""

from __future__ import annotations

import argparse
import os
import sys

from langchain.agents import create_agent
from langchain.agents.middleware import (
    HostExecutionPolicy,
    ModelCallLimitMiddleware,
    ShellToolMiddleware,
)


# ---------------------------------------------------------------------------
# Helper module that gets written into the container at /workspace/tavily_tools.py
# so the agent's Python scripts can `from tavily_tools import search, extract`
# ---------------------------------------------------------------------------

TAVILY_TOOLS_MODULE = '''\
"""Tavily helper functions — importable from agent-written Python scripts.

Usage in agent code:
    from tavily_tools import search, extract

    results = search("your query", max_results=5)
    for r in results:
        print(r["title"], r["url"])
        print(r["raw_content"][:500])  # filter in code, print only what matters

    pages = extract(["https://example.com"])
    for p in pages:
        print(p["url"], len(p["raw_content"]))
"""

import json
import os
from tavily import TavilyClient

_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def search(
    query: str,
    *,
    max_results: int = 5,
    search_depth: str = "advanced",
    topic: str = "general",
    include_raw_content: str = "markdown",
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    time_range: str | None = None,
) -> list[dict]:
    """Search the web via Tavily. Returns list of result dicts.

    Each result has: title, url, content (snippet), score, raw_content (full page).
    """
    kwargs = {
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "topic": topic,
        "include_raw_content": include_raw_content,
    }
    if include_domains:
        kwargs["include_domains"] = include_domains
    if exclude_domains:
        kwargs["exclude_domains"] = exclude_domains
    if time_range:
        kwargs["time_range"] = time_range

    response = _client.search(**kwargs)
    return response.get("results", [])


def extract(
    urls: list[str],
    *,
    extract_depth: str = "basic",
    format: str = "markdown",
    include_images: bool = False,
) -> list[dict]:
    """Extract clean content from URLs via Tavily. Returns list of result dicts.

    Each result has: url, raw_content.
    """
    response = _client.extract(
        urls=urls,
        extract_depth=extract_depth,
        format=format,
        include_images=include_images,
    )
    return response.get("results", [])
'''


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a web research agent with dynamic filtering capabilities. Your job is
to find, fetch, and **programmatically filter** web content to extract only the
information that answers the user's query.

## Your tool

You have ONE tool: a persistent bash/Python **shell** running in a container.

Inside the shell, you can write and run Python scripts that call:
- `from tavily_tools import search, extract`
- `search(query, max_results=5, ...)` → returns a list of dicts with keys:
  title, url, content (snippet), score, raw_content (full markdown page text)
- `extract(urls, ...)` → returns a list of dicts with keys: url, raw_content

## Your workflow

1. **Search**: Write a Python script that calls `search()` with a good query.
2. **Inspect**: In the SAME script, iterate over results and print a compact
   summary — titles, URLs, and short content previews. Do NOT print raw_content
   in full. Just check what you got.
3. **Filter with code**: Write a Python script that:
   - Calls `search()` or `extract()` to get raw content
   - Uses string ops, regex, or BeautifulSoup to extract relevant passages
   - Cross-references across sources if needed
   - Prints ONLY the filtered, relevant information
4. **Iterate**: If the first search didn't cover everything, do more targeted
   searches and filter those too.
5. **Synthesize**: After all filtering is done, provide a clean final answer
   with citations.

## Critical rules

- **ALL data retrieval and filtering happens in Python code via the shell tool.**
- Never ask for search results as a separate tool call. Write code that calls
  `search()` and processes the results in the same script.
- The raw_content can be 50K+ chars per page. NEVER print it in full. Always
  filter in code and print only relevant excerpts.
- Write scripts to /tmp/ for anything longer than ~5 lines:
  ```
  cat > /tmp/filter.py << 'PYEOF'
  from tavily_tools import search
  results = search("your query", max_results=8)
  for r in results:
      # filter logic here
      print(relevant_excerpt)
  PYEOF
  python3 /tmp/filter.py
  ```
- Available packages: tavily-python, beautifulsoup4, lxml, json, re, csv.
- Keep your final output focused and concise — high signal, zero noise.
- Always cite sources as [Title](url).
"""


# ---------------------------------------------------------------------------
# Agent construction + execution
# ---------------------------------------------------------------------------

def _write_tavily_tools_module():
    """Write the tavily_tools.py helper into /workspace so scripts can import it."""
    with open("/workspace/tavily_tools.py", "w") as f:
        f.write(TAVILY_TOOLS_MODULE)


def build_agent(model: str):
    """Build the filter agent with shell access only."""
    # Forward API keys into the shell session so agent-written scripts can use them
    shell_env = {}
    for var in ("TAVILY_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        val = os.environ.get(var)
        if val:
            shell_env[var] = val

    return create_agent(
        model=model,
        tools=[],  # No separate tools — everything goes through the shell
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            ShellToolMiddleware(
                workspace_root="/workspace",
                execution_policy=HostExecutionPolicy(
                    command_timeout=60.0,
                    max_output_lines=500,
                ),
                startup_commands=[
                    "export PYTHONDONTWRITEBYTECODE=1",
                    "export PYTHONPATH=/workspace:$PYTHONPATH",
                ],
                env=shell_env,
            ),
            ModelCallLimitMiddleware(run_limit=25, exit_behavior="end"),
        ],
    )


def run_filter(
    query: str,
    *,
    instructions: str | None = None,
    model: str = "anthropic:claude-sonnet-4-20250514",
) -> str:
    """Run the filter agent and return the final response text."""
    # Make tavily_tools importable from agent scripts
    _write_tavily_tools_module()

    agent = build_agent(model)

    # Build the user message
    user_message = query
    if instructions:
        user_message = f"{query}\n\nAdditional filtering instructions: {instructions}"

    result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})

    # Extract the final AI message
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "ai" and msg.content:
            return msg.content
        if isinstance(msg, dict) and msg.get("role") == "assistant":
            return msg.get("content", "")

    return "No response generated."


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Filter agent — search, extract, and filter web content."
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

    args = parser.parse_args()

    query = args.query
    if query == "-":
        query = sys.stdin.read(100_000).strip()
    if not query:
        print("Error: empty query", file=sys.stderr)
        sys.exit(1)

    # Suppress langchain warnings on stderr
    import warnings
    warnings.filterwarnings("ignore")

    try:
        output = run_filter(
            query,
            instructions=args.instructions,
            model=args.model,
        )
        print(output)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
