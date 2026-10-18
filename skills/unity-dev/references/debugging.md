# Debugging Unity Issues

The goal is a proven cause and a verified fix, not a plausible story. Diagnose before editing unless the user already chose a fix (see action mode in SKILL.md).

## 1. Bug reproduction strategy

1. **Validate the original bug using existing data:**
   - existing logs: user-provided logs and the Editor/Player log (use the newest session and confirm its timestamp);
   - code, configs, scenes, prefabs, ScriptableObjects, Animator controllers, etc.;
   - git history: compare against the last known good version (`log`, `diff`, `blame`). Who changed it, when, why, and was it a fix for something else? If the user says "it used to work", find when it stopped. A recent change is a hypothesis, not proof.
2. **If the data is not enough, offer the user two options:**
   - add extensive temporary logging and let the user reproduce manually;
   - if the user can't or doesn't want to reproduce, go to the advanced strategy (section 2).
3. **If you found evidence or a root cause by review,** verify it beyond reading code: use synthetic simulation where possible.
4. **If validation gives no strong evidence,** go to the advanced strategy.

**Sub-agent:** the stage-1 scout covers code, assets and project history. When there are logs to analyze or a last known good version to compare against, each is its own stage-2 item (see SKILL.md, Pipeline).

**Temporary logging** follows [play-mode.md](play-mode.md) → "Observe through logs", the same for your own runs and for QA. When the user reproduces manually, also tell them exactly what to do in the run.

## 2. Advanced strategy: the full chain

Identify the full end-to-end chain and every part of the code or project related to the problem. The visible symptom is rarely where the bug lives. Examples of why a narrow check is not enough (examples, not routes to follow):

- The user says a window doesn't open on a button click. Checking only the button or the window code may not be enough.
- A level trigger didn't launch a cutscene. The blocker can be anything.
- The issue may be server-related. Simulate real client/server requests and use them as mocks, but don't bypass the normal decision-making chain: the request and its data should go through the code end-to-end as usual.

Include in scope the whole chain: the related game logic, controllers, managers, etc. that may affect the issue or are needed for the case to work at all. For example, an AI-related issue needs the AI's full decision-making, its managers, etc. Avoid mocks where real functionality and data exist. Keep the case as close to real as possible.

**Sub-agent:** each subsystem the chain passes through is its own stage-2 item. Assemble the full chain yourself.

## 3. Reproduce it yourself

Reproduce it in Play Mode by the rules in [play-mode.md](play-mode.md): where to run it, what you may build, and what must stay original. They are shared with QA (stage 7), so the setup you build here is the one the tester reuses to verify the fix.

Debugging specifics:

- **Reproduce before any fix.** A reproduction that never showed the bug can't prove the fix. In the pipeline, the tester does it in stage 2 ([WHO-RUNS] in agents.md).
- **Isolating the problematic part** can mean copying the level, or cutting the problematic room or part into a separate playable scene, with temporary cheats or debug code that launch the needed sequence.
- **If the bug appears in one environment but not another,** compare the two environments first.

## 4. Bound and classify

- **Bound it:** deterministic, intermittent, machine-, scene-, editor- or build-only, platform-specific, etc. Find the smallest known repro and the nearest working path.
- **Classify it** to choose the checks: compile/import, editor configuration or prefab, play-mode runtime exception, build-only or platform, scene loading or lifecycle ordering, input / physics / UI / animation / audio / networking / save-load / Addressables / asset pipeline, performance, etc. Bug-class checklists: [unity-checklists.md](unity-checklists.md).
- **Correlate events by identity** when reading logs and data ([play-mode.md](play-mode.md) → "Observe through logs").

## 5. Hypotheses

Prefer a few strong hypotheses over a long speculative list:

| Hypothesis | Why plausible | Validation check | Result | Confidence |
| --- | --- | --- | --- | --- |

- **High:** direct evidence identifies the cause, and the repro or logs match the failure path.
- **Medium:** strong support, but one validation step or artifact is missing.
- **Low:** plausible from code or context only.

For each hypothesis, run the cheapest decisive check. Mark one "unresolved" only after naming the specific missing artifact or blocked check, and never present it as the root cause. When the code doesn't expose enough runtime evidence, name the exact logging points that would make the next run decisive.

**Sub-agent:** each independent hypothesis is its own stage-2 item. The sub-agent gets one hypothesis, its validation check and the artifacts to look at, and returns validated / rejected / unresolved with evidence. The verdict on the root cause stays with you.

## 6. Output for the user

Follow user-output.md:

- **Lead with what breaks and why, in gameplay words,** at a high level. The user isn't necessarily deep in the technical details.
- **Show it:** a causal-chain diagram, the decisive evidence (log excerpt, values per frame or step, screenshot, etc.).
- **Then, as relevant:** repro status, recent changes reviewed, hypotheses checked, missing information, logging gaps for the next run.

Fix candidates come from the R&D stage ([rnd.md](rnd.md)). Present them with these scope labels where they fit:

| Variant | Meaning |
| --- | --- |
| **Minimal** | Smallest regression surface; removes the validated cause without changing architecture |
| **Optimal** | Fixes the cause properly within the existing systems and nearby flow |
| **Architectural** | Prevents the whole class of issue: ownership, lifecycle contracts, validation, tests, etc. |

- **Check each variant before recommending:** for every one, check the outcome and consequences: what changes for the player, scope, regression risk, verification, and when to choose it.
- **Mark one as recommended** and say why.
- **Drop a variant that wouldn't really differ;** list several when a category has more than one viable option.

## 7. Bug fixing

1. When the user selects a fix, apply it.
2. Verify that it actually solved the issue: your previous reproductions no longer reproduce it. The tester sub-agent runs them as manual QA ([qa.md](qa.md)).
3. If it's not solved, the round ends with the report and the options (SKILL.md, [AUTONOMY]); a correction within the chosen fix is the round's work.
4. Check whether the fix can be minimized or improved:
   - Is there code to reuse?
   - Does it reuse or follow existing systems and pipelines, or build its own for no reason?
   - Can it bring back an old regression, e.g. fixing bug B that was created when someone fixed bug A in the past?
   - Does it follow the project's code and architecture standards?
   - Does it change third-party dependency code or resources? That is normally avoided: an update can overwrite the change or conflict with it.

## 8. After fixing

- Review the changes for regressions.
- For each issue found, verify whether it's real in gameplay (and under which conditions) or theoretical.
- **Sub-agent:** this is stage 6, before QA. The regression review is done by a reviewer sub-agent that didn't write the change. Findings get a status and are checked by [FIND-LEVEL] in [findings.md](findings.md); open ones go to QA as scenarios. Verifiers: [REV-VERIFY].
- Remove temporary diagnostics before any commit, unless the user wants specific lines kept and they don't cost performance.
- Give the user a short overview of the work done and the verification level.
