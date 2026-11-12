---
name: tavily-search
description: |
  Use this skill whenever a task needs the web: searching for information, checking current facts or news, finding sources, reading a URL, finding a page on a site, or collecting many pages from a site. Use it for anything past your training data or anything the user wants verified online. Runs the `tvly` command (Tavily's CLI).
allowed-tools: Bash(tvly *)
---

# Tavily search

Use the `tavily_search`, `tavily_extract`, `tavily_map` and `tavily_crawl` tools if your tool list has them
(some clients add a prefix such as `mcp__tavily__`). Otherwise run `tvly <command>` directly (the command is `tvly`); there's no
need to check for it first. If neither works, follow [setup](references/setup.md).

Parameters are named as in the API (`max_results`). The CLI spells them as flags (`--max-results`) with
comma-separated lists (`--include-domains sec.gov,reuters.com`). For exact parameters, read the tool schema,
run `tvly <command> --help`, or see the [API reference](https://docs.tavily.com/documentation/api-reference/endpoint/search).

| You have | You need | Use |
|---|---|---|
| A question or topic | Sources, facts or news | Search |
| URLs | Their content | Extract |
| A site, not the exact page | The right page's URL | [Map](references/map.md) |
| A site section | Many of its pages | [Crawl](references/crawl.md) |

## Search

**Use advanced search.** Set `search_depth` to `advanced` (`--depth advanced` in the CLI) for every search
unless the user needs a fast answer to a simple lookup. It reaches more sources and ranks the passages that match your query.

**Write queries for a search engine.** Use the names and terms you expect on the page, not the user's whole
request. Split a question with several parts into one focused search per part. For a long written report,
search each part separately and extract the main sources for each before you write.

**Follow your leads.** When a result names a likely answer, test it right away: search that name with the
other details you know, or extract its page. Keep a lead that fits most details until a source contradicts it; a detail you can't confirm doesn't rule it out. When a search misses,
search the details again in their own words before adding names or filters you guessed, and build lists of
candidates from results, not memory. When a detail keeps coming back empty, work out what it refers to, such as
the role, event or term, and search for that.

`tvly search` prints each result's title, full URL and the first 600 characters of its matching passages. Add
`-o .tavily/<name>.json` to also save every result whole, so you can go back to it instead of searching again.
`--max-chars 0` prints the passages whole. Read a promising page in full with `tvly extract <url>`.

**Batch independent searches.** Issue the searches for one step together in one turn, one call each: separate
`tavily_search` calls with MCP tools, or separate Bash calls with the CLI, each holding a single `tvly` command.
MCP calls run in parallel; Bash calls run one after another but still use one turn. Avoid `&`, `$(...)` and
loops, which make the client ask for permission. Put the query in single quotes:
`tvly search 'Rust 2024 edition release date' --depth advanced --max-results 10 -o .tavily/rust-2024.json`.

**Work from saved files.** Keep results in `.tavily/` in the current folder and read them with `head`, `grep` or
`python3`. `-o` creates the folder and keeps it out of git, so don't create it yourself. For example, to find a name or number in a long page:

```bash
tvly extract 'https://example.com/report' -o .tavily/report.json
python3 -c 'import json,re; t=json.load(open(".tavily/report.json"))["results"][0]["raw_content"]; [print(t[max(0,m.start()-200):m.end()+200], "\n---") for m in re.finditer("2019", t)]'
```

Read pages with `tvly extract`, not `curl` or `wget`.

**Ask for 10 results.** Set `max_results` to 10 (`--max-results 10`). **Narrow before you widen.** Filters help more than raising `max_results` further. Use `time_range` or dates for
recent events or a stated period. Use `include_domains` when the answer lives on an official or named site; it
is a hard filter, so search again without it if it doesn't find the page.

**Keep large results on disk.** When a result is long, such as raw page content or a crawl, save it under
`.tavily/` and read only the parts you need. An MCP result lands straight in your context, so keep those calls
small.

**With MCP tools, don't retype results into files.** An MCP result is text in your context, so saving it means
typing it out again, which costs tokens and can change the content. When the user asks for results stored raw or
exact, run `tvly` with `-o` (`--output-dir` for a crawl) if you can. Otherwise say the saved copy would be
retyped, not exact, and offer the CLI [setup](references/setup.md) instead of installing it unasked.

**Read the results critically.** Count independent sources, not results. Treat a generated answer as a summary
to check, never as a source.

## Extract

Extract returns up to 20 URLs per call as markdown, including pages built with JavaScript.

- Extract only the few results worth reading. Snippets answer most facts.
- Extract full pages by default. Pass `query` (`--query`) only to isolate one fact on a long page; if the passages come
  back cut off near what you need, extract again without it.
- Rerun with `extract_depth` set to `advanced` (`--extract-depth advanced`) when a page is built with JavaScript, the content is in a table, or
  `basic` came back empty. Check `failed_results` every time and say which pages couldn't be read.

## When to stop

- Stop once two independent sources agree on a fact.
- Before you answer, close any gap your draft would mark unconfirmed or fill from memory: run one targeted
  search or reread the saved page.
- For releases, ownership, official figures and decisions by a named body, confirm on the official domain or
  repository. A secondary site or a generated answer is not enough.

## Hand off the job

When the user wants an in-depth report that needs many sources gathered and weighed, such as an analysis, a
comparison across several criteria or an in-depth investigation, use `tavily-research` instead of your own searches.
If it isn't installed, run `npx skills add tavily-ai/skills --skill tavily-research` and read its SKILL.md first. A
single fact or answer to find stays here.
