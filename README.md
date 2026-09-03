# Tavily Agent Skills

Web search, content extraction, site crawling, URL discovery, and deep research — powered by the Tavily CLI.

## Installation

### Recommended: guided CLI setup

Install the [Tavily CLI](https://github.com/tavily-ai/tavily-cli):

```bash
curl -fsSL https://cli.tavily.com/install.sh | bash
```

On a fresh interactive desktop install, the installer starts `tvly init`
automatically. Otherwise run it after installation:

```bash
tvly init

# Headless or SSH sessions
tvly init --no-browser
```

`tvly init` authenticates, detects Claude Code, Codex, and Cursor, installs
these skills, and verifies a live search. It reuses an existing credential and
is safe to rerun. Skills installed this way are pinned to the CLI release, so
run `tvly update` before `tvly init` when refreshing them.

`tvly search` and `tvly extract` also work without authentication, subject to
a keyless rate-limit cap. Use `tvly init --skip-auth` to keep keyless mode while
installing the skills. `map`, `crawl`, and `research` require authentication.

### Manual skill installation

For other agents, or when you only want to install the skills:

```bash
npx skills add https://github.com/tavily-ai/skills
```

Install the CLI separately if needed:

```bash
uv tool install tavily-cli   # or: pip install tavily-cli
```

Then use `tvly init --skip-skills` for guided authentication and verification,
or `tvly login` when you only need to authenticate.

### Keep the CLI current

```bash
tvly update --check
tvly update
```

## Available Skills

| Skill | Description |
|-------|-------------|
| **[tavily-search](skills/tavily-search/SKILL.md)** | Search the web with LLM-optimized results. Supports domain filtering, time ranges, and multiple search depths. |
| **[tavily-extract](skills/tavily-extract/SKILL.md)** | Extract clean markdown/text content from specific URLs. Handles JS-rendered pages. |
| **[tavily-crawl](skills/tavily-crawl/SKILL.md)** | Crawl websites and extract content from multiple pages. Save as local markdown files. |
| **[tavily-map](skills/tavily-map/SKILL.md)** | Discover all URLs on a website without extracting content. Faster than crawling. |
| **[tavily-research](skills/tavily-research/SKILL.md)** | Comprehensive AI-powered research with citations. Multi-source synthesis in 30-120s. |
| **[tavily-dynamic-search](skills/tavily-dynamic-search/SKILL.md)** | Filter and deduplicate large search or extraction results without flooding agent context. |
| **[tavily-cli](skills/tavily-cli/SKILL.md)** | Overview skill with workflow guide, install/auth instructions. |
| **[tavily-best-practices](skills/tavily-best-practices/SKILL.md)** | Reference docs for building production-ready Tavily integrations. |

## Workflow

Start simple, escalate when needed:

1. **Search** — Find pages on a topic (`tvly search "query" --json`)
2. **Extract** — Get content from a specific URL (`tvly extract "https://..." --json`)
3. **Map** — Discover URLs on a site (`tvly map "https://..." --json`)
4. **Crawl** — Bulk extract from a site section (`tvly crawl "https://..." --output-dir ./docs/`)
5. **Research** — Deep multi-source analysis (`tvly research "topic" --model pro`)
