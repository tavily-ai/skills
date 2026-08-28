# tavily-enrich — Explanation

## Use Case

You have a list of companies, people, or products — maybe just names, maybe a half-finished spreadsheet — and you want Tavily to go find the missing details (CEO, funding raised, headquarters, employee count, contact info, whatever you specify) and hand you back a completed file.

## How it works, in plain terms

It reads your list, looks each item up on the web, and writes the answers into new columns next to your existing data — same file, filled in.

## Built With

`tavily-research`'s existing "structured output" mode, run once per row/entity with a schema you define (e.g. `{ceo, funding_raised, hq_location}`). That capability already exists in Tavily — this skill just wraps it in a "point it at a spreadsheet" workflow instead of requiring the user to write the loop and schema by hand.

## Ways to Use This Skill

- "Enrich this list of companies with funding and CEO info"
- "Fill in the missing contact info for each of these people"
- "Add headquarters and employee count to this spreadsheet from the web"
- "Complete these columns using web data"
