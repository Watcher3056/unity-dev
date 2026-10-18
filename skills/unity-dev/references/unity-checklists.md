# Unity Bug-Class Checklists

Prompts for building hypotheses once a failure is classified. They are not exhaustive and not a sequence: use the ones that match the failure class and add whatever the case suggests.

## Common hypothesis sources

- A missing serialized reference, a missing component, or a prefab override mismatch.
- A scene object that is absent, inactive, renamed, duplicated, or loaded in a different scene order.
- Ordering of `Awake` / `OnEnable` / `Start`, coroutines, async loads or event subscriptions.
- Unsubscribed events, persisting static state, or behavior with domain reload disabled.
- `Update` vs `FixedUpdate` timing, Rigidbody or collider setup, trigger flags, the collision matrix, layers or tags, navigation or physics settings.
- An input action map that isn't enabled, a wrong control scheme, UI focus consuming input, or an old/new Input System mismatch.
- An Animator state or transition mismatch, a root motion conflict, or an animation event target mismatch.
- UI canvas sort order, anchors, EventSystem or raycaster setup.
- Asset stripping, Addressables or Resources path mismatch, platform define differences, or build inclusion.
- Per-frame allocations, expensive `Find*`, LINQ or boxing, instantiation, logging, physics queries, pathfinding, rendering, or sync stalls.
- Etc.

## Prefab, scene and serialization

- Check for missing serialized references, prefab overrides, inactive, duplicate or renamed objects, and scene inclusion or build index.
- Compare prefab asset values against scene instance overrides.
- Check ScriptableObject references, Addressables or Resources paths, and asset import state.
- Verify assumptions about domain reload, static fields and editor-only initialization.

## Lifecycle and event flow

- Check the order of `Awake` / `OnEnable` / `Start`, coroutines, async loads, scene loads and object activation.
- Check that subscriptions and unsubscriptions are symmetric, and look for duplicate subscriptions.
- Check destroyed or disabled objects, pooled object reuse, and stale references.
- Verify that initialization contracts are explicit rather than dependent on inspector order or timing.

## Physics and movement

- Check Rigidbody mode, collider and trigger flags, the collision matrix, layers, tags and physics materials.
- Check `Update` vs `FixedUpdate`, transform vs Rigidbody movement, interpolation, constraints and time scale.
- Check query masks, query trigger interaction, ground checks and contact normals.
- Verify which authority drives the motion: AI, player input, root motion, networking, or several of them at once.

## Input and UI

- Check the active action map, enabled actions, control scheme, device pairing and rebinding.
- Check EventSystem presence, the selected object, raycasters, sort order and blocking panels.
- Check input gates: pause, modal, tutorial, cursor lock, application focus, etc.

## Animation and visual state

- Check Animator parameters, transition conditions, layers, masks, exit times, root motion and animation event targets.
- Check whether gameplay state and visual state can diverge.
- Check activation, material or property-block changes, render layer, culling mask, sorting and LOD.

## Build-only and platform

- Check player logs, scripting backend, stripping and `link.xml`, platform defines, case-sensitive paths, included scenes, Addressables/Resources catalogs and shader inclusion.
- Check development vs release build differences and platform permissions.
- Check whether editor-only APIs or `UNITY_EDITOR` assumptions leak into runtime code.

## Performance

- Check profiler markers, spikes, GC allocations, instantiation and destruction, logging, `Find*`, LINQ, boxing, physics queries, pathfinding, rendering and sync stalls.
- Compare before/after numbers for the exact marker or frame segment.
- Prefer focused profiling evidence over broad speculation. See [performance.md](performance.md).
