---
name: research  
description: "Comprehensive research grounded in web data with explicit citations. Use when you need multi-source synthesis—comparisons, current events, market analysis, detailed reports. "
---
# Research Skill

Conduct comprehensive research on any topic with automatic source gathering, analysis, and response generation with citations.

## Authentication

The script uses OAuth via the Tavily MCP server. **No manual setup required** - on first run, it will:
1. Check for existing tokens in `~/.mcp-auth/`
2. If none found, automatically open your browser for OAuth authentication

> **Note:** You must have an existing Tavily account. The OAuth flow only supports login — account creation is not available through this flow. [Sign up at tavily.com](https://tavily.com) first if you don't have an account.

### Alternative: API Key

If you prefer using an API key, get one at https://tavily.com and add to `~/.claude/settings.json`:
```json
{
  "env": {
    "TAVILY_API_KEY": "tvly-your-api-key-here"
  }
}
```

## Quick Start

> **Tip**: Research can take 30-120 seconds. Press **Ctrl+B** to run in the background.

### Using the Script

```bash
./scripts/research.sh '<json>' [output_file]
```

**Examples:**

```bash
# Basic research
./scripts/research.sh '{"input": "quantum computing trends"}'

# With pro model for comprehensive analysis
./scripts/research.sh '{"input": "AI agents comparison", "model": "pro"}'

# Save to file
./scripts/research.sh '{"input": "market analysis for EVs", "model": "pro"}' ./ev-report.md

# Quick targeted research
./scripts/research.sh '{"input": "climate change impacts", "model": "mini"}'
```

## Parameters

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `input` | string | Required | Research topic or question |
| `model` | string | `"mini"` | Model: `mini`, `pro`, `auto` |

## Model Selection

**Rule of thumb**: "what does X do?" -> mini. "X vs Y vs Z" or "best way to..." -> pro.

| Model | Use Case | Speed |
|-------|----------|-------|
| `mini` | Single topic, targeted research | ~30s |
| `pro` | Comprehensive multi-angle analysis | ~60-120s |
| `auto` | API chooses based on complexity | Varies |

## Examples

### Quick Overview

```bash
./scripts/research.sh '{"input": "What is retrieval augmented generation?", "model": "mini"}'
```

### Technical Comparison

```bash
./scripts/research.sh '{"input": "LangGraph vs CrewAI for multi-agent systems", "model": "pro"}'
```

### Market Research

```bash
./scripts/research.sh '{"input": "Fintech startup landscape 2025", "model": "pro"}' fintech-report.md
```
