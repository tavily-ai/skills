---
name: search
description: "Search the web using Tavily's LLM-optimized search API. Returns relevant results with content snippets, scores, and metadata. Use when you need to find web content on any topic without writing code."
---

# Search Skill

Search the web and get relevant results optimized for LLM consumption.

## Authentication

The script uses OAuth via the Tavily MCP server. **No manual setup required** - on first run, it will:
1. Check for existing tokens in `~/.mcp-auth/`
2. If none found, automatically open your browser for OAuth authentication

> **Note:** You must have an existing Tavily account. The OAuth flow only supports login — account creation is not available through this flow. [Sign up at tavily.com](https://tavily.com) first if you don't have an account.

### Alternative: API Key

If you prefer using an API key, get one at https://tavily.com and add to `~/.claude/settings.json`:
```json
{
  "env": {
    "TAVILY_API_KEY": "tvly-your-api-key-here"
  }
}
```

## Quick Start

### Using the Script

```bash
./scripts/search.sh '<json>'
```

**Examples:**
```bash
# Basic search
./scripts/search.sh '{"query": "python async patterns"}'

# With options
./scripts/search.sh '{"query": "React hooks tutorial", "max_results": 10}'

# Advanced search with filters
./scripts/search.sh '{"query": "AI news", "time_range": "week", "max_results": 10}'

# Domain-filtered search
./scripts/search.sh '{"query": "machine learning", "include_domains": ["arxiv.org", "github.com"], "search_depth": "advanced"}'
```

### Basic Search

```bash
curl --request POST \
  --url https://api.tavily.com/search \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "query": "latest developments in quantum computing",
    "max_results": 5
  }'
```

### Advanced Search

```bash
curl --request POST \
  --url https://api.tavily.com/search \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "query": "machine learning best practices",
    "max_results": 10,
    "search_depth": "advanced",
    "include_domains": ["arxiv.org", "github.com"]
  }'
```

## API Reference

### Endpoint

```
POST https://api.tavily.com/search
```

### Headers

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer <TAVILY_API_KEY>` |
| `Content-Type` | `application/json` |

### Request Body

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | Required | Search query (keep under 400 chars) |
| `max_results` | integer | 10 | Maximum results (0-20) |
| `search_depth` | string | `"basic"` | `ultra-fast`, `fast`, `basic`, `advanced` |
| `topic` | string | `"general"` | Search topic (general only) |
| `time_range` | string | null | `day`, `week`, `month`, `year` |
| `start_date` | string | null | Return results after this date (`YYYY-MM-DD`) |
| `end_date` | string | null | Return results before this date (`YYYY-MM-DD`) |
| `include_domains` | array | [] | Domains to include (max 300) |
| `exclude_domains` | array | [] | Domains to exclude (max 150) |
| `country` | string | null | Boost results from a specific country (general topic only) |
| `include_raw_content` | boolean | false | Include full page content |
| `include_images` | boolean | false | Include image results |
| `include_image_descriptions` | boolean | false | Include descriptions for images |
| `include_favicon` | boolean | false | Include favicon URL for each result |

### Response Format

```json
{
  "query": "latest developments in quantum computing",
  "results": [
    {
      "title": "Page Title",
      "url": "https://example.com/page",
      "content": "Extracted text snippet...",
      "score": 0.85
    }
  ],
  "response_time": 1.2
}
```

## Search Depth

| Depth | Latency | Relevance | Content Type |
|-------|---------|-----------|--------------|
| `ultra-fast` | Lowest | Lower | NLP summary |
| `fast` | Low | Good | Chunks |
| `basic` | Medium | High | NLP summary |
| `advanced` | Higher | Highest | Chunks |

**When to use each:**
- `ultra-fast`: Real-time chat, autocomplete
- `fast`: Need chunks but latency matters
- `basic`: General-purpose, balanced
- `advanced`: Precision matters (default recommendation)

## Examples

### Domain-Filtered Search

```bash
curl --request POST \
  --url https://api.tavily.com/search \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "query": "Python async best practices",
    "include_domains": ["docs.python.org", "realpython.com", "github.com"],
    "search_depth": "advanced"
  }'
```

### Search with Full Content

```bash
curl --request POST \
  --url https://api.tavily.com/search \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "query": "React hooks tutorial",
    "max_results": 3,
    "include_raw_content": true
  }'
```

## Tips

- **Keep queries under 400 characters** - Think search query, not prompt
- **Break complex queries into sub-queries** - Better results than one massive query
- **Use `include_domains`** to focus on trusted sources
- **Use `time_range`** for recent information
- **Filter by `score`** (0-1) to get highest relevance results
