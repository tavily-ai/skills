# Setup

Tavily is available as an MCP server or as the `tvly` CLI. Use whichever one
the agent already has. Set up the other only when the user asks, or when the
task needs something only that channel offers. Saving crawled pages as files, and saving a large search or extract so you
can filter it, both need the CLI.

## MCP

The remote server is at `https://mcp.tavily.com/mcp`. Clients that support
OAuth can connect to that URL and sign in through the browser. Other clients
pass an API key, either in the URL as `?tavilyApiKey=<key>` or as an
`Authorization: Bearer <key>` header.

In Claude Code:

```bash
claude mcp add --transport http tavily https://mcp.tavily.com/mcp
```

For other clients, see the setup steps in the
[tavily-mcp README](https://github.com/tavily-ai/tavily-mcp). Adding a server
usually takes effect after the client restarts, so tell the user that a restart
may be needed instead of retrying the tool right away.

If an MCP call fails with an authentication error, ask the user to reconnect
the server or check their API key. Don't try to work around it from inside the
session.

## CLI

Install it if `tvly` is missing:

```bash
curl -fsSL https://cli.tavily.com/install.sh | bash
```

You can also install it with `uv tool install tavily-cli` or `pip install
tavily-cli`.

Search and extract work without an account, up to a keyless rate limit. Don't
look for an API key or sign in before the first search or extract. Map, crawl
and research need authentication.

For first-time agent setup, start keyless unless the user asks to sign in or
the task needs map, crawl or research:

```bash
tvly init --skip-auth
```

When authentication is needed, run guided setup with `tvly init`, or `tvly init
--no-browser` to print the sign-in link instead of opening it. `tvly init`
reuses an existing credential, installs or updates the Tavily skills, and runs
a live test search. Use `tvly init --skip-skills` when the skills are already
installed. To sign in without the rest of setup, use `tvly login`, `tvly login
--api-key <key>`, or set `TAVILY_API_KEY`.

The browser sign-in returns to a localhost callback on the machine that runs
`tvly`. In a remote session, that callback must be reachable, which may need
SSH port forwarding. In an unattended agent or CI job, don't start a sign-in
flow. Leave authentication to the user or use a `TAVILY_API_KEY` they provided.

### Keyless limit

If search or extract hits the keyless limit in an interactive session, run
`tvly login`, then retry the original command once. In an unattended session,
report the limit and the ways to authenticate instead. Don't start a second
login right after guided setup finished.

### CLI details

- Quote every URL, because the shell treats `?` and `&` as special characters.
- Check the current login with `tvly --status --json` only when something
  fails. Don't run it before every command.
- Keep the CLI current with `tvly update --check` and `tvly update`.
- Run `tvly <command> --help` for the full list of options.
- Exit codes: 0 means success, 1 a setup or update failure, 2 bad input, 3 an
  authentication error, and 4 an API or live-test error.
