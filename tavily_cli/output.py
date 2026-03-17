"""Output formatting: Rich for humans, JSON for agents, -o for file output."""

from __future__ import annotations

import json
import sys
from typing import Any
from urllib.parse import urlparse

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.tree import Tree


# Override Rich's default markdown heading colors to use brand AQUA
_theme = Theme({
    "markdown.h1": "bold #5CD9E6",
    "markdown.h2": "bold #5CD9E6",
    "markdown.h3": "bold #5CD9E6",
    "markdown.h4": "bold #5CD9E6",
    "markdown.h5": "bold #5CD9E6",
    "markdown.h6": "bold #5CD9E6",
})
console = Console(theme=_theme)
err_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_label(score: float | None) -> Text:
    """Return a styled relevance score label."""
    if score is None:
        return Text("")
    label = Text()
    label.append(f" score: {score:.2f}", style="dim")
    return label


def _footer(label: str, count: int, unit: str, response_time: float | None) -> None:
    """Print a consistent footer line across all commands."""
    parts = [f"{count} {unit}"]
    if response_time:
        parts.append(f"{response_time:.2f}s")
    console.print()
    console.print(Rule(f"[dim]{' | '.join(parts)}[/dim]", style="dim"))


def _domain(url: str) -> str:
    """Extract domain from a URL."""
    try:
        return urlparse(url).netloc
    except Exception:
        return url


# ---------------------------------------------------------------------------
# JSON / file emit
# ---------------------------------------------------------------------------

def emit(data: Any, *, json_mode: bool, output_file: str | None = None, pretty: bool = False) -> None:
    """Write JSON data to stdout (or a file). Used in --json mode."""
    text = json.dumps(data, indent=2 if pretty else None, ensure_ascii=False)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        err_console.print(f"Output saved to {output_file}")
    else:
        click.echo(text)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def print_search_results(data: dict, *, json_mode: bool, output_file: str | None = None) -> None:
    if json_mode:
        emit(data, json_mode=True, output_file=output_file, pretty=True)
        return

    if output_file:
        emit(data, json_mode=True, output_file=output_file, pretty=True)
        return

    results = data.get("results", [])
    answer = data.get("answer")
    response_time = data.get("response_time")

    if answer:
        console.print()
        console.print(f"  [#5CD9E6 bold]Answer[/#5CD9E6 bold]")
        console.print()
        console.print(Markdown(answer), width=min(console.width, 100))
        console.print()

    if not results:
        console.print("[dim]No results found.[/dim]")
        return

    for i, r in enumerate(results, 1):
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        content = r.get("content", "")
        score = r.get("score")

        header = Text()
        header.append(f"{i}. ", style="bold #8385F9")
        header.append(title, style="bold")
        header.append("  ")
        header.append_text(_score_label(score))
        console.print(header)
        console.print(f"   [link={url}]{_domain(url)}[/link]", style="#9BC0AE")
        if content:
            snippet = content[:300]
            if len(content) > 300:
                snippet += "..."
            console.print(f"   {snippet}", style="dim")
        console.print()

    _footer("Search", len(results), "results", response_time)

    images = data.get("images")
    if images:
        console.print()
        console.print(f"[bold]Images ({len(images)}):[/bold]")
        for img in images:
            if isinstance(img, dict):
                console.print(f"  {img.get('url', img)}")
            else:
                console.print(f"  {img}")


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------

def print_extract_results(data: dict, *, json_mode: bool, output_file: str | None = None) -> None:
    if json_mode or output_file:
        emit(data, json_mode=True, output_file=output_file, pretty=True)
        return

    results = data.get("results", [])
    failed = data.get("failed_results", [])

    for r in results:
        url = r.get("url", "")
        raw = r.get("raw_content", "")
        char_count = len(raw) if raw else 0

        console.print()
        console.print(f"  [#5CD9E6 bold]{url}[/#5CD9E6 bold]")
        console.print(f"  [dim]{_domain(url)} ({char_count:,} chars)[/dim]")
        console.print()
        if raw:
            console.print(Markdown(raw[:3000]), width=min(console.width, 100))
        else:
            console.print("  [dim]No content[/dim]")
        console.print()

    if failed:
        console.print("[#FFC769]Failed extractions:[/#FFC769]")
        for f_item in failed:
            console.print(f"  [#9BC0AE]x[/#9BC0AE] {f_item.get('url')}: {f_item.get('error')}")

    response_time = data.get("response_time")
    _footer("Extract", len(results), f"extracted, {len(failed)} failed", response_time)


# ---------------------------------------------------------------------------
# Crawl
# ---------------------------------------------------------------------------

def print_crawl_results(
    data: dict,
    *,
    json_mode: bool,
    output_file: str | None = None,
    output_dir: str | None = None,
) -> None:
    if output_dir:
        _save_crawl_to_dir(data, output_dir)
        return

    if json_mode or output_file:
        emit(data, json_mode=True, output_file=output_file, pretty=True)
        return

    results = data.get("results", [])
    base_url = data.get("base_url", "")

    tree = Tree(f"[bold]{base_url}[/bold]")

    # Group pages by path prefix for a hierarchical view
    for r in results:
        url = r.get("url", "")
        raw = r.get("raw_content", "")
        char_count = len(raw) if raw else 0

        # Show path relative to base
        try:
            parsed = urlparse(url)
            path = parsed.path or "/"
        except Exception:
            path = url

        label = Text()
        label.append(path, style="#5CD9E6")
        label.append(f"  ({char_count:,} chars)", style="dim")

        node = tree.add(label)
        if raw:
            # First non-empty line as preview
            preview = raw.strip().split("\n")[0][:120]
            node.add(Text(preview, style="dim"))

    console.print(tree)

    response_time = data.get("response_time")
    _footer("Crawl", len(results), "pages", response_time)


def _save_crawl_to_dir(data: dict, output_dir: str) -> None:
    """Save each crawled page as a .md file in the output directory."""
    import os
    import re

    os.makedirs(output_dir, exist_ok=True)
    results = data.get("results", [])

    for r in results:
        url = r.get("url", "")
        raw = r.get("raw_content", "")
        if not raw:
            continue

        parsed = urlparse(url)
        slug = re.sub(r"[^\w\-.]", "_", parsed.netloc + parsed.path.rstrip("/"))
        slug = slug.strip("_") or "index"
        filename = f"{slug}.md"

        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {url}\n\n{raw}\n")

    err_console.print(f"Saved {len(results)} pages to {output_dir}/")


# ---------------------------------------------------------------------------
# Map
# ---------------------------------------------------------------------------

def print_map_results(data: dict, *, json_mode: bool, output_file: str | None = None) -> None:
    if json_mode or output_file:
        emit(data, json_mode=True, output_file=output_file, pretty=True)
        return

    results = data.get("results", [])
    base_url = data.get("base_url", "")

    tree = Tree(f"[bold]{base_url}[/bold]")
    for url in results:
        tree.add(f"[link={url}]{url}[/link]")

    console.print(tree)

    response_time = data.get("response_time")
    _footer("Map", len(results), "URLs", response_time)


# ---------------------------------------------------------------------------
# Research
# ---------------------------------------------------------------------------

def print_research_result(data: dict, *, json_mode: bool, output_file: str | None = None) -> None:
    if json_mode or output_file:
        emit(data, json_mode=True, output_file=output_file, pretty=True)
        return

    status = data.get("status", "unknown")
    content = data.get("content", "")
    sources = data.get("sources", [])

    if status != "completed" and not content:
        console.print(f"[bold]Status:[/bold] {status}")
        if data.get("error"):
            console.print(f"[#9BC0AE]Error:[/#9BC0AE] {data['error']}")
        return

    # Render the research report as markdown
    if content:
        console.print()
        console.print(f"  [#5CD9E6 bold]Research Report[/#5CD9E6 bold]")
        console.print()
        console.print(Markdown(content), width=min(console.width, 100))

    # Sources as a numbered table
    if sources:
        console.print()
        table = Table(title=f"Sources ({len(sources)})", show_lines=False, padding=(0, 1))
        table.add_column("#", style="bold #8385F9", width=4)
        table.add_column("Title", style="bold", ratio=2)
        table.add_column("URL", style="#9BC0AE", ratio=3)

        for i, s in enumerate(sources, 1):
            title = s.get("title", "")
            url = s.get("url", "")
            table.add_row(str(i), title, f"[link={url}]{url}[/link]")

        console.print(table)

    response_time = data.get("response_time")
    _footer("Research", len(sources), "sources", response_time)
