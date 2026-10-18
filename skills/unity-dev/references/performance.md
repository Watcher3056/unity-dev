# Unity Performance (CPU / GC)

Produce practical optimization plans and safe code changes for Unity CPU and GC hotspots. Focus on measurable impact and behavior parity.

## Rules

- **Remove direct cost first:** redundant calls, allocations, duplicated data flow, non-alloc APIs, caching, pooling with a clear lifetime, etc.
- **Don't hide cost.** Avoid optimization patterns that only hide cost as a default. For example, converting per-frame work to fixed 0.2-0.5 s polling.
- **Confirm before changing (hard rule).** Get explicit confirmation before applying optimization changes; a "fix" or "apply" request counts as that confirmation. Confirm again before moving from level 1 to level 2 or 3. If the estimated regression risk is above low, stop and ask before implementing.
- **Sub-agent:** these are typical stage-2 items in performance work: profiler marker interpretation, hot-path call graphs, allocation-source tracing, wiring or invariant review, git-history comparison, and the real-case hit-rate check of each proposed optimization, etc. You reconcile the evidence and decide (see SKILL.md, Pipeline).
- **R&D:** when a hotspot has more than one possible fix, those fixes go through the R&D stage ([rnd.md](rnd.md)) before the report recommends one.

## Workflow

1. **Capture context from profiler evidence:** scene and setup, entity count, frame type (`Update` / `FixedUpdate`), call count, self/total CPU, GC alloc, spike or sustained, etc. Use the captures and screenshots the user provides.
2. **For a regression** ("it got slower recently"), find the changes that introduced the cost and verify each one with evidence: who, when, what it costs.
3. **Produce a level 1 report by default.** Include level 2 and 3 details only when requested.
4. **Ask before applying** the approved level 1 items.
5. **Apply only the approved items,** with regression checks.
6. **Validate:**
   - it compiles with no errors;
   - an A/B profiler check against the baseline;
   - behavior parity on the affected systems.
7. **Offer deeper levels** (2, then 3) if the user wants more.

## Report format

For each issue, give these fields in this order. A table works well (see user-output.md):

| Priority | Place | Issue | Frequency | Approx. CPU and/or GC per frame | Suggested fix | Expected outcome | Safety |
| --- | --- | --- | --- | --- | --- | --- | --- |

After applying changes:

- show "before → after" for the same scenario and marker;
- when the user's baseline is a capture or screenshot, estimate the result per N entities compared with it;
- if near-zero allocation isn't reachable, say what blocks it.

## Optimization levels

- **Level 1 (default):** regression-safe, minor changes. Behavior unchanged; local refactors, non-alloc replacements, caching, duplicate-work removal. Low risk, easy rollback.
- **Level 2 (on request):** significant logic changes, mostly safe. Feature behavior is preserved, but flow changes go deeper. Requires explicit assumptions and targeted parity validation.
- **Level 3 (on request):** architectural changes or full module rewrites. Subsystem redesign with a migration plan and a risk matrix. Not implemented without explicit approval.

## Does it really help? (challenge each item)

- **Hit rate in the real case.** A cache or reuse helps only if the data actually stays the same between uses in this project's real scenarios. For example, a cached value that changes every frame, or a randomly regenerated point, never hits. Check each optimization against the real case and remove reuse that doesn't pay off.
- **Dynamic data.** Objects can move, change owner, get pooled, or spawn and despawn at runtime, etc. A cache must stay correct through those lifecycles. Heavy caches can often be built at editor time or level init and refreshed by events instead of polling.
- **Trade-offs are the user's call.** Reducing content, quality, update rate, LOD, etc. changes the product, so it isn't a free optimization. Present it as a trade-off.
- **Fragile code.** Large edits to fragile core components for a performance goal need a stated necessity and a safety argument, given up front.
- **Logging cost.** Logging in hot paths shouldn't allocate when disabled (conditional compilation, guarded formatting, etc.) while keeping the information it provides.

## Regression-safety checklist

- Verify invariants before the change: inputs, outputs, state transitions.
- Keep the legacy behavior path when uncertainty exists.
- Add profiler markers or samples around changed hotspots to confirm impact.
- Validate that changed hot paths have no new per-frame allocations.
- Re-profile the same scenario after each change.
