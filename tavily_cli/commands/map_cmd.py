"""tavily map — discover URLs on a website via the Tavily API."""

from __future__ import annotations

import click

from tavily_cli.common import handle_api_error, json_option


@click.command("map")
@click.argument("url")
@click.option("--max-depth", type=int, default=None, help="Levels deep to map (1-5, default: 1).")
@click.option("--max-breadth", type=int, default=None, help="Links per page (default: 20).")
@click.option("--limit", type=int, default=None, help="Maximum URLs to discover (default: 50).")
@click.option("--instructions", default=None, help="Natural language guidance for URL discovery.")
@click.option("--select-paths", default=None, help="Comma-separated regex patterns for paths to include.")
@click.option("--exclude-paths", default=None, help="Comma-separated regex patterns for paths to exclude.")
@click.option("--select-domains", default=None, help="Comma-separated regex patterns for domains to include.")
@click.option("--exclude-domains", default=None, help="Comma-separated regex patterns for domains to exclude.")
@click.option("--allow-external/--no-external", default=None, help="Include external domain links.")
@click.option("--timeout", type=float, default=None, help="Max wait time in seconds (10-150).")
@click.option("--output", "-o", "output_file", default=None, help="Save output to file.")
@json_option
def map_urls(
    url: str,
    max_depth: int | None,
    max_breadth: int | None,
    limit: int | None,
    instructions: str | None,
    select_paths: str | None,
    exclude_paths: str | None,
    select_domains: str | None,
    exclude_domains: str | None,
    allow_external: bool | None,
    timeout: float | None,
    output_file: str | None,
    json_output: bool,
) -> None:
    """Discover all URLs on a website (no content extraction).

    Returns a list of URLs found starting from the given URL.
    """
    from tavily_cli.config import get_client
    from tavily_cli.output import print_map_results

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
    if timeout is not None:
        kwargs["timeout"] = timeout

    from tavily_cli.theme import spinner

    try:
        with spinner(f"Mapping {url}...", json_mode=json_output):
            response = client.map(**kwargs)
    except Exception as e:
        handle_api_error(e, json_output)

    print_map_results(response, json_mode=json_output, output_file=output_file)
