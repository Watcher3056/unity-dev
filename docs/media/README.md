# README recordings

`unity-hook-*` (light and dark) are the README's short hooks: a caption with the
problem, the feature in the actual FlowAI Graph interface with the Unity-dev stage
profile, and a closing line. The captions are drawn into the recorded page;
nothing else is edited.

- `unity-hook-chat-*` and `unity-hook-proof-*` open on a **staged chat**: a
  generic chat page written for the recording, not any real product's interface,
  showing how the same popup bug reads as a long answer with code and logs, and
  as a "fixed, 0 errors" that never ran the game. Everything after "This is Flow"
  is the actual viewer.
- `unity-hook-pick-*` is the actual viewer throughout.

`unity-flow-*` and `unity-proof-*` are the full recordings the README links to.

All were captured on 2026-10-18 from viewer files matching Graph source `59271d6`;
the interface was not rebuilt or restyled. Parts of the hooks are sped up, the
captions are not.

The popup scenario is a scripted Normal-mode demonstration. Flow is recorded while
the trace grows; the choice of fix is clicked on its question card. Its code, log
excerpts and before → after pictures come from the retained Graph demo; the
displayed check results are illustrative, not evidence of a new Unity test run.

The camera pans and the cursor clicks real controls. Only a pointer and click
indicator are added to the browser frames. Both themes use the viewer's own
appearance settings.

The `trace-*` GIFs remain as historical assets; they show the older interface,
which is now the Decisions view.

See [asset provenance](../asset-provenance.md).
