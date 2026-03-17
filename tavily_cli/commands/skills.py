"""tvly skills — manage Tavily agent skills via npx."""

from __future__ import annotations

import shutil
import subprocess

import click


SKILLS_REPO = "https://github.com/tavily-ai/skills"


@click.group()
def skills() -> None:
    """Manage Tavily agent skills for Claude Code, Cursor, and other AI agents."""


@skills.command(
    context_settings={"ignore_unknown_options": True},
)
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def install(extra_args: tuple[str, ...]) -> None:
    """Install Tavily agent skills into your project.

    Runs: npx skills add https://github.com/tavily-ai/skills

    Any extra flags are forwarded to `npx skills`, for example:

    \b
        tvly skills install --global              Install skills globally
        tvly skills install --skill tavily-search  Install a specific skill
    """
    from tavily_cli.theme import err_console

    if not shutil.which("npx"):
        err_console.print()
        err_console.print("  [#FAA2FB]> npx not found.[/#FAA2FB]")
        err_console.print()
        err_console.print("  Install Node.js to get npx: [link=https://nodejs.org]nodejs.org[/link]")
        err_console.print()
        raise SystemExit(1)

    cmd = ["npx", "-y", "skills", "add", SKILLS_REPO, *extra_args]
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)
