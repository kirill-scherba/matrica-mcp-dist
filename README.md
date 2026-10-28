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
