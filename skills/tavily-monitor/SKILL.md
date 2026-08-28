---
name: tavily-monitor
description: |
  Watch a page, site, or topic for changes on a recurring schedule and only speak up when something meaningfully changed. Use this skill when the user wants to track a competitor's pricing page, watch for regulatory filings, keep an eye on a changelog, or says "monitor this page", "watch for changes", "alert me if X changes", "track this site", or "let me know when this updates". This is an orchestration skill built from Tavily's extract/search plus Claude Code's scheduling — Tavily itself has no scheduling API, so this skill documents that explicitly rather than implying otherwise.
allowed-tools: Bash(tvly *), Bash(python3 *)
---

# tavily monitor

Check something on the web on a recurring cadence, compare it to what you saw last time, and only report back when there's an actual change.

## Before running any command

If `tvly` is not found on PATH, install it first:

```bash
curl -fsSL https://cli.tavily.com/install.sh | bash && tvly login
```

See [tavily-cli](../tavily-cli/SKILL.md) for alternative install methods and auth options.

## Important: this is orchestration, not a Tavily platform feature

Tavily's API is stateless — it has no built-in scheduling, alerting, or "watch this" endpoint. This skill combines:

- **Tavily** (`tvly extract` or `tvly search`) for the actual "check the thing" step
- **Claude Code's scheduling primitives** (the `schedule` skill for cron-based recurring runs, or `/loop` for self-paced polling) for the "keep doing this on a cadence" step

Be upfront with the user about this — "monitor" here means "Claude Code re-runs a check for you," not "Tavily is watching this in the background on its own."

## When to use

- Watching a specific URL/page for content changes (pricing, terms, changelog, filing status)
- For a recurring *summary of new coverage* on a broad topic (rather than change-detection on one fixed page), that's a different pattern — see the `tavily-news-digest` idea in this repo's suggestions doc. This skill is for detecting *change*, not aggregating *new content*.

## How it works

1. **Baseline:** extract the target page (or run the target search) once, save the content and a hash/fingerprint of it to a local snapshot file.
2. **Schedule:** set up a recurring check (via the `schedule` skill for unattended cron, or `/loop` for an interactive session) at the cadence the user wants.
3. **Each run:** re-extract, compare to the saved snapshot.
   - No meaningful difference → stay quiet, update the snapshot's "last checked" timestamp, don't bother the user.
   - Real difference → summarize what changed and notify.
4. **Update the snapshot** with the new content after each check, whether or not it changed.

## Quick start

**1. Take the baseline snapshot:**

```bash
python3 << 'PYEOF'
import json, subprocess, hashlib, os

url = "https://example.com/pricing"
raw = subprocess.check_output(['tvly', 'extract', url, '--json'], stderr=subprocess.DEVNULL)
data = json.loads(raw)
content = data['results'][0]['raw_content']

os.makedirs('.tavily', exist_ok=True)
snapshot = {
    "url": url,
    "content": content,
    "hash": hashlib.sha256(content.encode()).hexdigest(),
}
with open('.tavily/monitor_pricing.json', 'w') as f:
    json.dump(snapshot, f)

print("Baseline saved.")
PYEOF
```

**2. Set up the recurring check** — use the `schedule` skill for an unattended cron job, or `/loop <interval>` for a session-scoped recurring check. Point it at the diff script below.

**3. Each scheduled run — diff against the saved snapshot:**

```bash
python3 << 'PYEOF'
import json, subprocess, hashlib

url = "https://example.com/pricing"
path = ".tavily/monitor_pricing.json"

with open(path) as f:
    prev = json.load(f)

raw = subprocess.check_output(['tvly', 'extract', url, '--json'], stderr=subprocess.DEVNULL)
data = json.loads(raw)
content = data['results'][0]['raw_content']
new_hash = hashlib.sha256(content.encode()).hexdigest()

if new_hash != prev['hash']:
    print(f"CHANGED: {url}")
    # Optionally diff prev['content'] vs content and summarize the change in plain English
    # (e.g. via a quick tavily-research call or a direct text diff) before alerting the user.
else:
    print(f"No change: {url}")

with open(path, 'w') as f:
    json.dump({"url": url, "content": content, "hash": new_hash}, f)
PYEOF
```

## Options

| Consideration | Guidance |
|---|---|
| Cadence | Match check frequency to how often the thing actually changes — a pricing page doesn't need hourly checks; a live filing tracker might |
| Snapshot storage | Keep one JSON file per monitored target under `.tavily/`, named for what it watches |
| Noisy pages | If a page has content that changes trivially every load (timestamps, ad slots), hash a specific section's content, not the whole page — extract with `--query`/`--chunks-per-source` to narrow to the relevant section first |
| What changed | For a human-readable summary of *what* changed (not just *that* it changed), diff the old and new text and optionally run it through `tvly research` for a plain-English summary |

## Tips

- **Don't over-schedule.** Every check costs an API call — pick a cadence that matches how often the target realistically changes.
- **Narrow what you hash.** Whole-page hashing catches every cosmetic change (ads, timestamps, view counts) as a "change" — extract just the section that matters when possible.
- **Say what kind of change, not just that one happened.** "Changed" is a weak alert — "the Pro plan price moved from $49 to $59" is a useful one.
- **Be explicit this is Claude Code doing the scheduling**, not a Tavily background service — if the user closes the session or the cron isn't wired up, monitoring stops.

## See also

- [tavily-extract](../tavily-extract/SKILL.md) — the underlying content-fetch this skill re-runs on a schedule
- [tavily-search](../tavily-search/SKILL.md) — for monitoring a topic broadly rather than one fixed URL
