"""Shared CLI utilities."""

from __future__ import annotations

import json
import functools

import click


class TavilyAPIError(Exception):
    """Structured error from the Tavily API."""

    def __init__(self, message: str, *, status: int | None = None, docs: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.docs = docs


def json_option(func):
    """Add --json flag to a command and resolve from parent context if not set."""
    @click.option("--json", "json_output", is_flag=True, default=False, help="Output as JSON.")
    @functools.wraps(func)
    def wrapper(*args, json_output: bool = False, **kwargs):
        ctx = click.get_current_context()
        if not json_output:
            json_output = (ctx.parent and ctx.parent.obj or {}).get("json_output", False)
        kwargs["json_output"] = json_output
        return func(*args, **kwargs)
    return wrapper


# Status codes that represent usage/plan limits rather than real errors.
_LIMIT_STATUSES = {429, 432}


def handle_api_error(e: Exception, json_mode: bool) -> None:
    """Print an API error and exit."""
    if json_mode:
        click.echo(json.dumps({"error": str(e)}))
        raise SystemExit(4)

    from tavily_cli.theme import err_console

    if isinstance(e, TavilyAPIError) and e.status in _LIMIT_STATUSES:
        err_console.print()
        err_console.print(f"  [#FFC769]>[/#FFC769] {e}")
        err_console.print()
        err_console.print("  [dim]Upgrade your plan at[/dim] [#9BC0AE link=https://tavily.com]tavily.com[/#9BC0AE link]")
        if e.docs:
            err_console.print(f"  [dim]Docs:[/dim] [dim link={e.docs}]{e.docs}[/dim link]")
        err_console.print()
        raise SystemExit(3)

    err_console.print(f"  [#FAA2FB]> Error:[/#FAA2FB] {e}")
    raise SystemExit(4)
