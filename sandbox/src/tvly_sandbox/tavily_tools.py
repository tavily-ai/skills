"""Tavily helper functions — importable from agent-written Python scripts.

Usage in agent code running inside the sandbox:

    from tvly_sandbox.tavily_tools import search, extract

    results = search("your query", max_results=5)
    for r in results:
        print(r["title"], r["url"])
        print(r["raw_content"][:500])

All API calls are logged to stderr with timing and result counts.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from typing import Any

from tavily import TavilyClient

# ---------------------------------------------------------------------------
# Logging — goes to stderr so stdout stays clean for filtered output
# ---------------------------------------------------------------------------

_log = logging.getLogger("tvly.tools")

if not _log.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)-7s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    _log.addHandler(_handler)
    _log.setLevel(
        logging.DEBUG if os.environ.get("TVLY_FILTER_VERBOSE") else logging.INFO
    )

# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

_api_key = os.environ.get("TAVILY_API_KEY")
if not _api_key:
    _log.error("TAVILY_API_KEY not set — search() and extract() will fail")
    _client: TavilyClient | None = None
else:
    _client = TavilyClient(api_key=_api_key)


def _require_client() -> TavilyClient:
    if _client is None:
        raise RuntimeError(
            "TAVILY_API_KEY is not set. Cannot call Tavily API."
        )
    return _client


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------


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
) -> list[dict[str, Any]]:
    """Search the web via Tavily. Returns list of result dicts.

    Each result has keys:
        title, url, content (snippet), score, raw_content (full page markdown).

    Args:
        query: The search query string.
        max_results: Maximum number of results (1-20).
        search_depth: One of "basic", "advanced", "fast", "ultra-fast".
        topic: One of "general", "news", "finance".
        include_raw_content: "markdown" or "text" — include full page content.
        include_domains: Only return results from these domains.
        exclude_domains: Exclude results from these domains.
        time_range: One of "day", "week", "month", "year".
    """
    client = _require_client()

    kwargs: dict[str, Any] = {
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

    _log.info("search(%r, max_results=%d, depth=%s)", query, max_results, search_depth)
    t0 = time.monotonic()

    try:
        response = client.search(**kwargs)
    except Exception:
        _log.exception("search() failed for query=%r", query)
        raise

    results = response.get("results", [])
    elapsed = time.monotonic() - t0

    total_chars = sum(len(r.get("raw_content", "") or "") for r in results)
    _log.info(
        "search() → %d results (%s chars raw_content) in %.1fs",
        len(results),
        f"{total_chars:,}",
        elapsed,
    )
    for i, r in enumerate(results):
        _log.debug(
            "  [%d] score=%.2f url=%s title=%s",
            i,
            r.get("score", 0),
            r.get("url", "?"),
            (r.get("title", "?") or "?")[:80],
        )

    return results


# ---------------------------------------------------------------------------
# extract()
# ---------------------------------------------------------------------------


def extract(
    urls: list[str] | str,
    *,
    extract_depth: str = "basic",
    format: str = "markdown",
    include_images: bool = False,
) -> list[dict[str, Any]]:
    """Extract clean content from URLs via Tavily.

    Each result has keys: url, raw_content.

    Args:
        urls: A single URL string or list of URLs (max 20).
        extract_depth: "basic" (default) or "advanced" (for JS-rendered pages).
        format: "markdown" or "text".
        include_images: Whether to include image URLs.
    """
    client = _require_client()

    if isinstance(urls, str):
        urls = [urls]

    _log.info("extract(%d urls, depth=%s)", len(urls), extract_depth)
    for u in urls:
        _log.debug("  url: %s", u)

    t0 = time.monotonic()

    try:
        response = client.extract(
            urls=urls,
            extract_depth=extract_depth,
            format=format,
            include_images=include_images,
        )
    except Exception:
        _log.exception("extract() failed for urls=%r", urls)
        raise

    results = response.get("results", [])
    failed = response.get("failed_results", [])
    elapsed = time.monotonic() - t0

    total_chars = sum(len(r.get("raw_content", "") or "") for r in results)
    _log.info(
        "extract() → %d results, %d failed (%s chars) in %.1fs",
        len(results),
        len(failed),
        f"{total_chars:,}",
        elapsed,
    )
    for f_item in failed:
        _log.warning("  extract failed: %s — %s", f_item.get("url"), f_item.get("error"))

    return results
