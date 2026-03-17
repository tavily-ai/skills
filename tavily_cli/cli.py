"""Main CLI entry point — wires all commands into the `tvly` group."""

from __future__ import annotations

import click

from tavily_cli import __version__
from tavily_cli.commands.auth import auth_status, login, logout
from tavily_cli.commands.crawl import crawl
from tavily_cli.commands.extract import extract
from tavily_cli.commands.map_cmd import map_urls
from tavily_cli.commands.research import research
from tavily_cli.commands.search import search
from tavily_cli.commands.skills import skills


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, default=False, help="Show version and exit.")
@click.option("--status", "show_status", is_flag=True, default=False, help="Show version and auth status.")
@click.option("--json", "json_output", is_flag=True, default=False, help="Output as JSON (for agents and scripts).")
@click.pass_context
def cli(ctx: click.Context, version: bool, show_status: bool, json_output: bool) -> None:
    """Tavily CLI — search, extract, crawl, map, and research from the command line.

    Authenticate with: tvly login --api-key tvly-YOUR_KEY
    Or set TAVILY_API_KEY environment variable.
    """
    ctx.ensure_object(dict)
    ctx.obj["json_output"] = json_output

    if version:
        if json_output:
            import json
            click.echo(json.dumps({"version": __version__}))
        else:
            click.echo(f"tavily-cli {__version__}")
        ctx.exit(0)
        return

    if show_status:
        _print_status(json_output)
        ctx.exit(0)
        return

    if ctx.invoked_subcommand is None:
        from tavily_cli.repl import run_repl
        run_repl()
        ctx.exit(0)


def _print_welcome() -> None:
    """Show a branded welcome screen with quick-start hints."""
    from rich.console import Console
    from rich.text import Text

    from tavily_cli.config import get_api_key
    from tavily_cli.theme import LOGO

    console = Console(stderr=True)
    key = get_api_key()

    # Logo + version
    console.print()
    console.print(LOGO)
    console.print(f"  [dim]v{__version__}[/dim]")
    console.print()

    # Auth status
    if key:
        source = _auth_source(key)
        console.print(f"  [#9BC0AE]>[/#9BC0AE] Authenticated via {source}")
    else:
        console.print(f"  [#FAA2FB]>[/#FAA2FB] Not authenticated")
        console.print(f"    [dim]Run:[/dim] tvly login")

    console.print()

    # Quick-start commands
    commands = Text()
    commands.append("  Commands\n\n", style="bold")
    commands.append("    tvly search ", style="#9BC0AE")
    commands.append('"your query"', style="dim")
    commands.append("            Web search\n")
    commands.append("    tvly extract ", style="#9BC0AE")
    commands.append("<url>", style="dim")
    commands.append("                  Extract content\n")
    commands.append("    tvly crawl ", style="#9BC0AE")
    commands.append("<url>", style="dim")
    commands.append("                    Crawl a website\n")
    commands.append("    tvly map ", style="#9BC0AE")
    commands.append("<url>", style="dim")
    commands.append("                      Discover URLs\n")
    commands.append("    tvly research ", style="#9BC0AE")
    commands.append('"your query"', style="dim")
    commands.append("          Deep research\n")
    commands.append("    tvly skills", style="#9BC0AE")
    commands.append("                          Install agent skills\n")

    console.print(commands)
    console.print("  [dim]Add --json to any command for machine-readable output.[/dim]")
    console.print("  [dim]Add --help to any command for full options.[/dim]")
    console.print()


def _auth_source(key: str) -> str:
    """Describe how the user is authenticated."""
    import os
    from tavily_cli.config import is_oauth_token

    if os.environ.get("TAVILY_API_KEY"):
        return "TAVILY_API_KEY"
    if is_oauth_token(key):
        return "OAuth (tvly login)"
    return "API key"


def _print_status(json_output: bool) -> None:
    """Show version + auth status."""
    import json

    from tavily_cli.config import get_api_key

    key = get_api_key()
    authenticated = key is not None

    if json_output:
        click.echo(json.dumps({
            "version": __version__,
            "authenticated": authenticated,
        }))
    else:
        from rich.console import Console
        console = Console()
        console.print(f"  [bold #9BC0AE]tavily[/bold #9BC0AE] v{__version__}")
        console.print()
        if authenticated:
            source = _auth_source(key)
            console.print(f"  [#9BC0AE]>[/#9BC0AE] Authenticated via {source}")
        else:
            console.print("  [#FAA2FB]>[/#FAA2FB] Not authenticated")
            console.print("    Run: tvly login")


cli.add_command(login)
cli.add_command(logout)
cli.add_command(auth_status)
cli.add_command(search)
cli.add_command(extract)
cli.add_command(crawl)
cli.add_command(map_urls)
cli.add_command(research)
cli.add_command(skills)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
