# Using crawl well

Crawl starts from a URL, follows links, and returns the content of each page
it reaches. Use it when you need many pages from one site, such as a whole
docs section, a changelog archive, or pages that aren't linked from the main
navigation.

## Always focus the crawl

An unfocused crawl returns every page it reaches and fills your context with
content you won't use. Give every crawl `instructions` that describe the
content you want. When the results go into your context, also ask for chunks
per page (`chunks_per_source`, where your channel supports it) so each page
comes back as its relevant parts instead of in full.

## Start small

Each extra level of depth multiplies the number of pages and the time the
crawl takes. Start at depth 1 with a `limit` of about 20 pages, look at what
came back, and widen the crawl only if the pages you need are missing. Always
set a `limit`, because without one a crawl can run much longer and cost much
more than expected.

## Aim it at the right section

When you know the section you need, restrict the crawl to it with
`select_paths`, such as `/docs/.*`, instead of starting at the home page. When
you don't know the site, map it first and build the path patterns from the
URLs you see.

## Reading pages or saving them

There are two reasons to crawl. When you need the content to answer a
question, keep the crawl focused and chunked as described above. When the user
wants a copy of the site, such as docs to keep locally, they want full pages
saved as files. Only the CLI can write files directly (`--output-dir`); tell an
MCP user that saving files needs the CLI.

## Check what failed

Look at `failed_results` after every crawl. Retry pages that failed with
`advanced` extract depth, and tell the user about any section the crawl
couldn't read.

Full parameter list: https://docs.tavily.com/documentation/api-reference/endpoint/crawl
