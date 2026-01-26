# Agent Skills

## Installation

```bash
npx skills add https://github.com/tavily-ai/skills
```

## Setup

**Tavily API Key Required** — Get your key at [https://tavily.com](https://tavily.com)

1. Open a terminal and run:
   ```bash
   open ~/.claude/settings.json
   ```

2. Add the following to your `settings.json`:
   ```json
   {
     "env": {
       "TAVILY_API_KEY": "tvly-your-api-key-here"
     }
   }
   ```

3. Replace `tvly-your-api-key-here` with your actual API key and save the file.

4. Restart Claude Code.

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Search** | `/search` | Search the web using Tavily's LLM-optimized API. Returns relevant results with content snippets, scores, and metadata. |
| **Research** | `/research` | Get research on any topic with citations. Supports structured JSON output for pipelines. |
| **Extract** | `/extract` | Extract clean content from specific URLs. Returns markdown/text from web pages. |
| **Crawl** | `/crawl` | Crawl websites to download documentation, knowledge bases, or web content as local markdown files. |
| **Tavily Best Practices** | `/tavily-best-practices` | Reference documentation for building production-ready Tavily integrations in agentic workflows, RAG systems, or autonomous agents. |