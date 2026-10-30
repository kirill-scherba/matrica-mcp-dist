# matrica-mcp-dist

Public distribution index for the MCP servers of the Matrica stack. Sources live in their own
repositories; this repository holds what the application actually downloads: `catalog.json` and, in
the releases, the archives built by CI.

## catalog.json

One file, schema version 1. Each server lists its versions, and each version lists per-platform
archives with a URL, a sha256 and the entry file inside the archive. Two transports exist:

- `stdio` — the gateway starts the binary and talks to it over stdin/stdout, `command` says how;
- `http` — the binary serves MCP itself, the gateway registers the URL.

`${config}` in `command` expands to the application's configuration directory.

Nothing is downloaded from this repository directly by a browser: the application reads the catalog,
verifies the sha256 of every archive and only then installs it.

## Releases

One release per server and version, tagged `<server>/v<version>`, with the archives and their
`sha256sums`. CI in the source repository creates them.

## chat-machines

Not a stdio tool like the rest: a **service** - rooms, an external connector, opencode behind them, and
an HTTP MCP endpoint at `/mcp`. It is built here by `chat-machines-release.yml`, because the archive is
what a person installs by hand; the catalog does not offer it yet, since nothing in an install would
start the service.

Release tag: `chat-machines/v<version>`. Unpack, run `deploy/install.sh`, set `CM_API_KEY` in
`~/.config/chat-machines/env`, start the user service, then register `http://127.0.0.1:8083/mcp`.
Linux gets a systemd unit; on Windows the binary runs as a console application with the same variables.
