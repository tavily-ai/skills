"""API key storage and retrieval for the Tavily CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".tavily"
CONFIG_FILE = CONFIG_DIR / "config.json"

MCP_AUTH_DIR = Path.home() / ".mcp-auth"


def _read_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _write_config(data: dict) -> None:
    old_umask = os.umask(0o077)  # ensure new files are owner-only from creation, sets the new umask to 0o077 and returns whatever the previous umask was.
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_DIR.chmod(0o700)
        CONFIG_FILE.write_text(json.dumps(data, indent=2) + "\n")
        CONFIG_FILE.chmod(0o600)
    finally:
        os.umask(old_umask)


def save_api_key(api_key: str) -> None:
    config = _read_config()
    config["api_key"] = api_key
    _write_config(config)


def clear_credentials() -> None:
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


def _decode_jwt_payload(token: str) -> dict | None:
    """Decode a JWT payload without verification (for issuer/expiry checks only)."""
    import base64

    parts = token.split(".")
    if len(parts) != 3:
        return None
    payload = parts[1]
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += "=" * padding
    try:
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return None


def _is_valid_tavily_token(token: str) -> bool:
    """Check if a JWT is a valid, non-expired Tavily token."""
    import time

    payload = _decode_jwt_payload(token)
    if not payload:
        return False
    if payload.get("iss") != "https://mcp.tavily.com/":
        return False
    exp = payload.get("exp")
    if exp is not None:
        if time.time() >= exp:
            return False
    return True


def _get_mcp_token() -> str | None:
    """Find a valid Tavily OAuth token from ~/.mcp-auth/."""
    if not MCP_AUTH_DIR.is_dir():
        return None
    for token_file in MCP_AUTH_DIR.rglob("*_tokens.json"):
        try:
            data = json.loads(token_file.read_text())
            token = data.get("access_token")
            if token and _is_valid_tavily_token(token):
                return token
        except (json.JSONDecodeError, OSError):
            continue
    return None


def get_api_key() -> str | None:
    """Resolve the API key with precedence: env var > config file > MCP OAuth token."""
    key = os.environ.get("TAVILY_API_KEY")
    if key:
        return key

    config = _read_config()
    key = config.get("api_key")
    if key:
        return key

    return _get_mcp_token()


def is_oauth_token(key: str) -> bool:
    """Check if a credential is an MCP OAuth JWT (vs a tvly-* API key)."""
    return not key.startswith("tvly-") and _decode_jwt_payload(key) is not None


def get_api_key_or_exit() -> str:
    """Get the API key or print an error and exit."""
    import sys

    key = get_api_key()
    if not key:
        from rich.console import Console
        console = Console(stderr=True)
        console.print("  [#FAA2FB]> Error:[/#FAA2FB] No Tavily API key found.")
        console.print()
        console.print("  Authenticate using one of:")
        console.print("    [#9BC0AE]tvly login[/#9BC0AE]")
        console.print("    [#9BC0AE]tvly login --api-key tvly-YOUR_KEY[/#9BC0AE]")
        console.print("    [dim]export TAVILY_API_KEY=tvly-YOUR_KEY[/dim]")
        console.print()
        console.print("  Get a key at [link=https://tavily.com]tavily.com[/link]")
        sys.exit(3)
    return key


def get_client():
    """Return the appropriate Tavily client (SDK or MCP) based on credential type."""
    key = get_api_key_or_exit()
    if is_oauth_token(key):
        from tavily_cli.mcp_client import McpTavilyClient
        return McpTavilyClient(api_key=key)
    else:
        from tavily import TavilyClient
        return TavilyClient(api_key=key)
