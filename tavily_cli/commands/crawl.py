"""tavily crawl — crawl a website via the Tavily API."""

from __future__ import annotations

import click

from tavily_cli.common import handle_api_error, json_option


@click.command()
@click.argument("url")
@click.option("--max-depth", type=int, default=None, help="Levels deep to crawl (1-5, default: 1).")
@click.option("--max-breadth", type=int, default=None, help="Links per page (default: 20).")
@click.option("--limit", type=int, default=None, help="Total pages cap (default: 50).")
@click.option("--instructions", default=None, help="Natural language guidance for the crawler.")
@click.option("--chunks-per-source", type=int, default=None, help="Chunks per page (1-5, requires --instructions).")
@click.option("--extract-depth", type=click.Choice(["basic", "advanced"]), default=None, help="Extraction depth.")
@click.option("--format", "fmt", type=click.Choice(["markdown", "text"]), default=None, help="Output format.")
@click.option("--select-paths", default=None, help="Comma-separated regex patterns for paths to include.")
@click.option("--exclude-paths", default=None, help="Comma-separated regex patterns for paths to exclude.")
@click.option("--select-domains", default=None, help="Comma-separated regex patterns for domains to include.")
@click.option("--exclude-domains", default=None, help="Comma-separated regex patterns for domains to exclude.")
@click.option("--allow-external/--no-external", default=None, help="Include external domain links.")
@click.option("--include-images", is_flag=True, default=False, help="Include images.")
@click.option("--timeout", type=float, default=None, help="Max wait time in seconds (10-150).")
@click.option("--output", "-o", "output_file", default=None, help="Save JSON output to file.")
@click.option("--output-dir", default=None, help="Save each page as a .md file in this directory.")
@json_option
def crawl(
    url: str,
    max_depth: int | None,
    max_breadth: int | None,
    limit: int | None,
    instructions: str | None,
    chunks_per_source: int | None,
    extract_depth: str | None,
    fmt: str | None,
    select_paths: str | None,
    exclude_paths: str | None,
    select_domains: str | None,
    exclude_domains: str | None,
    allow_external: bool | None,
    include_images: bool,
    timeout: float | None,
    output_file: str | None,
    output_dir: str | None,
    json_output: bool,
) -> None:
    """Crawl a website starting from URL.

    Returns full content for each discovered page.
    """
    from tavily_cli.config import get_client
    from tavily_cli.output import print_crawl_results

    client = get_client()

    kwargs: dict = {"url": url}
    if max_depth is not None:
        kwargs["max_depth"] = max_depth
    if max_breadth is not None:
        kwargs["max_breadth"] = max_breadth
    if limit is not None:
        kwargs["limit"] = limit
    if instructions is not None:
        kwargs["instructions"] = instructions
    if chunks_per_source is not None:
        kwargs["chunks_per_source"] = chunks_per_source
    if extract_depth is not None:
        kwargs["extract_depth"] = extract_depth
    if fmt is not None:
        kwargs["format"] = fmt
    if select_paths:
        kwargs["select_paths"] = [p.strip() for p in select_paths.split(",")]
    if exclude_paths:
        kwargs["exclude_paths"] = [p.strip() for p in exclude_paths.split(",")]
    if select_domains:
        kwargs["select_domains"] = [d.strip() for d in select_domains.split(",")]
    if exclude_domains:
        kwargs["exclude_domains"] = [d.strip() for d in exclude_domains.split(",")]
    if allow_external is not None:
        kwargs["allow_external"] = allow_external
    if include_images:
        kwargs["include_images"] = True
    if timeout is not None:
        kwargs["timeout"] = timeout

    from tavily_cli.theme import spinner

    try:
        with spinner(f"Crawling {url}...", json_mode=json_output):
            response = client.crawl(**kwargs)
    except Exception as e:
        handle_api_error(e, json_output)

    print_crawl_results(response, json_mode=json_output, output_file=output_file, output_dir=output_dir)
