# QA Checklist

## Build integrity

- [ ] MCP health PASS
- [ ] Validated `PHOTOSHOP_RECONSTRUCTION_MASTER_PROMPT_ZH.md` was read before build-manifest generation
- [ ] No reference tile / patch is used in the production PSD
- [ ] Background is built from real Photoshop layers
- [ ] Every required image component exists and its placement is verified
- [ ] Every image component is a Smart Object with audited source provenance
- [ ] Required layer masks exist and their feather/density/invert settings match the manifest
- [ ] Text remains editable
- [ ] Paths, arrows, frames, circuits, and effects are built as planned
- [ ] Layer order and occlusion are correct
- [ ] PSD is not flattened
- [ ] Required masks, contact shadows, highlights, glows, gradients, background light fields, material integration, local adjustments, and final grading exist as editable Photoshop layers/groups

## Reference-match loop

- [ ] Explicit bottom-to-top layer order is recorded and matches the real Photoshop layer stack
- [ ] Every material layer was isolated with the reference overlay for shape, size, position, perspective, and edge comparison
- [ ] Every isolated layer was checked for color, opacity, blur, glow, lighting, shadow, reflection, and material fidelity
- [ ] Required adjacent layers were restored to verify occlusion, contact, overlap, and transition before the next layer was accepted
- [ ] Full-canvas composition, scale, position, spacing, and hierarchy match
- [ ] Normal overlay comparison completed
- [ ] Difference comparison completed
- [ ] Clean rendered PNG exported through Photoshop MCP
- [ ] Pixel comparison evidence contains current reference/render hashes and passes configured thresholds
- [ ] 100% edge, sharpness, text, and component inspection completed
- [ ] 200%–400% mask, glow, blur, texture, particle, and micro-detail inspection completed
- [ ] Shape, perspective, and transform mismatches corrected
- [ ] Retained Photoshop paths exist for complex paths and curved arrows
- [ ] Opacity, blend mode, and occlusion mismatches corrected
- [ ] Blur, depth-of-field, and softness mismatches corrected
- [ ] Lighting, glow, reflection, highlight, and shadow mismatches corrected
- [ ] Hue, saturation, brightness, contrast, and local tonal mismatches corrected
- [ ] Mask edges, halos, and transparent fringes corrected
- [ ] Text content, font, size, tracking, leading, and alignment match
- [ ] Missing details are added; wrong core components are returned for Web repair
- [ ] Every correction was followed by a fresh comparison against the reference
- [ ] Failed comparisons produced `difference_localization.json`; automatic corrections were limited to uniquely attributed whitelist actions
- [ ] Every major reference shape has a corresponding production layer/path and reaches the highest practical overlap
- [ ] Element-to-element contact, overlap, masking, occlusion, shadow, reflection, and edge transitions match the reference
- [ ] Foreground/background transitions, atmospheric depth, blur hierarchy, lighting continuity, and color integration match
- [ ] Hard pasted edges were resolved with justified extraction/cropping, real masks, feathering, local light/shadow, opacity, blend mode, or clipped adjustments
- [ ] Layer-level, relationship-level, and full-canvas inspections all pass independently

## Delivery gate

- [ ] `99_REFERENCE_OVERLAY` is hidden for clean-view QA
- [ ] `verify_photoshop_build_state.py --final` confirms both reference layers have `visibility=false`
- [ ] The final image remains complete without the reference layer
- [ ] No known material visual or semantic mismatch remains at target output size
- [ ] No known mismatch remains in detail inspection
- [ ] `FINAL_VISUAL_MATCH = TRUE`
- [ ] User review completed

For an explicitly user-directed adaptation, use `validate_final_qa.py --mode adaptation`. It still requires real Photoshop export, current hashes, hidden reference layers, resolved recorded differences, and the user's approval quote/scope, but it records `FINAL_USER_DIRECTED_RESULT = TRUE` instead of falsely claiming exact reference matching.

必须保存 `04_photoshop/qa/VISUAL_DIFFERENCE_REPORT.json`，并通过 `scripts/validate_final_qa.py`。口头声称“已经一致”不能替代该记录和门禁验证。

If any item above fails, set `FINAL_VISUAL_MATCH = FALSE`, record the mismatch, apply the appropriate correction, and repeat QA. Do not export or claim completion before all delivery-gate items pass.
