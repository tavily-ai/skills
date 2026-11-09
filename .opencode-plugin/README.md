# opencode-tavily

OpenCode plugin for [Tavily](https://tavily.com) — gives your AI agent reliable web search, content extraction, crawling, URL discovery, and deep research with citations.

Supports OpenCode **v1.18.29+ (1.x)** and **v2** using OpenCode's [documented dual-version entrypoint](https://opencode.ai/v2/docs/build/plugins/migrate-v1): v1 calls `server()`, and v2 calls `setup()`.

## Installation

Add the plugin to your `opencode.json`. The configuration key differs between versions.

### OpenCode v2

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugins": ["opencode-tavily"]
}
```

### OpenCode v1.18.29+

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["opencode-tavily"]
}
```

OpenCode installs the package automatically on next launch

### Install the Tavily CLI

Then install the Tavily CLI globally:

```bash
curl -fsSL https://cli.tavily.com/install.sh | bash
```

Or via Python:

```bash
uv tool install tavily-cli
# or
pip install tavily-cli
```

## Authentication

On first use, the agent will prompt you to authenticate. You can also set up in advance:

```bash
# Browser login (recommended)
tvly login
# Or set an API key
export TAVILY_API_KEY=tvly-your-api-key
```

Get an API key at [tavily.com](https://tavily.com).

If `TAVILY_API_KEY` is set in your environment, the plugin automatically passes it to shell commands.

## What It Does

This plugin registers the [Tavily Agent Skills](https://github.com/tavily-ai/skills) with OpenCode:

| Skill | Use it for |
|-------|------------|
| `tavily-search` | Web search, reading URLs, mapping and crawling sites with the `tvly` CLI |
| `tavily-research` | Multi-source research reports with citations |
| `tavily-entity` | Filling in a company or person record from the web |
| `tavily-list` | Building a deduplicated table of matches |
| `tavily-monitor` | Recurring checks for new information on a topic |
| `tavily-sdk` | Adding Tavily to application code with the Python or JavaScript SDK |

It also tells the agent to pass `--client-name opencode` to `tvly` commands for request attribution.

## Development

The plugin lives in the `.opencode-plugin/` folder of [tavily-ai/skills](https://github.com/tavily-ai/skills). `./build.sh` copies the repo's skills into the package, and `npm pack` runs it automatically. Publishing a release of the repo publishes the package to npm at the release version.

```bash
cd opencode
bun install
./build.sh
bun run check
bun test
```

## Links

- [Tavily](https://tavily.com)
- [Tavily Documentation](https://docs.tavily.com)
- [Tavily CLI Installation](https://cli.tavily.com)
- [OpenCode Plugin Docs](https://opencode.ai/docs/plugins)
- [OpenCode Ecosystem](https://opencode.ai/docs/ecosystem)

## License

MIT
