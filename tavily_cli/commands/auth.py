"""Authentication commands: login, logout, auth status."""

from __future__ import annotations

import click

from tavily_cli.config import (
    CONFIG_FILE,
    MCP_AUTH_DIR,
    clear_credentials,
    get_api_key,
    save_api_key,
)


def _clear_stale_mcp_state() -> None:
    """Remove stale mcp-remote client registrations so OAuth can re-register fresh."""
    if not MCP_AUTH_DIR.is_dir():
        return
    for client_file in MCP_AUTH_DIR.rglob("*_client_info.json"):
        try:
            client_file.unlink()
        except OSError:
            pass
    for token_file in MCP_AUTH_DIR.rglob("*_tokens.json"):
        try:
            token_file.unlink()
        except OSError:
            pass


@click.command()
@click.option("--api-key", default=None, help="Tavily API key (tvly-...). If omitted, opens browser for OAuth.")
def login(api_key: str | None) -> None:
    """Authenticate with Tavily. Stores credentials for future use."""
    from tavily_cli.theme import console, err_console

    if api_key:
        save_api_key(api_key)
        _print_login_success("API key", f"Saved to {CONFIG_FILE}")
        return

    # OAuth flow via mcp-remote
    import subprocess
    import time

    from tavily_cli.config import _get_mcp_token

    # Clear stale client registrations that cause "client ID not found" errors
    _clear_stale_mcp_state()

    token = None
    with err_console.status("[#5CD9E6]Waiting for browser authentication...[/#5CD9E6]", spinner="dots") as live:
        proc = subprocess.Popen(
            ["npx", "-y", "mcp-remote", "https://mcp.tavily.com/mcp"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        timeout = 120
        elapsed = 0
        try:
            while elapsed < timeout:
                time.sleep(3)
                elapsed += 3
                live.update(f"[#5CD9E6]Waiting for browser authentication... {elapsed}s[/#5CD9E6]")
                token = _get_mcp_token()
                if token:
                    break
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    if token:
        _print_login_success("OAuth", "Token stored in ~/.mcp-auth/")
    else:
        err_console.print()
        err_console.print("  [#FAA2FB]> Authentication timed out.[/#FAA2FB]")
        err_console.print()
        err_console.print("  If you don't have an account, sign up at [link=https://tavily.com]tavily.com[/link]")
        err_console.print("  Or use an API key:")
        err_console.print("    [#9BC0AE]tvly login --api-key tvly-YOUR_KEY[/#9BC0AE]")
        err_console.print()
        raise SystemExit(3)


def _print_login_success(method: str, detail: str) -> None:
    """Print a branded success screen after login."""
    from rich.text import Text

    from tavily_cli.theme import LOGO, console

    console.print()
    console.print(LOGO)
    console.print()
    console.print(f"  [#9BC0AE]> Authenticated via {method}[/#9BC0AE]")
    console.print(f"    [dim]{detail}[/dim]")
    console.print()

    hints = Text()
    hints.append("  Get started\n\n", style="bold")
    hints.append("    tvly search ", style="#9BC0AE")
    hints.append('"your first query"', style="dim")
    hints.append("\n")
    hints.append("    tvly extract ", style="#9BC0AE")
    hints.append("<url>", style="dim")
    hints.append("\n")
    hints.append("    tvly crawl ", style="#9BC0AE")
    hints.append("<url>", style="dim")
    hints.append("\n")
    hints.append("    tvly map ", style="#9BC0AE")
    hints.append("<url>", style="dim")
    hints.append("\n")
    hints.append("    tvly research ", style="#9BC0AE")
    hints.append('"deep dive topic"', style="dim")
    hints.append("\n")
    hints.append("    tvly skills install", style="#9BC0AE")
    hints.append("\n")
    console.print(hints)

    _prompt_skills_install()


def _prompt_skills_install() -> None:
    """Ask the user if they'd like to install Tavily agent skills."""
    import shutil

    from tavily_cli.theme import console

    if not shutil.which("npx"):
        return

    if not click.confirm("  Install Tavily agent skills? (for Claude Code, Cursor, etc.)", default=True):
        console.print()
        console.print("  [dim]You can install later with:[/dim] [#9BC0AE]tvly skills install[/#9BC0AE]")
        console.print()
        return

    console.print()
    from tavily_cli.commands.skills import run_skills_install
    run_skills_install()


@click.command()
def logout() -> None:
    """Clear stored Tavily credentials."""
    from tavily_cli.theme import err_console

    clear_credentials()
    err_console.print("  [dim]Credentials cleared.[/dim]")
    err_console.print("  Run [#9BC0AE]tvly login[/#9BC0AE] to authenticate again.")


@click.command("auth")
@click.option("--json", "json_flag", is_flag=True, default=False, help="Output as JSON.")
@click.pass_context
def auth_status(ctx: click.Context, json_flag: bool) -> None:
    """Check authentication status."""
    import json as json_mod
    import os

    from tavily_cli.config import is_oauth_token
    from tavily_cli.theme import console

    json_mode = json_flag
    if not json_mode and ctx.parent and ctx.parent.obj:
        json_mode = ctx.parent.obj.get("json_output", False)

    key = get_api_key()
    source = None
    if key:
        if os.environ.get("TAVILY_API_KEY"):
            source = "TAVILY_API_KEY environment variable"
        elif is_oauth_token(key):
            source = "OAuth (~/.mcp-auth/)"
        elif CONFIG_FILE.exists():
            source = f"config file ({CONFIG_FILE})"

    if json_mode:
        click.echo(json_mod.dumps({
            "authenticated": key is not None,
            "source": source,
        }))
    else:
        console.print()
        if key:
            masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
            console.print(f"  [#9BC0AE]>[/#9BC0AE] Authenticated via {source}")
            console.print(f"    [dim]Key: {masked}[/dim]")
        else:
            console.print(f"  [#FAA2FB]>[/#FAA2FB] Not authenticated")
            console.print()
            console.print("  Run [#9BC0AE]tvly login[/#9BC0AE] to authenticate.")
        console.print()
