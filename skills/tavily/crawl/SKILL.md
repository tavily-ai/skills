---
name: crawl-url
description: "Crawl any website and save pages as local markdown files. Use when you need to download documentation, knowledge bases, or web content for offline access or analysis. No code required - just provide a URL."
---

# Crawl Skill

Crawl websites to extract content from multiple pages. Ideal for documentation, knowledge bases, and site-wide content extraction.

## Prerequisites

**Tavily API Key Required** - Get your key at https://tavily.com

Add to `~/.claude/settings.json`:
```json
{
  "env": {
    "TAVILY_API_KEY": "tvly-your-api-key-here"
  }
}
```

## Quick Start

### Basic Crawl

```bash
curl --request POST \
  --url https://api.tavily.com/crawl \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "url": "https://docs.example.com",
    "max_depth": 1,
    "limit": 20
  }'
```

### Focused Crawl with Instructions

```bash
curl --request POST \
  --url https://api.tavily.com/crawl \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "url": "https://docs.example.com",
    "max_depth": 2,
    "instructions": "Find API documentation and code examples",
    "chunks_per_source": 3,
    "select_paths": ["/docs/.*", "/api/.*"]
  }'
```

## API Reference

### Endpoint

```
POST https://api.tavily.com/crawl
```

### Headers

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer <TAVILY_API_KEY>` |
| `Content-Type` | `application/json` |

### Request Body

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | Required | Root URL to begin crawling |
| `max_depth` | integer | 1 | Levels deep to crawl (1-5) |
| `max_breadth` | integer | 20 | Links per page |
| `limit` | integer | 50 | Total pages cap |
| `instructions` | string | null | Natural language guidance for focus |
| `chunks_per_source` | integer | 3 | Chunks per page (1-5, requires instructions) |
| `extract_depth` | string | `"basic"` | `basic` or `advanced` |
| `format` | string | `"markdown"` | `markdown` or `text` |
| `select_paths` | array | null | Regex patterns to include |
| `exclude_paths` | array | null | Regex patterns to exclude |
| `allow_external` | boolean | true | Include external domain links |
| `timeout` | float | 150 | Max wait (10-150 seconds) |

### Response Format

```json
{
  "base_url": "https://docs.example.com",
  "results": [
    {
      "url": "https://docs.example.com/page",
      "raw_content": "# Page Title\n\nContent..."
    }
  ],
  "response_time": 12.5
}
```

## Depth vs Performance

| Depth | Typical Pages | Time |
|-------|---------------|------|
| 1 | 10-50 | Seconds |
| 2 | 50-500 | Minutes |
| 3 | 500-5000 | Many minutes |

**Start with `max_depth=1`** and increase only if needed.

## Examples

### Documentation Crawl

```bash
curl --request POST \
  --url https://api.tavily.com/crawl \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "url": "https://docs.example.com",
    "max_depth": 2,
    "extract_depth": "advanced",
    "select_paths": ["/docs/.*", "/guides/.*"]
  }'
```

### Blog Archive Crawl

```bash
curl --request POST \
  --url https://api.tavily.com/crawl \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "url": "https://example.com/blog",
    "max_depth": 2,
    "max_breadth": 50,
    "select_paths": ["/blog/.*"],
    "exclude_paths": ["/blog/tag/.*", "/blog/category/.*"]
  }'
```

### Semantic-Focused Crawl

```bash
curl --request POST \
  --url https://api.tavily.com/crawl \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "url": "https://example.com",
    "max_depth": 2,
    "instructions": "Find all documentation about authentication and security",
    "chunks_per_source": 3
  }'
```

## Map API (URL Discovery)

Use `map` instead of `crawl` when you only need URLs, not content:

```bash
curl --request POST \
  --url https://api.tavily.com/map \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "url": "https://docs.example.com",
    "max_depth": 2,
    "instructions": "Find all API docs and guides"
  }'
```

Returns URLs only (faster than crawl):

```json
{
  "base_url": "https://docs.example.com",
  "results": [
    "https://docs.example.com/api/auth",
    "https://docs.example.com/guides/quickstart"
  ]
}
```

## Tips

- **Use `instructions` + `chunks_per_source`** to get only relevant content
- **Start conservative** (`max_depth=1`, `limit=20`) and scale up
- **Use path patterns** to focus on relevant sections
- **Use Map first** to understand site structure before full crawl
- **Always set a `limit`** to prevent runaway crawls
