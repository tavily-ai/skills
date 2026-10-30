---
name: tavily-list
description: |
  Build a deduplicated table of matches for a set, using Tavily. The table is what search returned, not every match that exists. Use when the user wants a list, all of something, or a table with duplicates removed. Confirm the columns and a cap before searching. For one CRM record, or a CSV of rows they already have, use tavily-entity. For a deep comprehensive report use tavily-research.
allowed-tools: Bash(tvly *)
---

# Tavily list

Return the matches you can verify for a set, one row each, with duplicates
merged. The table is the result. It is not every match that exists. Do not
collapse rows into a summary, and do not call the table complete.

Use `tavily-search` to search and read pages. If it isn't installed, run `npx skills add tavily-ai/skills --skill tavily-search` and read its SKILL.md before continuing. When you open many list pages, save the responses and filter them the way that skill describes, so the raw pages stay out of context.

## When this is the wrong skill

- The user wants one record filled in, or fields added to a CSV of rows they already have. Use `tavily-entity`. If it isn't installed, run `npx skills add tavily-ai/skills --skill tavily-entity` and read its SKILL.md before continuing.
- The user wants a deep comprehensive report. Use `tavily-research`. If it isn't installed, run `npx skills add tavily-ai/skills --skill tavily-research` and read its SKILL.md before continuing.

## Steps

1. Before any search, fix the inclusion rule in one sentence, the columns, and
   a cap. Columns always include name, website or profile, a one-line
   description, and the source URL, plus any the user named. If they did not
   name the extra columns or a cap, ask once and wait. If the set is unbounded
   ("every restaurant"), that question includes the boundary, such as a city
   or a category. A row gets in only when it matches the inclusion rule.
2. Search the set from several angles: the category, "list of" roundups,
   directories, and the names that appear on pages you have already opened. One
   query does not cover the set. Pull every name off a page that is itself a
   list.
3. Give each row an identity. For an organization, that is the website host
   with `www` removed. For a person, it is the profile URL, or the name plus
   the organization when there is no profile. For a product on a shared host,
   it is the canonical URL.
4. Merge rows that share an identity. Keep the fuller row and record the names
   you folded in. When a match has no website yet, search for it once before
   you finish. If it still has none, keep the row and leave the website blank.
5. Stop at the cap, or when two new angles in a row add no rows. Say which.
   Either stop means this pass is finished. Neither means the set is complete.
6. When the user wants more, search again and exclude every name and website
   already in the table. Append only new rows, then merge by identity again.
   Raise the cap by the number they asked for.

Use the same columns on every row. Leave a cell blank when no page states it.

Use `tavily-entity` for a row only when the user asked for CRM fields on each match. If it isn't installed, run `npx skills add tavily-ai/skills --skill tavily-entity` and read its SKILL.md before continuing. Otherwise a list row stays a list row.

## Output

Show the table in the reply, and save the same markdown to `lists/{title}.md`
in the working directory. The title is sentence case, 3 to 6 words, letters,
numbers, and single spaces.

```markdown
# {Title}

Inclusion: {one sentence}
As of: {YYYY-MM-DD}
Cap: {N}
Stop: {two angles added nothing | hit the cap}
Rows: {count after dedup}
Coverage: not exhaustive. This is what the angles below returned.

| Name | Website | Description | {asked columns} | Source |
|---|---|---|---|---|

## Merged
- {kept name} ← {other names} ({shared website})

## Coverage
Angles: {the queries and the list pages you opened}
Excluded this pass: {names and websites already kept, or none}
Likely gaps: {the part of the set this pass could not see}
```
