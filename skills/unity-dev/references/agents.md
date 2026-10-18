# Running the team (hard rule)

Part of the unity-dev skill, read by every role (SKILL.md, **Skill files by role**).

[WHO-RUNS] **Who runs when (hard rule).** Roles run at the same time only as this table says.

| Stage | Runs at the same time | Holds Unity | Waits |
| --- | --- | --- | --- |
| 0–1. Profile, scout | profile agents, then the scout | nobody | main thread (reads what the user gave) |
| 2. Spec, then facts | the spec critic; then fact agents + recipe agents, then tool agents; then the tester (reproduction of the reported symptoms, for a bug) | tester | main thread (writes the spec, asks the questions) |
| 3. R&D | branches, then critics and the audience critic, then the judge; in Deep the tester measures the "before" of the spec's other situations meanwhile | tester | main thread |
| 4. Choice | main thread | — | everyone |
| 5. Implementation | plan checker; then implementers, one per module; then the integrator | the integrator | main thread |
| 6a. Review | reviewer (without Unity) + tester (base setup) | tester | main thread |
| 6b. Review | reviewer (Editor checks, if any) | reviewer | tester, main thread |
| 7. QA | tester: extends the setup for the review's open items, then runs every scenario | tester | main thread |

- [ONE-UNITY] **One Unity per project.** Only the role that holds it launches it; anyone else who needs Unity waits or hands the task to the holder. In the Fast profile no tester runs and nobody holds Unity: the Editor serves only the checks without Play Mode of the implementation and the Fast QA (a compile, a data read, the changed chain exercised on the original asset, etc.: the result of each spec item the change touches, in that item's situations, with the events that belong to it and the repeats a measurement needs; a sweep of inputs, sizes, variants, etc. and what only the running game shows go to the user's checklist) and the one Play Mode check the user takes from the report's offer, never the review ([PROFILE-STAGES] in [profiles.md](profiles.md)).
- [MAIN-WAITS] **While sub-agents work, the main thread waits** for their results, in one call ([WAIT-RESULT]), at every stage that has them at work: facts, R&D, implementation, review, QA, etc. Its own work meanwhile is orchestration: the next briefs, the spec and its updates, the direction sheet, the trace, the draft of the report, knowledge notes, etc. It doesn't investigate the chain itself, read code to answer a question it gave an agent, or use the Editor or the bridge while agents work: that is their role's work, done once, by them. The wait is one call with the client's longest timeout ([WAIT-RESULT]), and an update to the user goes out with an event (a report, a question, a blocker, a change of plan): a wake-up that brought nothing writes nothing, since a status line per wake-up repeats itself and fills the context until it is compacted.
  - Example: the fact agents are out → the main thread writes the R&D briefs from the spec and waits; their reports, not its own reading, decide the cause; etc.
  - Anti-examples: while the fact agents work, the main thread reads the same code and inspects the actor's prefab in the Editor, then merges "its" findings with theirs; it waits in short slices and fills each pause with a check of its own.
- [MAIN-QUIET] **The main thread writes to a running sub-agent only when its task changes:** a new version to check, a review finding, the user's answer, a stop, etc. It doesn't steer it step by step; the sub-agent records its own progress ([TRACE-PLAN]).
  - Anti-example: a message to the tester after every scenario, again and again.
- [WAIT-RESULT] **Wait for results; don't watch progress (every role).** Whoever needs a result waits for its completion signal in one call: a sub-agent's return ({{wait-signal}}), the end mark of a round ([PM-WAIT-ONCE]), a ready editor ([PM-COMPILE]), etc. Progress is shown by whoever does the work, in its own trace node; a sub-agent writes to the main thread only with its final report, a question it can't decide or a blocker, since every message wakes the main thread. The expected return: conclusion first, evidence with file:line / log line / commit, confidence (High / Medium / Low), and what it couldn't check. Nobody reads another agent's trace, intermediate files or state to report on it, and the main thread's update to the user names who does the work.
  - Example: the tester runs a QA round → the main thread waits once; the round's report wakes it, and its update reads "the tester is running the round"; etc.
  - Anti-examples: waking every minute to read the tester's trace and stand folder, then telling the user "I'm checking…"; a sleep, a look at the log, another sleep.

[PRESETS] **Agent presets** (this skill explicitly requests these overrides):

| Role | Model | Reasoning |
| --- | --- | --- |
| Tester: Play Mode reproduction (stage 2), manual QA in the game (stage 7), reproducing review findings | inherits the main thread's model; no separate model for the tester | inherits the main thread's reasoning |
| Everything else | inherits the main thread's model | inherits |

- **Overrides need a fresh context.** Spawn agents with a model override using {{fresh}}, so they need a self-contained brief.{{role-fresh}}
- **Model not available** (e.g. another account or client): inherit the main thread's model.
- **Queueing.** The client limits how many sub-agents run at once; {{spawn-overflow}}.
- [AGENT-LIMIT] **Offer to raise the limit.** When a spawn is refused because the limit is reached ("{{limit-error}}", etc.), or a stage needs more agents at once than the limit allows, run the rest as earlier agents finish{{free-slots}}, and add an item to the next menu: raise the limit ×2, from the current value to double it, or keep it (the default). {{agent-limit}} This changes the user's global config, so only on their choice; it applies to sessions started after the change.

[BRIEF] **Brief every sub-agent with:**

- first, its role: spawn it with the {{role-param}} of its row, `{{role-prefix}}unity-dev-<set>` (`tester`; `reviewer`; `branch`; `critic` for a critic or the judge; `audience` for the audience critic; `spec`; `fact`; `scout`; `profile`; `recipe` for a recipe or tool agent; `implementer` for an implementer or plan checker). The role's rule set (its row's files in **Skill files by role** minus the rules only other roles need, `roles.json`) comes as its {{role-rules}}, in its context before its first step, so the brief doesn't ask it to read them. When the type is refused (unknown {{role-param}}: the roles aren't installed), spawn without it and the brief names its rule set `roles/<set>-*.md` from **Skill files by role**, to read in full, one file per call, before anything else; a sub-agent spawned with the main thread's history reads only the ones it doesn't have;
- that its first action saves this brief, word for word, to `.ai-profile/work/<task-id>/agents/<its task name>/brief.md` and appends every later message or task from the main thread to the same file, and that before it returns its final report goes to `report.md` next to it: {{agent-msgs}}, and these files are what the user and a later review can read;
- the documents it builds on, by path: `task.md` ([TASK-DOC]), the spec and the numbers of its items this agent works on ([SPEC-REFS] in [spec.md](spec.md)), the reports it needs, etc.; the brief names them and doesn't restate them ([BRIEF-DOCS]);
- the task's depth profile and what it sets for this agent's stage ([PROFILE-STAGES] in [profiles.md](profiles.md)): a sub-agent reads only its own rules and can't look it up;
- for a scout, a fact agent or anyone given the task's materials (a capture, a log, a snapshot, a screenshot, etc.): each material by name, with the ask to say under what conditions it was taken and what it shows, before anything is built on it ([FIND-SOURCE], [FIND-GIVEN] in [findings.md](findings.md));
- for an R&D branch: its direction as a principle or a rejected assumption, not a mechanism (the YAGNI branch: "the smallest change that makes the spec items pass, from what the project already has"; the challenger: "rejects the first idea's assumption that X"; a flagged-risk branch: "rejects the shared assumption Y"; etc.; the one exception: a merged core the judge sent to the next round, [RND-VERDICT]), the spec items it must close and the standard it is written to ([RND-STANDARD]); the place and the way are the branch's to find, so the sketch's core and parts are its own ([RND-PARTS] in [rnd.md](rnd.md)). Anti-example: "retry the request three times" or "a debounce on the save button" as a direction: a solution already, the branch only dresses it;
- for the judge: a merged core it sees is named for the next round, not left out ([RND-VERDICT] in [rnd.md](rnd.md)); the brief doesn't forbid naming one. Anti-example: "compare only the critiqued cores, no merges" in the judge's brief;
- for every agent of the R&D stage (a branch, a critic, the audience critic, the judge): the direction sheet ([RND-DIRS] in [profiles.md](profiles.md); a branch: its user, link, analogue, usual and kept rows and its own line of the taken row, [RND-ISOLATE]); and no brief settles what the comparison decides (that a stop or a wait is acceptable, that a result need not be kept, that the smaller change is preferred, that the effects tie because none was measured, etc.): a limit comes only from the user's words, the task's documents, a hard rule or the profile's cell as its words stand ([PROFILE-STAGES] in [profiles.md](profiles.md)), each with its source ([RND-BRIEF-SCOPE] in [rnd.md](rnd.md)). Anti-example: "a job that gives up when no worker is free is acceptable" in the judge's brief, so a kept result (every job completes) is traded before the comparison;
- for the tester's reproduction (a bug, Normal): the reported symptoms to reproduce, every part of their wording, and nothing to measure beyond them; the report comes as soon as they are reproduced or refuted. Example: "reproduce: the popup stays open after the second purchase and after a refund (the report's two situations); return when both are seen or refuted"; etc. Anti-example: "reproduce, then the baseline of every item of the spec".
- one question and the decision it informs;
- the artifacts to look at (files, folders, logs, commits, scenes, etc.);
- the trace folder, the id of the node opened for it and its trace file name, and the ids of the problems on the graph it checks ([trace-agent.md](trace-agent.md), [TRACE-SAME]).

[BRIEF-DOCS] **The documents a brief names are the base.** A sub-agent builds on them (`task.md` with the user's words, the spec and its items, the reports, etc.): the brief's own words about them are a guide, not their replacement.

[NO-DELEGATE] **Never delegate:** choosing the fix, declaring the root cause, recommendations, git, and communication with the user.

[ROLE-OWN] **Each role does its own work, and only its own.** Work that comes back unfinished goes back to its role: the same agent or a new one of that role; another role doesn't finish it. A role isn't stopped halfway to save time: the next step waits for its result ([WAIT-RESULT]). The rules that keep one role out of another's work are cases of this one: the reviewer doesn't play scenarios ([REV-DATA]), the tester doesn't fix the product ([QA-NO-FIX]), the main thread doesn't hand away decisions ([NO-DELEGATE]), doesn't build stands or run the game, and doesn't write the product change ([IMPL-TEAM]).
- Example: the tester returns the baseline with two scenarios not reached → its next task is those two, in its own setup; the main thread waits; etc.
- Anti-examples: the main thread stops the tester to start the comparison sooner, then fixes the tester's setup and runs the game itself; a critic rewrites the branch it was asked to break.

[LOOP-STOP] **Notice a loop and step out of it.** Goal: time goes to what brings the result closer, not to brute force. Before your next attempt to make something work (a correction, a rerun, a setup fix, another branch, another question to the same evidence, etc.; a planned repeat or measurement isn't one), look back at the attempts behind it: is the work converging or circling? Signs of a loop: an attempt that differs from an earlier one only by a value; the same check failing the same way; a failure that moves from one place to another and back; a fix of the tool that leaves the result as unknown as before; etc. A loop isn't fixed by one more turn of it: stop, name what the attempts share (the reading of the cause, an assumption, the tool), and change that at its root where it is yours to change; a sub-agent whose root lies outside its brief returns with it ([WAIT-RESULT]); where the change is the user's (another form, another reading of the request or of the product's cause, the scope), the main thread ends the round with the report ([AUTONOMY] in SKILL.md).

- What did the last attempt show that the one before didn't? → nothing new: it's a loop.
- If the next attempt fails, will I know more than now? → no: don't run it; change what the attempts share.
- Am I testing a reading of the cause, or trying values? → values: name the reading the next value tests, or test another reading.
- What do all the attempts have in common? → that is what to change.
- Example: an upload times out; retries raised 3 → 5 → 10, the same error each time → a loop on "it needs more retries": test another reading (the file size, the auth) or report; etc.
- Anti-example: a tuning that converges (each change of a cache size visibly lowers the miss rate) stopped after its second step as "a loop".

[TASK-DOC] **The task in the user's words.** At the start the main thread writes `.ai-profile/work/<task-id>/task.md`: the user's request word for word, with what they attached (texts, links, etc.), and later appends each answer of the user the same way. Every brief points to it. A summary loses details and adds readings, and each agent then takes the summary for the task.
- Example: a bug report with three symptoms and "only after the second purchase" goes into `task.md` as it is; a later "and don't touch the tutorial" is appended; etc.
- Anti-example: briefs that say "fix the purchase popup", so the condition "only after the second purchase" reaches no agent.

[IMPL-TEAM] **Implementation by implementers.** After the choice, the main thread expands the chosen sketch into an implementation spec, `.ai-profile/work/<task-id>/impl-spec.md`:

- the modules, each with its files and assets and the spec items it covers (every spec item is in some module);
- the contracts between modules: the signatures, events and data one module gives another;
- the owner of every file more than one module needs: the others reach it through a contract;
- the order, where a module waits for another;
- how each module is checked, and what is out of scope.

A plan checker (read-only, without the main thread's history) checks it against the chosen variant and the spec: every item covered, contracts that fit, no file split between modules; the main thread fixes what it finds. Then one implementer per independent module works in parallel, without Unity (a compile check outside the Editor where the project allows); a variant that doesn't split is one module with one implementer. A module that doesn't fit the chosen variant comes back to the main thread as a question, not as a different design ([RND-LATER] in [rnd.md](rnd.md), [NO-DELEGATE]). Then one implementer, the integrator, holds Unity, compiles all modules together and settles the contracts. A fix after review or QA goes to the implementer of the module it's in; a fix across modules goes to the integrator ([ROLE-OWN]).

- Example: a shop feature splits into "price calculation", "purchase flow" and "receipt screen", with the contract "the purchase flow calls the price calculation and passes the result to the receipt" → three implementers, then the integration; etc.
- Anti-example: three implementers each edit the same shared handler with no owner, and the integration finds three versions of it.
