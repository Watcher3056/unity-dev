# Findings: status and verification

Part of the unity-dev skill, read by the main thread, the tester, the reviewer, R&D branches, critics, the audience critic, the judge, fact agents, verifiers and the scout (SKILL.md, **Skill files by role**).


Every finding from review, R&D critics or QA gets a status and the level that established it.

[FIND-STATUS] **Status** — how sure we are that it happens in the game:

- **Theoretical:** the defect exists in the code or assets, but needs conditions so specific that it may never occur in the real game loop.
- **Real:** review and analysis of how it arises in the game loop show it is likely to occur. This status doesn't need a Play Mode run.
- **Confirmed:** established for certain, at a level where the claim can be seen ([FIND-LEVEL]); the report says how (by reading, in the Editor, in Play Mode). A claim about behavior in the running game (timing, stalls, physics, animation, etc.) checked only by reading is Real at most.

[FIND-LEVELS] **Verification levels:**

1. **Reading:** code, text-serialized assets, configs, git history, etc.
2. **Editor inspection, without Play Mode:** a short editor script in batch mode reads what text can't show: data inside binary assets (models, textures, audio, etc.), import settings, resolved prefab values, etc. The script stays in the project like any test setup.
3. **Targeted Play Mode run:** the smallest setup by [play-mode.md](play-mode.md) that answers this one question, instead of the full scenario list.
4. **Full QA:** the stage-7 scenarios.

[FIND-LEVEL] **Pick the level per step, by where that step can be seen.** Lay out the chain from evidence to conclusion. Each step is either seen (in code, an asset, a log, the running game, etc.) or assumed. When the conclusion rests on an assumed step that could change the decision, check that step at the level where it can be seen. For such steps ask:

- **Is it decided?** Could a careful reviewer with the same material reach a different answer? If not, stop here; no higher level is needed.
- **Where to look next?** What observation would change my mind, and at which level can I make it?

Examples and anti-examples:

- Examples:
  - the code sets a flag after a fixed wait and nothing else writes it → seen by reading, no run needed;
  - the conclusion needs "this imported file doesn't contain that data", and text can't show it → Editor inspection;
  - the conclusion needs "these two systems act in this order", and the order depends on scene setup or emerges at runtime → targeted Play Mode;
  - the change is done and needs acceptance → full QA;
  - which asset or object a serialized field points to (in a scene, a prefab, a ScriptableObject, etc.) → its `guid` and `fileID` in the text asset and the target's `.meta`, seen by reading; the Editor only for what the text doesn't settle: the value after nested prefabs and variants resolve, a sub-asset inside a model or another binary asset, a script inside a compiled library, etc.;
  - etc.
- Anti-examples, level too low:
  - "probably", "should", "likely" inside a conclusion that changes the fix, i.e. an assumed step presented as seen;
  - a change to a shared asset called safe after reading only the change, assuming nothing else depends on it;
  - guessing a binary file's contents from its name or from the code that loads it;
  - etc.
- Anti-examples, level too high:
  - a Play Mode run for a step already seen in the code;
  - a full QA round for one assumed step a targeted run settles;
  - "may affect X, check in Play Mode" when X can be read in the Editor;
  - the Editor taken to see which asset a field references when the text asset shows its `guid`: the Editor has one holder at a time, and whoever needs it next waits;
  - etc.

[CAUSE-PARTS] **A culprit made of parts: find which part.** Whoever runs the check (the main thread, the tester, the reviewer, a critic), when the culprit is made of parts, check each part separately before the fix is chosen. Removing or disabling the whole culprit shows that it is involved, not which of its parts is at fault, and different parts need different fixes.

- Examples: requests fail through a proxy and work without it → check its parts one by one (the header it adds, its timeout, its URL rewrite, etc.) before changing it; a slow screen gets fast with one widget hidden → check that widget's data binding, its layout pass and its image loading separately; etc.
- Anti-examples: turning the whole component off, seeing the symptom go away, and rewriting the part that looked likely; copying how an older version did it, without checking which of today's parts differs.

[FIND-SOURCE] **Every piece of evidence carries where it came from, and that decides what it can show.** The task's materials and what the agents gather (a log, a state snapshot, a performance capture, a screenshot, a video, a measurement file, a config, a QA comment, the user's or a designer's words, a test's output, etc.) come with a provenance: the build and branch, the scene and setup, the mode it was taken in (instrumented or not, a debug or a release build, a development tool or the shipped product, etc.), the moment relative to the event, who recorded it and with what, the sample (one moment, one run, one user), etc. The provenance is read first, from the material itself where it shows it. Then every value (a number, a count, a state, a claim) is used: as it is where the provenance doesn't touch it; with a correction and a range, in the direction the provenance pushes it, where it does; never dropped for being distorted. When the choice between variants rests on a value inside its range, that value is the first item of the user's measurement list, and the estimate stays a range, not "unknown". The provenance is named next to the value wherever it is used: the spec, the comparison, the report. Challenge questions: what in this value comes from how it was taken, and what from the product itself? Which comparison does that distort, and which does it leave alone? What would the value be in the shipped product (no instrumentation, a release build), and does the conclusion survive that range?
- Example: a debug trace that logs every query → the count of queries and of the rows each returns are used as they are; its milliseconds are marked inflated, more for fast queries than for slow ones, and given as a range; the comparison still says "one query instead of one per row in any build"; etc.
- Example: a state snapshot saved a second after the event → it shows what remained; what was there at the moment is a claim, Real at most, and the report says so; etc.
- Example: captures from another branch or an older build → every fact they suggest is checked against the current HEAD before it is used; etc.
- Anti-example: "the recording mode is unknown", so no estimate is given and the variants tie; or inflated milliseconds taken as the real cost and the target built on them.

[FIND-GIVEN] **What the materials show is known, and what can be computed from it is computed.** The numbers and states in the task's materials (counts, sizes, rates, field values, log lines, timestamps, etc.) are data for estimates and comparisons, marked as read, not measured. What can be derived from them by counting is derived, as an estimate with its assumptions: how often a step runs per unit of time (per second, per update, per call, etc.) × how many items one run touches × what one item costs (a cheap check, a memory read, an allocation, a disk or network call, etc.). "Unknown" is said only of what no material shows and no count bounds. Challenge question: before writing "unknown", what do the materials show for at least one moment, one event, one case, and what does counting give from it?
- Example: a log shows one sync per minute and a batch of at most 500 changes → a variant that sends only the changes sends at most 500 of the account's tens of thousands: an estimate by reading, one to two orders of magnitude; etc.
- Example: a variant drops one extra disk read per report from a job that writes a few reports a day → a handful of reads a day, each a few milliseconds: a saving far below the job's own run time; the comparison says so instead of "effect unknown"; etc.
- Example: a log shows three purchase attempts within a second → the estimate of the rate for this case comes from the log, not "the rate is unknown"; etc.
- Anti-example: a judge writes "the number of syncs per minute is unknown" when the log shows it, and decides by "the smaller change wins".

[FIND-VERIFY] Verify what can change the decision: a finding that could block or change the fix is pushed to Confirmed by checking its assumed steps this way. Others are listed with their status and the check that would decide them; a Theoretical finding is listed, not dropped.

## Challenge questions


Use the ones that matter for the task. The list is not exhaustive.

**Understand the problem**

- What is the real goal behind the request, and what would "achieved" look like in the game?
- What is the actual cause or invariant, and what evidence do I have for it?
- Which cases, modes and states does this touch (disabled AI, pooled objects, other scenes, platforms, multiplayer, etc.)?

**Look at the project** (answered by the scout, stage 1)

- How does the project already solve similar cases? Did I check those implementations, and why they were built that way?
- Does existing code, a system or a pipeline already cover part of this?
- Does it follow the project's code style, architecture and standards (`AGENTS.md`, docs, established patterns, etc.)?
- Was this area changed or fixed before, according to git history? Why?

**Compare options**

- What are the realistic alternatives, including doing less?
- What if the requirements change for one part, a new state is added, or the feature is reused elsewhere?
- If this breaks in 3 months, why, and which option makes that less likely?
- What does each option cost to change, debug or remove later?
- Which option would a careful reviewer question, and what would I answer?
- If I'm unsure, what small experiment or prototype would settle it instead of a guess?

**Impact and safety** (after a change, answered by the reviewer, stage 6)

- Does behavior stay identical outside the case being changed?
- Who else calls or depends on this, and what happens to them?
- Can it bring back an old regression or create a new one?
- Does it add per-frame cost or allocations, or scale badly with the number of entities?
- Will a designer need to tune it, and can they?

**Verification and honesty** (after a change, the tester's QA in stage 7 answers the first two)

- How will I prove it works in the real game, not just that it compiles?
- Did I re-run the original reproduction?
- What remains unverified, and did I say so?
- Etc.
