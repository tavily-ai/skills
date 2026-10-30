---
name: tavily-research
description: |
  Research a topic in depth with Tavily. Use this skill when a question needs many sources gathered and weighed together: analysing a market, policy, technology or trend, comparing options across several criteria, reviewing the literature, or any request to research, investigate or analyze something in depth. A single fact or answer to find, even one with many clues, is a tavily-search task. For one CRM record use tavily-entity, for a table of matches use tavily-list, and for a recurring check use tavily-monitor.
allowed-tools: Bash(tvly *)
---

# Tavily research

Use this when the answer has to be built from many sources. A single fact or
answer to find is a search: follow `tavily-search` instead.

Search and read pages as `tavily-search` describes. Load it only if it isn't
loaded yet.

## Steps

### 1. Ask only when the answer would change the research

Ask when a term has two meanings, the user assumed a place, or a name is two
different entities. Otherwise start.

### 2. Split the question

Split into subtopics that do not overlap and that together cover the question.
Carry the user's limits with every subtopic: dates, places, and what is out of
scope. Use 3 subtopics when you are unsure, 4 for a comparison with separate
criteria, 5 for separate entities, regions or domains, and more only for a
large set.

### 3. Research the subtopics together

**With subagents:** choose a title of 3 to 6 words, create
`research_notes/{title}/` and `reports/` in the working directory, and start
one general-purpose subagent per subtopic in the same turn. Give each the
subtopic, the key questions, the user's limits, the absolute path of its notes
file, and this first step: read `references/researcher.md` at its absolute path
next to this skill.

**On your own:** run each subtopic's searches in parallel, as `tavily-search`
describes, and extract the main sources for each. Keep the findings and their
URLs in your context. Don't write notes files.

### 4. Fill thin parts, then write

Before writing, run another round for any part of the question that would
leave its section thin.

### 5. Write and deliver the answer

Follow `references/report-writer.md`. On your own, write it once, as
your reply. Save it to `reports/{title}.md` only when the user asked for a
file, and then give the path after the report. With subagents, have one agent
write `reports/{title}.md` from the notes, then give the user the full report
in your reply, followed by its path.

If this conversation already produced a report on the subject, build on it:
research only what is new or needs checking again.
