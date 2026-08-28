---
name: tavily-findall
description: |
  Build a structured, deduplicated list of entities matching a description you give — companies, people, products, laws, anything — instead of a pile of articles you have to read yourself. Use this skill when the user doesn't have a starting list and wants one built from criteria, or says "find all companies that...", "find every X that does Y", "list all the...", "who are all the...", "build me a list of...", or describes a filter/criteria they want matched across the web. Returns a clean table of matching entities with supporting sources. Do NOT use this when the user already has a list and wants fields added to it (see tavily-enrich), or wants one exhaustive report on a single known entity (see tavily-research).
allowed-tools: Bash(tvly *), Bash(python3 *)
---

# tavily findall

Find every entity on the web that matches a natural-language description, and return one organized, deduplicated list — not a pile of search results you have to read and compile yourself.

## Before running any command

If `tvly` is not found on PATH, install it first:

```bash
curl -fsSL https://cli.tavily.com/install.sh | bash && tvly login
```

See [tavily-cli](../tavily-cli/SKILL.md) for alternative install methods and auth options.

## Known issue: `--output-schema` currently requires API-key auth, not OAuth

**TODO: remove this section once Tavily's MCP server adds `output_schema` support to its `tavily_research` tool — tracked as a gap report filed 2026-08-28.**

As of 2026-08, `--output-schema` fails when the CLI is authenticated via `tvly login` (OAuth) — that path routes through Tavily's MCP server (`mcp.tavily.com`), which doesn't yet accept an `output_schema` parameter on its `tavily_research` tool, even though the direct REST API/SDK does. If you see `Unexpected keyword argument` / `Internal error... call[tavily_research]`, this is why.

Fix: authenticate with a raw API key instead of OAuth before using this skill:

```bash
tvly login --api-key tvly-YOUR_KEY
# or: export TAVILY_API_KEY=tvly-YOUR_KEY
```

## When to use

- You want a list of things matching a description, and you don't have a starting list yet
- Examples: "AI startups that raised a Series A in 2026", "US states that passed a data-privacy law this year", "open-source alternatives to X"

Not this skill:
- You already have the list and want fields added to each row → [tavily-enrich](../tavily-enrich/SKILL.md)
- You want one exhaustive report on a single, already-known entity → [tavily-research](../tavily-research/SKILL.md)

## How it works

Same underlying primitive as `tavily-enrich` — `tavily-research`'s `--output-schema` — but shaped as a *list*, not a single object, and combined with multiple search angles to maximize coverage before deduplicating.

1. Turn the user's criteria into a research query, and define a schema shaped as an array of matches.
2. Run `tvly research` (often with `--model pro` — finding *every* match needs more thorough multi-source search than a single narrow lookup).
3. Optionally, run a couple of differently-phrased queries to widen coverage, then merge and dedupe by name/URL.
4. Return the list as a table (and optionally write it to CSV/JSON).

## Quick start

**1. Write a schema shaped as a list:**

```json
{
  "properties": {
    "results": {
      "type": "array",
      "description": "Every distinct entity found that matches the criteria",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string", "description": "Name of the matching entity"},
          "evidence": {"type": "string", "description": "One-sentence reason it matches the criteria"},
          "source_url": {"type": "string", "description": "URL supporting this match"}
        },
        "required": ["name", "evidence", "source_url"]
      }
    }
  },
  "required": ["results"]
}
```

**2. Run the research call:**

```bash
tvly research "Find AI startups that publicly announced a Series A funding round in 2026. \
List each distinct company once, with a one-sentence reason and a supporting source URL." \
  --model pro --output-schema schema.json --json -o findall_results.json
```

**3. (Optional) Widen coverage with a second angled query and merge/dedupe:**

```bash
python3 << 'PYEOF'
import json

with open('findall_results.json') as f:
    result = json.load(f)
    content = result.get('content', {})
    r1 = json.loads(content) if isinstance(content, str) else content

# Run a second, differently-worded query the same way, save it, and load it here as r2,
# then merge both result sets before deduplicating.
all_entries = r1['results']  # + r2['results'] once you have a second angle

seen, merged = set(), []
for entry in all_entries:
    key = entry['name'].strip().lower()
    if key not in seen:
        seen.add(key)
        merged.append(entry)

for m in merged:
    print(f"- {m['name']}: {m['evidence']} ({m['source_url']})")
PYEOF
```

## Options

Same underlying flags as [tavily-research](../tavily-research/SKILL.md):

| Option | Description |
|--------|-------------|
| `--model` | `pro` recommended by default — "find *all*" needs broader multi-angle search than a narrow lookup; drop to `mini` only for tightly scoped criteria |
| `--output-schema` | Schema with a top-level array field — this is what makes the output a list instead of a report |
| `--json` | Required to parse the array programmatically |
| `--citation-format` | Use if you need formatted citations per entity rather than raw URLs |

## Tips

- **Ask for "distinct"/"each once" explicitly in the query.** Without it, results can repeat the same entity under slightly different phrasing.
- **Widen with multiple angled queries for anything that matters.** One `research` call is good coverage, not guaranteed *complete* coverage — for a "find all" claim you're going to rely on, run 2-3 differently-worded queries and dedupe, the same multi-source pattern already used in `tavily-dynamic-search`.
- **Always require a source URL per entry.** A finding with no source is unverifiable — treat schema fields like `evidence`/`source_url` as non-optional.
- **`pro` over `mini` for breadth.** This is the one place where `pro`'s extra time is usually worth it — the whole point is not missing matches.
- **Tell the user what was NOT covered.** If you scoped the search to certain sources/time ranges, say so — silent narrowing looks like completeness when it isn't.

## See also

- [tavily-research](../tavily-research/SKILL.md) — the underlying structured-output capability this skill wraps
- [tavily-enrich](../tavily-enrich/SKILL.md) — for completing a list you already have, rather than building one
- [tavily-dynamic-search](../tavily-dynamic-search/SKILL.md) — the multi-angle-search-then-dedupe pattern this skill borrows
