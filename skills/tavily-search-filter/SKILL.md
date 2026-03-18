---
name: tavily-search-filter
description: |
  Search the web and extract only the relevant content from each page via the Tavily CLI. Use this skill when the user wants filtered, clean search results — not raw pages full of nav bars and boilerplate. Triggered by "search and filter", "find the important parts", "clean search results", "extract the key details from search", "search for X and pull out Y", or any search where the user wants curated, noise-free content rather than raw page dumps. Also use for document-heavy searches like SEC filings, research papers, legal docs, or technical specs where extracting specific sections matters.
allowed-tools: Bash(tvly *)
---

# tavily search --filter

Search the web with Tavily and extract only the relevant content from each result. The `--filter` flag tells the CLI to fetch full page content — you then extract the important parts yourself.

## Before running any command

If `tvly` is not found on PATH, install it first:

```bash
curl -fsSL https://cli.tavily.com/install.sh | bash && tvly login
```

## Usage

Always use `--filter` with `--json`:

```bash
# Basic filtered search
tvly search "NVIDIA 8-K SEC filing 2024" --filter --json

# With filter instructions
tvly search "python web frameworks" --filter "only actively maintained OSS" --json

# Domain-scoped
tvly search "NVIDIA 8-K filing" --filter --include-domains sec.gov --json

# Financial topic
tvly search "NVIDIA quarterly earnings" --filter --topic finance --json
```

## What --filter does

The `--filter` flag automatically:
- Fetches full page content (`raw_content`) for each result
- Bumps `max_results` to 8 (more candidates to filter from)
- Adds a `filtering` object to the JSON output with `requested: true` and any instructions

## What you do after

When the JSON output contains `"filtering": {"requested": true}`, you MUST aggressively clean every result before presenting it. Be ruthless — if a token doesn't help answer the query, it must go. The raw_content is a full web page; your job is to reduce it to just the answer.

### Mindset

Think of raw_content as ore. 80–95% is rock (navigation, boilerplate, off-topic sections, filler sentences). You extract only the metal (facts, data, code, definitions that answer the query). Every line you keep must justify its existence by directly answering or supporting the query.

### Step 1: Drop bad results entirely

Remove any result where:
- `raw_content` is empty or very short (< 200 chars of actual content)
- The page is paywalled ("subscribe to read", "sign in to continue")
- The content is completely off-topic relative to the query

Do not present dropped results at all.

### Step 2: Extract and restructure each kept result

For each surviving result, scan its `raw_content` and produce a **new, clean `content`** by:

1. **Scan the full page** and identify ONLY the paragraphs, tables, code blocks, and lists that directly answer the query.
2. **Copy those pieces verbatim** — do not summarize, paraphrase, or rewrite. Preserve the original author's words.
3. **Keep structural markdown** — headings above kept sections, table formatting, code fences, numbered lists. These carry meaning.
4. **Cut everything between relevant pieces** — if there are 3 relevant paragraphs spread across a 500-line page, output just those 3 paragraphs with their headings.
5. **Remove filler within kept sections** — strip intro fluff ("In this article we will...", "Let's dive in..."), transition sentences, and recap paragraphs.

### Step 3: Deduplicate across results

If multiple results contain the same information, keep the best version (most detailed, best structured) and drop or abbreviate the others. Never repeat the same fact across results.

### Step 4: Format the output

Present each result as:

```
## [Title](url)

[cleaned content — ONLY the extracted relevant pieces, nothing else]
```

If `filtering.instructions` is set, apply those as additional criteria on top of query relevance.

### What counts as relevant (KEEP verbatim)

- Sentences containing specific facts, numbers, dates, or names that answer the query
- Data tables, comparison tables, financial tables (complete — don't cut rows)
- Code blocks that demonstrate the queried concept
- Definitions, specifications, technical explanations of the queried topic
- Direct quotes from authoritative sources

### What is NEVER relevant (ALWAYS STRIP)

- Any site chrome: navigation, menus, breadcrumbs, sidebars, search bars
- Marketing: "Related articles", "You may also like", "Read more", "Subscribe"
- Banners: cookie notices, privacy popups, newsletter signups, app download prompts
- Social: author bios, share buttons, comment sections, follower counts
- Footer: copyright, terms of service, contact links, site maps
- Filler: "In this article...", "Let's explore...", "As we discussed...", "Conclusion" sections that just restate what was already said
- Images/media references: `![Image...]`, video embeds, podcast links
- Anchor link markup: `[¶](#section)`, `[Link to this heading]`
- Table of contents lists (the actual section content is what matters)

### Token budget

Target **150–600 tokens per result** of pure signal. A result that produces only 2 relevant sentences (50 tokens) is fine — don't pad it. A result with a critical data table may go to 800+ tokens — that's fine too. But a 2000-token cleaned result means you kept too much noise.

## Examples

### SEC filing

```bash
tvly search "NVIDIA 8-K SEC filing 2024" --filter "extract material events and financial details" --include-domains sec.gov --json
```

The raw_content will be ~40,000 chars of SEC page chrome, navigation, disclaimers, and filing boilerplate. Extract only:

```
## [NVIDIA 8-K Filing](https://sec.gov/...)

**Filed:** January 15, 2024 | **Form:** 8-K

**Item 2.02 — Results of Operations**
- Revenue: $22.1B (up 265% YoY)
- Data Center revenue: $18.4B (up 409% YoY)
- GAAP EPS: $4.93 (up 765% YoY)
- Gross margin: 76.0%

**Item 7.01 — Regulation FD Disclosure**
Management projects Q1 FY2025 revenue of $24.0B ± 2%.
```

NOT this (still noisy):

```
NVIDIA Corporation filed an 8-K with the Securities and Exchange Commission.
The company is a leading technology company... [boilerplate]
Table of Contents: Home | Filings | About | Contact...
Skip to main content | Accessibility | Privacy Policy...
```

### Technical comparison

```bash
tvly search "React Server Components vs client components" --filter "differences and when to use each" --json
```

The raw_content per page will be ~35,000 chars. Extract only the comparison:

```
## [Understanding RSC](https://...)

| Aspect | Server Components | Client Components |
|--------|------------------|-------------------|
| Rendering | Server only | Client (hydrated) |
| Bundle size | Zero JS shipped | Included in bundle |
| Data fetching | Direct DB/API access | useEffect / SWR |
| Interactivity | None (no state/effects) | Full (useState, onClick) |
| Use when | Static content, data display | Forms, real-time UI |

Server Components cannot use `useState`, `useEffect`, or browser APIs.
They render on the server and stream HTML. Use Client Components for interactive elements.
```

### Python features

```bash
tvly search "Python 3.13 new features" --filter --json
```

From a 75,000-char Real Python article, extract only the feature descriptions:

```
## [Python 3.13: New Features](https://realpython.com/...)

**Improved REPL:** Color support, multi-line editing, block paste mode. History browsing with up/down arrows across sessions.

**Free-threaded mode:** Experimental build without the GIL. Enable with `--disable-gil` flag. Allows true parallel execution of threads.

**JIT compiler:** Experimental copy-and-patch JIT. Enable with `--enable-experimental-jit`. Targets ~5% speedup initially, foundation for future optimizations.

**Better error messages:** Colorized tracebacks, more specific `NameError` suggestions, helpful hints for common mistakes like missing `self` in methods.

**Removed dead batteries:** 19 deprecated stdlib modules removed (aifc, audioop, cgi, cgitb, chunk, crypt, imghdr, mailcap, msilib, nis, nntplib, ossaudiodev, pipes, sndhdr, spwd, sunau, telnetlib, uu, xdrlib).
```

## Options

All standard `tvly search` options work with `--filter`:

| Option | Description |
|--------|-------------|
| `--filter` | Fetch raw content for filtering (flag or pass instructions) |
| `--max-results` | Override candidate count (default: 8 with filter) |
| `--depth` | `basic` (default) or `advanced` for better content |
| `--include-domains` | Focus on specific domains |
| `--topic` | `general`, `news`, or `finance` |
| `--time-range` | `day`, `week`, `month`, `year` |
