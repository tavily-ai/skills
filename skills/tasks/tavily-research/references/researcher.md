# Researching one subtopic

You cover only the subtopic you were given. Other work is covering the rest.

Your notes are the only material the report writer gets. It will not search
again, so every finding the report might use has to be in the file, with its
URL.

## Before you search

Use `tavily-search` for every search and page read. If it isn't installed, run
`npx skills add tavily-ai/skills --skill tavily-search` and read its SKILL.md
before continuing. Follow that skill for how to write a query, when to extract
a page, and when to save large results and filter them. Do that before the
first search.

## How to gather

1. Name the gaps that stand between you and the key questions.
2. Search for those gaps. Run independent searches in parallel.
3. Extract the pages you expect to cite. A snippet is a lead. A number, a date,
   or a quote needs the page.
4. Repeat until a stop condition below is met.

Prefer the authoritative source, and cite that page. That is the institution
in a position to know: the company's own site, the paper, the filing, the
dataset, the official docs, a government or regulator, or a standards body.
Use another source when it adds a fact the authoritative page does not, and
say which is which.

When a page is long, or you are opening several at once, save the response and
filter it the way `tavily-search` describes, and write the notes from that
result. Keep the URL next to the fact.

Search again with different words when a query is thin. Repeating the same
query returns the same pages. For a recent topic, trust what you just
retrieved over your training data.

A subtopic usually takes about eight searches and extracts. Stop by twelve.

## When to stop

- The key questions have sourced answers.
- New searches return pages you already have.
- You are approaching twelve calls.

## What may go in the notes

Write a finding only when you can point at the page it came from. When several
pages support the same fact, cite the authoritative page. Cite a news story,
blog, or aggregator only when that page does not state the fact. When two
sources disagree, record both, authoritative first, and the disagreement.
When you cannot find a reliable source, write that as a gap. A gap is a useful
result.

Leave out a claim that is only a prediction, an unnamed source, or a number
that appears on aggregators and nowhere else, unless you label it that way in
the finding.

## Notes file

Save the file at the path in your assignment. The parent folder exists. Use
these sections, and no other top-level sections:

```markdown
# {Subtopic}

## {Key question}

### Takeaway
{One or two sentences.}

### Cited findings
- {Fact} — [Authoritative source](URL)
- {Fact only another source has} — [Secondary source](URL)
- {Fact} — [Authoritative source](URL); contradicted by [Other source](URL)

### Inferences
- {What the findings support, beyond what any one page states.}

### Gaps
- {What you could not answer, and what you tried.}
```

Repeat the key-question section for each question you were given. Every bullet
under Cited findings has a URL, and that URL is the authoritative page when
one exists. A fact with no URL goes under Gaps instead.
