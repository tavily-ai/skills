# migrate-to-tavily — Explanation

Skill definition: [SKILL.md](SKILL.md)

## Use Case

You've already got working code that calls a competitor's search/extract/research API, and you want to swap it for Tavily without re-architecting anything or breaking what already works.

## How it works, in plain terms

It reads your existing integration, figures out which competitor calls map to which Tavily calls, and rewrites the code (imports, function calls, env vars, error handling) to use Tavily instead — same behavior, new provider.

## Built With

A mapping table per competitor, similar in shape to reference docs already in this repo (`tavily-best-practices`):

- Exa `search` / `get_contents` → `tavily-search` / `tavily-extract`
- Firecrawl `scrape` / `crawl` / `map` → `tavily-extract` / `tavily-crawl` / `tavily-map`
- Perplexity `sonar` research calls → `tavily-research`
- Parallel `web-search` / `web-extract` / `deep-research` / `findall` / `data-enrichment` / `monitor` / `memory` → `tavily-search` / `tavily-extract` / `tavily-research` / `tavily-findall` / `tavily-enrich` / `tavily-monitor` / `tavily-runs`

## Ways to Use This Skill

- "Switch this from Exa to Tavily"
- "Migrate this Firecrawl integration to Tavily"
- "Replace this Perplexity research call with Tavily"
- "Port this Parallel-based integration over to Tavily"
