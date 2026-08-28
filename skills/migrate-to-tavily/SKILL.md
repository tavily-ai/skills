---
name: migrate-to-tavily
description: |
  Migrate an existing integration from a competing web-search/research API — Exa, Firecrawl, Perplexity, or Parallel — over to Tavily, preserving behavior while swapping calls, imports, environment variables, and error handling. Use this skill when the user has working code against a competitor's SDK and wants to switch providers, or says "migrate this to Tavily", "switch from Exa/Firecrawl/Perplexity/Parallel to Tavily", "replace this competitor API with Tavily", or "port this integration over". Do NOT use this for greenfield Tavily integrations with no existing competitor code — start with tavily-best-practices instead.
allowed-tools: Read, Edit, Grep, Glob, Bash(pip *), Bash(npm *)
---

# migrate to tavily

Convert an existing integration against a competitor's search/extract/research API into an equivalent Tavily integration.

## When to use

- There's existing code calling Exa, Firecrawl, Perplexity, or Parallel
- The user wants the same behavior, just backed by Tavily instead

Not this skill:
- No existing competitor code to migrate → start with [tavily-best-practices](../tavily-best-practices/SKILL.md) for a fresh integration

## Process

1. **Find what's actually used.** Grep the codebase for the competitor's SDK import, client construction, and each method call site — don't assume every method the SDK offers is in use.
2. **Map each call site** using the tables below.
3. **Rewrite** imports, client construction, method calls, and response field access.
4. **Update dependencies** (`package.json`/`requirements.txt`) and environment variables (`.env`, config, CI secrets references — flag secret rotation as the user's responsibility, don't invent new key values).
5. **Update error handling** to match Tavily's exceptions/response shape (see [tavily-best-practices/references/sdk.md](../tavily-best-practices/references/sdk.md)).
6. **Flag anything with no clean equivalent** rather than silently dropping functionality — call it out to the user explicitly.

## Mapping tables

### From Exa

| Exa | Tavily | Notes |
|---|---|---|
| `exa.search(query, ...)` | `client.search(query, ...)` → [tavily-search](../tavily-search/SKILL.md) | Exa's neural/keyword `type` param has no direct Tavily equivalent — Tavily's `search_depth` (basic/advanced) is the closest lever |
| `exa.get_contents(urls)` | `client.extract(urls)` → [tavily-extract](../tavily-extract/SKILL.md) | |
| `exa.find_similar(url)` | No direct equivalent | Approximate with `client.search()` using the source page's title/topic as the query |
| `exa.search_and_contents(...)` | `client.search(..., include_raw_content=True)` | One-call combined pattern, same idea |

### From Firecrawl

| Firecrawl | Tavily | Notes |
|---|---|---|
| `firecrawl.scrape_url(url)` | `client.extract(urls=[url])` → [tavily-extract](../tavily-extract/SKILL.md) | |
| `firecrawl.crawl_url(url, ...)` | `client.crawl(url, ...)` → [tavily-crawl](../tavily-crawl/SKILL.md) | Firecrawl's `limit`/`maxDepth` map to Tavily's `limit`/`max_depth` |
| `firecrawl.map_url(url)` | `client.map(url)` → [tavily-map](../tavily-map/SKILL.md) | |
| Firecrawl's markdown/structured extraction modes | Tavily's `extract_depth="advanced"` + `format="markdown"` | |

### From Perplexity

| Perplexity | Tavily | Notes |
|---|---|---|
| `sonar`/`sonar-pro` chat-completions call used for research | `client.research(input, model="mini"/"pro")` → [tavily-research](../tavily-research/SKILL.md) | Perplexity returns research as a chat completion; Tavily's `research()` is purpose-built, async, and supports `output_schema` for structured results |
| Inline citations in the completion text | `response["sources"]` + `citation_format` | Tavily returns citations as structured data rather than inline markers — update any citation-parsing code accordingly |

### From Parallel

| Parallel | Tavily | Notes |
|---|---|---|
| `parallel-web-search` | `client.search(...)` → [tavily-search](../tavily-search/SKILL.md) | |
| `parallel-web-extract` | `client.extract(...)` → [tavily-extract](../tavily-extract/SKILL.md) | |
| `parallel-deep-research` | `client.research(..., model="pro")` → [tavily-research](../tavily-research/SKILL.md) | |
| `parallel-findall` | [tavily-findall](../tavily-findall/SKILL.md) | Same underlying idea — structured list of matching entities |
| `parallel-data-enrichment` | [tavily-enrich](../tavily-enrich/SKILL.md) | Same underlying idea — fill in fields on an existing list |
| `parallel-monitor` | [tavily-monitor](../tavily-monitor/SKILL.md) | Parallel's is a hosted platform feature; Tavily's equivalent is orchestration-based (see that skill's notes) — call this difference out to the user rather than promising an identical hosted experience |
| `status` / `result` (run ID lookup) | `client.get_research(request_id)` / `tvly research status`/`poll` | Built into [tavily-research](../tavily-research/SKILL.md) rather than separate calls |
| `parallel-memory` | [tavily-runs](../tavily-runs/SKILL.md) | Tavily has no hosted memory store — this is a local logging convention, say so |

## Tips

- **Preserve response shape at the boundary if the rest of the app depends on it.** If a wholesale rewrite is risky, write a thin adapter function that calls Tavily internally but returns the old shape, rather than touching every call site.
- **Don't invent parity that doesn't exist.** Where Tavily has no equivalent (e.g., Exa's `find_similar`), say so plainly rather than approximating silently and letting behavior quietly change.
- **Check rate limits and pricing separately** — this skill migrates code, not commercial terms; flag that the user should confirm their Tavily plan covers their call volume.
- **Test against real data before removing the old integration.** Run both side-by-side on a few known cases and compare outputs.

## See also

- [tavily-best-practices](../tavily-best-practices/SKILL.md) — full SDK reference for the target Tavily integration
- [tavily-enrich](../tavily-enrich/SKILL.md), [tavily-findall](../tavily-findall/SKILL.md), [tavily-monitor](../tavily-monitor/SKILL.md), [tavily-runs](../tavily-runs/SKILL.md) — Tavily-side equivalents for Parallel's higher-level skills
