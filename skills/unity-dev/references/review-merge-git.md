# Code Review, Merges, Git

## Code review

- **Scope.** Review what was asked: a branch against its base, specific commits, or the current uncommitted changes. Focus on issues introduced by that change. Mention a pre-existing problem only if it matters for the change, in one line.
- **Worth reporting.** An issue is worth reporting when it meaningfully affects correctness, performance, security or maintainability; when it is discrete and actionable; and when the author would likely fix it once aware. Prefer no findings over speculative ones.
- **Each finding:** priority (P1/P2/P3), file:line, and the concrete scenario in plain gameplay words. Mark it **real in gameplay** (under which conditions) or **theoretical**.
- **Every mode the code runs in.** Think through it: disabled AI, pooled or re-enabled objects, different scenes or platforms, interrupted animations or actions, etc.
- **Project standards.** Check compliance with the project's own rules (`AGENTS.md`, `CLAUDE.md`, docs, etc.).
- **Shared things and the report format:** follow [review.md](review.md) (each user of a shared thing before → after; statuses; open items as scenarios; the map of the change).
- **Review doesn't fix.** It may run checks (Editor scripts, etc.; see [findings.md](findings.md)), but doesn't edit the project's code or assets. After "fix", fix only the confirmed findings.
- **Sub-agent:** each review dimension (correctness and regressions, performance, project standards, etc.) is its own stage-2 item. Each finding gets a status ([FIND-STATUS] in [findings.md](findings.md)) and, where [REV-VERIFY] in [review.md](review.md) says so, a verifier that tries to refute it. Open findings that only the game can decide go to the tester. Report only what survives.

## Merge conflicts

- **"Identify the merge strategy"** means a short read-only overview. For each conflicted file: what each side changed and the plan (ours / theirs / semantic union) with a reason. Resolve after the user says so.
- **Semantic union.** When both sides changed behavior independently, the aim is usually to keep both sides' invariants (e.g. each feature's own setup, cleanup and restoration). Decide per conflict. When intent is unclear, check the related commits or past discussions, or ask.
- **Sub-agent:** each conflicted file's intent (commits, discussions) is its own stage-2 item. The resolution itself stays in the main thread.
- **Generated files.** Regenerate them (e.g. Unity project files) rather than hand-merging.
- **No conflict markers doesn't mean a finished merge.** Report the real state: staged, builds, Play Mode verified or not.
- **Regression safety.** When the user names a category ("all X"), cover every member of it, not only the first one found.

## Git

- **Branches.** Switch the current branch; no worktree unless the user asks (hard rule). If git is slow, say so instead of silently changing approach. Follow the project's branch naming; create from the base branch when asked.
- **Before committing:** review `git status` and the staged diff. Stage only this task's files and keep unrelated changes intact.
- **Amend and push** only when asked. After a push, report the branch and the commit.
- **Changes in an unexpected branch.** Explain exactly where each change lives before doing anything else.
- **Diagnosis is read-only.** Don't revert, cherry-pick or rewrite history as part of it.
