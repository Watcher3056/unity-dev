# The spec (hard rule)

Part of the unity-dev skill, read by the main thread and the spec critic (SKILL.md, **Skill files by role**).

A task usually comes as a few lines, and the user may not see the project's side of it. Every agent that works from a retelling works from the reteller's reading: one changed word ("retry 3 times" read as "3 attempts in all", "ideally" read as "must", "notifies the user" read as "emails the user") reaches every agent and then the fix. The spec spells out what is wanted once, checked against the user's words, and every agent works from its items.

## [SPEC-FORMAT] What's in it

`.ai-profile/work/<task-id>/spec.md` is a design document of the change. `task.md` stays its base ([TASK-DOC] in [agents.md](agents.md)): the spec expands the user's words, it doesn't replace them.

- **Goal:** what changes for the player or the user, in one paragraph.
- **Situations:** numbered items. Each has:
  - the source's words, verbatim, with the user's own degree of certainty ("ideally", "if possible", "maybe", etc.): a hedge stays a hedge, not a hard check;
  - the expected behavior as "now → after", in a situation the user knows, as what is seen there (a state, a value, an event, etc.), not an intention ("no longer tries to", etc.);
  - every situation the words cover, not only the first that comes to mind, and the ways into the touched link that the scout's links table shows ([SCOUT-LINKS] in [scout.md](scout.md)): a result that holds on the first entry and fails on another is a situation of the item, not a surprise of QA;
  - how it's checked: these checks are the acceptance scenarios that R&D, the choice and QA refer to;
  - its status: confirmed by the user, kept ([SPEC-KEEP]), an assumption, or found during work.
  - Example: "the page loads too slowly" → the item covers the first visit, a return visit, a slow network and a signed-in user, each with its check; etc.
  - Anti-example: the item says "slow on the first visit" where the user's words say "loads too slowly", so the other situations reach no agent.
- [SPEC-KEEP] **Kept: what the touched chain delivers now, outside what the request changes, is an item in every profile.** A result of the chain, in the situations the change goes through, that someone outside the code observes (a user, another system, a file, etc.) and the design fixes (a document, a setting, a test, a contract, an explicit expectation in code, etc.), and that the request doesn't ask to change: "now → after: the same", with its check. Its "now" comes from the scout's map and the facts; one found later goes in as "found during work — kept" ([SPEC-LIVE]). It is the baseline of any change ([PM-BEFORE-AFTER]: «PASS means the behavior stayed the same, or changed exactly as intended»), not an assumption ([RND-ASSUMED]). In a merge, each side's intended result is kept, from its own branch; where the two can't hold together, it is a question ([SPEC-ASK]). Not kept:
  - how the chain gets there: the order or moment a value is read, when a cache refreshes, the exact route a request takes, a file's byte layout, etc., where no design fixes it ([RND-BEHAVIOR] in [rnd.md](rnd.md));
  - a coupling the request's change replaces between the system it changes and its neighbours (a shared cache key, a common rate limit, an event both subscribe to, etc.): the neighbours' own results are kept, that coupling is not;
  - what the request's words ask for in a situation they cover, and a reading they leave open there, even where the profile's spec leaves the situation unnamed: a term's reading, a question or an assumption ([SPEC-TERMS], [SPEC-ASK]); a result the words don't speak to in that situation stays kept (each booking still gets its reminder while the duplicate stops, etc.);
  - an assumption: a guess at a want the request doesn't state, or at how a wanted result is reached.
  - Example: "reminders go out twice after a reschedule" → kept: each booking still gets its reminder, at its time; not kept: the order the job scans the bookings; assumed: "fixed means the scheduler drops the second job", a guess at how; etc.
  - Anti-example (too narrow): the spec names only the symptom, so a branch that stops the reminders breaks no item and wins as the smaller change; or "each booking still gets its reminder" marked as the main thread's reading, so it ranks nothing.
  - Anti-example (too wide): "the save file stays byte-identical" kept for a refactor whose format's reader accepts any layout; "items stay where the user put them" kept for "sort the inventory"; "the discount still lowers the shipping fee" kept when the request replaces the discount rules that tie them.
- [SPEC-TERMS] **Terms:** every number, level, order word ("first", "second", etc.), quantity, comparison, hedge ("ideally", "roughly", "at once", etc.) and named concept of the product (a game term, a business term, etc.) in the user's words and the task's documents gets a row, without a first sort into "clear" and "ambiguous": the author already holding one mechanism in mind can't see another reading. Words about how to work rather than what the result must be get no row: the verbs and depth words [ACTION-MODE] in SKILL.md decides ("investigate", "fix", "pick and do it yourself", "quickly", "thoroughly", etc.), and the spec takes its decision as given. The same word about the result keeps its row ("the page must load quickly", "a fix of one line", etc.). Each row has the term verbatim; its readings; what the project says about each, from a search of the project for the term (names of assets, prefabs and items, enums and constants, settings, localization strings, documents, etc., with the hits); the chosen reading and why. "One reading" needs its reason. A reading the project's own names support is always listed. A number or an order word always has at least two readings in its row, of different kinds (a level vs a count, an ordinal being a count too; a duration vs a number of steps; a position from 0 vs from 1; one unit vs another; etc.). Each reading carries what the project says about it: a row without two readings of different kinds is a finding for the critic. Still open: a question about what ([SPEC-WHAT]) or an assumption about how, as [SPEC-ASK] sets.
  - Example: "page 2" in the request; the API counts pages from 0 and the screen shows "Page 1" for the first → readings: "the second page" (the screen), "index 2, the third page" (the API); chosen: the second page, the request quotes the screen; etc.
  - Anti-example: "keep 30 days" retold as "keep 30 files" because the job writes one file a day, with no search for what the retention setting counts.
  - Anti-example: "find why the export drops rows and fix it" gets a row "fix" with the readings "fix now / recommend", and the work ends at the diagnosis.
- **Out of scope:** what isn't done and why, with the source.
- [SPEC-ARTIFACT] **An item that can't fail in the product or its build is an artifact of delivery, not a behavior.** The spec keeps two kinds of items apart: situations (what the product or the build must do, with a before → after that can pass or fail) and artifacts (what is handed over at the end: a screenshot, a report, a page in the knowledge base, a summary of the diff, a video, etc.). An artifact item says what to deliver, where, from which scenario and what it must show; variants aren't ranked by it, any design that leaves the deliverable obtainable satisfies it, and it is checked at delivery. Challenge question: can this item fail in the product or its build? If not, it is an artifact.
  - Example: "the import's log before and after, for the same table" → an artifact: the job, the table and the log line to capture; a design that splits the import into two steps still delivers it; etc.
  - Example: "keep the public API" → it can fail in the build: a situation, not an artifact; etc.
  - Anti-example: "for the same table" read as "from the same import step", and the variant that splits the import loses points on it.
- **Mismatches:** where the request differs from the project, its design documents or its rules, or where the user likely doesn't see a consequence (a reused system brings its own behavior, the change reaches other users of a shared asset, etc.). Each one is a question.
- **Questions and assumptions:** a question gives its options and what each changes, in the user's terms ([CHOICE-ITEMS] in SKILL.md); an assumption says what was taken and why. An assumption chosen among several readings stays open: it keeps the other readings, R&D says how each design changes under them ([RND-RETURNS] in [rnd.md](rnd.md)), and the choice and the final report name the reading they stand on.
- [ACC-SOURCE] **Each statement names its source:** the user's words (`task.md`), a design document, a finding, what works now ([SPEC-KEEP]), or the main thread's reading. A reading that changes behavior the user didn't describe is a question for the user ([SCOPE-TRIGGER] in SKILL.md), not a requirement.
  - Example: "the popup closes after the second purchase — the user's words"; "the other popups keep their behavior — kept, what works now"; "the mail popup closes too — the main thread's reading: a question"; etc.
  - Anti-example: the main thread's guess about a neighbouring case written as a requirement, then checked by every agent as if the user had asked for it.

## [SPEC-CRITIC] The spec critic

A read-only sub-agent spawned with {{fresh}}. It gets `task.md`, the task's documents, the scout's report and `spec.md`, and searches the project itself for the spec's terms; it doesn't get the main thread's reasoning. It looks for:

- narrowing: the user's words cover more situations than the item;
- distortion: the item means something other than the words (a hedge turned into a hard check, a duration read as a number of steps, etc.);
- an ambiguity the terms don't name, or a term row whose readings miss what the project's own names say; a number or order word whose row lacks two readings of different kinds ([SPEC-TERMS]);
- a gap: a complaint, a requirement or a kept result ([SPEC-KEEP]) with no item;
- an addition: an item with no source, presented as a requirement, or a "kept" item past where [SPEC-KEEP] ends (a how, a coupling, what the words ask for);
- a mismatch with the project that the spec doesn't name.

It returns each finding with the item, the source's words and what's wrong. The main thread fixes the spec and sends the new version back; the critic checks its findings again, and the loop ends at the first pass with no open finding. A finding is closed by the critic, not by the main thread's own note. Then the main thread asks the questions.

## [SPEC-ASK] Questions go before R&D

- [SPEC-WHAT] **What the user wants is the user's answer.** Before asking, understand the case: what the user has in front of them, what they want and what for, and what result they picture. Expect a request to be loose rather than literal: a few words often stand for a wider wish, and the work starts by unfolding it. Think divergently: before settling on one picture of the task or of the result, look for the others the words allow, then ask about the ones that would change the work, in the user's terms. Which reading of the request (of a defect, a feature, a term, etc.), which product result, in which situation it counts, etc.: no R&D, choice or implementation is built on a reading the user hasn't given and the project's own documents don't fix, whatever the request says about autonomy ("decide yourself", "work autonomously", etc. cover how: the form and the place of the change, the checks, etc.; only an explicit "nobody will answer" changes this, below). The project's evidence narrows the readings; it doesn't pick among them, and the question offers them as equals: no recommended reading and none taken by default (the recommended option of rule 11 in [user-output.md](user-output.md) belongs to questions about how and to the choice). How is the main thread's, as a marked assumption.
  - What does the user want, and what for?
  - What would the result look like to them?
  - Where could two people read this request differently?
  - Then act on the answers: what the user's words or the project's own documents settle goes into the spec; what they leave open goes to the user as a question.
  - Example: "the report loads too slowly" → which report, slow at which step, what time counts as fixed: questions; the facts and a timing of each step go on meanwhile; etc.
  - Example: "add dark mode" → all screens or the reader only; a switch in the settings or following the system; images dimmed too: questions; etc.
  - Example: "the file upload is broken" → it never starts, it fails on large files, or the file arrives damaged: the reproduction of each goes on while the user answers; etc.
  - Example (no question): "retry 3 times", and the client's documented contract counts retries after the first attempt → the document fixes the reading; etc.
  - Anti-example: the terms list "stale" as "older than a day" and as "not refreshed since the last edit", the spec notes "the evidence will decide", and R&D builds on the first.
  - Anti-example: "add an export button" built as a button that exports every record, while the user meant the rows on screen with the current filter.
  - Anti-example: "make search faster" read as the server's response time; the work tunes the database while the user is waiting on the lag after the first keystroke.
- **The user is there:** one message with every question, as soon as the critic's findings are fixed. Meanwhile the work that doesn't rest on an open reading goes on: the stage-2 agents from the spec ([WHO-RUNS]), the reproduction of each open reading, and what the user's words name literally. When it is done and a question about what is still open, the turn ends with the report: what was done, the questions, what waits on each; R&D, the choice and implementation wait for the answers about what, even a design that would carry every reading. The answers go into `task.md` ([TASK-DOC]) and into the items' status.
- **Nobody will answer** (the request says so: the user is away, no questions, etc.; "work autonomously" alone is not that): nothing waits for an answer; a question about how becomes a marked assumption; a question about what keeps every reading open: each is reproduced and carried through R&D and QA, and the report opens with the reading taken and what changes under the others.

## [SPEC-LIVE] The spec lives; the user sees its changes at gates

Any stage can change the spec: facts and the reproduction (how the project really works: a new situation the user's words cover, a term the project resolves, a symptom that differs from the report, etc.), R&D (what a variant brings beyond the task), the choice (the chosen option's side effects), implementation, review and QA (behavior nobody described). Only the main thread edits it, with a new version number at the top; every agent the change affects gets it appended to its brief ([BRIEF] in [agents.md](agents.md)).

- **Within the user's words** (a situation the words already cover, a term the project itself resolves, etc.; not a reading of what the user wants that the words leave open, [SPEC-WHAT]): the item goes in marked "found during work — assumption", and the work goes on; a kept result found later goes in as "found during work — kept" ([SPEC-KEEP]). The main thread decides this itself: the spec keeps the work autonomous, it doesn't turn every detail into a question.
- **Beyond the words or against them** (new behavior, another reading, a dropped item, etc.): a question. It waits for the next gate, unless the next step depends on it: then it is asked now if the user is there, or handled as [SPEC-ASK] sets if nobody will answer.
- **Gates**, where the user sees what changed in the spec since their last answer, with the sources: the spec's questions before R&D ([SPEC-ASK]), the choice menu, the final report.
- A change after the choice that touches the reasons the option won re-checks the choice ([CHOICE-RESCOPE] in SKILL.md).
- Example: the facts show the purchase popup also opens from the mail screen → item 1 gets the situation "opened from mail — found during work, assumption, within the words 'the purchase popup'", and the work goes on; the user sees it in the choice menu. A branch shows that the shared inventory makes the item tradable → a question in the choice menu; etc.
- Anti-examples: the main thread adds the mail case to QA silently, and the user learns of it from the diff; every new detail goes to the user as a separate question mid-work, and the work stalls on answers.

## [SPEC-REFS] Everyone works from the items

- Briefs name the spec's items by number and don't restate them.
- R&D: each branch says which items it covers and how.
- The choice shows which items each option covers ([CHOICE-ITEMS]).
- Review: the map of the change goes by the spec's items ([REV-MAP]).
- QA: the scenarios go by the spec's items, every situation of each.
- The final report goes item by item: done, not done, or an assumption.
