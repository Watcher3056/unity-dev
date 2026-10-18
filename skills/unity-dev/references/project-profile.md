# Project Profile and Knowledge Base (`.ai-profile/`)

A private, evidence-backed picture of the project and of the developer running the task. It gives hints toward fitting directions; it is not a set of rules.

## Location and privacy

- **Where:** a folder `.ai-profile/` at the project root. It must never be committed.
- **Before writing,** check with `git check-ignore .ai-profile/` that it is ignored. If it isn't, ask the user via a menu before adding `.ai-profile/` to their global gitignore (`git config --global core.excludesFile`). Never commit it, and never add it to the project's own `.gitignore` without asking.
- **Developer profile:** only for the current git user (`git config user.email`). Never profile other people.

## Files

| File | Contents |
| --- | --- |
| `project.md` | Stack (engine version, render pipeline, DI, asset systems, packages, etc.); architecture and patterns with where each is used and file examples (e.g. "dependencies injected via X and serialized fields; factories for A, B"); naming and code style; testing approach; areas that keep appearing in fix commits; links to the project's own rules; the product and its audience: what it is (genre, platform, etc.), who uses it and what they expect, worked out from the project and its context (its documents, the product's own content and controls, a store page, etc.) |
| `developer.md` | Areas the current developer works in, typical patterns and commit style, with samples |
| `knowledge.md` | Facts learned during tasks: decisions the user made, fragile spots found, conventions confirmed or refuted, gotchas, etc. |

- **Evidence:** every claim carries file:line or a commit, plus a confidence level.
- **Build commit:** each file records the commit it was built or last updated from.

## Priority

The project's own rules (`AGENTS.md`, `CLAUDE.md`, docs) come first, then `project.md`, then `knowledge.md`, then `developer.md`, then model defaults. A personal habit never overrides project standards or hard rules.

## Init and refresh (stage 0 of the pipeline)

- **No profile yet:** build it with sub-agents, one per section: stack, architecture and patterns, conventions, testing, history, developer, product and audience.
- **Profile exists:** list the files changed since its recorded commit (`git diff --name-only <commit>..HEAD`). Refresh only the claims whose evidence files are in that list, then update the recorded commit. A section from the list above that the profile doesn't have yet is built as for a new profile. Only where the project and the context don't tell who the product's users are does the section say so; the main thread then puts the question among the spec's questions ([SPEC-ASK] in [spec.md](spec.md)) of the first task that needs it, as one nothing waits on: it neither ends the turn nor holds R&D: until the answer, the audience critic works with the user the spec describes, marked as assumed. The answer goes into this section.

## Growing the knowledge base (last stage of the pipeline)

After each task, append what was learned and verified to `knowledge.md`: date, task, evidence, commit.

- **Do record:**
  - the user's decisions and corrections;
  - fragile spots;
  - confirmed root causes;
  - conventions that turned out different from the profile;
  - etc.
- **Don't record:**
  - unverified guesses;
  - secrets;
  - personal data beyond the developer profile;
  - chat content that doesn't describe the project.
- **When evidence changes,** mark the entry as stale instead of silently keeping it.
