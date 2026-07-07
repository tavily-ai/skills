# Security Considerations for Agentic Workflows

Tavily is designed to bring real-time web content into AI agent context windows. That same capability introduces a surface for adversarial content: a web page can contain text that tries to redirect an agent's behavior, override its instructions, or exfiltrate information through the queries it makes. This document covers practical steps to reduce that exposure.

---

## Table of Contents

- [Prompt Injection via Search Results](#prompt-injection-via-search-results)
- [Restricting Search Scope](#restricting-search-scope)
- [Validating Content Before Use](#validating-content-before-use)
- [Logging and Auditing Agent Actions](#logging-and-auditing-agent-actions)
- [Minimizing Permissions](#minimizing-permissions)
- [Research Background](#research-background)

---

## Prompt Injection via Search Results

A prompt injection attack embeds instructions inside content that an LLM processes as data. When an agent fetches a web page through Tavily and surfaces that content in its context, any instructions hidden in the page are interpreted alongside legitimate instructions.

**Common patterns in the wild:**
- Hidden text (white-on-white, zero font size) telling the agent to ignore its system prompt
- Markdown or HTML comments containing override instructions
- Pages that specifically target known AI assistants by name

**What makes agentic use riskier than simple retrieval:**  
A stateless QA pipeline that retrieves and answers has limited blast radius. An autonomous agent that can call tools, write files, send messages, or make further API calls gives an injection point much more leverage.

---

## Restricting Search Scope

The simplest mitigation is limiting which domains Tavily queries.

```python
from tavily import TavilyClient

client = TavilyClient()

# Restrict to a vetted allowlist
response = client.search(
    query="quarterly earnings report",
    include_domains=[
        "sec.gov",
        "reuters.com",
        "bloomberg.com",
        "ft.com",
    ],
    search_depth="advanced"
)
```

```python
# Or exclude known high-risk categories
response = client.search(
    query=user_query,
    exclude_domains=[
        "pastebin.com",
        "hastebin.com",
        "rentry.co",
    ]
)
```

**Guidance:**
- Use `include_domains` whenever the agent's task is scoped to a known set of sources (internal wikis, regulatory filings, specific news outlets).
- Use `exclude_domains` as a secondary control when the query must be open-ended.
- Combine `topic="news"` or `topic="finance"` with domain filters to further constrain the result set.

---

## Validating Content Before Use

Before handing search results to an agent, scan them for known injection patterns.

```python
import re

# Patterns that appear in documented prompt injection attacks
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above|prior)\s+instructions",
    r"disregard\s+(your|all)\s+(previous\s+)?instructions",
    r"you\s+are\s+now\s+(?!a\s+(?:news|research|data))",  # persona overrides
    r"system\s*prompt\s*:",
    r"<\|(?:im_start|endoftext|system)\|>",
    r"\[\s*INST\s*\]",  # Llama instruction tokens
]

_compiled = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def contains_injection(text: str) -> bool:
    return any(p.search(text) for p in _compiled)


def filter_results(results: list[dict]) -> list[dict]:
    """Drop any search result whose content contains a known injection pattern."""
    clean = []
    for r in results:
        content = r.get("content", "") + r.get("raw_content", "")
        if not contains_injection(content):
            clean.append(r)
        else:
            print(f"[security] Dropped result from {r.get('url')}: injection pattern detected")
    return clean


response = client.search(query="...", search_depth="advanced")
safe_results = filter_results(response["results"])
```

**Notes:**
- Pattern lists must be maintained; attackers adapt. Treat this as a first-pass filter, not a complete defense.
- For high-sensitivity workflows, add a second LLM call that classifies each result before it enters the main agent context.
- The `include_answer` field generates an LLM-synthesized answer server-side; the synthesized text is generally safer than raw `raw_content`, but should still be treated as untrusted.

---

## Logging and Auditing Agent Actions

When an agent makes autonomous decisions based on search results, log enough context to reconstruct what it saw.

```python
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("tavily-agent")


def audited_search(client, query: str, **kwargs) -> dict:
    response = client.search(query=query, **kwargs)
    logger.info(json.dumps({
        "ts": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "kwargs": kwargs,
        "result_urls": [r["url"] for r in response.get("results", [])],
        "result_count": len(response.get("results", [])),
    }))
    return response
```

**What to log at minimum:**
- The query string sent to Tavily
- The URLs returned (and any that were filtered)
- The downstream tool calls or outputs the agent produced after processing the results

Structured logs make it possible to replay an incident and identify which search result contributed to unexpected agent behavior.

---

## Minimizing Permissions

Apply least-privilege to the agent itself, not just to Tavily:

| Principle | Implementation |
|-----------|---------------|
| Read-only by default | Give the agent no write tools unless the task specifically requires them |
| Scoped credentials | Use API keys with the minimum permissions the task needs |
| Human-in-the-loop gates | Require confirmation before the agent executes irreversible actions (file writes, API POSTs, emails) |
| Sandboxed execution | Run the agent in an isolated environment where lateral movement is limited |

An agent that can only read information has a much smaller blast radius than one that can also write files, run code, or call external APIs.

---

## Research Background

Recent work on agentic AI safety has characterized techniques by which external content can cause an agent to deviate from its operating constraints — a class of attacks sometimes called *constraint modification* or *agent escape*. These include:

- **Indirect prompt injection**: Adversarial instructions embedded in content the agent retrieves from the web (directly relevant to Tavily-powered agents).
- **Context poisoning via environment**: Manipulating files, search results, or API responses that the agent treats as ground truth.

Dwivedi (2026, preprint, under review) reports experiments across 29 models and 8 providers measuring susceptibility to four constraint-modification techniques (C1-C4). Web-enabled agents (those with browse/search tools) showed higher susceptibility to indirect injection than chat-only baselines, because each search call adds an untrusted content boundary to the context window.

**Practical takeaway**: The mitigations above — domain allowlisting, content validation, least-privilege, and audit logging — together address the main environmental attack surface identified in that line of research.

---

## See Also

- [Search API Reference](search.md) — `include_domains`, `exclude_domains`, depth options
- [Tavily documentation: Rate limits and quotas](https://docs.tavily.com)
- [OWASP LLM Top 10 — LLM06: Excessive Agency](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [OWASP LLM Top 10 — LLM02: Sensitive Information Disclosure](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
