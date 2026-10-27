# Conventions

`skills/core/tavily-search` is the core skill: it teaches the agent to use search, extract, map and crawl as one
toolkit, with search in `SKILL.md` and map, crawl and setup in `references/`. Task skills built on it (a report, a CRM
record, a table of matches, a recurring check) and the reworked SDK reference come in later changes.

`skills/tavily-research` and `skills/tavily-best-practices` are unchanged from before this layout and sit outside
`skills/core/` until those changes land.

## Naming

- The folder name must match the `name:` field in `SKILL.md`.
- Installed skills land side by side in one flat folder, so every name must be unique across the repo.
- Skill names start with `tavily-`.

## Where guidance lives

- Search and extract guidance (depth, result count, filters, when to extract) lives in the core `SKILL.md`; map, crawl
  and setup live in `skills/core/tavily-search/references/`. Other skills point to the core skill instead of restating
  that guidance, so a change there reaches every skill that uses it.

## Referencing another skill

Write every reference to another skill in this form:

> Use `tavily-research` for the report. If it isn't installed, run `npx skills add tavily-ai/skills --skill tavily-research` and read its SKILL.md before continuing.

The install line covers users who installed a single skill directly without running `tvly init`.
