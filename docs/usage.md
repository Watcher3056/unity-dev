# Unity-dev usage

This repository and plugin are named `unity-dev`. The only included skill is
`unity-dev`; everyday-assistant is distributed independently.

Initialize the Graph submodule before building. The gitlink pins source; the
generated plugin bundles its required Graph runtime, so dependency availability
does not rely on an unsupported cross-plugin manifest field. `SOURCES.json`
records the Unity source and exact Graph dependency commits. The Graph plugin
can also be built independently from its own repository.

Change the dependency deliberately: commit Graph in its own repository, fetch
the desired commit into the submodule, check it out detached, stage the gitlink,
and commit the Unity dependency update. Builds fail for missing, dirty or
incorrectly checked-out dependency source. They never follow Graph's latest main
automatically. Re-run package, runtime and disclosure checks after a pin update.

Codex role identifiers remain `unity-dev-<role>`. Claude role identifiers use
`unity-dev:unity-dev-<role>`, matching the new plugin namespace. The skill's
source rules are unchanged by the repository split.

Use one enabled Graph provider per chat to avoid duplicate graph tools if you
also installed the standalone FlowAI Graph plugin.

Remove through `codex plugin remove unity-dev@unity-dev` or
`claude plugin uninstall unity-dev@unity-dev`. Codex role files copied into its
`agents/` folder are separate; remove only files matching this product's generated
roles when no longer needed. Existing evidence and data are retained.


## Requirements and checks

Python 3.11+ and Git. From the repository root:

```sh
python -m pip install -r requirements-dev.txt
python tools/build_plugin.py
python tools/build_plugin.py --host claude
python -m unittest discover -s tests -v
```

Use `py -3` instead of `python` on Windows when needed, or `python3` on
macOS/Linux. Plugin runtime uses Python's standard library. Skill builds also
need the pinned PyYAML build dependency. Claude hooks need bash (Git Bash on
Windows). The graph MCP command defaults to `py -3` on Windows and `python3`
elsewhere; `--python-command` selects another executable name on PATH.

## Local installation and updates

Build and validate first, then use the selected host:

```sh
python tools/build_plugin.py --install
python tools/build_plugin.py --host claude --install
```

Only run the command for the host you use. The installer registers this local
checkout's marketplace. It changes client installation only with `--install`.
Start a new client session afterward. In Codex, review and trust hooks through
`/hooks`; Claude Code can also use `/reload-plugins`. Codex role files, where
present, are copied into the configured Codex home's `agents/` directory.

For an update, review the new source/dependency revision, repeat the dependency
setup, build, checks and selected install command. Generated builds use a new
timestamp version, or `--version X.Y.Z` for a fixed candidate. `--dist-root DIR`
stages a package without installing. Previous generated outputs are retained
under an ignored `.previous/` folder instead of deleting diagnostics.

## Data, permissions and limitations

Hooks and MCP processes run with the client's local permissions. Project traces,
profiles and evidence are retained under `.ai-profile/`. Viewer state and attached
files use the host plugin data directory, falling back to `~/.agent-trace/`.
Session logs stay in the client data directory. Data is not automatically deleted;
an indexing window is not a retention limit. Keep these directories out of Git.

The optional/embedded graph viewer binds to `127.0.0.1:8765` by default. Keep it
on loopback: it has no login and is not a network service. Registered projects
and trusted trace citations can expose local evidence, including cited absolute
paths outside the project. Only import trusted traces and add-ons. The viewer
rejects uncited evidence requests and attachment-directory escapes; served
evidence/media are browser-sandboxed. Local processes can access its APIs.

Viewing uses the local server. External links open their websites. Asking the
agent questions or sending chat messages uses the configured model provider,
its permissions and usage; task context can leave the machine through that
client. No cloud service or project-specific API key is provided by these repos.

Model output and graph traces are an agent's account, not independent proof of
correctness. Packaging tests do not establish Unity gameplay or agent behavior.
Other hosts beyond Codex and Claude Code are not packaged by these builders.

After publication, use the repository issue tracker for minimal synthetic bug
reports. Do not post credentials or real chats/customer data. Use private
vulnerability reporting if enabled, otherwise request a private reporting channel.

## License

[MIT](../LICENSE). See [dependency notices](../THIRD_PARTY_NOTICES.md) and
[asset provenance](asset-provenance.md).
