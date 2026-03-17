# Tavily CLI

CLI and agent tools for the [Tavily API](https://docs.tavily.com) — search, extract, crawl, map, and research from the command line.

> **Note:** This package provides the `tvly` command-line tool. It depends on
> [`tavily-python`](https://pypi.org/project/tavily-python/), the official Tavily Python SDK.

## Features

- **Interactive REPL** — Run `tvly` with no arguments for a chat-like shell experience
- **CLI for Humans & AI Agents** — Rich-formatted output for humans, `--json` for agents
- **Web Search** — LLM-optimized search with domain/date filtering and relevance scoring
- **Content Extraction** — Extract clean markdown from any URL
- **Website Crawling** — Crawl sites with depth/breadth control and path filtering
- **URL Discovery** — Map all URLs on a site without content extraction
- **Deep Research** — AI-powered research with citations and structured output

## Installation

Requires **Python 3.10+**.

### Quick install

```bash
curl -fsSL https://raw.githubusercontent.com/tavily-ai/skills/main/install.sh | sh
```

This will detect your environment and install via `uv` (fastest), `pipx`, or `pip`.

### uv (recommended)

```bash
uv tool install tavily-cli
```

Or run without installing:

```bash
uvx --from tavily-cli tvly search "AI news"
```

### pipx

```bash
pipx install tavily-cli
```

### pip

```bash
pip install tavily-cli
```

### From source

```bash
git clone https://github.com/tavily-ai/skills.git
cd skills
pip install -e .
```

## Quick Start

### 1. Authenticate

```bash
# Set API key directly
tvly login --api-key tvly-YOUR_KEY

# Or use environment variable
export TAVILY_API_KEY=tvly-YOUR_KEY

# Or OAuth (opens browser)
tvly login

# Check auth status
tvly auth
```

### 2. Interactive Mode

```bash
# Launch the interactive REPL
tvly
```

This opens a chat-like shell where you can run commands without the `tvly` prefix:

```
❯  search "latest AI trends"
❯  extract https://example.com
❯  help
```

### 3. Search the Web

```bash
# Basic search
tvly search "latest AI trends"

# Advanced search with filters
tvly search "quantum computing" --depth advanced --max-results 10 --time-range week

# Search specific domains
tvly search "SEC filings for Apple" --include-domains sec.gov,reuters.com

# JSON output for agents
tvly search "AI news" --json
```

### 4. Extract Content from URLs

```bash
# Extract a single URL
tvly extract https://example.com/article

# Extract multiple URLs with a focus query
tvly extract https://example.com https://other.com --query "pricing information"

# Advanced extraction for JS-heavy pages
tvly extract https://spa-app.com --extract-depth advanced
```

### 5. Crawl a Website

```bash
# Basic crawl
tvly crawl https://docs.example.com

# Deep crawl with filters
tvly crawl https://docs.example.com --max-depth 2 --limit 100 --select-paths "/api/.*,/guides/.*"

# Semantic focus
tvly crawl https://docs.example.com --instructions "Find authentication docs" --chunks-per-source 3

# Save pages as markdown files
tvly crawl https://docs.example.com --output-dir ./docs
```

### 6. Map URLs

```bash
# Discover all URLs on a site
tvly map https://example.com

# Filter by path
tvly map https://example.com --select-paths "/blog/.*" --limit 500
```

### 7. Deep Research

```bash
# Run research and wait for results
tvly research "Competitive landscape of AI code assistants"

# Use pro model for comprehensive analysis
tvly research "Electric vehicle market analysis" --model pro

# Stream results in real-time
tvly research "AI market trends" --stream

# Async: start and poll separately
tvly research "topic" --no-wait --json        # returns request_id
tvly research status <request_id> --json      # check status
tvly research poll <request_id> --json        # wait and get result

# Structured output
tvly research "AI market size" --output-schema schema.json --json
```

## CLI Overview

```
tvly
├── (no command)                # Interactive REPL
├── login                       # Authenticate (OAuth or API key)
├── logout                      # Clear stored credentials
├── auth                        # Check authentication status
├── search <query>              # Web search
├── extract <urls...>           # Extract content from URLs
├── crawl <url>                 # Crawl a website
├── map <url>                   # Discover URLs (no content)
└── research <query>            # Deep research (async)
    ├── run <query>             # Start a research task (same as above)
    ├── status <id>             # Check task status
    └── poll <id>               # Poll until completion
```

## Non-Interactive Mode (for AI Agents & Scripts)

All commands support `--json` output and can be fully controlled via CLI arguments.

```bash
# Every command supports --json for structured output
tvly search "query" --json
tvly auth --json
tvly extract https://example.com --json

# Read input from stdin with "-"
echo "What is the latest funding for Anthropic?" | tvly search - --json
echo "Research question" | tvly research - --json

# Async research: launch then poll separately
tvly research "question" --no-wait --json        # returns request_id
tvly research status <id> --json                 # check status
tvly research poll <id> --json                   # wait and get result

# Global options
tvly --version         # show version
tvly --status          # show version + auth status
tvly --status --json   # structured status
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | Invalid input / usage error |
| 3 | Authentication error |
| 4 | API error |

## Command Reference

### `tvly search`

| Option | Description |
|--------|-------------|
| `--depth` | `ultra-fast`, `fast`, `basic` (default), `advanced` |
| `--max-results` | Maximum results, 0-20 (default: 5) |
| `--topic` | `general` (default), `news`, `finance` |
| `--time-range` | `day`, `week`, `month`, `year` |
| `--start-date` | Results after date (YYYY-MM-DD) |
| `--end-date` | Results before date (YYYY-MM-DD) |
| `--include-domains` | Comma-separated domains to include |
| `--exclude-domains` | Comma-separated domains to exclude |
| `--country` | Boost results from country |
| `--include-answer` | Include AI answer (`basic` or `advanced`) |
| `--include-raw-content` | Include full page (`markdown` or `text`) |
| `--include-images` | Include image results |
| `--chunks-per-source` | Chunks per source (advanced/fast depth only) |
| `-o` / `--output` | Save output to file |

### `tvly extract`

| Option | Description |
|--------|-------------|
| `--query` | Rerank chunks by relevance |
| `--chunks-per-source` | Chunks per source (1-5, requires `--query`) |
| `--extract-depth` | `basic` (default) or `advanced` |
| `--format` | `markdown` (default) or `text` |
| `--include-images` | Include image URLs |
| `--timeout` | Max wait (1-60 seconds) |
| `-o` / `--output` | Save output to file |

### `tvly crawl`

| Option | Description |
|--------|-------------|
| `--max-depth` | Levels deep (1-5, default: 1) |
| `--max-breadth` | Links per page (default: 20) |
| `--limit` | Total pages cap (default: 50) |
| `--instructions` | Natural language guidance |
| `--chunks-per-source` | Chunks per page (1-5, requires `--instructions`) |
| `--extract-depth` | `basic` or `advanced` |
| `--format` | `markdown` or `text` |
| `--select-paths` | Regex patterns for paths to include |
| `--exclude-paths` | Regex patterns for paths to exclude |
| `--select-domains` | Regex for domains to include |
| `--exclude-domains` | Regex for domains to exclude |
| `--allow-external` | Include external links (default: true) |
| `--include-images` | Include images |
| `--timeout` | Max wait (10-150 seconds) |
| `-o` / `--output` | Save JSON to file |
| `--output-dir` | Save each page as .md file in directory |

### `tvly map`

| Option | Description |
|--------|-------------|
| `--max-depth` | Levels deep (1-5, default: 1) |
| `--max-breadth` | Links per page (default: 20) |
| `--limit` | Max URLs to discover (default: 50) |
| `--instructions` | Natural language guidance |
| `--select-paths` | Regex patterns for paths to include |
| `--exclude-paths` | Regex patterns for paths to exclude |
| `--allow-external` | Include external links |
| `--timeout` | Max wait (10-150 seconds) |
| `-o` / `--output` | Save output to file |

### `tvly research <query>` / `tvly research run <query>`

| Option | Description |
|--------|-------------|
| `--model` | `mini`, `pro`, or `auto` (default) |
| `--no-wait` | Return request_id immediately |
| `--stream` | Stream results in real-time |
| `--output-schema` | Path to JSON schema file |
| `--citation-format` | `numbered`, `mla`, `apa`, `chicago` |
| `--poll-interval` | Seconds between checks (default: 10) |
| `--timeout` | Max wait seconds (default: 600) |
| `-o` / `--output` | Save output to file |

### `tvly research status`

Check research task status by request ID.

### `tvly research poll`

Poll until completion and return results. Same `--poll-interval`, `--timeout`, `-o` options as `run`.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TAVILY_API_KEY` | API key (highest priority, no login needed) |

## Related

- [`tavily-python`](https://pypi.org/project/tavily-python/) — Official Tavily Python SDK
- [Tavily Docs](https://docs.tavily.com) — Full API documentation

## License

MIT
