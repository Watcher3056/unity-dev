<div align="center">

# Unity-dev

### Understand the cause. Compare the fixes. See what was checked.

A Unity development skill with a structured agent team and **FlowAI Graph built in**.<br>
Follow the work in Flow, ask about an approach, and choose with the evidence in view.

**Codex · Claude Code · Unity Editor**

[Watch the workflow](#your-unity-task-in-flow) · [Why use it](#what-unity-dev-adds) · [Get started](#get-started)

</div>

## Your Unity task in Flow

**From the player's problem to the chosen approach and its checks—in one connected view.**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/media/unity-flow-dark.gif">
  <img src="docs/media/unity-flow-light.gif" alt="Actual Flow interface: inspect a popup bug, compare two fixes, ask why the listener fix was chosen, and open the Play Mode check details." width="100%">
</picture>

<sub>Recorded from the actual Graph viewer. Scripted Normal-mode popup scenario with illustrative evidence; this recording is not a new Unity gameplay test.</sub>

[Full-size recording: light](docs/media/unity-flow-light.gif) · [dark](docs/media/unity-flow-dark.gif)

Instead of reconstructing the task from a long conversation, you can:

- **Read the gameplay meaning first.** What the player sees, why it happens, and what the proposed change would do.
- **Compare fixes where you choose them.** Benefits, risks and rejected alternatives stay together.
- **Ask about a specific step.** Why and How open beside its card; a connected live session also accepts your own contextual questions.
- **Open the supporting detail.** Inspect the change, cited source, screenshots and verification reports without losing your place in Flow.
- **Keep going from the result.** See what passed, what remains unverified, and where the agent needs your decision.

Flow is the everyday view. **Decisions** exposes the step-by-step reasoning and evidence; **Tech** shows agent activity, time and tokens.

## What Unity-dev adds

A general AI agent can investigate, review and test when asked. Unity-dev makes these practices part of an explicit, reusable workflow.

| Practice | What the skill adds for you |
| --- | --- |
| **Investigate before editing** | Maps the affected behavior and separates confirmed causes from hypotheses. In Normal and Deep, reproduces bugs in Play Mode. |
| **Compare approaches** | Develops competing directions, critiques them and presents their trade-offs before implementation. |
| **Keep control of scope** | You choose the approach, or explicitly delegate the choice. Changes to behavior outside the requested scenario require your decision. |
| **Separate author and reviewer** | Uses a reviewer who did not write the change; Normal and Deep also use a tester for gameplay verification. |
| **Show the verification level** | Distinguishes compilation, Editor checks and Play Mode evidence. Missing gameplay verification remains visible. |
| **Retain project knowledge** | Keeps project notes and verified findings in a private `.ai-profile/` directory for later tasks. |

The trade-off is extra agent work, time and tokens. Choose the depth you need; comparative success rates have not been established here.

## Choose the verification depth

**Fast is the fallback default. Ask for Normal when you want the behavior checked in the game.** A project's configured default can change this.

| Mode | What to expect |
| --- | --- |
| **Fast** | Investigation, competing approaches, review and targeted Editor checks. No Play Mode test round; the result states what you still need to check in the game. |
| **Normal** | Bug reproduction in Play Mode, followed by checks of the chosen fix, acceptance scenarios and relevant regressions. |
| **Deep** | Broader investigation and gameplay verification, with measured before-and-after evidence across the task's scenarios. |

These modes change the depth of work, not the need to respect scope or distinguish evidence from assumptions.

## How a task progresses

**Understand → Investigate → Compare → You choose → Implement → Review → Verify → Retain findings**

The skill covers features, bugs, refactors, performance work, reviews and merges. Its checks follow the task and the selected mode.

For gameplay work, it operates through your Unity Editor and a Unity MCP bridge. Test setups keep the original behavior under examination and retain their artifacts for inspection. If a check exposes a problem, the report shows the failure; a broader change of approach comes back to you.

## Get started

**Requirements:** a Unity project, Python 3.11+, Git, and Codex or Claude Code. Editor and Play Mode checks need a working Unity MCP connection. Claude Code hooks also require Bash; use Git Bash on Windows.

### Prepare the local checkout

Graph is a required, pinned Git submodule and is bundled into the generated Unity-dev plugin. **You do not need a second Graph installation.**

For the current local setup, keep the sibling `flow-ai-graph` checkout, then run from this repository:

```sh
git -c protocol.file.allow=always submodule update --init --recursive
python -m pip install -r requirements-dev.txt
python tools/build_plugin.py
```

The file-transport setting applies only to that local submodule command. This repository has not been published yet.

### Install for your app

<details open>
<summary><b>Codex</b></summary>

```sh
python tools/build_plugin.py --install
```

Start a new session and review the hooks through `/hooks`. In your Unity project, try:

```text
$unity-dev Use Normal. Investigate why the shop popup stays open after
a second purchase. Compare fixes, let me choose, then verify in Play Mode.
```

</details>

<details>
<summary><b>Claude Code</b></summary>

```sh
python tools/build_plugin.py --host claude --install
```

Start a new session or use `/reload-plugins`. In your Unity project, try:

```text
/unity-dev:unity-dev Use Normal. Investigate why the shop popup stays open
after a second purchase. Compare fixes, let me choose, then verify in Play Mode.
```

</details>

Use `py -3` instead of `python` on Windows if needed, or `python3` on macOS/Linux.

**What you should see:** Flow opens beside the conversation, the agent investigates your scenario, and the proposed approaches appear before implementation. In this example you choose the fix, then follow its review and Play Mode checks.

## Graph and your project

- The bundled **FlowAI Graph** is the same general-purpose system that can connect to other agent workflows. Unity-dev adds its development process and stage profile.
- Keep one Graph provider enabled per chat if you also use the standalone Graph plugin.
- Project notes, traces and evidence stay in local data folders. Questions sent to the agent use your configured model provider.
- Builds pin the Graph dependency to an exact commit. Updating the standalone Graph repository does not silently update this plugin.

[Builds, updates, removal and data](docs/usage.md) · [Skill source](skills/unity-dev/SKILL.md) · [Bundled Graph documentation](vendor/flow-ai-graph/README.md) · [Media notes](docs/media/README.md) · [MIT license](LICENSE)
