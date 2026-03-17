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

    Runs: npx -y skills add https://github.com/tavily-ai/skills

    All flags after `install` are forwarded directly to `npx skills add`.
    Common options:

    \b
        -g, --global             Install globally (user-level)
        -a, --agent <agents>     Target specific agents (e.g. claude-code cursor)
        -s, --skill <skills>     Install specific skills (e.g. tavily-search)
        -y, --yes                Skip confirmation prompts
        --all                    All skills, all agents, no prompts
        --full-depth             Search all subdirectories
        --copy                   Copy files instead of symlinking

    \b
    Examples:
        tvly skills install                        Install interactively
        tvly skills install --global               Install globally
        tvly skills install --skill tavily-search  Install a specific skill
        tvly skills install --all                  Install everything, no prompts

    Full docs: https://github.com/vercel-labs/skills
    """
    from tavily_cli.theme import err_console

    if not shutil.which("npx"):
        err_console.print()
        err_console.print("  [#FAA2FB]> npx not found.[/#FAA2FB]")
        err_console.print()
        err_console.print("  Install Node.js to get npx: [link=https://nodejs.org]nodejs.org[/link]")
        err_console.print()
        raise SystemExit(1)

    cmd = ["npx", "-y", "skills", "add", SKILLS_REPO, "--yes", "--full-depth", "--global", *extra_args]
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)
