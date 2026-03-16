"""MCP client for Tavily — calls the MCP endpoint with OAuth tokens.

Used when authenticating via OAuth (JWT tokens). The tavily-python SDK
only works with tvly-* API keys against api.tavily.com, so OAuth tokens
need to go through the MCP JSON-RPC endpoint at mcp.tavily.com/mcp,
exactly like the bash scripts in skills/ do.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

MCP_URL = "https://mcp.tavily.com/mcp"


def _raise_if_api_error(parsed: dict) -> None:
    """Raise TavilyAPIError if the parsed response contains an error."""
    if not isinstance(parsed, dict) or "error" not in parsed:
        return
    from tavily_cli.common import TavilyAPIError
    detail = parsed.get("detail", {})
    msg = detail.get("error", parsed["error"]) if isinstance(detail, dict) else parsed["error"]
    raise TavilyAPIError(
        msg,
        status=parsed.get("status"),
        docs=parsed.get("documentation"),
    )


def _call_mcp_tool(token: str, tool_name: str, arguments: dict) -> dict:
    """Call a Tavily MCP tool via JSON-RPC and return the parsed result."""
    request_body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }

    response = httpx.post(
        MCP_URL,
        json=request_body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "x-client-source": "tavily-cli",
        },
        timeout=180.0,
    )
    response.raise_for_status()

    # Parse SSE response: look for lines starting with "data:"
    text = response.text
    for line in text.splitlines():
        if line.startswith("data:"):
            data = json.loads(line[5:])
            if "error" in data:
                raise RuntimeError(data["error"].get("message", str(data["error"])))
            result = data.get("result", {})
            # MCP wraps the response in structuredContent or content[0].text
            structured = result.get("structuredContent")
            if structured:
                parsed = structured if isinstance(structured, dict) else json.loads(structured)
                _raise_if_api_error(parsed)
                return parsed
            content_list = result.get("content", [])
            if content_list:
                text_val = content_list[0].get("text", "")
                try:
                    parsed = json.loads(text_val)
                except (json.JSONDecodeError, TypeError):
                    return {"raw": text_val}
                _raise_if_api_error(parsed)
                return parsed
            return result

    # If no SSE data lines, try parsing entire response as JSON
    try:
        data = json.loads(text)
        if "error" in data:
            raise RuntimeError(data["error"].get("message", str(data["error"])))
        return data.get("result", data)
    except json.JSONDecodeError:
        raise RuntimeError(f"Unexpected MCP response: {text[:500]}")


class McpTavilyClient:
    """Drop-in replacement for TavilyClient that uses the MCP endpoint with OAuth tokens."""

    def __init__(self, api_key: str) -> None:
        self._token = api_key

    def search(self, **kwargs: Any) -> dict:
        return _call_mcp_tool(self._token, "tavily_search", kwargs)

    def extract(self, **kwargs: Any) -> dict:
        return _call_mcp_tool(self._token, "tavily_extract", kwargs)

    def crawl(self, **kwargs: Any) -> dict:
        return _call_mcp_tool(self._token, "tavily_crawl", kwargs)

    def map(self, **kwargs: Any) -> dict:
        return _call_mcp_tool(self._token, "tavily_map", kwargs)

    def research(self, **kwargs: Any) -> dict:
        return _call_mcp_tool(self._token, "tavily_research", kwargs)

    def get_research(self, request_id: str) -> dict:
        return _call_mcp_tool(self._token, "tavily_get_research", {"request_id": request_id})
