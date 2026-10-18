# The open Editor

Part of the unity-dev skill, read by the main thread, the tester and the reviewer (SKILL.md, **Skill files by role**): how every role works with the one open Editor and its bridge. Offering, connecting and updating the bridge itself is in [bridge.md](bridge.md).

- [PM-EDITOR] **One open Editor.** When the project has an editor bridge (Unity MCP, etc.), work through it: build the setup, enter Play Mode, read the state, adjust and run again without relaunching Unity. If the Editor isn't open, or it closed, launch it the way the bridge needs (its documented start for batch mode, required settings, etc.), wait until the bridge answers, and never start a second instance; record the launch recipe in `.ai-profile/knowledge.md`.
- Offering, connecting and updating the bridge is the main thread's work at the start of the task ([bridge.md](bridge.md)); a sub-agent that finds no bridge reports it.
- [PM-SHARED-EDITOR] **Don't close a shared Editor.** An open Editor may be the user's, with unsaved work. Before invoking a project method in it, read the method: entry points made for batch runs (builds, validators, test scripts, etc.) often end with `EditorApplication.Exit`.
  - Anti-example: invoking a validator written for `-executeMethod` in the open Editor, which closes it; etc.
- [PM-WINDOW] **A window or batch mode is the user's choice.** Ask before the first Play Mode run: with a window (the user can watch the run) or without one (batch mode, nothing pops up on the screen). Keep the answer for the task. With no answer, use batch mode unless a check needs a picture (screenshots of the Game or Scene view, UI layout, rendering, etc.). A modal dialog in a windowed Editor can stall the run; treat it as a technical blocker.
