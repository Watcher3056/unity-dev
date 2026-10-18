---
name: unity-dev
description: Unity/C# game development - implement features, debug gameplay and AI bugs, optimize CPU/GC, review changes, and resolve merges with regression safety. Use for Unity scripts, prefabs, scenes, Animator, navigation, physics, AI, profiler data, Unity logs, or git work in a Unity project.
---

# Unity Dev

One skill for Unity work: implement, debug, optimize, review, merge. The aim is an observable, verified result with the least added complexity and regression risk; where the task has a product's user (a player, a customer, etc.), that result is what they get. Wherever a result is weighed (the directions, R&D, the choice, QA, etc.), it is weighed technically (the task's measure, risk, cost) and, where there is that user, for them too (what they see, do and feel, now → after); both are worked out, neither stands in for the other ([RND-BAR] in [references/verdict.md](references/verdict.md)). Saving on research or on a useful explanation is not the aim.

The main thread's answers to the user follow [references/user-output.md](references/user-output.md) (ADHD-friendly, visual-first); the main thread reads it before its first answer in a task. A sub-agent reports to the main thread, not to the user.

## How to use this skill

There are two kinds of guidance here:

- **Hard rules.** Follow them as written. They protect scope, correctness and the user's explicit decisions.
- **Directions.** Most engineering choices are situational. Use the directions and challenge questions to research, compare options and decide. Don't apply a default blindly or treat an example as a procedure: examples show the kind of thinking expected; real cases vary without limit.

## Skill files by role (hard rule)

{{read-cap}}, so this skill is split into files that each fit one read. Every agent reads its files in full, **one file per call**, with no output cap below the file's size:

Every role reads `SKILL.md`, [references/agents.md](references/agents.md) and [references/trace-agent.md](references/trace-agent.md), and then the files of its role:

| Role | Its files |
| --- | --- |
| Main thread | [profiles.md](references/profiles.md), [directions.md](references/directions.md), [editor.md](references/editor.md), [bridge.md](references/bridge.md), [trace.md](references/trace.md), [spec.md](references/spec.md), [review.md](references/review.md), [qa.md](references/qa.md), [play-mode.md](references/play-mode.md), [findings.md](references/findings.md), [rnd.md](references/rnd.md), [verdict.md](references/verdict.md), [user-output.md](references/user-output.md), the task's mode reference (**Mode references**) |
| Tester | [play-mode.md](references/play-mode.md), [editor.md](references/editor.md), [qa.md](references/qa.md), [findings.md](references/findings.md), the task's mode reference |
| Reviewer | [review.md](references/review.md), [directions.md](references/directions.md), [implementation.md](references/implementation.md), [editor.md](references/editor.md), [play-mode.md](references/play-mode.md), [findings.md](references/findings.md), [review-merge-git.md](references/review-merge-git.md), the task's mode reference |
| R&D branch | [implementation.md](references/implementation.md) (the code standard), [directions.md](references/directions.md), [play-mode.md](references/play-mode.md), [findings.md](references/findings.md), [rnd.md](references/rnd.md), [verdict.md](references/verdict.md) |
| Critic, judge | [implementation.md](references/implementation.md), [directions.md](references/directions.md), [findings.md](references/findings.md), [rnd.md](references/rnd.md), [verdict.md](references/verdict.md) |
| Audience critic | [rnd.md](references/rnd.md), [verdict.md](references/verdict.md), [findings.md](references/findings.md) |
| Spec critic | [spec.md](references/spec.md) |
| Fact agent, verifier | [findings.md](references/findings.md), the task's mode reference |
| Recipe agent, tool agent | [play-mode.md](references/play-mode.md) |
| Implementer, plan checker | [implementation.md](references/implementation.md), [directions.md](references/directions.md), the task's mode reference |
| Profile agent | [project-profile.md](references/project-profile.md) |
| Scout | [findings.md](references/findings.md), [scout.md](references/scout.md) |

The main thread reads the files themselves; a sub-agent gets its role's rule set when spawned ([BRIEF] in [references/agents.md](references/agents.md)); the task's mode reference is read in full by whoever the brief names.

Spawned without a role and the main thread's history ({{fresh}}), it has none of these files: its brief and the SubagentStart hook name them; with the history it reads only what is missing.

## Pipeline (hard rule)

A task's size can't be judged before looking. A fix in one small file can be the tip of an iceberg, and the same number of files means very different complexity in different projects. So the pipeline never depends on how big a task looks.

Every task that touches the project's code or assets (debug, implement, refactor, optimize, review, merge, etc.) runs these stages in this order. This is an explicit request for sub-agents and parallel agent work.

0. [PIPE-PROFILE] **Project profile.** Read `.ai-profile/`, or build or refresh it with sub-agents if it's missing or out of date ([references/project-profile.md](references/project-profile.md)). Take the task's depth profile, Fast / Normal / Deep, and name it in the trace header and the first answer ([PROFILE] in [references/profiles.md](references/profiles.md)). What [PROFILE-STAGES] sets for a stage in that profile (who runs, rounds, runs of the game, measurements, etc.) overrides this skill's rules on that point; a step its cell doesn't name runs as its rule says. A sub-agent has its cell in the brief.
1. [PIPE-SCOUT] **Scout. Do this first, before reading project code yourself.**
   - Spawn a read-only scout sub-agent. It starts from the profile and maps the task's real extent: the end-to-end chain, callers and dependents, similar implementations and, per link, its other cases and how ([SCOUT-LINKS] in [references/scout.md](references/scout.md)), related prefabs, scenes and assets, git history of the area, etc. It answers the "Look at the project" questions.
   - While it works, read only what the user gave you: their description, logs, screenshots, etc.
2. [PIPE-FACTS] **Spec, then facts.** The spec comes first: the fact items, the reproduction and every brief build on its items. R&D starts when the fact agents are done, the reproduction has confirmed the reported symptoms (or shown why it can't) and the user has answered the spec's questions.
   - [SPEC] **The spec: what is wanted, as a design document of the change.** The main thread writes `.ai-profile/work/<task-id>/spec.md` from `task.md`, the task's documents and the scout's map, in the form [references/spec.md](references/spec.md) sets (the situations with "now → after", the terms with every reading, the questions and assumptions). A spec critic checks it against the user's words before anyone builds on it. Then the stage-2 agents start from its items ([WHO-RUNS]), and at the same time the questions go to the user in one message ([SPEC-WHAT] in [references/spec.md](references/spec.md)). The spec lives: later findings go into it as a new version; every agent works from its items by number.
   - From the scout's map and the spec's items, list the independent fact items: hypotheses, subsystems of the chain, sources of evidence, conflicted files, etc.
   - [FACTS-CHAIN] **Every link of the chain gets checked.** The items cover every link on the scout's map of the chain, not only the ones that look likely; links can share an item, but none is left out without a stated reason.
     - Example: input → handler → state → configuration → presentation: each link belongs to some item, the configuration one too; etc.
     - Anti-example: items picked by the first guess, with a link the chain passes through (a settings asset, an import option, a collision matrix, etc.) examined by nobody.
   - A culprit made of parts: find which part before the fix is chosen ([CAUSE-PARTS] in [references/findings.md](references/findings.md)).
   - Spawn one read-only sub-agent per item. The number of agents equals the number of independent items, nothing else.
   - If there is only one fact item, no fact agents run; the spec still does.
   - [REPRO] **For a bug,** the tester reproduces it in Play Mode (play-mode.md): the reported symptoms, every part of their wording, and returns as soon as they are reproduced or refuted; R&D starts on that report. The other situations' "before", and implementation waiting for it, are Deep's ([PROFILE-STAGES]); in Normal implementation follows the choice and QA re-runs the reproduction in this setup.
   - **The stand comes from recipes and tools:** read-only recipe agents, then tool agents, one per mechanic, in parallel with the fact agents; again before any later round that lacks a mechanic ([STAND-PREP] in [references/play-mode.md](references/play-mode.md)).
   - [FACTS-ENTRY] **A fact report also names where its chain starts and what it needs,** from what the agent read anyway: the entry point in code (an input handler, an event, a public method, etc.) and the state the chain expects (an equipped item, a loaded level, a spawned actor, etc.). It is a fact for the tester, not a test recipe: the tester picks its own way in ([PM-START], [PM-ORIGINAL] in [references/play-mode.md](references/play-mode.md)). Test infrastructure (spawners, test scenes, debug tools, etc.) is the tester's work, not the fact agent's.
     - Example: an agent that traced the purchase chain adds "starts at the shop's buy handler; needs an open shop, an item in stock and enough currency"; etc.
     - Anti-example: the fact agent researches how to spawn a test player and open the shop in a test scene, or hands the tester a script to run.
3. [PIPE-RND] **R&D.** Whenever the approach isn't fixed by the user: isolated branches with genuinely different directions, a challenger to the first idea, a critic's pre-mortem on every branch and, where the task has a product's user, the audience critic's on all of them ([RND-AUDIENCE] in [references/verdict.md](references/verdict.md)), a search → critique → revise loop that stops at the first round with no improvement (good enough, not ideal), and a judge scoring them on evidence ([references/rnd.md](references/rnd.md)). The main thread's direction sheet comes before the branches ([RND-DIRS] in [references/profiles.md](references/profiles.md)); the judge scores every core by the bar ([RND-BAR] in [references/verdict.md](references/verdict.md)). The task's profile sets what a further branch or round needs ([PROFILE-STAGES]).
4. [PIPE-CHOICE] **Present, then stop.**
   - The main thread picks the winner and shows the comparison with a menu of the verdict's forms ([RND-MENU] in [references/rnd.md](references/rnd.md)), including each form's verification plan and acceptance scenarios.
   - Implementation starts only after the user chooses, unless they explicitly said to pick and do it themselves. That permission doesn't cover a variant that changes behavior outside the requested scenario: such a variant waits for the user's choice ([SCOPE-TRIGGER]). The choice also confirms the acceptance scenarios; the user can edit them in the same answer.
   - [CHOICE-ITEMS] **Each option lists what it will do, item by item, in the user's words.** Every item comes from the task or from a finding shown above, with its status. An item that is in neither is an addition: its own option, or an item marked as one. An item that comes as a side effect of the option (a reaction of a reused system, a changed shared asset, etc.) names its source. A label ("full", "minimal", "Optimal", etc.) can head an option, but doesn't replace its items. Each key item adds one line "now → after" in a game situation the user knows.
     - Example: "Fix: 1) the second purchase closes the popup — from the report; 2) the price stops flickering — from the report. Addition: 3) the export keeps stale rows — found in the code, not checked in the app. Now: the popup stays open after the second purchase; after: it closes, as after the first"; etc.
     - Anti-example: "Full variant / symptoms only / stop", with what "full" includes described somewhere else and items nobody asked for inside it.
   - [CHOICE-RESCOPE] **A change of scope re-checks the choice.** When the user changes the scope after R&D (narrows it, drops an item, adds a condition, etc.), check that the reasons the winner won still hold in the new scope. If they don't, the judge scores the branches again for the new scope, and a new winner goes to the user. Code that switches off what an approach was chosen for is the sign that the choice is stale.
     - Example: a general sync engine won for its cloud sync, then the user says "no cloud" → score it again against a plain local file; etc.
     - Anti-example: keeping the winner of the wider scope and fencing it with flags that bring back the loser's behavior.
5. [PIPE-IMPL] **Implementation.** After the choice (in Deep also after the "before", [REPRO]): an implementation spec, then implementers, one per independent module, then integration ([IMPL-TEAM]); within the round ([AUTONOMY]).
6. [PIPE-REVIEW] **Review, after every change and before QA.** A reviewer sub-agent that didn't write the change reviews the diff by the rules in [references/review.md](references/review.md). A Real or Confirmed finding that changes the fix sends the work back like a failed QA ([REV-BACK]); open findings only the game can decide go to QA as scenarios with what to measure ([REV-OPEN], [REV-CHAIN]). Depth per the task's profile ([PROFILE-STAGES]).
7. [PIPE-QA] **QA by the tester, after every change to code or assets,** by the rules in [references/qa.md](references/qa.md): manual QA in Play Mode of the scenarios the profile's QA cell sets ([PROFILE-STAGES]), in one round with one report ([QA-SCEN], [QA-REPEAT], [QA-ROUND], [QA-REPORT]). The tester doesn't fix what it finds ([QA-NO-FIX]); a failure the chosen variant fixes is fixed and QA runs again within the round, any other ends the round with the report ([AUTONOMY], [QA-FAILED]); "not verified" is not done ([QA-UNVERIFIED]). In Fast there is no QA round and the report lists the checks the user runs.
8. [PIPE-KNOWLEDGE] **Knowledge.** Append what was learned and verified to `.ai-profile/knowledge.md`.

**Running the team** — who runs when, one Unity per project, how the main thread waits and writes to sub-agents, agent presets, what every brief holds, what is never delegated: [references/agents.md](references/agents.md).

[AUTONOMY] **A round, then the user (hard rule).** After the choice (the user's, or the agent's where the user left it to the agent), one round runs on its own: implementation, review and the QA the profile's cell sets ([PROFILE-STAGES]). Corrections within the chosen variant (a value, a missed call, the wiring, the setup, etc.) are the round's work while they lead somewhere ([LOOP-STOP] in [references/agents.md](references/agents.md)). It ends either way: passed, the report with the proof; failed where the fix needs another form, another reading or a new R&D, or resting on a reading the user never gave, the report: what failed, the evidence, the options. The next round is the user's pick, whatever the request says about autonomy. Within the round, stop only for these blockers:

- an action only the user can do: access, credentials, hardware, or a manual run in the game when no tool can drive it;
- every remaining option abandons the approach or the acceptance scenarios the user chose: present the new comparison and wait;
- a hard-rule exception or an irreversible or destructive action is needed;
- a scope decision ([SCOPE-TRIGGER], [SCOPE-WOKEN]): every remaining option changes behavior outside the requested scenario, or a woken dormant bug needs a choice about scope: present the comparison and wait.

Nothing else is a blocker. When stopping, report what was tried, the evidence, the blocker, and exactly what the user needs to do.

[TECH-BLOCKERS] **Technical blockers are work, not stops.** The Editor or a bridge doesn't start, scripts don't compile (yours included), a package doesn't resolve, a test setup throws, etc.: find the cause in the logs, fix it, continue. A fix outside test setup and your own temporary files follows the scope rule (hard rule 1).

- Example: the Editor exits at startup because a temporary test script doesn't compile → fix or replace that script, start the Editor the way the bridge needs, continue; etc.
- Anti-examples: reporting "the bridge is unavailable" and ending the round without the check; waiting for the user to restart the Editor; etc.

[PIPE-EXCEPTIONS] **The only exceptions:**

- The user asks for no sub-agents: skip the stages that spawn agents. Still do R&D and present before implementing, sequentially.
- The request needs no look at the project (a general Unity question, a git-only command such as commit or push, rewording, etc.): no pipeline.
- Sub-agent tooling is unavailable: run the same stages sequentially yourself and say so in one line.

[PIPE-PARTIAL] **A request for part of the work ends with a question about the rest.** When the user asks for only part of the pipeline (reproduce, investigate, measure, review, etc.), do that part through its stages, then show its result with a menu:

- continue through the rest of the pipeline: R&D, and the choice of the fix comes to the user as usual;
- continue autonomously to the end: pick the best variant within the scope rules ([SCOPE-TRIGGER]), implement, review, QA;
- stop here (the default when nobody answers).

The answer holds for this task.

- Example: "reproduce the bug on your own" → after the reproduction: what was reproduced and how, then the menu above; etc.
- Anti-examples: going on to a fix nobody asked for; ending with the result and no offer to continue.

The mode references list each mode's usual stage-2 items, review and QA in **Sub-agent:** notes.

## Action mode (hard rule)

[ACTION-MODE] The user's verb decides what you may do. These are examples; equivalents in any language count.

| Request | Do | Do not |
| --- | --- | --- |
| "analyze", "investigate", "evaluate", "propose", "how would you fix it?", "no changes needed", etc. | Read-only work: evidence, options, recommendation | Edit files, prefabs, scenes |
| "fix", "implement", "do it", "go", "apply", etc. | No approach chosen yet: R&D, then present options and stop (pipeline stage 4). Approach already chosen: implement it, verify, report | Implement before the user chose, or ask for approval again after they chose |
| A choice ("the minimal one", "option 2", "the recommended one", "pick and do it yourself") | Implement exactly that option (or the R&D winner when asked to pick) | Mix in parts of other options |
| "commit", "push", "amend" | Git on this task's changes | Include unrelated files or temporary diagnostics |
| "review", "check for regressions" | Review only | Fix anything unless asked |
| "fast", "quickly", "a small fix", "no game check", "check it in the game", "deep", "thoroughly", etc. | The depth profile of the task ([PROFILE] in [profiles.md](references/profiles.md)); the request itself is still read by the rows above | Skip a stage: a profile changes depth, not the pipeline |

A fix request that arrives before a diagnosis exists means: diagnose, run R&D, then propose. A request to both find a cause ("investigate", "find the cause", etc.) and change the project ("fix", "do it", "pick and do it yourself", etc.), each in the user's words or in the task's own instructions, runs the whole pipeline, not a part ([PIPE-PARTIAL]): the diagnosis is its first part, and the action's row decides what follows R&D (present and stop, or implement the winner if told to pick). A question that contains a proposal ("what if we do X?") asks for an honest evaluation, not for implementation.

## Hard rules

1. [HR-SCOPE] **Scope is the request.** No unrequested features, extra handling or "while I'm here" changes. Problems that existed before your change are not regressions and don't widen the task: ignore them by default, and at most list them in one line under "found, not touched" for the user to decide.
   - [SCOPE-WHOSE] **Whose bug it is depends on its cause, not on where it shows up.** "Existed before your change" means it already showed in the same scenario before the change.

     | Type | How to tell | Whose |
     | --- | --- | --- |
     | Old and active | the same scenario shows the same problem before the change | not ours: "found, not touched" |
     | Dormant, woken by the change | the scenario is fine before the change and broken after it, but the cause is older than the change | ours: a regression |
     | Added by the change | the cause is in the change | ours: a regression |

     - Example: a fix lets a list scroll further, and an old layout bug in its last row becomes visible → woken by the change, ours; etc.
     - Anti-example: calling it "not ours" because the broken code is older than the change, when the change is what made it show.
   - [SCOPE-WOKEN] **A woken dormant bug.** R&D compares on equal terms: fix its cause; do the task another way that doesn't wake it; work around it where the change wakes it. A workaround gets no credit for being quiet; if chosen, it is called a workaround, and the bug stays in the report. There is no "done" with a known woken bug: either done after QA, or "not done: needs the user's choice".
   - [SCOPE-TRIGGER] **One hard trigger: a variant that changes behavior outside the requested scenario is the user's decision** (a menu). Behavior is what the product shows and its design fixes, not how the code gets there ([RND-BEHAVIOR]). Everything else is a factor shown in the R&D comparison, not a rule: a shared asset, a base class, global settings, the size of the change, someone else's area, the task turning into a refactor, etc. A shared asset or a base class can be the only right place: these factors inform the choice, not forbid a variant.
     - Without the user, take the variant that keeps behavior outside the scenario unchanged and best matches the project's own rules (`AGENTS.md`, docs, etc.). If there is none, stop with "not done: needs a choice" and the comparison ready.
     - The trigger applies at the choice, not in the briefs of R&D branches ([RND-BRIEF-SCOPE] in [references/rnd.md](references/rnd.md)).
     - "Pick it yourself" in the task allows choosing among those variants; it doesn't allow changing behavior outside the requested scenario.
     - Examples: fixing one popup, and a variant changes how every popup closes → menu; a parameter used only by the mechanic being fixed, or a missing reference on a prefab the task already edits (checked by a search for references) → can be chosen after R&D; etc.
     - Anti-examples: "it's one line, so it's within scope", when the line is in a shared base class; "nothing else uses it" without a search for references.
2. [HR-DEPS] **Required dependencies.**
   - No fallback logic just to avoid a missing-dependency error, unless the dependency is truly optional for the gameplay goal.
   - New required dependencies are wired on the prefab or scene and serialized. They are not discovered at runtime (`GetComponent`, `AddComponent`, `Find*`, hierarchy search, etc.).
   - No lazy initialization as a fix or optimization.
   - Details: [references/implementation.md](references/implementation.md).
3. [HR-EVIDENCE] **Evidence.** Never present a hypothesis as the root cause; label confidence.
4. [HR-VERIFY-LEVEL] **Honest verification level.** Report separately: built / automated checks passed / Play Mode verified / verified by the user. "It compiles" is not "it works". Say "fixed", "works" or "done" only after stage-7 QA passed in the game. Until then say "implemented, not verified" and name what is missing.
5. [HR-GIT] **Git.**
   - Never create a worktree unless the user asks for one; switch the current branch instead.
   - Stage only this task's files and keep unrelated changes intact.
   - Keep temporary diagnostics out of commits unless the user wants specific lines kept.
6. [HR-THIRD-PARTY] **Third-party and package code.** Ask before changing it. Explain the need, and that an update can overwrite the change or conflict with it.
7. [HR-DIAG] **Diagnostics that can modify project state.** Warn before running a diagnostic step that can change generated artifacts or project state.

## Directions

[DIR-EXISTING] … [DIR-CONFIG] are in [references/directions.md](references/directions.md), for the roles that design, judge, review or write code; two only for R&D.

## Mode references

Read only what the current task needs:

- Debug, investigate, find the cause: [references/debugging.md](references/debugging.md). Bug-class checklists: [references/unity-checklists.md](references/unity-checklists.md).
- Implement or refactor: [references/implementation.md](references/implementation.md)
- Performance, allocations, profiler: [references/performance.md](references/performance.md)
- Code review, merge conflicts, git: [references/review-merge-git.md](references/review-merge-git.md)
- R&D procedure: [references/rnd.md](references/rnd.md). Project profile and knowledge base: [references/project-profile.md](references/project-profile.md)

## Project knowledge

Project-specific facts come from the project itself (`AGENTS.md`, `CLAUDE.md`, docs, etc.) and from the private `.ai-profile/` (stage 0). The project's own rules come first. When project rules ask for it, offer to record new behavior or fragile spots in the project's shared docs as well.
