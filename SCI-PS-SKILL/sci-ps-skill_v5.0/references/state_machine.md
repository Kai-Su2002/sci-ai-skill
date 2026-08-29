# State Machine

## States

0. `CAPABILITY_PRECHECK`
1. `CAPABILITY_BOOTSTRAP`
2. `PROJECT_INIT`
3. `UNIVERSAL_IMAGE2_WEB_HANDOFF`
4. `WAIT_IMAGE2_HANDOFF`
5. `COMPONENT_PACKAGE_VALIDATION`
6. `PHOTOSHOP_BUILD_PRECHECK`
7. `PHOTOSHOP_REAL_BUILD`
8. `BUILD_QA`
9. `TRANSPARENT_ASSET_EXPORT`
10. `USER_REVIEW`
11. `REVISION`
12. `FINAL_EXPORT`
13. `DONE`

After `PROJECT_INIT` saves the reference, go directly to `UNIVERSAL_IMAGE2_WEB_HANDOFF`. Semantic recognition, semantic locking, component planning, and batching occur only in the Web conversation under the universal prompt.

`BUILD_QA` is a correction loop, not a one-pass inspection. After final QA passes, enter `TRANSPARENT_ASSET_EXPORT`, export and validate the unified transparent-element library, then enter `USER_REVIEW`. `USER_REVIEW` and `FINAL_EXPORT` are legal only after a validated final result and a validated transparent-element manifest exist.

## Next-action router

“继续” performs exactly one next legal action:

- Resolve an existing blocker first.
- If user action is required, repeat the exact action and paths without advancing.
- Complete and verify the current state before entering the next state.
- Never repeat a state already marked `PASS`.
- Treat repeated commands idempotently. Re-validating the same component ZIP hash or re-running an already committed action is forbidden; resume at the first incomplete action.

Before writing state, run the equivalent of `scripts/validate_state_consistency.py`. `USER_REVIEW`, `FINAL_EXPORT`, and `DONE` require either `FINAL_VISUAL_MATCH = TRUE`, or an explicitly approved user-directed result with a non-empty approval quote. The second path must never be described as exact reference matching.

## Build loop guard

If two consecutive Photoshop build cycles add neither a verified layer nor a verified component placement, set `BUILD_LOOP_DETECTED = TRUE`, pause, and report why no real progress occurred.
