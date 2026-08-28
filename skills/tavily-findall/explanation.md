# tavily-findall — Explanation

## Use Case

You don't have a starting list — you want Tavily to build one. "Find every AI startup that raised a Series A in 2026." "List every state that passed a data-privacy law this year." You want a clean table back, not ten browser tabs you have to read yourself.

## How it works, in plain terms

It searches the web from several angles, pulls out the specific things (companies, people, laws, products) that match what you asked for, drops duplicates, and hands you back one organized list — not a pile of articles you have to comb through.

## Built With

This is genuinely `tavily-research` under the hood, with its structured-output (`output_schema`) feature shaped as a *list* (e.g. `{results: [{name, description, source_url}]}`) instead of a single-entity object like `tavily-enrich` uses. That's a real, deliberate distinction worth its own skill even though the plumbing is shared:

- `tavily-enrich` = you already have the rows, you're adding columns.
- `tavily-findall` = you don't have rows yet, you're building the list itself.

## Ways to Use This Skill

- "Find all companies that raised a Series A in AI this year"
- "List every US state with a data-privacy law"
- "Who are all the competitors to X in this market"
- "Build me a list of open-source alternatives to Y"
