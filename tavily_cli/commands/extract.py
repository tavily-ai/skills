"""tavily extract — extract content from URLs via the Tavily API."""

from __future__ import annotations

import click

from tavily_cli.common import handle_api_error, json_option


@click.command()
@click.argument("urls", nargs=-1, required=True)
@click.option("--query", default=None, help="Rerank chunks by relevance to this query.")
@click.option("--chunks-per-source", type=int, default=None, help="Chunks per source (1-5, requires --query).")
@click.option("--extract-depth", type=click.Choice(["basic", "advanced"]), default=None, help="Extraction depth.")
@click.option("--format", "fmt", type=click.Choice(["markdown", "text"]), default=None, help="Output format.")
@click.option("--include-images", is_flag=True, default=False, help="Include image URLs.")
@click.option("--timeout", type=float, default=None, help="Max wait time in seconds (1-60).")
@click.option("--output", "-o", "output_file", default=None, help="Save output to file.")
@json_option
def extract(
    urls: tuple[str, ...],
    query: str | None,
    chunks_per_source: int | None,
    extract_depth: str | None,
    fmt: str | None,
    include_images: bool,
    timeout: float | None,
    output_file: str | None,
    json_output: bool,
) -> None:
    """Extract content from one or more URLs.

    Provide URLs as positional arguments (max 20).
    """
    from tavily_cli.config import get_client
    from tavily_cli.output import print_extract_results

    client = get_client()

    url_list = list(urls)
    if len(url_list) > 20:
        raise click.UsageError("Maximum 20 URLs per request.")

    kwargs: dict = {"urls": url_list}
    if query is not None:
        kwargs["query"] = query
    if chunks_per_source is not None:
        kwargs["chunks_per_source"] = chunks_per_source
    if extract_depth is not None:
        kwargs["extract_depth"] = extract_depth
    if fmt is not None:
        kwargs["format"] = fmt
    if include_images:
        kwargs["include_images"] = True
    if timeout is not None:
        kwargs["timeout"] = timeout

    from tavily_cli.theme import spinner

    try:
        with spinner(f"Extracting {len(url_list)} URL{'s' if len(url_list) > 1 else ''}...", json_mode=json_output):
            response = client.extract(**kwargs)
    except Exception as e:
        handle_api_error(e, json_output)

    print_extract_results(response, json_mode=json_output, output_file=output_file)
