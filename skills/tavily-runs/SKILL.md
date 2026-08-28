---
name: tavily-runs
description: |
  Look up a past research run by what you asked, not by remembering its run ID. Use this skill when the user wants to revisit a previous tavily-research task and doesn't have the request_id handy, or says "what did that research on X find again", "pull up my last research on Y", "show me past research tasks", or "find that report I ran earlier". Also use it right after a research run to log it, so it can be found later. Do NOT use this for a fresh research task — start there with tavily-research directly.
allowed-tools: Bash(tvly *), Bash(python3 *)
---

# tavily runs

Keep a local, searchable record of past `tavily-research` runs, so they can be found later by topic instead of by remembering a `request_id`.

## Known issue: `research status`/`poll` currently require API-key auth, not OAuth

**TODO: remove this section once Tavily's MCP server exposes a `tavily_get_research` tool — tracked as a gap report filed 2026-08-28.**

As of 2026-08, re-fetching a run by `request_id` (the last step below) fails when the CLI is authenticated via `tvly login` (OAuth) — that path routes through Tavily's MCP server (`mcp.tavily.com`), which doesn't currently expose a `tavily_get_research` tool at all. `research status` returns `Unknown tool: 'tavily_get_research'`; `research poll` silently retries until it times out instead of surfacing that error. The local logging/lookup steps in this skill are unaffected — only the "re-fetch the full result" step needs this.

Fix: authenticate with a raw API key instead of OAuth before using the re-fetch step:

```bash
tvly login --api-key tvly-YOUR_KEY
# or: export TAVILY_API_KEY=tvly-YOUR_KEY
```

## Why this exists

`tavily-research` already supports checking a specific run by ID (`tvly research status <request_id>`, `tvly research poll <request_id>`) — that's "I have the ID, what's the status." This skill covers the gap: "I don't have the ID anymore, I just remember roughly what I asked." Tavily's API has no cross-session history endpoint to query, so this is a local logging convention, not a new Tavily capability.

## How it works

1. **After every `tavily-research` run**, append a record to a local log: timestamp, the query, the model used, the `request_id`, and where the output was saved.
2. **To look something up later**, search that local log by keyword instead of trying to recall the ID.

## Quick start

**Log a run right after it completes:**

```bash
python3 << 'PYEOF'
import json, os
from datetime import datetime, timezone

log_path = ".tavily/runs.jsonl"
os.makedirs(os.path.dirname(log_path), exist_ok=True)

record = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "query": "Competitive landscape for AI code assistants",
    "model": "pro",
    "request_id": "req_abc123",     # from the research() response
    "output_file": "reports/ai_code_assistants.md",
}

with open(log_path, "a") as f:
    f.write(json.dumps(record) + "\n")

print("Logged.")
PYEOF
```

**Look up a past run by keyword:**

```bash
python3 << 'PYEOF'
import json

with open(".tavily/runs.jsonl") as f:
    records = [json.loads(line) for line in f if line.strip()]

keyword = "code assistants"
matches = [r for r in records if keyword.lower() in r["query"].lower()]

for m in matches:
    print(f"[{m['timestamp']}] [{m['request_id']}] {m['query']}")
    print(f"  model={m['model']}  output={m.get('output_file', 'n/a')}")
PYEOF
```

**Re-fetch the full result for a match, if still within Tavily's retention window:**

```bash
tvly research poll req_abc123 --json
```

## Options

| Consideration | Guidance |
|---|---|
| Log location | `.tavily/runs.jsonl` at the project root keeps it alongside the project; use a home-directory path instead for logging across projects |
| What to log | query text, model, request_id, output file path, and a short free-text tag if the user gives one ("Q1 competitor scan") |
| Retention | Tavily's own run retrieval (`research poll`) may expire after some time — if the user needs the actual report kept forever, always also save `-o <file>` on the original run, and log that file path here |

## Tips

- **Log at the moment of running, not after the fact.** It's cheap to append one line right after a research call completes; it's much harder to reconstruct after the fact.
- **Always pair with `-o <file>`** on the original `tvly research` call — the log should point at a durable local copy of the report, not rely solely on Tavily's hosted retention.
- **This can be a habit inside `tavily-research` rather than a separate step** — if it's simpler for a given workflow, just always log after research calls without treating it as a distinct invocation.

## See also

- [tavily-research](../tavily-research/SKILL.md) — the skill this one logs runs for
