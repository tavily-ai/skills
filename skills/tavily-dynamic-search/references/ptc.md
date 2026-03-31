# Programmatic Tool Calling (PTC)

This skill replicates the architecture of [Anthropic's Programmatic Tool Calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling) (PTC) for web search.

## What PTC is

In standard tool calling, each tool invocation requires a full round-trip through the model — the result enters the context window, the model reasons about it, then calls the next tool. For 50 tool calls, that's 50 round-trips with intermediate results piling up in context.

PTC inverts this. Instead of calling tools individually, the model writes code that orchestrates tool calls inside an execution environment. When the code calls a tool (e.g., `await web_search(query)`), the result returns **to the running code**, not to the model's context window. The code processes it — filtering, aggregating, cross-referencing — and only the final `print()` output reaches the model.

As [Lance Martin describes it](https://x.com/RLanceMartin/status/2027450018513490419):

> Rather than pulling 50 raw search results into context for the model to reason over, the code can parse, filter, and cross-reference results programmatically — keeping what's relevant and discarding the rest. Across BrowseComp and DeepsearchQA benchmarks, this improved accuracy by 11% while using 24% fewer input tokens.

PTC can reduce token consumption by up to 37% on complex research tasks ([source](https://www.ikangai.com/programmatic-tool-calling-with-claude-code-the-developers-guide-to-agent-scale-automation/)). The gains come from two sources: reduced context pollution from intermediate results, and explicit programmatic control flow replacing conversational orchestration.

## How PTC works in the Anthropic API

Three components work together:

1. **Code Execution Tool**: A sandboxed container where the model writes and runs Python code.
2. **Tool Opt-In**: Tools declare `"allowed_callers": ["code_execution_20250825"]` so they can be called from inside the sandbox.
3. **Script Generation**: The model writes code that calls tools, processes results, and prints only what matters. Intermediate data stays in the container.

The API setup:

```python
tools = [
    {"type": "code_execution_20260120", "name": "code_execution"},  # the sandbox
    {"type": "web_search_20260209", "name": "web_search"},          # callable from sandbox
    {"type": "web_fetch_20260209", "name": "web_fetch"},            # callable from sandbox
]
```

## What the API responses look like

When PTC activates, the response contains a sequence of blocks. Here's a real trace from a quantum computing query:

```
① server_tool_use: code_execution (caller: direct)
   code: results = await web_search({"query": "quantum computing developments 2025"})

② server_tool_use: web_search (caller: code_execution_20260120)
   → This was called FROM the sandbox, not by the model directly

③ web_search_tool_result: 10 results, ALL with encrypted_content
   → Raw page content is opaque blobs — the model cannot see them

④ code_execution_tool_result: encrypted_code_execution_result
   → The variable `results` now lives in sandbox memory
   → The model has NOT seen any of the raw content

⑤ server_tool_use: code_execution (caller: direct)
   code: for r in parsed: print(f"[{i}] {r['title']}...")
   → Model writes code to inspect what it got

⑥ code_execution_tool_result: plain stdout (19,681 chars)
   → THIS is what the model finally sees — titles, URLs, selected excerpts

⑦ text: Model writes its answer based on the filtered output
```

The critical distinction between block types:

| Code does... | Result type | What happens |
|---|---|---|
| `await web_search(...)` | **encrypted** | Raw data enters sandbox memory, invisible to model |
| `await web_fetch(...)` | **encrypted** | Same — raw page content stays sealed in sandbox |
| `for r in results: print(r['title'])` | **plain stdout** | This crosses into the model's context window |

Any code execution block that calls a tool gets its entire output encrypted. The data goes into sandbox memory (variables) but never into the model's context. Only when a subsequent code block processes those variables and `print()`s something does plain stdout appear.

## How the model iterates in PTC

Real PTC traces show the model making decisions across multiple code blocks. From a solid-state batteries research query:

```
Block 1: results = await web_search({"query": "solid-state battery 2025"})
         → encrypted, saved to sandbox memory

Block 2: for i, r in enumerate(parsed):
             print(f"[{i}] {r['title']}")
         → model sees titles, decides which to investigate

Block 3: urls = ["https://idtechex.com/...", "https://insideevs.com/..."]
         fetched = [await web_fetch({"url": u}) for u in urls]
         → encrypted, raw pages in sandbox memory

Block 4: for f in fetched:
             content = f.get('content', '')
             print(content[:3000])
         → model sees first 3000 chars of each page

Block 5: for name in ['linknovate', 'cars']:
             body_lines = [l for l in lines if len(l.strip()) > 100]
             print('\n'.join(body_lines[40:80]))
         → model drills into specific sections of specific sources

Block 6: extra = [await web_fetch({"url": u}) for u in extra_urls]
         → model found new URLs to chase, fetches more
```

The model made different decisions at every step. It didn't follow a template — it explored, triaged, drilled in, and followed leads.

## How this skill replicates PTC

This skill applies the same principle using local Python execution instead of Anthropic's encrypted sandbox:

| PTC concept | This skill's equivalent |
|---|---|
| Sandboxed code execution container | Python process (via `python3 -c` or script file) |
| Variables persist across code blocks | Files persist on disk (`/tmp/tavily_results.json`) |
| `encrypted_content` stays in sandbox | Raw data stays in Python memory or on disk |
| Only `print()` stdout enters context | Only `print()` stdout enters context |
| Model writes code to filter | Model writes code to filter |

The architectural guarantee is different — PTC uses encryption so the model *cannot* see raw data, while this skill relies on the model *choosing* not to dump raw data. But the context-saving effect is the same: raw search results (300K+ chars) stay outside the context window, and only the model's curated `print()` output (1-3K chars) enters it.

## Sources

- [Anthropic PTC Documentation](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling)
- [Anthropic PTC Cookbook](https://platform.claude.com/cookbook/tool-use-programmatic-tool-calling-ptc)
- [Lance Martin — "Give Claude a computer"](https://x.com/RLanceMartin/status/2027450018513490419)
- [Anthropic Engineering — Introducing advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use)
- [iKangai — Programmatic Tool Calling with Claude Code](https://www.ikangai.com/programmatic-tool-calling-with-claude-code-the-developers-guide-to-agent-scale-automation/)
- [iKangai — Code as Action: The Pattern Behind PTC](https://www.ikangai.com/code-as-action-the-pattern-behind-programmatic-tool-calling/)
