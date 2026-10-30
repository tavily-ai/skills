# Using map well

Map lists the URLs on a site without reading their content, so it is much
faster than crawling. Use it when you know which site holds the answer but not
which page, or when you need to see how a site is organized before you crawl
it.

## Find a page, then extract it

The most common use is a two-step lookup. Map the site with `instructions`
that describe what you're looking for, such as "API authentication" or
"pricing and plans", then extract the one or two URLs that match. This costs
much less than crawling the site to find a single page.

## Learn the structure before a crawl

When you need many pages from a site you don't know, map it first and read the
paths. The URL patterns tell you which section to crawl, for example
`/docs/api/` instead of the whole domain, and they let you write `select_paths`
patterns that match real URLs.

## Keep it bounded

Map starts one level deep from the URL you give it. Raise the depth only when
the page you need is buried, and keep a `limit` on every call. If the site has
a docs or blog subdomain, start the map there instead of at the home page.

Full parameter list: https://docs.tavily.com/documentation/api-reference/endpoint/map
