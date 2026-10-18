// The development pipeline (the unity-dev skill) on the board: an add-on. The board shows any task by the common kinds
// of a step; this profile adds what only this skill's work has: its stages by their kinds (and the finer roles the
// board uses for them: the facts of a gathering, the variants and the choice of a decision, the knowledge kept), the
// parts of its gathering (the task's spec, the work in the game), the rules its R&D branches and its judge cite, the
// rules of the steps that build a stand (their new files are made for the checks, not the fix), and its own words for
// some moments. The viewer loads it from this skill's graph/ folder, so the board knows this pipeline wherever the skill
// is installed and only there. It shows how a skill's profile is written (the viewer's README, "Add-ons")
(() => {
  TraceBoard.addProfile({
    id: 'unity-dev',
    // a trace of this skill: it says so in its first line, or its stages carry the pipeline's tags
    match: (model) => model.skill === 'unity-dev' || (model.nodes || []).some((n) => /^PIPE-/.test(String(n.sg || ''))),
    // stage tag → the board's role (gather: context, facts; found; choose: rnd, choice; do: impl; check: checks)
    roles: {
      'PIPE-PROFILE': 'context', 'PIPE-SCOUT': 'context', 'PIPE-FACTS': 'facts', 'PIPE-RND': 'rnd', 'PIPE-CHOICE': 'choice',
      'PIPE-IMPL': 'impl', 'PIPE-REVIEW': 'checks', 'PIPE-QA': 'checks', 'PIPE-KNOWLEDGE': 'knowledge',
    },
    // the parts of a gathering, each a card of its own beside the facts: the steps right under a facts stage that cite
    // the spec's rules; or that cite, themselves or in a step under them, the reproduction's rule or the rules of a run
    // in the game (the step the main thread opens for the reproduction may cite none: the tester's steps under it do)
    parts: {
      spec: ['SPEC', 'SPEC-CRITIC', 'TASK-DOC'],
      game: ['REPRO', 'PM-START', 'PM-OWN-SCENE', 'PM-SESSION', 'PM-REPRO-IS-QA', 'PM-DRIVER', 'PM-LANES', 'PM-BEFORE-AFTER', 'PM-OBSTACLE'],
    },
    // a variant of R&D cites a branch rule; what weighs the variants, the judge's or a deciding check's
    branch: /^RND-(FIRST-IDEA|MINIMAL|DIRECTIONS|EXISTING|REUSE|CHALLENGER|FLAGGED|ISOLATE|BRIEF-SCOPE|RETURNS|SKETCH)$/,
    weigh: /^RND-(JUDGE|DECIDING|AUDIENCE)$/,
    // a new file a step that builds or runs a stand names is made for the checks
    standTags: ['STAND-PREP', 'PM-OWN-SCENE', 'PM-DRIVER', 'PM-LANES', 'PM-OBSTACLE', 'PM-SESSION', 'PM-START', 'PM-REPRO-IS-QA', 'REPRO'],
    // a step that prepares the stand (a recipe, a tool, the stand itself): under a check it is no round of the check
    prepTags: ['STAND-PREP'],
    // the steps that find or check (a new file only they name is made for the checks): the gathering, the facts, QA;
    // not the review, which names the fix it reads
    finders: (s, role) => role === 'context' || role === 'facts' || s.sg === 'PIPE-QA',
    // the stages' short names, under the task's track and on the graph's stations
    stageNames: {
      'PIPE-PROFILE': { en: 'Prepare', ru: 'Подготовка' }, 'PIPE-SCOUT': { en: 'Scout', ru: 'Разведка' }, 'PIPE-FACTS': { en: 'Facts', ru: 'Факты' },
      'PIPE-RND': 'R&D', 'PIPE-CHOICE': { en: 'Choice', ru: 'Выбор' }, 'PIPE-IMPL': { en: 'Implement', ru: 'Реализация' },
      'PIPE-REVIEW': { en: 'Review', ru: 'Ревью' }, 'PIPE-QA': 'QA', 'PIPE-KNOWLEDGE': { en: 'Knowledge', ru: 'Знания' },
    },
    // the stages that must have come before a stage: implementing after a skipped R&D or choice is an issue
    needs: { 'PIPE-IMPL': ['PIPE-RND', 'PIPE-CHOICE'] },
    // in Decisions: the judge comes after the variants; critics hung on the choice itself are one group after them
    judgeTags: ['RND-JUDGE'],
    criticTags: ['RND-CRITIC'],
    // traces written before the stages had tags: their numbers, as the pipeline had them then
    legacy: {
      stages: { 0: 'PIPE-PROFILE', 1: 'PIPE-SCOUT', 2: 'PIPE-FACTS', 3: 'PIPE-RND', 4: 'PIPE-CHOICE', 4.5: 'PIPE-IMPL', 5: 'PIPE-REVIEW', 6: 'PIPE-QA', 7: 'PIPE-KNOWLEDGE' },
      numbered: 'PIPE-',
    },
    // what the facts find are problems
    glyphs: { found: '⚠' },
    labels: {
      decision: { en: 'Choosing the approach', ru: 'Выбор подхода' },
      changes: { en: 'Changes', ru: 'Изменения' },
      looking: { en: 'looking for the cause', ru: 'ищем причину' },
    },
  });
})();
