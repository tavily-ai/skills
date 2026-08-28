# tavily-monitor — Explanation

## Use Case

You want to keep an eye on a page, a company, or a topic — a competitor's pricing page, a regulatory filing tracker, a product's changelog — and get told only when something actually changes, instead of checking it yourself every day.

## How it works, in plain terms

On a schedule you set, it re-checks the thing you asked about, compares it to what it saw last time, and only speaks up when there's a real change to report.

## Built With

`tavily-extract`/`tavily-search` for the actual "check the page" step, plus Claude Code's built-in scheduling (`/loop` or cron) to handle the "keep doing this on a cadence" part — Tavily itself has no scheduling API, so this skill is explicit that it's an orchestration layer on top of Tavily, not a new Tavily platform feature.

## Ways to Use This Skill

- "Monitor this page for changes"
- "Watch for pricing or policy updates on this site"
- "Alert me if this competitor's page changes"
- "Track this changelog and let me know when it updates"
