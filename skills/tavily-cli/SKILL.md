---
name: tavily-cli
description: |
  Set up, authenticate, update, troubleshoot, or choose between Tavily CLI web commands. Use when the user asks about the Tavily CLI, installing Tavily skills, first-time setup, authentication, keyless limits, CLI updates, or which Tavily command to use. For an ordinary web task, use the specific search, extract, map, crawl, research, or dynamic-search skill instead.
allowed-tools: Bash(tvly *)
---

# Tavily CLI

Web search, content extraction, site crawling, URL discovery, and deep research. Returns JSON optimized for LLM consumption.

Requires `tavily-cli`. Search and extract support capped keyless access; map,
crawl, and research require authentication.

Run `tvly --help` or `tvly <command> --help` for full option details.

## Setup

If `tvly` is not installed:

```bash
curl -fsSL https://cli.tavily.com/install.sh | bash
```

Or manually: `uv tool install tavily-cli` / `pip install tavily-cli`

On a fresh interactive desktop install, the installer starts guided setup
automatically. Otherwise run:

```bash
tvly init

# Prefer to open the sign-in link yourself
tvly init --no-browser
```

`tvly init` reuses an existing credential, installs or updates the Tavily
skills bundled with that CLI release, and verifies a live search. Run `tvly
update` first when refreshing bundled skills. Use `tvly init --skip-auth` to
keep keyless mode, or `tvly init --skip-skills` when the skills are already
installed and only authentication or verification is needed.

Search and extract can run immediately without authentication, subject to a
keyless rate-limit cap. Map, crawl, and research require authentication. Check
the current state only when needed with `tvly --status --json`.

For authentication without full setup, use `tvly login`, `tvly login
--no-browser`, `tvly login --api-key tvly-YOUR_KEY`, or `TAVILY_API_KEY`.

Browser-based OAuth is the preferred interactive sign-in method. `--no-browser`
simply prints the sign-in link instead of opening it automatically; the flow
still returns to a localhost callback on the machine running `tvly`. In remote
sessions, make sure that callback is reachable (SSH may require port
forwarding). In an unattended agent or CI environment, leave authentication to
the user or use a securely provided `TAVILY_API_KEY`, then resume the original
command.

Keep an existing installation current with `tvly update --check` and `tvly
update`.

## Workflow

Follow this escalation pattern — start simple, escalate when needed:

1. **Search** — No specific URL. Find pages, answer questions, discover sources.
2. **Extract** — Have a URL. Pull its content directly.
3. **Map** — Large site, need to find the right page. Discover URLs first.
4. **Crawl** — Need bulk content from an entire site section.
5. **Research** — Need comprehensive, multi-source analysis with citations.

| Need | Command | When |
|------|---------|------|
| Find pages on a topic | `tvly search` | No specific URL yet |
| Get a page's content | `tvly extract` | Have a URL |
| Find URLs within a site | `tvly map` | Need to locate a specific subpage |
| Bulk extract a site section | `tvly crawl` | Need many pages (e.g., all /docs/) |
| Deep research with citations | `tvly research` | Need multi-source synthesis |

For detailed command reference, use the individual skill for each command (e.g., `tavily-search`, `tavily-crawl`) or run `tvly <command> --help`.

Run `tvly` without a subcommand for the interactive REPL.

## Output

Search, extract, crawl, map, and research support `--json` for structured output.
Result-producing commands support `-o` to save the JSON response; crawl also
supports `--output-dir` for one Markdown file per page. Setup, authentication,
status, and update commands expose `--json` where documented but do not support
`-o`.

```bash
tvly search "react hooks" --json -o results.json
tvly extract "https://example.com/docs" -o docs.json
tvly crawl "https://docs.example.com" --output-dir ./docs/
```

## Tips

- **Always quote URLs** — shell interprets `?` and `&` as special characters.
- **Use `--json` for agentic workflows** when the selected command exposes it.
- **Read from stdin with `-`** — `echo "query" | tvly search -`
- **Exit codes**: 0 = success, 1 = setup/update failure, 2 = bad input, 3 = auth error, 4 = API or live-verification error.
