# R&D Before Any Fix or Implementation

Models tend to take the shortest path and stick with the first idea. This stage forces real alternatives and a comparison before anything is proposed or written.

## When it runs

- [RND-WHEN] **Always,** when the approach is not already fixed by the user. That covers bug fixes, features, refactors, optimizations, etc.
- **The user fixed the approach** ("do it like X"): don't research alternatives. Check X for blockers and risks, and challenge it only if it is clearly bad (healthy skepticism).
- **There is no alternative at all** (a mechanical rename, a git command, etc.): no R&D.

## Inputs

- The project profile and knowledge base (`.ai-profile/`, see [project-profile.md](project-profile.md)).
- The scout's map.
- The stage-2 facts.
- **How it worked before**, if this is a regression: what changed in history and what the working structure looked like.
- **How the project already solves similar cases** (precedents: the scout's links table, [SCOUT-LINKS] in [scout.md](scout.md)).

These inputs feed the directions; they are not a menu of fixed options.

## Branches

1. [RND-FIRST-IDEA] **Write down the first idea.** Record the first or shortest idea explicitly as one candidate. It may still win, but only through the comparison.
   - [RND-MINIMAL] **A YAGNI branch in the first wave.** One branch aligns to YAGNI: the smallest change that makes every spec item pass, from what the project already has. It competes like any other and can lose (a patch over a symptom, edits spread thin, etc.).
     - Example: a popup stays open after the second purchase → the YAGNI branch "call the existing close in the second purchase's handler" next to "one window manager for all popups"; etc.
     - Anti-example: the first wave holds only general mechanisms, and the smallest working change isn't in the comparison, so it can't be chosen even when it is the best.
2. [RND-DIRECTIONS] **Pick directions from the problem.** Use the first idea, the inputs above, and the assumptions behind the first idea; rejecting one assumption gives another direction. Each direction must solve the problem in a genuinely different way, not just differ in detail. A direction is a principle or a rejected assumption (the smallest change from what exists, "rejects the assumption that the shared rule stays", etc.); the mechanism is the branch's result, not its input: the branches named in this file by their result got a principle in their brief. Don't pad the list with every possible option, and don't stop at a minimum: the critic loop below decides when there are enough. The main thread lists them in the direction sheet before the branches start ([RND-DIRS] in [profiles.md](profiles.md)); a brief names the sheet. What exists comes first ([RND-EXISTING]); the field's usual techniques, or an unusual one, are a source in every profile ([DIR-USUAL]); both in [directions.md](directions.md).
   - [RND-REUSE] **Reusing a system brings all of its behavior.** A branch that connects to an existing system (inventory, events, permissions, notifications, etc.) uses it the way the project's other objects of that kind do, and lists what the system will do beyond the task, each item as a situation in the user's terms. Those items are behavior outside the requested scenario ([SCOPE-TRIGGER] in SKILL.md) and go into the menu with their source ([CHOICE-ITEMS]). Trimming or fencing the system for this object (anything that changes what the system does to this object, unlike its other objects of that kind: rules skipped, replaced or filtered for it, etc.; what the object's own mechanics feed into it, through the entry points the other objects use, isn't fencing) is a separate variant for the user, with its cost.
     - Example: a new pickup is connected to the shared inventory, which also stacks items, shows them in the trade window and saves them → the branch lists "it will also stack, appear in trade and be saved, like other items"; keeping it out of trade is a separate variant; etc.
     - Anti-example: picking the shared notification service because it "fits the project", then making this alert skip the service's digest and mute settings, without a word to the user.
3. [RND-CHALLENGER] **Add a challenger.** At least one branch rejects a key assumption of the first idea.
   - [RND-FLAGGED] **A shared assumption already flagged as a risk is challenged in the same wave.** Whenever branches start, at the beginning or after a critique, look at what they all assume (that a component stays, that a value has one source, that an order of calls holds, etc.). If something already found marks it as a risk (a stage-2 fact, an earlier critique, a measurement, etc.), a branch that rejects it starts together with them. A branch added later comes only from what was found after that wave started.
     - Examples: every first direction keeps a settings cache that a fact report flags as stale after a reload → the first wave also has a branch "no cache"; a save order both revised branches share fails a measurement → the next wave has one without it; etc.
     - Anti-example: the facts flag the shared assumption, the branches build on it, and the branch that drops it starts only after a critic repeats the same risk, so the comparison waits for one more full loop.
4. [RND-ISOLATE] **Isolate the branches.** Each branch is its own read-only sub-agent, spawned with {{fresh}}. It gets the task, the facts, pointers to the profile, and its direction only. It doesn't see the other branches or the main thread's preference. If more branches exist than can run at once, {{rnd-overflow}}.
   - [RND-BRIEF-SCOPE] **A branch's brief doesn't narrow its direction by the main thread's reading of the scope.** A limit in the brief comes only from the user's words, the task's documents, a hard rule or the profile's cell as its words stand, and names its source. The branch develops its direction fully and lists what it changes outside the requested scenario. Whether that is acceptable is decided at the choice ([SCOPE-TRIGGER] in SKILL.md).
     - Example: the task says "the new invoice exports like the other invoices" → the branch "the shared export pipeline" lists what else will happen to the invoice (scheduled mailing, archiving, etc.).
     - Anti-example: the challenger's brief says "the full integration is out of scope, don't add X silently" → both branches bring the same trimmed variant, and there is nothing to choose from.
5. [RND-RETURNS] **Each branch returns:**
   - [RND-SKETCH] a design sketch at the depth the comparison needs: which spec items and paths it covers and how, where the change goes (the files, assets and systems it touches), what it changes outside the scenario. Edits written out line by line wait for implementation: they lengthen the branch and its critique, and the choice doesn't use them.
     - Example: a branch for a save-format change says "a version field and a one-time migration on load; touches the save writer, the loader and the settings asset; old saves migrate once"; etc.
     - Anti-example: the same branch writes out every changed method of all three save paths, so the comparison waits for a document the choice never reads.
   - evidence from the project that supports it;
   - risks and what could regress;
   - why it would break in 3 months;
   - cost to change or remove later;
   - which criteria apply to it, and why the others don't;
   - for each open assumption of the spec it relies on ([SPEC-FORMAT] in [spec.md](spec.md)): how the design changes under the other readings, in a line each;
   - a verification plan: how to prove it works (the reproduction to re-run, acceptance scenarios, regression scenarios, logs or values to check, etc.).
6. [RND-CRITIC] **Pre-mortem by a critic.** Every branch, including ones that look weak or that rejected themselves, goes to a separate read-only critic sub-agent ({{fresh}}) whose only job is to break it. It answers with evidence from the project:
   - "Imagine this shipped, and a month later it caused a problem. What happened?"
   - "What else depends on what this changes, and what happens to it?"
   - "Which scenarios get worse?"
   - "Which earlier fix or decision does it undo?"
   - "What would the team lead or the user reject, and why?"
   - "What gets worse for the product's user around the change: what they see, how it behaves or responds, how it is to use, etc.?"
   - Each finding gets a status and the level that established it ([FIND-STATUS] and [FIND-LEVEL] in [findings.md](findings.md)), and the critic checks its own findings where it can: code and asset files itself; Editor checks as [ONE-UNITY] allows; runs in Play Mode belong to the tester.
   - etc.

   - [RND-EVIDENCE] **Evidence rule.** A claim like "it's safe" without evidence counts as an **unknown risk, not a low one**.
   - [RND-OWN] **Only the branch's own problems count** ([HR-SCOPE], [SCOPE-WHOSE] in SKILL.md).
7. [RND-LOOP] **Search → critique → revise loop.**
   - **Revise first.** The branch answers every shown finding on its core ([RND-RISK-COST]) with one of two: "fixed inside the direction: how, and what it took from where" or "not fixable without leaving the direction: why". A direction is its principle ([RND-DIRECTIONS]), not the rules of the code the branch found where its change goes (a check, a guard, an order of calls, etc.): changing one is inside it. A new direction comes from the second answer or from a shared assumption a critique flagged ([RND-FLAGGED]).
     - Example: the YAGNI branch finds the existing check rejecting legitimate retries → it changes the check to return the earlier result: fixed inside; etc. Anti-example: the critic shows that the validator the branch reuses rejects the new field's format; the branch keeps it as it is and answers "the direction can't carry this".
   - **Critique again.** Only what changed is critiqued again.
   - **The next round** comes from what the critique shows, within the profile's budget ([RND-NEXT] in [profiles.md](profiles.md), in the brief).
   - [RND-STOP] **Stop** at the first round that neither changed the winner nor closed a flaw.
8. [RND-GOOD-ENOUGH] **Good enough, not ideal.** The goal is a solution that:
   - fixes the real cause;
   - has no serious risk of its own left, as shown by evidence;
   - shows its remaining unknowns in the comparison.

   Don't keep searching for a perfect solution.

9. [RND-STANDARD] **Every branch meets the code standard.** [implementation.md](implementation.md) and the project's own rules (`AGENTS.md`, `CLAUDE.md`, docs, `.ai-profile/knowledge.md`, etc.) are the standard every branch is written to: dependencies, lookups, lifecycle, gates, performance-aware coding, style. A branch brings its sketch to the standard before it returns; the critic checks the sketch against it and names each deviation; the judge scores a deviation as a flaw. Where a direction can't meet a point of the standard, the branch says so and why, and competes with that on the table. This is alignment, not the revise loop: it runs in every profile.
   - Example: a sketch builds a minimap's marker list with LINQ every frame → the standard says to avoid LINQ in hot paths, so the branch fills a pre-allocated list instead, before the critic sees it; etc.
   - Anti-example: the critic notes "a LINQ query per frame" as a remark, the judge scores the branch high for its small size, and the query ships.

10. [RND-RISK-COST] **A risk buys a cost in code only when it is shown in the project.** A critic that names a risk against a branch says one of two things about it: **shown** (the file, asset, scene or flow in the project where the case arises) or **not shown**. A risk not shown doesn't change a branch's design when the guard against it costs something in code (an extra lookup, a state, a branch, a pass, etc.): the branch stays the cheaper one, and the risk goes into the comparison and the report with its case. A design rebuilt for a risk not shown is scored as a deviation from the standard ([RND-STANDARD]). A guard that costs nothing (the order of two checks, a name, etc.) is taken for any risk.
   - Example: a critic says "a discount could apply twice if one coupon sat under two carts", finds no such wiring, writes "not shown" → the sketch keeps its single check; etc.
   - Example: a critic says "a message could go out twice if the app resumes mid-send" and names the screen that does so: shown → the branch handles it; etc.
   - Anti-example: a critic calls a parser's single date format "a defect" because a source might one day send another, shows no such source, and the branch adds a format detection every row now pays.

11. [RND-PARTS] **A sketch is a core plus removable parts.** The core is the smallest form of the direction that makes the spec items pass, from what the project already has. Everything beyond it is a named part: what it adds, why the direction needs it, how it stands against the standard ([RND-STANDARD]), that the core works without it, and whether it is **portable** (fits another core unchanged) or **tied**. A part the core can't do without isn't a part: the branch designs the core without it, or puts it into the core and carries its cost into the comparison. A part that fails the standard the branch drops before it returns. Challenge questions: what is left without this part, does it still close the spec items? Does the direction need it, or do I? Would it sit on another core unchanged?
   - Example: "hide the price tooltip until hover" → core: the tooltip's visibility bound to the hover state; parts: a fade (not needed: removable), a cache of formatted strings (fails the project's rule on lazy caches: dropped); etc.
   - Example: "check the balance before a purchase" → core: the check in the purchase call; a part: a purchase log, needed by the refunds item, kept and named; etc.
   - Anti-example: a sketch whose "part" is a retry queue the core can't run without, listed as removable; or a monolithic sketch where the judge can't tell the direction from its extras.

12. [RND-VERDICT] **A flaw hits a part or the core, never the direction as a whole.** The critic ties every finding to the part or the core it sits in: for a part it says keep, drop, or replace with something the project already has; for the core it is a flaw the branch answers in its revision ([RND-LOOP]); only a core flaw still open when the critique ends ([RND-STOP]) rejects the direction. The judge compares directions by their cores, then decides every part of the winner: keep / drop / replace, with the reason (a deviation from the standard or a shown risk; not taste). The winner's form may take a portable part of another branch, with that part's own critic findings. The judge never picks a merged core, a new direction nobody critiqued; where it sees one, it names it as the next round's branch, in every profile, until [RND-STOP], and the choice stays among the critiqued forms. The verdict names one form: the direction with its parts as decided; the implementation spec is written in that form, nothing goes back to a branch.
   - Example: the judge: "the hover direction wins by its core; drop the fade (not needed); keep the log (spec item 3); take the other branch's portable debounce"; etc.
   - Example: two cores, "check the balance in the purchase call" and "reserve the amount at cart time" → a merged core (reserve, then check at purchase): the next round's branch, in Fast too; etc.
   - Anti-example: a direction that only needs a flag is rejected because its sketch also added a background sync the standard forbids; or a judge who scores sketches as wholes and lets the extras decide.

13. [RND-ASSUMED] **An assumption in the spec doesn't rank branches; what keeps working isn't one.** A spec item whose status is an assumption (the main thread's reading, not the user's words or a fact) is not a criterion by itself. What the touched chain delivers now and the design fixes ([RND-BEHAVIOR]), outside what the request changes, is the baseline of any change (not a coupling the change replaces, nor what the words ask for: [SPEC-KEEP] in [spec.md](spec.md)): a branch whose design stops it in the requested scenario (a cart no longer keeps its items, a list no longer sorts, a job no longer retries, etc.) falls short on effect ([RND-EFFECT]); a stop only under conditions not shown is a risk ([RND-DECIDING]); outside that scenario it is the user's choice ([SCOPE-TRIGGER]); kept by degree, not stopped, for the goal (some accuracy for speed, etc.), it is a trade-off the comparison names. An assumption guesses beyond that: at a want the request doesn't state, or at how a wanted result is reached; it neither ranks nor narrows the branches. Where branches differ on an assumed item, the judge either shows which behavior is right, by code, documents or facts, and the item stops being an assumption, or hands it to the user as a question with the options and what each changes ([CHOICE-ITEMS]), and the comparison scores the branches without that item. When nobody will answer, the assumption stands, and the verdict and the report say the choice rests on it.
   - Example: "a retry charges twice" → kept: a retry after a real timeout still completes the payment; assumed: "accepted means the pay button locks after the first tap", a guess at how: a branch that makes the repeat harmless where it lands closes the item too; etc.
   - Example: the spec assumes "the new column is exported too"; branches differ → the export's design doc lists every visible column: scored by that; no source: ask, and compare the rest; etc.
   - Anti-example: the judge marks a branch down "pending agreement" on an assumed item, the rest ties, and "the smaller change wins" decides for the user.

14. [RND-EFFECT] **A branch is measured first against what the request came for.** Every branch states its expected effect on what the user's request came for, in their words (a bug's symptom, a feature's spec items, the number a performance pass must move, etc.), twice: for the product's user, where the task has one, as what they will see, do and feel in the spec's situations, now → after, for what the request came for and at the scope it names (one screen, one wait, one action, etc.), predicted from the design and the facts; and in the task's own measure (time, memory, clicks, error rate, the spec items that pass, etc.), as an estimate from the materials and by counting ([FIND-GIVEN]); each with what it rests on: a prediction, not "not checked". A branch whose effect falls short of what the task asks for in one of the two isn't a candidate, however small and safe. An assumed item or reading ([RND-ASSUMED]), or a hedge in the user's words ("ideally", etc.), doesn't take a branch out. The comparison ranks the candidates by effect first, then by risk and size; "the smaller change wins" ([RND-DECIDING]) applies only among branches that close it.
   - Example: a checkout page takes 4 s → a branch that saves 50 ms says so, is left out, and the comparison says the wait stays; etc.
   - Example: "export to CSV and PDF" → a CSV-only branch covers item 1 of 2: not a candidate; etc.
   - Example: a double charge fixed on one of three paths → not a candidate until the others are covered or the task is split; etc.
   - Example: a list that sorts right but jumps back to the top on every open; a new window that works but snaps in with a stall and puts its close button out of reach; a reload that works but drops the player's input for a moment → in the measure ✅, for the user ⚠️ with that named ([RND-BAR] in [verdict.md](verdict.md)): a candidate, below one that keeps the experience; etc.
   - Example: "the search API takes 2 s" → the server answers in 0.2 s while the results still appear a second after the keystroke → in the measure ✅, for the user ❌: not a candidate; etc.
   - Anti-example: a branch that removes a few percent of the symptom's cost wins "for safety", and the report says the symptom is addressed.

15. [RND-BEHAVIOR] **Behavior is what the product shows; how the code gets there is implementation.** Goal: what matters to the product's user stays as it is; what is under the hood is free to change. Behavior: a result, a state, an order or a moment that someone outside the code observes (a user, another system, a file, etc.) and that the design fixes (a document, a setting, a test, a contract, an explicit expectation in code, etc.). The order of computation, the moment a value is read, when a cache refreshes, which structure holds the data, etc. are implementation: a difference there isn't a behavior change until a critic shows ([RND-RISK-COST]) where it reaches an observable result. A shown difference inside the requested scenario is compared on effect and risk ([RND-EFFECT]); outside it, it is the trigger of [SCOPE-TRIGGER]. Challenge questions: who outside the code sees the difference, and where? What fixes the former result (a document, a test, a contract, etc.)? If nothing: behavior, or a risk to show?
   - Example: a save file with another field order → implementation where the format's reader accepts any order, behavior where its spec fixes it; etc.
   - Example: notifications batched so some arrive a minute later → behavior (a moment the user sees); a path buffer that changes how NPCs queue at a door → behavior outside the scenario; etc.
   - Anti-example: "sums the cart on read, not on each add" called a behavior change, and the branch with a far larger effect loses uncompared.

## Experiments

[RND-EXPERIMENT] R&D is read-only by default. If a question can only be settled by trying it in the engine (e.g. whether a setup behaves at runtime the way the code or docs suggest), ask the user via a menu (see user-output.md) before creating anything. Say what will be created and where. Experiments go into a scratch scene or folder and are never committed; they stay in the project, and the user removes them. Never use a worktree.

## Criteria, comparison and choice

The criteria every branch is written to and the critics break it against, the bar the judge scores every core by, and how the comparison ends are in [verdict.md](verdict.md): [RND-CRITERIA], [RND-BAR], [RND-AUDIENCE], [RND-JUDGE], [RND-PROS], [RND-DECIDING], [RND-CHOICE].

## Present, then stop (hard gate)

- [RND-SHOW-ALL] **Always show every branch** in the comparison table, including the rejected ones with the flaw that sank them. A single recommendation without the comparison is not allowed. This also holds when the user said to pick and do it: the final report still shows what was compared and why the winner won. Its rows are the bar's ([RND-BAR] in [verdict.md](verdict.md)), in the user's words, ✅ ⚠️ ❌ per row. Where it fits, label the candidates by scope as **Minimal / Optimal / Architectural**, and mark the recommended one ([CHOICE-ITEMS] in SKILL.md).
- [RND-ACCEPTANCE] **Show the acceptance scenarios** with the options. The user's choice confirms them ([PIPE-CHOICE] in SKILL.md).
- [RND-MENU] **Offer the choice through a menu of forms, not of raw branches.** Goal: the user chooses among the best forms R&D found, not its raw material. The options are the forms the verdict built ([RND-VERDICT]): the winner's core with the parts it took from other branches, a merged core once its round critiqued it, the alternatives compared. The menu shows the base forms still in the running and the combined ones where R&D built any. Each form: the spec items it closes, its effect in the task's measure and, where there is one, for the product's user, the limitations and risks its critique showed (a limitation: what the form itself doesn't do, or does worse, as the critique predicts; a risk: what else the change may affect, which reading can't predict), its verification plan, and its tags (user-output.md). A limitation is closed in the form before implementation or named as a known one, as is rational for the case (what closing costs against how often and how badly the user meets it); the choice is made knowing them. "A or B" stays only where the cores are incompatible and nothing is portable. Challenge questions: what did a losing branch have, checked by its critic, that fits the winner's core? Which form closes the goal whole?
  - Examples: prices cached → base forms «cache for a minute» and «invalidate on change», and the combined «invalidate, a minute as a fallback», each with its limitations; the combined one's «a price edited outside the shop stays old for a minute» is closed before implementation by listening to that edit too, a few lines; «a lost event leaves a minute of staleness» is named as known; etc.
  - Anti-examples: the chosen form's limitation only in a critic's report, so the user first learns of it from a failed QA; every limitation closed whatever it costs, a week of work for a case nobody meets.
  - Example: not "1) a cache 2) pagination" but "1) pagination with the first branch's cache invalidation (closes the response time) 2) the cache alone (smaller; the symptom stays on a cold start)"; etc.
  - Anti-example: the judge built a form, and the menu still says "A or B", so the portable part is lost.
- [RND-GATE] **Stop.** Implementation starts only after the user chooses. Its exception and its limit: [PIPE-CHOICE] in SKILL.md.
- [RND-LATER] **Complexity found later** (mid-implementation) that the chosen variant can't absorb ends the round with the report ([AUTONOMY] in SKILL.md); R&D for the affected part is one of its options. It never skips ahead.
- [RND-POSTMORTEM] **Post-mortem after implementation.** Review and QA compare what the pre-mortem predicted with what actually happened: review against the diff, QA through the risks ([QA-SCEN] in [qa.md](qa.md)). Anything that went wrong and wasn't predicted goes into the round's report, with R&D for the affected part as an option ([AUTONOMY] in SKILL.md).
