---
name: tavily-entity
description: |
  Fill in a company, person, or organization for a CRM from the web, using Tavily, including a CSV of rows the user already has. Identifies the right entity when others share the name, then fills the fields from authoritative sources. Use when the user wants to enrich an account, a spreadsheet, or a pasted list of known names, or says "enrich", "CRM", or "who is". For discovering matches use tavily-list. For a deep comprehensive report use tavily-research.
allowed-tools: Bash(tvly *)
---

# Tavily entity

Resolve one entity and return a CRM record. The name is not the identity.
Confirm which entity it is, then fill the record from authoritative sources.
Every value comes from a page you read. An empty field stays empty.

Search and extract as `tavily-search` describes; load it only if it isn't
loaded yet. To discover new matches use `tavily-list`; for a deep report use
`tavily-research`.

## Identify the entity first

People and companies share names. A record that mixes two of them is worse
than an empty one. Isolate a single entity before you fill any field.

1. Take the type (company, person, or organization) and every identifier the
   user already gave: a domain, a city, an employer, a title, a product.
2. Search the name and look for other entities that use it. A common name, a
   name that is also a product or a place, or a person with a common name is a
   collision until you prove otherwise.
3. You have the right entity only when two identifiers agree. For a company,
   the name plus its own domain. For a person, the name plus an employer, a
   location, or a profile they control, and the organization on that profile
   has to match. One page that mentions the name is not identification.
4. If more than one entity still fits, stop and return the candidates. Do not
   pick the one with more results, and do not copy a field from one candidate
   onto another.
5. Put a stable identifier, the domain or the employer, into every later
   search, not the bare name.

## Read authoritative sources

Fill a field from the page that owns the fact. Extract that page. A snippet is
not enough for a number.

- The entity's own site, an official profile, and a filing or registry come
  first for facts the entity publishes: what it is, where it is, who leads it,
  what it sells. For a person, the employer's team page or a profile the person
  controls comes before a people-search site.
- A directory, a data broker, or a roundup is a lead to that page. Use it as
  the source of a field only when no authoritative page states the fact, and
  say so in the source note.
- When two authoritative pages disagree on a number, keep the more direct one
  and record the other in the source note. Do not average them.
- Include a published email or phone number only when a page shows it.

Extract the pages that own the fields you need in one call. Search for recent
news, with the domain or employer in the query, only when the user wants recent
signals or a full record.

## A CSV of known rows

When the user already has the entities, in a file or a pasted table, enrich
those rows. Do not go looking for new names.

1. Read the rows and count them. Use the fields they named. If they did not
   name fields, ask once, then use the same fields on every row.
2. Above 25 rows, tell them the count and the fields and wait for a go-ahead.
3. For each row, follow Identify the entity first and Read authoritative
   sources. A row you cannot isolate stays unresolved: blank new fields, a note
   on what collided, and no guessed values.
4. Write the original columns plus the new fields, a source for each new
   field, and a status of `filled` or `unresolved` to
   `{name}-enriched-{YYYY-MM-DD}.csv`. Use a CSV writer.

The CSV is the result. In the reply, give the number filled, the number
unresolved, and the path. Do not paste a record per row.

## Output

When the user asked specific questions, answer those in the reply, with a source
for each value, and skip the template. For a full record, use this:

```markdown
# {Name}

type: company | person | organization
identified by: {domain, employer, or other stable identifier}
as_of: {YYYY-MM-DD}

| Field | Value | Source |
|---|---|---|
| website | | |
| description | | |
| industry | | |
| headquarters | | |
| founded | | |
| employees | | |
| funding | | |
| revenue | | |
| linkedin | | |

## People
| Name | Title | Source |
|---|---|---|

## Recent signals
- {YYYY-MM-DD}: {fact} — {url}

## Unknown
- {field}: {what you tried}
```

For a person, the field rows are title, organization, location, and profile URL,
and People appears only when the user asked for related people. Drop a field
row that does not apply to this type. A field that applies and could not be
filled stays in the table with a blank value and a line under Unknown.
Description is one or two sentences grounded in the about page or profile.
Recent signals are at most five dated items: funding, a launch, a leadership
change, hiring. Omit a section that has no rows.

When you cannot pick one entity:

```markdown
# {Query}

| Name | Website | What separates it from the others |
|---|---|---|
```
