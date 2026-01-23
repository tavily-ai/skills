---
name: research
description: "Get AI-synthesized research on any topic with citations, directly in your terminal. Supports structured JSON output for pipelines. Use when you need comprehensive research grounded in web data without writing code."
---

# Research Skill

Conduct comprehensive research on any topic with automatic source gathering, analysis, and response generation with citations.

## Prerequisites

**Tavily API Key Required** - Get your key at https://tavily.com

Add to `~/.claude/settings.json`:
```json
{
  "env": {
    "TAVILY_API_KEY": "tvly-your-api-key-here"
  }
}
```

## Quick Start

> **Tip**: Research can take 30-120 seconds. Press **Ctrl+B** to run in the background.

### Basic Research

```bash
curl -N --request POST \
  --url https://api.tavily.com/research \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "input": "Latest developments in quantum computing",
    "model": "mini",
    "stream": true,
    "citation_format": "numbered"
  }'
```

The `-N` flag disables buffering so you see streaming progress. The call waits until research completes.

### With Custom Schema

```bash
curl -N --request POST \
  --url https://api.tavily.com/research \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "input": "Electric vehicle market analysis",
    "model": "pro",
    "stream": true,
    "citation_format": "numbered",
    "output_schema": {
      "properties": {
        "market_overview": {
          "type": "string",
          "description": "2-3 sentence overview of the market"
        },
        "key_players": {
          "type": "array",
          "description": "Major companies in this market",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string", "description": "Company name"},
              "market_share": {"type": "string", "description": "Approximate market share"}
            },
            "required": ["name"]
          }
        }
      },
      "required": ["market_overview", "key_players"]
    }
  }'
```

## API Reference

### Endpoint

```
POST https://api.tavily.com/research
```

### Headers

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer <TAVILY_API_KEY>` |
| `Content-Type` | `application/json` |

### Request Body

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `input` | string | Required | Research topic or question |
| `model` | string | `"mini"` | Model: `mini`, `pro`, `auto` |
| `stream` | boolean | `true` | Stream results (single call, waits for completion) |
| `output_schema` | object | null | JSON schema for structured output |
| `citation_format` | string | `"numbered"` | Citation format: `numbered`, `mla`, `apa`, `chicago` |

### Response Format (SSE)

```
event: chat.completion.chunk
data: {"choices":[{"delta":{"tool_calls":{"tool_call":[{"name":"Planning","arguments":"Initializing..."}]}}}]}

event: chat.completion.chunk
data: {"choices":[{"delta":{"content":"# Research Results\n\n..."}}]}

event: research.sources
data: {"sources":[{"url":"https://...","title":"Source Title"}]}

event: done
data: {"response_time":45.2}
```

Key events:
- **Planning/WebSearch chunks**: Show research progress
- **content chunks**: Research content (markdown or JSON if schema provided)
- **sources**: Array of citations used
- **done**: Final event with response time

## Model Selection

**Rule of thumb**: "what does X do?" -> mini. "X vs Y vs Z" or "best way to..." -> pro.

| Model | Use Case | Speed |
|-------|----------|-------|
| `mini` | Single topic, targeted research | ~30s |
| `pro` | Comprehensive multi-angle analysis | ~60-120s |
| `auto` | API chooses based on complexity | Varies |

## Schema Usage

Schemas make output structured and predictable. Every property **MUST** include both `type` and `description`.

```json
{
  "properties": {
    "summary": {
      "type": "string",
      "description": "2-3 sentence executive summary"
    },
    "key_points": {
      "type": "array",
      "description": "Main takeaways",
      "items": {"type": "string"}
    }
  },
  "required": ["summary", "key_points"]
}
```

## Examples

### Market Research

```bash
curl -N --request POST \
  --url https://api.tavily.com/research \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "input": "Fintech startup landscape 2025",
    "model": "pro",
    "stream": true,
    "citation_format": "numbered",
    "output_schema": {
      "properties": {
        "market_overview": {"type": "string", "description": "Executive summary of fintech market"},
        "top_startups": {
          "type": "array",
          "description": "Notable fintech startups",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string", "description": "Startup name"},
              "focus": {"type": "string", "description": "Primary business focus"},
              "funding": {"type": "string", "description": "Total funding raised"}
            },
            "required": ["name", "focus"]
          }
        },
        "trends": {"type": "array", "description": "Key market trends", "items": {"type": "string"}}
      },
      "required": ["market_overview", "top_startups"]
    }
  }'
```

### Technical Comparison

```bash
curl -N --request POST \
  --url https://api.tavily.com/research \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "input": "LangGraph vs CrewAI for multi-agent systems",
    "model": "pro",
    "stream": true,
    "citation_format": "mla"
  }'
```

### Quick Overview

```bash
curl -N --request POST \
  --url https://api.tavily.com/research \
  --header "Authorization: Bearer $TAVILY_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "input": "What is retrieval augmented generation?",
    "model": "mini",
    "stream": true
  }'
```
