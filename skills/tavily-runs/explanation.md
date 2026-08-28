# tavily-runs — Explanation

Skill definition: [SKILL.md](SKILL.md)

## Use Case

You kicked off a big research task last week, or a few days ago, and you don't remember the run ID — you just remember roughly what you asked. This lets you find and re-open it by topic instead of by ID.

## How it works, in plain terms

Every time you run a research task, it quietly keeps a local record of what you asked and where the result lives, so later you can say "what did that research on X find again?" instead of needing to have saved the ID yourself.

## Built With

`tavily-research`'s existing async run tracking (`request_id`, `status`, `poll`) already covers "check on a run I have the ID for." This adds the missing piece: a local index so you don't need the ID in the first place.

## Ways to Use This Skill

- "What did that research run on X find again?"
- "Pull up my last research on Y"
- "Show me past research tasks"
- "Find that report I ran last week"
