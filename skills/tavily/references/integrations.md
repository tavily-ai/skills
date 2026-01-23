# Framework Integrations

## Table of Contents

- [LangChain](#langchain)
- [LlamaIndex](#llamaindex)
- [OpenAI Function Calling](#openai-function-calling)
- [Anthropic Tool Use](#anthropic-tool-use)

---

## LangChain

The `langchain-tavily` package is the official LangChain integration supporting Search, Extract, Map, Crawl, and Research.

### Installation

```bash
pip install -U langchain-tavily
```

### Search

```python
from langchain_tavily import TavilySearch

tool = TavilySearch(
    max_results=5,
    topic="general",  # or "news", "finance"
    # search_depth="basic",
    # include_answer=False,
    # include_raw_content=False,
)

# Direct invocation
result = tool.invoke({"query": "What happened at Wimbledon?"})

# With agent
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

agent = create_agent(
    model=ChatOpenAI(model="gpt-4"),
    tools=[tool],
    system_prompt="You are a helpful research assistant."
)
response = agent.invoke({
    "messages": [{"role": "user", "content": "What are the latest AI trends?"}]
})
```

**Dynamic parameters at invocation:**
- `include_images`, `search_depth`, `time_range`, `include_domains`, `exclude_domains`, `start_date`, `end_date`

### Extract

```python
from langchain_tavily import TavilyExtract

tool = TavilyExtract(
    extract_depth="basic",  # or "advanced"
    # include_images=False
)

result = tool.invoke({
    "urls": ["https://en.wikipedia.org/wiki/Lionel_Messi"]
})
```

### Map

```python
from langchain_tavily import TavilyMap

tool = TavilyMap()

result = tool.invoke({
    "url": "https://docs.example.com",
    "instructions": "Find all documentation and tutorial pages"
})
# Returns: {"base_url": ..., "results": [urls...], "response_time": ...}
```

### Crawl

```python
from langchain_tavily import TavilyCrawl

tool = TavilyCrawl()

result = tool.invoke({
    "url": "https://docs.example.com",
    "instructions": "Extract API documentation and code examples"
})
# Returns: {"base_url": ..., "results": [{url, raw_content}...], "response_time": ...}
```

### Research

```python
from langchain_tavily import TavilyResearch, TavilyGetResearch

# Start research
research_tool = TavilyResearch(model="mini")
result = research_tool.invoke({
    "input": "Research the latest developments in AI",
    "citation_format": "apa"
})

# Get results
get_tool = TavilyGetResearch()
final = get_tool.invoke({"request_id": result["request_id"]})
```

---

## LlamaIndex

```python
from llama_index.tools.tavily_research import TavilyToolSpec

# Initialize tools
tavily_tool = TavilyToolSpec(api_key="tvly-YOUR_API_KEY")
tools = tavily_tool.to_tool_list()

# Use with agent
from llama_index.agent.openai import OpenAIAgent

agent = OpenAIAgent.from_tools(tools)
response = agent.chat("What are the latest AI developments?")
```

---

## OpenAI Function Calling

Define Tavily as an OpenAI function:

```python
from openai import OpenAI
from tavily import TavilyClient
import json

openai_client = OpenAI()
tavily_client = TavilyClient()

tools = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    }
}]

def handle_tool_call(tool_call):
    if tool_call.function.name == "web_search":
        args = json.loads(tool_call.function.arguments)
        return tavily_client.search(args["query"])

# Chat completion with tools
response = openai_client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What are the latest AI trends?"}],
    tools=tools
)

if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    search_results = handle_tool_call(tool_call)

    # Continue conversation with results
    messages = [
        {"role": "user", "content": "What are the latest AI trends?"},
        response.choices[0].message,
        {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(search_results)}
    ]
    final = openai_client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
```

---

## Anthropic Tool Use

Define Tavily as an Anthropic tool:

```python
from anthropic import Anthropic
from tavily import TavilyClient
import json

anthropic_client = Anthropic()
tavily_client = TavilyClient()

tools = [{
    "name": "web_search",
    "description": "Search the web for current information using Tavily",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            }
        },
        "required": ["query"]
    }
}]

def process_tool_use(tool_use):
    if tool_use.name == "web_search":
        return tavily_client.search(tool_use.input["query"])

# Initial request
response = anthropic_client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What are the latest AI trends?"}]
)

# Handle tool use
if response.stop_reason == "tool_use":
    tool_use = next(b for b in response.content if b.type == "tool_use")
    search_results = process_tool_use(tool_use)

    # Continue with results
    final = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=tools,
        messages=[
            {"role": "user", "content": "What are the latest AI trends?"},
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tool_use.id, "content": json.dumps(search_results)}
            ]}
        ]
    )
```

---

## Other Integrations

Tavily also integrates with:
- **CrewAI** - Multi-agent frameworks
- **Pydantic AI** - Type-safe AI applications
- **Vercel AI SDK** - Next.js/React applications
- **N8N, Make, Zapier** - No-code automation
- **Flowise, Dify** - Visual LLM builders

See the [full integrations documentation](https://docs.tavily.com/documentation/integrations) for details.
