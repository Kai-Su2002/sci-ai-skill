# Photoshop Revision Transactions

Apply a revision only to the requested scope.

## Before mutation

1. Resolve the active document and target by stable layer ID plus full parent path. Names alone are insufficient.
2. Fail on duplicate-name ambiguity unless a stable ID uniquely resolves it.
3. Read target visibility, parent visibility, bounds, blend mode, and the layers above it.
4. Detect a visible full-canvas opaque layer above the target. If it would hide the result, report the occlusion before increasing effect intensity.
5. Save a lightweight checkpoint containing target IDs, properties, bounds, parent order, and the current clean export hash.

## Mutation

- Preserve user-locked and deferred categories such as `TEXT_REVISION_POLICY = DEFERRED_BY_USER`.
- Put multi-layer effects in one named selectable group with a stable group ID.
- Prefer one retained path/shape or Smart Object instances over dozens of segment layers.
- Keep the user-replaced source as the active source and retain the previous version only as a hidden backup.

## Verification and rollback

After mutation, verify a state delta: changed or added layer IDs, expected parent, visibility, bounds, and a fresh export. If the requested result is not visible or the measured comparison worsens, revert only the current transaction and diagnose; do not blindly intensify the effect.

For transparent luminous assets, inspect semi-transparent edge RGB for black/near-black matte. Repair with alpha-aware recoloring, defringe/remove-matte, or additive reconstruction so the edge follows: blue-white core → pale blue → light cyan-blue → alpha naturally decays to zero.
