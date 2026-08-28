---
name: tavily-enrich
description: |
  Fill in missing data on a list of companies, people, or products by looking each one up on the web. Use this skill when the user has a spreadsheet, CSV, or list of names and wants missing fields added — CEO, funding raised, headquarters, employee count, contact info, pricing, or any other web-discoverable attribute — or says "enrich this list", "fill in the missing columns", "add company data from the web", "find the CEO for each of these", "complete this spreadsheet", or "add contact info to this list". Takes a list you already have and adds columns to it. Do NOT use this for building a list from scratch (see tavily-findall) or for single-entity deep research reports (see tavily-research).
allowed-tools: Bash(tvly *), Bash(python3 *)
---

# tavily enrich

Add web-sourced fields to a list of entities you already have — companies, people, products, anything with a name. Turns a bare list (or a spreadsheet with gaps) into a completed table.

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

- You have a list of names (companies, people, products) and want specific fields filled in for each
- You have a CSV/spreadsheet with some columns empty and want them completed from the web
- You know exactly what fields you want — this is about breadth (many rows), not depth (one exhaustive report)

Not this skill:
- No existing list yet, you want to *build* one from criteria → [tavily-findall](../tavily-findall/SKILL.md)
- One entity, want an exhaustive deep-dive → [tavily-research](../tavily-research/SKILL.md)

## How it works

This skill is `tavily-research`'s structured output (`--output-schema`) run once per row, with the results merged back into your original list. There's no separate Tavily "enrichment" API — this is a recipe on top of research.

1. Define the schema for the fields you want (one field = one column).
2. For each row, run `tvly research` with a query built from that row's identifying info (e.g. company name) and the shared schema.
3. Merge the structured result back into that row.
4. Write the completed list back out (CSV in, CSV out — or JSON, if that's the input).

## Quick start

**1. Write the schema once** (`schema.json`) — shared across all rows:

```json
{
  "properties": {
    "ceo": {"type": "string", "description": "Current CEO's full name, or null if not found"},
    "funding_raised": {"type": "string", "description": "Total funding raised to date, with currency, or null"},
    "hq_location": {"type": "string", "description": "City and country of headquarters, or null"},
    "employee_count": {"type": "string", "description": "Approximate employee count or range, or null"}
  },
  "required": ["ceo", "funding_raised", "hq_location", "employee_count"]
}
```

**2. Run one row to sanity-check the schema before batching:**

```bash
tvly research "Find the CEO, total funding raised, HQ location, and employee count for the company Anthropic." \
  --model mini --output-schema schema.json --json
```

**3. Loop over the full list, merging results back in:**

```bash
python3 << 'PYEOF'
import csv, json, subprocess

with open('companies.csv') as f:
    rows = list(csv.DictReader(f))

schema_path = 'schema.json'
fields = ['ceo', 'funding_raised', 'hq_location', 'employee_count']

for row in rows:
    name = row['company']
    query = f"Find the CEO, total funding raised, HQ location, and employee count for the company {name}."
    try:
        raw = subprocess.check_output(
            ['tvly', 'research', query, '--model', 'mini',
             '--output-schema', schema_path, '--json'],
            stderr=subprocess.DEVNULL, timeout=120
        )
        result = json.loads(raw)
        content = result.get('content', {})
        data = json.loads(content) if isinstance(content, str) else content
    except Exception:
        data = {}

    for field in fields:
        row[field] = data.get(field, '')

with open('companies_enriched.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Enriched {len(rows)} rows -> companies_enriched.csv")
PYEOF
```

## Options

Same underlying flags as [tavily-research](../tavily-research/SKILL.md):

| Option | Description |
|--------|-------------|
| `--model` | `mini` (default choice here — fast, good for narrow per-row lookups) or `pro` for harder-to-find entities |
| `--output-schema` | Path to the shared JSON schema — keep it identical across every row so columns line up |
| `--json` | Structured JSON output (required to parse programmatically) |
| `--timeout` | Raise if rows are timing out (default 600s is usually generous per row) |

## Tips

- **Use `mini`, not `pro`, by default.** Enrichment is many small, narrow lookups — `pro`'s multi-agent depth is overkill and much slower per row. Reach for `pro` only if `mini` keeps missing fields for well-known entities.
- **Never let the model guess.** Every schema field description should say "or null if not found" — a blank cell is correct and honest; a hallucinated one is worse than no data.
- **Sanity-check on 2-3 rows before running the full list.** Cheaper to fix a bad schema/query early than after 200 API calls.
- **Batch size and rate limits.** For large lists (100+ rows), add a short delay between calls or run in small parallel batches — check your Tavily plan's rate limits first.
- **Keep the original columns.** Merge new fields alongside existing ones rather than replacing the file structure, so the enriched output is a strict superset of the input.

## See also

- [tavily-research](../tavily-research/SKILL.md) — the underlying structured-output capability this skill wraps
- [tavily-findall](../tavily-findall/SKILL.md) — for building a list from scratch instead of completing one you already have
