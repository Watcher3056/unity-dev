# Unity Dev

An AI skill pipeline for Unity development: investigate, compare approaches,
implement, review and verify in the Editor. Its reusable rules and role files
live in `skills/unity-dev/`; private benchmark cases and authoring records stay
in the private workspace.

## Required FlowAI Graph dependency

`vendor/flow-ai-graph` is a Git submodule pinned to an exact Graph commit.
The builder verifies the gitlink, checked-out commit and clean dependency tree.
It embeds that Graph runtime in the generated Unity-dev plugin, with composed
skill/graph hooks and declared MCP tools. Installing this plugin supplies the
Graph dependency; a second Graph plugin installation is not required.

For this local-only setup, keep the sibling `flow-ai-graph` repository and run:

```sh
git -c protocol.file.allow=always submodule update --init --recursive
python -m pip install -r requirements-dev.txt
python tools/build_plugin.py
```

The file-transport permission is command-scoped for local sibling repositories.
The tracked `.gitmodules` URL is relative (`../flow-ai-graph`), with no local
account path or invented hosted remote. After publication, normal recursive
clone/update resolves sibling repositories on that host.

Example: `$unity-dev investigate the popup close bug` in Codex, or
`/unity-dev:unity-dev investigate the popup close bug` in Claude Code.

[Build/install/update/removal and permissions](docs/usage.md) · [MIT](LICENSE)

This repository is prepared locally; nothing has been published.
