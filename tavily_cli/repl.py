"""Interactive REPL — gives tvly a clean, chat-like shell."""

from __future__ import annotations

import os
import readline  # noqa: F401 — enables arrow-key history in input()
import shlex
import sys

import click
from rich.console import Console
from rich.rule import Rule
from rich.text import Text

from tavily_cli import __version__
from tavily_cli.config import get_api_key
from tavily_cli.theme import LOGO


err_console = Console(stderr=True)

# Commands that the REPL recognises (mapped by the CLI group).
_REPL_COMMANDS = {"search", "extract", "crawl", "map", "research", "login", "logout", "auth", "skills"}


def _print_banner() -> None:
    """Print the branded welcome banner inside the REPL."""
    key = get_api_key()

    err_console.print(LOGO)
    err_console.print(f"  [dim]v{__version__}[/dim]")
    err_console.print()

    if key:
        from tavily_cli.cli import _auth_source
        source = _auth_source(key)
        err_console.print(f"  [#9BC0AE]>[/#9BC0AE] Authenticated via {source}")
    else:
        err_console.print(f"  [#FAA2FB]>[/#FAA2FB] Not authenticated")
        err_console.print(f"    Type [#9BC0AE]login[/#9BC0AE] to authenticate.")

    err_console.print()

    tips = Text()
    tips.append("  Tips: ", style="bold")
    tips.append("search ", style="#9BC0AE")
    tips.append('"query"', style="dim")
    tips.append("  |  ", style="dim")
    tips.append("extract ", style="#9BC0AE")
    tips.append("<url>", style="dim")
    tips.append("  |  ", style="dim")
    tips.append("research ", style="#9BC0AE")
    tips.append('"topic"', style="dim")
    tips.append("  |  ", style="dim")
    tips.append("skills install", style="#9BC0AE")
    tips.append("  |  ", style="dim")
    tips.append("help", style="#9BC0AE")
    tips.append("  |  ", style="dim")
    tips.append("exit", style="#9BC0AE")
    err_console.print(tips)
    err_console.print()


def _print_help() -> None:
    """Print REPL help."""
    err_console.print()
    cmds = Text()
    cmds.append("  Commands\n\n", style="bold")
    cmds.append('    search "your query"', style="#9BC0AE")
    cmds.append("            Web search\n")
    cmds.append("    extract <url>", style="#9BC0AE")
    cmds.append("                  Extract content\n")
    cmds.append("    crawl <url>", style="#9BC0AE")
    cmds.append("                    Crawl a website\n")
    cmds.append("    map <url>", style="#9BC0AE")
    cmds.append("                      Discover URLs\n")
    cmds.append('    research "topic"', style="#9BC0AE")
    cmds.append("              Deep research\n")
    cmds.append("    login", style="#9BC0AE")
    cmds.append("                         Authenticate\n")
    cmds.append("    logout", style="#9BC0AE")
    cmds.append("                        Clear credentials\n")
    cmds.append("    auth", style="#9BC0AE")
    cmds.append("                          Auth status\n")
    cmds.append("    skills install", style="#9BC0AE")
    cmds.append("                  Install agent skills\n")
    cmds.append("    exit / quit / Ctrl+C", style="#9BC0AE")
    cmds.append("          Leave\n")
    err_console.print(cmds)


def _prompt() -> str:
    """Print the separator + prompt and read input."""
    err_console.print(Rule(style="dim"))
    try:
        # \001 and \002 tell readline to ignore non-printable chars for cursor math.
        return input("\001\033[38;2;92;217;230m\002\u276f\001\033[0m\002  ")
    except EOFError:
        return "exit"


def run_repl() -> None:
    """Enter the interactive REPL loop."""
    err_console.print()

    _print_banner()

    while True:
        try:
            line = _prompt()
        except KeyboardInterrupt:
            err_console.print()
            err_console.print("  [dim]Goodbye![/dim]")
            err_console.print()
            break

        line = line.strip()
        if not line:
            continue

        if line in ("exit", "quit", "q"):
            err_console.print()
            err_console.print("  [dim]Goodbye![/dim]")
            err_console.print()
            break

        if line in ("help", "?"):
            _print_help()
            continue

        # Parse the line into args, dispatch through the CLI group.
        try:
            args = shlex.split(line)
        except ValueError as e:
            err_console.print(f"  [#FAA2FB]Parse error:[/#FAA2FB] {e}")
            continue

        # Strip leading "tvly" if user typed it out of habit.
        if args and args[0] == "tvly":
            args = args[1:]

        if not args:
            continue

        # Dispatch via Click — invoke the CLI group with standalone_mode=False
        # so exceptions are caught and don't kill the REPL.
        from tavily_cli.cli import cli
        err_console.print()
        try:
            cli(args, standalone_mode=False)
        except SystemExit:
            # Commands raise SystemExit on error — just continue the REPL.
            pass
        except KeyboardInterrupt:
            # User pressed Ctrl+C to cancel a running command — just return to prompt.
            err_console.print()
            err_console.print("  [dim]Cancelled.[/dim]")
        except click.exceptions.UsageError as e:
            err_console.print(f"  [#FAA2FB]>[/#FAA2FB] {e.format_message()}")
        except Exception as e:
            err_console.print(f"  [#FAA2FB]> Error:[/#FAA2FB] {e}")

        err_console.print()
