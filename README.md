# Tavily Agent Skills

Web search, content extraction, site crawling, URL discovery, and deep research — powered by the [Tavily CLI](https://github.com/tavily-ai/tavily-cli).

## Installation

### Install skills

```bash
# Agent skills (Claude Code, Cursor, etc.)
npx skills add https://github.com/tavily-ai/skills

# Claude Code plugin
/plugin marketplace add tavily-ai/skills
/plugin install tavily@tavily-plugins
```

### Install the Tavily CLI

The skills require the Tavily CLI (`tvly`) to be installed:

```bash
# Recommended (isolated install)
uv tool install tavily-cli

# Alternative
pip install tavily-cli
```

### Authenticate

```bash
tvly login --api-key tvly-YOUR_KEY
# or: tvly login                      (opens browser for OAuth)
# or: export TAVILY_API_KEY=tvly-...
```

Get an API key at [tavily.com](https://tavily.com).

## Available Skills

| Skill | Description |
|-------|-------------|
| **[tavily-search](skills/tavily-search/SKILL.md)** | Search the web with LLM-optimized results. Supports domain filtering, time ranges, and multiple search depths. |
| **[tavily-extract](skills/tavily-extract/SKILL.md)** | Extract clean markdown/text content from specific URLs. Handles JS-rendered pages. |
| **[tavily-crawl](skills/tavily-crawl/SKILL.md)** | Crawl websites and extract content from multiple pages. Save as local markdown files. |
| **[tavily-map](skills/tavily-map/SKILL.md)** | Discover all URLs on a website without extracting content. Faster than crawling. |
| **[tavily-research](skills/tavily-research/SKILL.md)** | Comprehensive AI-powered research with citations. Multi-source synthesis in 30-120s. |
| **[tavily-cli](skills/tavily-cli/SKILL.md)** | Overview skill with workflow guide, install/auth instructions. |
| **[tavily-best-practices](skills/tavily-best-practices/SKILL.md)** | Reference docs for building production-ready Tavily integrations. |

## Workflow

Start simple, escalate when needed:

1. **Search** — Find pages on a topic (`tvly search "query" --json`)
2. **Extract** — Get content from a specific URL (`tvly extract "https://..." --json`)
3. **Map** — Discover URLs on a site (`tvly map "https://..." --json`)
4. **Crawl** — Bulk extract from a site section (`tvly crawl "https://..." --output-dir ./docs/`)
5. **Research** — Deep multi-source analysis (`tvly research "topic" --model pro`)
