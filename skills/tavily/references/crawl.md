# Crawl & Map API Reference

## Table of Contents

- [Crawl vs Map](#crawl-vs-map)
- [Key Parameters](#key-parameters)
- [Instructions and Chunks](#instructions-and-chunks)
- [Path and Domain Filtering](#path-and-domain-filtering)
- [Use Cases](#use-cases)
- [Map then Extract Pattern](#map-then-extract-pattern)
- [Performance Optimization](#performance-optimization)
- [Common Pitfalls](#common-pitfalls)
- [Response Fields](#response-fields)

---

## Crawl vs Map

| Feature | Crawl | Map |
|---------|-------|-----|
| **Returns** | Full content | URLs only |
| **Speed** | Slower | Faster |
| **Best for** | RAG, deep analysis, documentation | Site structure discovery, URL collection |

**Use Crawl when:**
- Full content extraction needed
- Building RAG systems
- Processing paginated/nested content
- Integration with knowledge bases

**Use Map when:**
- Quick site structure discovery
- URL collection without content
- Planning before crawling
- Sitemap generation

---

## Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | Required | Root URL to begin |
| `max_depth` | integer | 1 | Levels deep to crawl (1-5). **Start with 1-2** |
| `max_breadth` | integer | 20 | Links per page. 50-100 for focused crawls |
| `limit` | integer | 50 | Total pages cap |
| `instructions` | string | null | Natural language guidance (2 credits/10 pages) |
| `chunks_per_source` | integer | 3 | Chunks per page (1-5). Only with `instructions` |
| `extract_depth` | enum | `"basic"` | `"basic"` (1 credit/5 URLs) or `"advanced"` (2 credits/5 URLs) |
| `format` | enum | `"markdown"` | `"markdown"` or `"text"` |
| `select_paths` | array | null | Regex patterns to include |
| `exclude_paths` | array | null | Regex patterns to exclude |
| `select_domains` | array | null | Regex for domains to include |
| `exclude_domains` | array | null | Regex for domains to exclude |
| `allow_external` | boolean | true | Include external domain links |
| `include_images` | boolean | false | Include images |
| `timeout` | float | 150 | Max wait (10-150 seconds) |

---

## Instructions and Chunks

Use `instructions` and `chunks_per_source` for semantic focus and token optimization:

```python
response = client.crawl(
    url="https://docs.example.com",
    max_depth=2,
    instructions="Find all documentation about authentication and security",
    chunks_per_source=3  # Only top 3 relevant chunks per page
)
```

**Key benefits:**
- `instructions` guides crawler semantically, focusing on relevant content
- `chunks_per_source` returns only relevant snippets (max 500 chars each)
- Prevents context window explosion in agentic use cases
- Chunks appear in `raw_content` as: `<chunk 1> [...] <chunk 2> [...] <chunk 3>`

**Note:** `chunks_per_source` only works when `instructions` is provided.

---

## Path and Domain Filtering

### Path patterns (regex)

```python
# Target specific sections
response = client.crawl(
    url="https://example.com",
    select_paths=["/docs/.*", "/api/.*", "/guides/.*"],
    exclude_paths=["/blog/.*", "/changelog/.*", "/private/.*"]
)

# Paginated content
response = client.crawl(
    url="https://example.com/blog",
    max_depth=2,
    select_paths=["/blog/.*", "/blog/page/.*"],
    exclude_paths=["/blog/tag/.*"]
)
```

### Domain control (regex)

```python
# Stay within subdomain
response = client.crawl(
    url="https://docs.example.com",
    select_domains=["^docs.example.com$"],
    max_depth=2
)

# Exclude specific domains
response = client.crawl(
    url="https://example.com",
    exclude_domains=["^ads.example.com$", "^tracking.example.com$"]
)
```

---

## Use Cases

### 1. Deep/Unlinked Content
Deeply nested pages, paginated archives, internal search-only content.

```python
response = client.crawl(
    url="https://example.com",
    max_depth=3,
    max_breadth=50,
    limit=200,
    select_paths=["/blog/.*", "/changelog/.*"],
    exclude_paths=["/private/.*", "/admin/.*"]
)
```

### 2. Documentation/Structured Content
Documentation, changelogs, FAQs with nonstandard markup.

```python
response = client.crawl(
    url="https://docs.example.com",
    max_depth=2,
    extract_depth="advanced",
    select_paths=["/docs/.*"]
)
```

### 3. Multi-modal/Cross-referencing
Combining information from multiple sections.

```python
response = client.crawl(
    url="https://example.com",
    max_depth=2,
    instructions="Find all documentation pages that link to API reference docs",
    extract_depth="advanced"
)
```

### 4. Rapidly Changing Content
API docs, product announcements, news sections.

```python
response = client.crawl(
    url="https://api.example.com",
    max_depth=1,
    max_breadth=100
)
```

### 5. RAG/Knowledge Base Integration

```python
response = client.crawl(
    url="https://docs.example.com",
    max_depth=2,
    extract_depth="advanced",
    include_images=True,
    instructions="Extract all technical documentation and code examples"
)
```

### 6. Compliance/Auditing
Comprehensive content analysis for legal checks.

```python
response = client.crawl(
    url="https://example.com",
    max_depth=3,
    max_breadth=100,
    limit=1000,
    extract_depth="advanced",
    instructions="Find all mentions of GDPR and data protection policies"
)
```

---

## Map then Extract Pattern

Discover structure first, then extract strategically:

```python
# Step 1: Map to discover structure
map_result = client.map(
    url="https://docs.example.com",
    max_depth=2,
    instructions="Find all API docs and guides"
)

# Step 2: Filter discovered URLs
api_docs = [url for url in map_result["urls"] if "/api/" in url]
guides = [url for url in map_result["urls"] if "/guides/" in url]
print(f"Found {len(api_docs)} API docs, {len(guides)} guides")

# Step 3: Extract from filtered URLs
target_urls = api_docs + guides
response = client.extract(
    urls=target_urls[:20],  # Max 20 per extract call
    extract_depth="advanced",
    query="API endpoints and usage examples",
    chunks_per_source=3
)
```

**Benefits:**
- Discover site structure before committing to full crawl
- Identify relevant path patterns
- Avoid unnecessary extraction
- More control over what gets extracted

---

## Performance Optimization

### Depth Impact

Each depth level increases crawl time exponentially:

| Depth | Typical Pages | Time |
|-------|---------------|------|
| 1 | 10-50 | Seconds |
| 2 | 50-500 | Minutes |
| 3 | 500-5000 | Many minutes |

**Best practice:** Start with `max_depth=1`, increase only if needed.

### Conservative vs Comprehensive

```python
# Conservative (start here)
response = client.crawl(
    url="https://example.com",
    max_depth=1,
    max_breadth=20,
    limit=20
)

# Comprehensive (use carefully)
response = client.crawl(
    url="https://example.com",
    max_depth=3,
    max_breadth=100,
    limit=500
)
```

---

## Common Pitfalls

| Problem | Impact | Solution |
|---------|--------|----------|
| `max_depth=4+` | Exponential time, unnecessary pages | Start with 1-2, increase if needed |
| No `instructions` | Wasted resources, irrelevant content | Use instructions for semantic focus |
| No `limit` | Runaway crawls, unexpected costs | Always set reasonable limit |
| Ignoring `failed_results` | Incomplete data | Monitor and adjust parameters |
| Full content without chunks | Context explosion | Use `instructions` + `chunks_per_source` |

---

## Response Fields

### Crawl Response

| Field | Description |
|-------|-------------|
| `results` | List of crawled pages |
| `results[].url` | Page URL |
| `results[].raw_content` | Extracted content (or chunks if instructions provided) |
| `failed_results` | Pages that failed extraction |
| `response_time` | Time in seconds |

### Map Response

| Field | Description |
|-------|-------------|
| `urls` | List of discovered URLs |
| `base_url` | Starting URL |
| `response_time` | Time in seconds |

For more details, see the [full API reference](https://docs.tavily.com/documentation/api-reference/endpoint/crawl)
