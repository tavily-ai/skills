"""tavily search — web search via the Tavily API."""

from __future__ import annotations

import sys

import click

from tavily_cli.common import handle_api_error, json_option


@click.command()
@click.argument("query", required=False)
@click.option("--depth", "search_depth", type=click.Choice(["ultra-fast", "fast", "basic", "advanced"]), default=None, help="Search depth (default: basic).")
@click.option("--max-results", type=int, default=None, help="Maximum results, 0-20 (default: 5).")
@click.option("--topic", type=click.Choice(["general", "news", "finance"]), default=None, help="Search topic.")
@click.option("--time-range", type=click.Choice(["day", "week", "month", "year"]), default=None, help="Relative time filter.")
@click.option("--start-date", default=None, help="Results after date (YYYY-MM-DD).")
@click.option("--end-date", default=None, help="Results before date (YYYY-MM-DD).")
@click.option("--include-domains", default=None, help="Comma-separated domains to include.")
@click.option("--exclude-domains", default=None, help="Comma-separated domains to exclude.")
@click.option("--country", default=None, help="Boost results from country.")
@click.option("--include-answer", is_flag=False, flag_value="basic", default=None, help="Include AI answer (pass 'basic' or 'advanced').")
@click.option("--include-raw-content", is_flag=False, flag_value="markdown", default=None, help="Include full page content ('markdown' or 'text').")
@click.option("--include-images", is_flag=True, default=False, help="Include image results.")
@click.option("--include-image-descriptions", is_flag=True, default=False, help="Include AI image descriptions.")
@click.option("--chunks-per-source", type=int, default=None, help="Chunks per source (advanced/fast depth only).")
@click.option("--output", "-o", "output_file", default=None, help="Save output to file.")
@click.option(
    "--filter",
    "filter_instruction",
    default=None,
    metavar="INSTRUCTION",
    help="Run dynamic filtering in Docker; INSTRUCTION says what to extract or focus on.",
)
@json_option
def search(
    query: str | None,
    search_depth: str | None,
    max_results: int | None,
    topic: str | None,
    time_range: str | None,
    start_date: str | None,
    end_date: str | None,
    include_domains: str | None,
    exclude_domains: str | None,
    country: str | None,
    include_answer: str | None,
    include_raw_content: str | None,
    include_images: bool,
    include_image_descriptions: bool,
    chunks_per_source: int | None,
    output_file: str | None,
    filter_instruction: str | None,
    json_output: bool,
) -> None:
    """Search the web using Tavily.

    QUERY is the search query. Use "-" to read from stdin.

    With --filter INSTRUCTION, the query is sent to a filter agent inside a
    Docker container. The agent uses Tavily search, extract, and a shell to
    fetch raw content, filter it per INSTRUCTION, and return only relevant
    signal (raw page text never enters the LLM context).
    """
    if query == "-":
        query = sys.stdin.read(100_000).strip()
    if not query:
        raise click.UsageError("QUERY is required. Pass a query string or use '-' to read from stdin.")

    # ── Filter mode: delegate entirely to the sandboxed agent ──
    if filter_instruction is not None:
        instr = filter_instruction.strip()
        if not instr:
            raise click.UsageError("--filter requires a non-empty instruction.")
        _run_filter(
            query,
            instructions=instr,
            json_output=json_output,
            output_file=output_file,
        )
        return

    # ── Normal search mode ──
    from tavily_cli.config import get_client
    from tavily_cli.output import print_search_results

    client = get_client()

    kwargs: dict = {"query": query}
    if search_depth is not None:
        kwargs["search_depth"] = search_depth
    if max_results is not None:
        kwargs["max_results"] = max_results
    if topic is not None:
        kwargs["topic"] = topic
    if time_range is not None:
        kwargs["time_range"] = time_range
    if start_date is not None:
        kwargs["start_date"] = start_date
    if end_date is not None:
        kwargs["end_date"] = end_date
    if include_domains:
        kwargs["include_domains"] = [d.strip() for d in include_domains.split(",")]
    if exclude_domains:
        kwargs["exclude_domains"] = [d.strip() for d in exclude_domains.split(",")]
    if country is not None:
        kwargs["country"] = country
    if include_answer is not None:
        kwargs["include_answer"] = include_answer
    if include_raw_content is not None:
        kwargs["include_raw_content"] = include_raw_content
    if include_images:
        kwargs["include_images"] = True
    if include_image_descriptions:
        kwargs["include_image_descriptions"] = True
    if chunks_per_source is not None:
        kwargs["chunks_per_source"] = chunks_per_source

    from tavily_cli.theme import spinner

    try:
        with spinner("Searching...", json_mode=json_output):
            response = client.search(**kwargs)
    except Exception as e:
        handle_api_error(e, json_output)

    print_search_results(response, json_mode=json_output, output_file=output_file)


_FILTER_TIMEOUT_S = 120


def _run_filter(
    query: str,
    *,
    instructions: str,
    json_output: bool,
    output_file: str | None,
) -> None:
    """Delegate to the Docker-sandboxed filter agent."""
    import json as json_mod
    import subprocess

    from tavily_cli.output import console, emit
    from tavily_cli.theme import ACCENT, err_console, spinner

    try:
        from tavily_cli.sandbox import run_filter_sandbox

        with spinner("Running filter agent in sandbox...", json_mode=json_output):
            output = run_filter_sandbox(
                query,
                instructions=instructions,
                timeout=_FILTER_TIMEOUT_S,
            )
    except subprocess.TimeoutExpired:
        if json_output:
            click.echo(
                json_mod.dumps({"error": f"Filter agent timed out after {_FILTER_TIMEOUT_S}s"})
            )
        else:
            err_console.print(
                f"  [#FAA2FB]> Error:[/#FAA2FB] Filter agent timed out after {_FILTER_TIMEOUT_S}s"
            )
        raise SystemExit(4)
    except Exception as e:
        if json_output:
            click.echo(json_mod.dumps({"error": str(e)}))
        else:
            err_console.print(f"  [#FAA2FB]> Error:[/#FAA2FB] {e}")
        raise SystemExit(4)

    if json_output:
        data = {"query": query, "filtered_output": output}
        data["filter_instructions"] = instructions
        emit(data, json_mode=True, output_file=output_file, pretty=True)
    elif output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        err_console.print(f"  Output saved to {output_file}")
    else:
        from rich.markdown import Markdown

        console.print()
        console.print(f"  [{ACCENT} bold]Filtered Results[/{ACCENT} bold]")
        console.print()
        console.print(Markdown(output), width=min(console.width, 100))
        console.print()
