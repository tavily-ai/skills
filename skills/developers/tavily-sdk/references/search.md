# Search API Reference

## Table of Contents

- [Query Optimization](#query-optimization)
- [Search Depth](#search-depth)
- [Key Parameters](#key-parameters)
- [Basic Usage](#basic-usage)
- [Filtering Results](#filtering-results)
- [Async Patterns](#async-patterns)
- [Response Fields](#response-fields)
- [Post-Filtering Strategies](#post-filtering-strategies)

---

## Query Optimization

**Keep queries under 400 characters.** Think search query, not long-form prompt.

**Break complex queries into sub-queries:**
```python
# Instead of one massive query, break it down:
queries = [
    "Competitors of company ABC",
    "Financial performance of company ABC",
    "Recent developments of company ABC"
]
responses = await asyncio.gather(*(client.search(q) for q in queries))
```

## Search Depth

Controls the latency vs. relevance tradeoff:

| Depth | Latency | Relevance | Content Type |
|-------|---------|-----------|--------------|
| `ultra-fast` | Lowest | Lower | Content (NLP summary) |
| `fast` | Low | Good | Chunks |
| `basic` | Medium | High | Content (NLP summary) |
| `advanced` | Higher | Highest | Chunks |

**Content types:**
- **Content**: NLP-based summary of the page, providing general context
- **Chunks**: Short snippets (max 500 chars) reranked by relevance to your query

**When to use each:** 
- `ultra-fast`: Latency-critical (real-time chat, autocomplete)
- `fast`: Need chunks but latency matters
- `basic`: General-purpose, balanced relevance and latency
- `advanced`: Specific information queries, precision matters - default (Still fast and suitable for almost all use cases) 

## Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | Required | Search query (keep under 400 chars) |
| `search_depth` | enum | `"basic"` | `"ultra-fast"`, `"fast"`, `"basic"`, `"advanced"` |
| `topic` | enum | `"general"` | `"general"`, `"news"`, `"finance"` |
| `chunks_per_source` | integer | 3 | Chunks per source (advanced/fast depth only) |
| `max_results` | integer | 10 | Maximum results (0-20) |
| `time_range` | enum | null | `"day"`, `"week"`, `"month"`, `"year"` |
| `start_date` | string | null | Results after date (YYYY-MM-DD) |
| `end_date` | string | null | Results before date (YYYY-MM-DD) |
| `include_domains` | array | [] | Domains to include (max 300, supports wildcards like `*.com`) |
| `exclude_domains` | array | [] | Domains to exclude (max 150) |
| `country` | enum | null | Boost results from country |
| `include_answer` | bool/enum | false | `true`/`"basic"` or `"advanced"` for LLM answer |
| `include_raw_content` | bool/enum | false | `true`/`"markdown"` or `"text"` for full page |
| `include_images` | boolean | false | Include image results |
| `include_image_descriptions` | boolean | false | AI descriptions for images |
| `include_favicon` | boolean | false | Favicon URL per result |
| `auto_parameters` | boolean | false | Auto-configure based on query intent |
| `include_usage` | boolean | false | Include credit usage info |

**Notes:**

- **`include_answer`**: Only use if you don't want to bring your own LLM. Most users bring their own model.

- **`auto_parameters`**: May set `search_depth="advanced"` (2 credits). Set `search_depth` manually to control cost.


## Basic Usage

```python
from tavily import TavilyClient

client = TavilyClient()

response = client.search(
    query="latest developments in quantum computing",
    max_results=10,
    search_depth="advanced",
    chunks_per_source=5
)

for result in response["results"]:
    print(f"{result['title']}: {result['url']}")
    print(f"Score: {result['score']}")
```


## Filtering Results

### By domain

```python
# Only search trusted sources
response = client.search(
    query="machine learning best practices",
    include_domains=["arxiv.org", "github.com", "pytorch.org"],
)

# Exclude specific domains
response = client.search(
    query="openai product reviews",
    exclude_domains=["reddit.com", "quora.com"]
)

# Restrict to LinkedIn profiles
response = client.search(
    query="CEO background at Google",
    include_domains=["linkedin.com/in"]
)
```

### By date

```python
# Relative time range
response = client.search(query="latest ML trends", time_range="month")

# Specific date range
response = client.search(
    query="AI news",
    start_date="2025-01-01",
    end_date="2025-02-01"
)
```

### By country

```python
# Boost results from specific country
response = client.search(query="tech startup funding", country="united states")
```

## Async Patterns

Leveraging the async client enables scaled search with higher breadth and reach by running multiple queries in parallel. This is the best practice for agentic systems where you need to gather comprehensive information quickly before passing it to a model for analysis.

```python
import asyncio
from tavily import AsyncTavilyClient

# Initialize Tavily client
tavily_client = AsyncTavilyClient("tvly-YOUR_API_KEY")

async def fetch_and_gather():
    queries = ["latest AI trends", "future of quantum computing"]

    # Perform search and continue even if one query fails (using return_exceptions=True)
    try:
        responses = await asyncio.gather(*(tavily_client.search(q) for q in queries), return_exceptions=True)

        # Handle responses and print
        for response in responses:
            if isinstance(response, Exception):
                print(f"Search query failed: {response}")
            else:
                print(response)

    except Exception as e:
        print(f"Error during search queries: {e}")

# Run the function
asyncio.run(fetch_and_gather())
```


## Response Fields

**Top-level response:**

| Field | Description |
|-------|-------------|
| `query` | The original search query |
| `answer` | AI-generated answer (if `include_answer` enabled) |
| `results` | Array of search result objects |
| `images` | Array of image results (if `include_images=True`) |

**Each result object:**

| Field | Description |
|-------|-------------|
| `title` | Page title |
| `url` | Source URL |
| `content` | Extracted text snippet(s) |
| `score` | Semantic relevance score (0-1) |
| `raw_content` | Full page content (if `include_raw_content` enabled) |
| `favicon` | Favicon URL (if `include_favicon=True`) |

**Top-level response also includes:**

| Field | Description |
|-------|-------------|
| `request_id` | Unique identifier for support reference |
| `response_time` | Response time in seconds |

**Each image object (if `include_images=True`):**

| Field | Description |
|-------|-------------|
| `url` | Image URL |
| `description` | AI-generated description (if `include_image_descriptions=True`) |

---


For more details, please read the [full API reference](https://docs.tavily.com/documentation/api-reference/endpoint/search)