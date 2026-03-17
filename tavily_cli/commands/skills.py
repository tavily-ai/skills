"""tvly skills — install Tavily agent skills via npx."""

from __future__ import annotations

import shutil
import subprocess

import click


SKILLS_REPO = "https://github.com/tavily-ai/skills"


@click.command(
    context_settings={"ignore_unknown_options": True},
)
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def skills(extra_args: tuple[str, ...]) -> None:
    """Install Tavily agent skills for Claude Code, Cursor, and other AI agents.

    Runs: npx skills add https://github.com/tavily-ai/skills

    Any extra flags are forwarded to `npx skills`, for example:

    \b
        tvly skills --global          Install skills globally
        tvly skills --skill tavily-search   Install a specific skill
    """
    from tavily_cli.theme import err_console

    if not shutil.which("npx"):
        err_console.print()
        err_console.print("  [#FAA2FB]> npx not found.[/#FAA2FB]")
        err_console.print()
        err_console.print("  Install Node.js to get npx: [link=https://nodejs.org]nodejs.org[/link]")
        err_console.print()
        raise SystemExit(1)

    cmd = ["npx", "skills", "add", SKILLS_REPO, *extra_args]
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)
