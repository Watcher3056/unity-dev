# Implementing Unity Gameplay Code

Implement Unity gameplay code in a production-oriented way. Prefer simple, readable solutions that fit the existing project style and avoid unnecessary abstraction.

## Start here

- Inspect the existing codebase before changing architecture or code style.
- Follow established local patterns when they are coherent, and match the project conventions unless they directly conflict with the task.
- When the user asks for implementation, make the change instead of stopping at advice.

## Before writing: understand, compare, decide

- **Find the real invariant:** ownership, authority, eligibility, permission, routing of effects, state lifetime, a lock on control or input, validity of an interaction, progression state, etc.
- **Existing vs new:** see [DIR-EXISTING]. Look at what already covers part of the task, then decide by comparison. Neither "always extend" nor "always add new" is right.
- **Consider every mode the feature runs in.** For example: objects driven by scripts or cutscenes with their AI disabled, pooled and re-enabled objects, different scenes or game modes, etc.
- **Ask only what changes the design.** For ambiguous requirements, ask those questions and propose a default for each, so the user can simply confirm.
- **Run R&D before writing** ([rnd.md](rnd.md)) unless the user fixed the approach: genuinely different directions, a challenger to the first idea, comparison by criteria, then present and wait for the choice. When only trying it can settle a question, ask before experimenting.
- **Sub-agent:** the stage-1 scout runs before any design work. It covers similar implementations, existing systems, call sites, prefab/scene wiring impact, code style, etc. Each design option that needs separate research is a stage-2 item. After implementation, a reviewer reviews the diff (stage 6), then the tester runs manual QA in the game (stage 7) (see SKILL.md, Pipeline).

## Dependency rules (hard rules)

These are strict by the user's explicit decision.

- **No fallbacks to avoid errors.** Never add or keep fallback logic only to avoid an exception or a missing-dependency issue. Fallbacks are only for dependencies that are genuinely optional for the business or gameplay goal.
- **No runtime discovery for new required dependencies.** When a script gets a new required dependency, don't initialize it with `GetComponent`, `AddComponent`, `FindObjectOfType` or similar runtime discovery in `Awake`, `Start`, `OnEnable` or update paths. Add the required component to the prefab or scene object and wire it through serialized references.
- **Prefer authored references and caches.** Avoid `AddComponent`, `GetComponent`, `FindObjectOfType`, `FindAnyObjectByType`, hierarchy searches and similar runtime-heavy methods for dependency setup and object discovery. Prefer serialized dependencies, prefab or scene wiring, editor-time baking, and runtime caches (lists, dictionaries, registries) for repeated lookups.
- **No lazy initialization as a fix or optimization.** That includes lazy service lookup, lazy caching or any similar deferred setup. Initialize and wire dependencies and caches explicitly at the appropriate prefab, scene, level-load or lifecycle point. Defer work only when the gameplay or product behavior truly requires it. What this protects: moving the same work to first use doesn't fix its cost, it spreads it; work is cut, moved to initialization, registration or level load, or the mechanism changes. Doing less work, only for what the request needs, with explicit invalidation, isn't lazy initialization: it is a design R&D weighs like any other.
  - Example: a lookup table filled on the first query and kept for the session, while every query still scans everything once → lazy initialization, the cost only moves; etc.
  - Example: a list that creates views only for the rows on screen, instead of for every row of the table, with a row's view rebuilt when its data changes → less work, not deferred work; etc.
  - Anti-example: a critic rejects the second design as "lazy caching" by the word, without asking whether the total work drops.

## Core design defaults

- **ScriptableObject** for shared non-scene configuration and reusable authored data. Keep it focused on data rather than orchestration logic. The preferred shape:

  ```csharp
  public class SampleSO : ScriptableObject
  {
      [SerializeField] private int _value;
      public int Value => _value;
  }
  ```

- **Prefabs as the prototype pattern** rather than runtime object construction. Avoid `AddComponent` for feature setup, and avoid building complex runtime hierarchies in code when a prefab can represent them. Prefer pre-authored scene objects and prefabs with the required components already attached.
- **Direct component references.** Reference the specific component rather than its `GameObject` when the dependency is that component.
- **Root orchestrator.** When a prefab or scene object owns several required sub-components, expose them from a root orchestrator component and wire them explicitly.
- **Assume serialized and externally provided dependencies are valid.** Don't add defensive dependency checks, fallback assignment, null-guard logging or exception-heavy setup unless the task is explicitly about hardening or the dependency is truly optional.

## Gameplay system architecture

- **Rules, not the first object.** Design gameplay systems around stable rules, relationships and lifecycle events, not around the first object, enemy, weapon, scene or feature that exposed the problem.
- **Shared invariants become shared contracts.** If an invariant can apply to more than one gameplay object or future mechanic, consider implementing it as a shared system, API or contract that concrete objects feed with context. Weigh that against the cost of generalizing too early.
- **Explicit lifecycle for transient state.** Who registers it, who reads it, and which gameplay event clears it: create, destroy, enable, disable, attach, detach, a move between containers, the start and end of an animation or a transition, a cancel, an ownership change, etc.
- **No timing workarounds by default.** Avoid frame-count, tick-count or arbitrary-delay fixes unless the issue is proven to be engine ordering only, and that proof is documented in code.
- **One authoritative gate per decision.** Route gameplay side effects through it before they execute. Side effects of one decision (health or score changes, sounds, notifications, unlocks, etc.) shouldn't each invent separate local rules for it.
- **Work within existing structures by default.** That covers the Animator controller structure, command and event patterns, AI architecture, etc. A new layer or a parallel mechanism is a design decision. Compare it with integrating into the existing structure, and raise it with the user (or the animator, for Animator changes) before committing to it.

Use these architecture references as short reasoning anchors (each with when to use it and when to avoid it):

| Pattern | Use when | Avoid when |
| --- | --- | --- |
| Domain-Driven Design / invariant modeling | Behavior depends on gameplay meaning (ownership, authority, eligibility, progression, rules shared across objects) | A purely local presentation tweak, a simple data move, or a one-off authored asset correction |
| Single Source of Truth | Multiple call sites can trigger the same decision or side effect | Unifying would hide genuinely independent states with different lifecycles or owners |
| Finite State Machine / State Pattern | Behavior changes through explicit modes or lifecycle transitions | A stateless calculation or a small one-shot command |
| ECS-style system ownership | Many objects provide data and one broad rule operates over them | The behavior is tightly authored to one prefab, animation or hand-placed object |
| Event-Driven Architecture | State should register or clear from real gameplay events | Event indirection would obscure a direct synchronous call or make ordering harder to prove |
| Separation of Concerns / SRP | One class mixes unrelated decisions (input, movement, collision, damage, UI, animation) | Splitting by nouns creates tiny wrappers with no independent responsibility |
| Policy / Strategy | An eligibility rule varies by context and must be reusable or swappable ("can damage", "can interrupt", etc.) | There is one stable rule and a direct method is clearer |

Examples of the reasoning expected (illustrations, not recipes):

- **A dragged item is taken back by its own slot the moment the drag starts.**
  - Bad: ignore that slot for two frames.
  - Good: model the ignore of the source slot as drag-lifecycle state. Set it on drag start; clear it on the next meaningful event (the item over another slot, a cancel, the item removed, a new drag).
- **One item, payment method, role or enemy type causes a blocker.**
  - Bad: a type-specific bypass at the failing call site.
  - Good: identify the shared relationship (owner, holder, payer, source, target, authority, etc.), put the rule in a shared gate, and let the concrete type supply context.
- **An order confirmation goes out wrong on one of the ways an order is placed.**
  - Bad: suppress it on that one path.
  - Good: define its eligibility once (from the order's kind, its source, the customer's state and settings, etc.) and make every path ask that rule.
- **A race appears during animation, collision or ability transitions.**
  - Bad: add a short delay.
  - Good: trace the real event order and bind state changes to the transition that owns the behavior.
- **A future feature might need this.**
  - Bad: build a broad framework before real call sites exist.
  - Good: generalize only to the proven invariant and the nearest expected extension point, with a small API named after the gameplay relationship.

## Architecture balance

- **Balanced design,** neither monoliths nor over-fragmentation. Keep responsibilities clear, but don't explode simple features into many types. A single MonoBehaviour is acceptable while complexity stays reasonable, roughly up to 400 lines.
- **SOLID, KISS and single responsibility,** without forcing indirection where direct code is clearer.
- **Don't keep obsolete abstractions** just to leave old call sites untouched.
- **Prefer direct data flow.** For example:
  - a prefab has baked metrics → read them directly from the prefab definition;
  - a controller needs a pool → inject the pool component directly;
  - a system needs a renderer, marker or guide → reference that exact component.
- **One type per file by default,** and no multiple MonoBehaviours in one file. Group small related helper types only when that clearly improves readability.

## Performance-aware coding

Deep optimization work: [performance.md](performance.md).

- **Watch CPU cost and GC pressure.** Pre-allocate collections and reusable objects when usage repeats. Use Unity pooled collections for temporary hot-path work when helpful.
- **Prefer non-alloc APIs** for raycasts, overlaps and similar repeated queries, when available and justified.
- **Avoid repeated allocation** in `Update`, preview loops, animation callbacks, placement logic, etc. Avoid LINQ in hot gameplay paths.
- **No fake optimization.** Don't split trivial work across frames or throttle core logic without evidence that it helps. Write simple code first, then optimize real hotspots.
- **Bake stable prefab metadata at editor time.** Use `OnValidate` for authored-data baking when appropriate. Don't instantiate and destroy temporary objects inside `OnValidate` when direct asset inspection can solve the problem.

## Scene, prefab and pooling

- **Explicit references over discovery.** Prefer explicit serialized references over runtime discovery. Prefer authored scene roots and prefabs for markers, guides, pooled object roots, feedback objects, reusable visual helpers, etc.
- **Pooling ownership in a dedicated component.** If an object must be reused, put pooling ownership into a dedicated pool component. Don't mix pool management, input handling, solver logic and view creation in one controller when they are distinct responsibilities.
- **When pooling:**
  - reuse objects instead of destroying and re-instantiating them;
  - reset transform and visual state before returning or reusing;
  - keep the pool API simple and direct.

## Rendering and authoring

- **Per-instance visuals:** use `MaterialPropertyBlock` instead of cloning materials at runtime. Don't mutate shared material assets at runtime unless the task explicitly requires it.
- **Editor-only code:** separate it with `#if UNITY_EDITOR`, and keep runtime logic out of editor-only baking code.
- **Tunable values:** prefer authored serialized values for user-facing visuals and tuning data (colors, timings, scales, distances, amplitudes, etc.). Values a designer is likely to tune shouldn't be hidden as private constants.

## Code style

Follow the project's style first. Where it has none:

- **Naming:** private fields `_camelCase`; `[SerializeField] private` rather than public fields for authored references.
- **Member order:** serialized private fields, public properties, private fields, Unity callbacks, public methods, private methods.
- **Readability:** readable code over clever code. No bit-packing, opaque constants or binary tricks in gameplay code unless the task needs them. Use human-readable constants and descriptive names.
- **No pointless wrappers:** prefer direct field or property access over helper wrappers that add no value, and no convenience layers that only rename obvious data flow.
- **Comments:** short single lines, only where the code is non-obvious, in a neutral tone.

## Deliverables beyond code

When useful:

- a short guide for designers (where it lives, which fields matter, sane ranges, how to see it in a test scene);
- "how to test" notes for the team;
- a knowledge-base entry if project rules ask for one.

## Implementation checklist

- Are dependencies wired directly instead of discovered dynamically?
- Are all new required components present and serialized on the relevant prefabs or scene objects?
- Did you avoid fallback logic for missing required dependencies, and lazy initialization or lookup as a fix or optimization?
- Is the change modeled around a stable gameplay invariant, not only the object that exposed the issue?
- Does every transient state have a clear lifecycle owner and a clearing event?
- Does each decision with side effects (a health or score change, a notification, an unlock, etc.) go through the gate that owns it?
- Are prefabs and scene references used instead of runtime construction where practical?
- Is runtime allocation minimized in hot paths?
- Is the code simpler than before, not just more abstract?
- Does the result match the project's style and architecture?
- Did you compare the alternatives, and would the choice survive "what if this changes?" and "why would it break in 3 months?"
- Did QA pass the acceptance scenarios confirmed at the gate, in the game? If not, the work isn't done; keep iterating.
