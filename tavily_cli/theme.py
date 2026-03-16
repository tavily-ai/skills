"""Tavily CLI theme — consistent branding, colors, and spinner helpers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from rich.console import Console
from rich.status import Status

# Brand colors — from tavily.com
AQUA = "#5CD9E6"
PINK = "#FAA2FB"
YELLOW = "#FFC769"
PURPLE = "#8385F9"
GREEN = "#9BC0AE"

BRAND = GREEN       # primary brand accent
ACCENT = AQUA       # secondary accent (headings, highlights)
SUCCESS = GREEN
WARN = YELLOW
ERROR = PINK
DIM = "dim"

console = Console()
err_console = Console(stderr=True)

LOGO = """\
[#5CD9E6]   _              _ _       [/#5CD9E6]
[#FAA2FB]  | |_ __ ___   _(_) |_   _ [/#FAA2FB]
[#FFC769]  | __/ _` \\ \\ / / | | | | |[/#FFC769]
[#8385F9]  | || (_| |\\ V /| | | |_| |[/#8385F9]
[#9BC0AE]   \\__\\__,_| \\_/ |_|_|\\__, |[/#9BC0AE]
[dim]                       |___/ [/dim]"""

LOGO_COMPACT = "[#9BC0AE bold]tavily[/#9BC0AE bold]"


@contextmanager
def spinner(message: str, *, json_mode: bool = False) -> Generator[None, None, None]:
    """Show a live spinner on stderr while work is in progress.

    In json_mode the spinner is suppressed so stdout stays clean.
    """
    if json_mode:
        yield
        return

    with err_console.status(f"[{BRAND}]{message}[/{BRAND}]", spinner="dots") as _status:
        yield
