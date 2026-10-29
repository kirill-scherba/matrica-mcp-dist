#!/usr/bin/env python3
"""Build catalog.json from the repositories that publish MCP servers.

Each repository declares its servers in mcp.json at its root. This script reads those declarations, takes
the newest release (or the newest with a given tag prefix), finds the archives per platform, reads their
sha256 files and writes the catalog. Nothing is typed by hand, so the catalog cannot drift from what is
actually published, and a missing platform is reported instead of being silently absent.

Hosted and third-party servers cannot be derived from our releases; they live in extra.json and are merged
in unchanged.
"""
import datetime
import json
import os
import sys
import urllib.request

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
PLATFORMS = ("linux-amd64", "windows-amd64")


def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "matrica-catalog-builder"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=40) as resp:
        body = resp.read()
    return body.decode() if raw else json.loads(body)


def manifest(repo, path):
    try:
        return json.loads(get(f"{RAW}/{repo}/main/{path}", raw=True))
    except Exception as exc:  # noqa: BLE001
        print(f"  {repo}: no {path}: {exc}", file=sys.stderr)
        return None


def release_for(repo, tag_prefix):
    try:
        if tag_prefix:
            for rel in get(f"{API}/repos/{repo}/releases?per_page=50"):
                if rel.get("tag_name", "").startswith(tag_prefix):
                    return rel
            return None
        return get(f"{API}/repos/{repo}/releases/latest")
    except Exception as exc:  # noqa: BLE001
        print(f"  {repo}: no release: {exc}", file=sys.stderr)
        return None


def sha_of(assets, zip_name):
    sha_name = zip_name + ".sha256"
    if sha_name not in assets:
        return ""
    text = get(assets[sha_name]["browser_download_url"], raw=True).split()
    return text[0] if text else ""


def collect_assets(release, server, version):
    """Archives of one server: per platform when published that way, otherwise one for both."""
    assets = {a["name"]: a for a in release.get("assets", [])}
    base = server.get("asset_base") or server["name"]
    entries = server.get("entries", {})
    out = {}
    for platform in PLATFORMS:
        for candidate in (f"{base}_{version}_{platform}.zip", f"{base}_{version}.zip"):
            if candidate in assets:
                out[platform] = {
                    "url": assets[candidate]["browser_download_url"],
                    "sha256": sha_of(assets, candidate),
                    "size": assets[candidate]["size"],
                    "entry": entries.get(platform, entries.get("any", "")),
                }
                break
        else:
            print(f"  {server['name']}: no archive for {platform}", file=sys.stderr)
    return out


def build():
    sources = json.load(open("sources.json"))
    servers = []

    for src in sources["repos"]:
        repo = src["repo"]
        print(repo)
        man = manifest(repo, src.get("manifest", "mcp.json"))
        if not man:
            continue
        rel = release_for(repo, src.get("tag_prefix", ""))
        if not rel:
            continue
        tag = rel.get("tag_name", "")
        version = tag[len(src.get("tag_prefix", "")):] if src.get("tag_prefix") else tag.lstrip("v")

        for srv in man.get("servers") or [man]:
            entry = {
                "name": srv["name"],
                "title": srv.get("title", {}),
                "description": srv.get("description", {}),
                "category": srv.get("category", "tools"),
                "repository": f"https://github.com/{repo}",
                "core": False,
                "latest": version,
                "versions": {},
            }
            if srv.get("docs"):
                entry["docs"] = srv["docs"]

            if srv.get("transport") == "http" or srv.get("install") == "http":
                v = {"transport": "http", "url": srv["url"]}
                if srv.get("settings"):
                    v["settings"] = srv["settings"]
                entry["versions"][version] = v
                servers.append(entry)
                continue

            assets = collect_assets(rel, srv, version)
            if not assets:
                continue
            v = {"transport": "stdio"}
            if srv.get("install") == "script":
                v["install"] = "script"
            v["command"] = srv.get("command", [srv["name"]])
            if srv.get("settings"):
                v["settings"] = srv["settings"]
            if srv.get("env"):
                v["env"] = srv["env"]
            v["assets"] = assets
            entry["versions"][version] = v
            servers.append(entry)

    if os.path.exists("extra.json"):
        for srv in json.load(open("extra.json"))["servers"]:
            servers = [s for s in servers if s["name"] != srv["name"]]
            servers.append(srv)

    servers.sort(key=lambda s: s["name"])
    catalog = {
        "schema": 1,
        "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "servers": servers,
    }
    with open("catalog.json", "w") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"catalog: {len(servers)} servers")


if __name__ == "__main__":
    build()
