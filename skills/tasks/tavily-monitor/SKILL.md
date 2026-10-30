---
name: tavily-monitor
description: |
  Build a Tavily search or extraction that runs on a cadence, with a saved baseline. Search monitors set max_age_hours to the interval so a cached copy from before it is not returned. Use when the user wants to monitor, track, watch, or be alerted when something changes, or asks for a recurring check of a query or a page. For a deep comprehensive report use tavily-research. For a one-time lookup use tavily-search. For a one-time table use tavily-list.
allowed-tools: Bash(tvly *)
---

# Tavily monitor

Turn a watch into a search or an extraction that can run again unchanged, then
run it once and save the baseline. The monitor file is the result.

Use `tavily-search` to run the check. If it isn't installed, run `npx skills add tavily-ai/skills --skill tavily-search` and read its SKILL.md before continuing.

## When this is the wrong skill

- The user wants a deep comprehensive report. Use `tavily-research`. If it isn't installed, run `npx skills add tavily-ai/skills --skill tavily-research` and read its SKILL.md before continuing.
- The user wants every current match, once. Use `tavily-list`. If it isn't installed, run `npx skills add tavily-ai/skills --skill tavily-list` and read its SKILL.md before continuing.

## Pick the kind

| You have | Kind | What "changed" means |
|---|---|---|
| A topic, and the pages are not known yet | search | A result URL that was not in the previous snapshot |
| One or more known URLs | extract | The hash of that page's extracted content changed |

Use search for mentions, news, jobs, and anything where new pages appear. Use
extract for a pricing page, a changelog, a docs page, or a status page.

## Steps

1. Write the query or the URL list so the next run can reuse it verbatim. Follow
   `tavily-search` for how to shape it. Leave dates and "latest" out of the
   query. The snapshot, not the wording, decides what is new.
2. Write the change rule in one sentence. For a search, a new URL is the
   alert. A URL from the last snapshot that is missing this run is not an
   alert: a page that could not be fetched live is left out. For an extract, a
   changed hash is the alert, and the alert quotes the part the user cares
   about (the price, the version), not the whole page.
3. Name a cadence. Use the one the user asked for. If they did not, use daily
   for news and changelogs, and weekly for a page that changes slowly, and say
   which you chose. On a search, set `max_age_hours` to that interval in hours,
   so a cached copy older than the cadence is not returned. Daily is 24, weekly
   is 168. Use `0` when the interval is under an hour, and `720` when it is
   longer than 30 days. Read how the parameter works in the search reference of
   `tavily-search`. Write the number in the monitor file and send it on every
   run, including the first. Extract does not take `max_age_hours`.
4. Run it once. If the results are the wrong kind of thing, fix the query or
   the URLs and run again before you save anything. If the search is refused
   with `434`, the run did not complete. Say so, and leave `snapshot.json` as
   it was.
5. Save the monitor and the snapshot. The next run reads the monitor, runs the
   same search or extract, reports only what the change rule flags, and
   replaces `snapshot.json`.

Create `monitors/{name}/` in the working directory. The name is sentence case,
3 to 6 words, letters, numbers, and single spaces. Quote it in shell commands.

Do not start a scheduler unless the user asks for one. When they do, and the
environment has a way to run on that cadence, point it at this folder.

A later change to the query or the URL list is a new monitor. It gets a new
folder and a new baseline. Editing them in place makes the next diff meaningless.

## Output

`monitors/{name}/monitor.md`:

```markdown
# {Name}

- Cadence: {daily | weekly on Monday | the schedule the user asked for}
- Kind: search | extract
- Query: {the query, for a search}
- URLs: {one per line, for an extract}
- max_age_hours: {the cadence in hours, search only}
- Alert when: {the change rule}
- Snapshot: snapshot.json

## Run again

Read this file. Use `tavily-search` to run the same search or extract. On a
search, pass `max_age_hours` from this file. Compare the result to
snapshot.json using the alert rule above. Report only the changes. Then
replace snapshot.json with this run. If the search is refused with `434`,
report that and keep the snapshot.
```

`monitors/{name}/snapshot.json`:

```json
{
  "ran_at": "YYYY-MM-DD",
  "kind": "search",
  "query": "",
  "items": [{ "url": "", "title": "", "snippet": "" }]
}
```

For an extract, store `pages` instead of `items`: `url`, `sha256` of the
extracted content, and a short excerpt of the part being watched.

In the reply, give the cadence, `max_age_hours` for a search, the query or the
URLs, the alert rule, and the folder path, plus what the baseline already shows.
