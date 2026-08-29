---
name: sci-ps-skill
description: Reconstruct a reference image as a high-fidelity, structured, editable Photoshop PSD using deterministic reference extraction, a Web GPT/Image2 component handoff, and Photoshop MCP. Use for projects needing validated components, real Photoshop layers, transparent-asset export, QA, and revision.
---

# Sci PS Skill

## Goal

Convert the user's reference image into a high-fidelity, structured, editable Photoshop PSD. All user-visible conversation must be in Simplified Chinese.

## Required resources

Read only the resource needed for the current state:

- State routing: [references/state_machine.md](references/state_machine.md)
- Capability checks: [references/capability_precheck_policy.md](references/capability_precheck_policy.md)
- Web handoff: [references/image2_handoff_policy.md](references/image2_handoff_policy.md)
- Photoshop build: [references/photoshop_mcp_build_spec.md](references/photoshop_mcp_build_spec.md)
- Advanced native parameters: [references/advanced_native_elements.md](references/advanced_native_elements.md)
- QA: [references/qa_checklist.md](references/qa_checklist.md)
- Status format: [references/phase_interaction_templates_zh.md](references/phase_interaction_templates_zh.md)
- Production route hint: [references/reference_production_routing.md](references/reference_production_routing.md)
- Safe revisions: [references/revision_transaction_policy.md](references/revision_transaction_policy.md)

## User commands

- “开始一个新的高保真复刻项目” starts a new project.
- “继续” reads `.visual_recon/project_state.json` and performs only the next legal action.
- “组件包已放入” validates the returned component ZIP and continues if it passes.
- A revision request changes only the requested part unless a broader change is explicitly requested.

## Workflow

### 1. Capability precheck

Before every new project, verify `Codex → Photoshop MCP → Photoshop` with a real tool-inventory JSON and a real `ps_health` result. Run or reuse the version-keyed real canary through `scripts/run_production_canary.py`, then run the strict capability script with `--canary-json`. A legacy seven-tool POC is not production-capable: PNG export plus either `ps_execute_jsx` or the complete granular editing tool set is mandatory. Never enter the build stage on a static-only or historical PASS.

If unavailable, stop project production and use `bootstrap/photoshop_mcp/BOOTSTRAP_PROMPT_ZH.md`. Computer Use is not a substitute for the production Photoshop MCP path.

### 2. Project initialization

Create the project with `scripts/init_project.py`. Collect the reference image, target dimensions, final copy, logo, and font requirements; save the reference as the only `00_reference/reference_master.*`, then run `scripts/create_project_manifest.py` so the build never depends on an improvised manifest.

After saving the reference, provide one non-blocking production-route hint using [references/reference_production_routing.md](references/reference_production_routing.md). Illustrator or an existing vector source is optional and may be asked about once for obviously hand-drawn or flat-vector elements. If it is unavailable, do not pause: every complex element that Photoshop cannot reliably build natively defaults to the Web GPT/Image2 component path.

Do not perform semantic locking, component planning, batch planning, or component extraction in Codex.

### 3. Web GPT/Image2 handoff and extraction planning

Use `scripts/copy_reference_to_outbound.py` to prepare both `reference_master.*` and `UNIVERSAL_IMAGE_COMPONENT_EXTRACTION_PROMPT_ZH_V2.md` in `02_component_handoff/OUTBOUND/`. The user must not search inside the installed Skill.

Tell the user to open a new Web GPT/Image2 conversation and upload:

1. `reference_master.*`
2. `UNIVERSAL_IMAGE_COMPONENT_EXTRACTION_PROMPT_ZH_V2.md`

The Web conversation starts at `STAGE 1 / 6 — REFERENCE ANALYSIS`. It classifies the reference type only to select the right analysis emphasis, then performs dynamic semantic recognition. Regardless of confidence, it must show the image type, semantic inventory, and preliminary boundary among `REFERENCE_EXTRACTION`, Image2 generation, and Photoshop-native construction. Only explicit user confirmation may set `CONTENT_SEMANTIC_LOCK = TRUE`. It then creates the component plan, batch plan, transparent `ASSET_CROP` PNG components, reference-extraction specifications, QA results, and, immediately before packaging, `PHOTOSHOP_RECONSTRUCTION_MASTER_PROMPT_ZH.md`, followed by the final `COMPONENT_HANDOFF.zip`. Web QA judges component fidelity/alpha and extraction eligibility/spec completeness, not final canvas position or scale.

`REFERENCE_EXTRACTION` is a non-generative exact-pixel route for an element already visible in the reference. Use it only when the complete visible contour is clear, materially unobstructed, sufficiently resolved, and separable without borrowing background pixels. The ZIP contains its closed Photoshop path/mask specification and evidence, not a generated PNG. Ordinary text remains editable Photoshop text. A title, wordmark, or logo may use this route only with explicit user acceptance that the extracted result is raster and non-editable. If eligibility is uncertain, route to Photoshop-native construction or Image2 instead.

Tell the user to place the returned ZIP at `02_component_handoff/INBOX/COMPONENT_HANDOFF.zip`, then return and say “组件包已放入”.

Never dynamically generate a project-specific Image2 task Markdown file. Never pre-split the reference in Codex.

### 4. Validate the returned component package

Run `scripts/validate_component_handoff.py`. Reject unsafe ZIP paths, missing manifests, missing component files, unapproved components, or PNGs without usable alpha.

If validation fails, report only the exact failed component and what the user must repair in the Web conversation. Do not enter Photoshop.

If validation passes, use the validated `component_manifest.json` as the sole component and font-asset source for the Photoshop build, and read `PHOTOSHOP_RECONSTRUCTION_MASTER_PROMPT_ZH.md` before generating the build manifest. The master prompt is the project-specific visual execution and finishing brief; it may refine layer order, comparison focus, masks, occlusion, lighting, blur, grading, and integration, but it never overrides manifest coordinates, user decisions, capability gates, or real Photoshop state. Rasterized art text/wordmarks/logos are allowed only when the manifest contains explicit user acceptance and marks them non-editable; ordinary text remains Photoshop-native.

### 5. Photoshop build precheck

Confirm extraction paths and reference hashes together with the existing component/font/capability checks. Every `REFERENCE_EXTRACTION` item must have a closed path, passed eligibility evidence, edge treatment, and an explicit fallback route; otherwise fail before Photoshop starts.

Confirm the strict production capability result, validated manifest, component files, reference dimensions, fonts, logos, and placement information. When an exact font is unavailable, use `ps_list_fonts` first to present the closest installed candidates and their visible tradeoffs; only use a substitute after explicit user selection. If the user rejects installed substitutes and validated open-source fonts are present, show their source/license and ask for explicit approval before running `scripts/install_project_fonts.py --user-approved-install`; never substitute, download, or install silently. Restart/refresh Photoshop when requested, then require `ps_list_fonts` to confirm every selected PostScript name before building editable text. Generate the deterministic build manifest with `scripts/generate_build_manifest.py`, then generate a fully executable `mcp_action_queue.json` with `scripts/generate_mcp_action_queue.py`. Every Photoshop-native element must have a structured `build_spec`; unsupported or incomplete types fail before Photoshop starts.

### 6. Real Photoshop build

Immediately after creating the reference overlay, execute all validated `REFERENCE_EXTRACTION` items first. Copy only the selected reference pixels into separate transparent production layers, clean and verify their edges, and never leave a full-reference copy in a production group. Then continue the existing bottom-to-top build.

Run `scripts/execute_mcp_action_queue.py` through the registered stdio MCP server. Build actual editable layers in the explicit bottom-to-top order defined by the manifest and the validated master prompt: document, background, Smart Object components, masks/occlusion, retained vector paths/curved arrows, effects, editable text, finishing. For each layer, temporarily isolate the current layer with the reference overlay and only the adjacent layers needed to judge contact or occlusion; compare shape, size, position, perspective, color, opacity, blur, lighting, and shadow, correct mismatches, then restore the needed context and verify layer-to-layer integration before continuing. For each `ASSET_CROP` component, use `tool_target_layer_bounds`, then execute its explicit rotation/skew/perspective plan and optional real layer mask. The queue must hide the reference group, save the layered PSD, and export the clean review PNG. After every material mutation, read Photoshop state back and verify a real layer or verified component placement was added.

Photoshop is the visual finishing center, not merely an assembly surface. After structural placement, it must perform the required real masks, local occlusion, contact shadows, reflections, material integration, highlights, glows, gradients, background light fields, atmospheric separation, local adjustments, and final color grading as separate editable layers/groups. Read [references/revision_transaction_policy.md](references/revision_transaction_policy.md) for safe local revisions, unique layer targeting, visibility checks, and rollback checkpoints.

The reference image may exist only in `99_REFERENCE_OVERLAY`. It is for alignment and Difference comparison, never final output and never a tiled or patched baseline.

If two consecutive build cycles add neither `VERIFIED_LAYER_INCREMENT` nor `VERIFIED_COMPONENT_PLACEMENT`, set `BUILD_LOOP_DETECTED = TRUE` and pause.

### 7. QA, correction loop, user review, and export

Compare the build against the reference at full canvas and detail zoom. After a failed pixel comparison, run `scripts/localize_visual_differences.py`; use its region-to-layer evidence and `scripts/generate_correction_queue.py` for high-confidence deterministic corrections only. Execute the correction queue, re-export, re-compare, and repeat. Ambiguous attribution, semantic errors, exact-logo/font absence, or two non-improving cycles must pause instead of blind adjustment. Record every mismatch and correction in `04_photoshop/qa/VISUAL_DIFFERENCE_REPORT.json`, bind current evidence hashes, verify final Photoshop state, and run `scripts/validate_final_qa.py` before delivery.

Keep exact-reference fidelity distinct from an explicitly user-directed adaptation. An adaptation may record `FINAL_USER_DIRECTED_RESULT = TRUE` with the user's approval evidence, but it must not set `FINAL_VISUAL_MATCH = TRUE` unless the reference-comparison gate also passes. `USER_REVIEW` is illegal while both final-result flags are false.

After final QA passes, enter `TRANSPARENT_ASSET_EXPORT`: run `scripts/generate_transparent_asset_export_queue.py`, execute its queue through `scripts/execute_mcp_action_queue.py --queue-file`, then run `scripts/validate_transparent_asset_library.py`. Only after that validation passes may the workflow enter `USER_REVIEW`. Export every approved Image2 component layer and every approved `REFERENCE_EXTRACTION` layer from the final Photoshop state as a tightly cropped, true-alpha PNG into `05_output/transparent_elements/`. Keep one file per element, preserve the source class in its filename and `transparent_elements_manifest.json`, and validate count, PNG decoding, usable alpha, and SHA-256 before final delivery. Do not flatten effects from unrelated layers into an element.

## Required project folders

```text
PROJECT/
├── 00_reference/
├── 01_spec/
├── 02_component_handoff/
│   ├── OUTBOUND/
│   ├── INBOX/
│   └── VALIDATED/
├── 03_components/
│   ├── approved/
│   ├── temporary/
│   └── rejected/
├── 04_photoshop/
│   ├── manifests/
│   ├── scripts/
│   └── qa/
├── 05_output/
│   ├── psd/
│   ├── review/
│   ├── transparent_elements/
│   └── final/
├── 06_logs/
└── .visual_recon/
    ├── project_state.json
    ├── capability_status.json
    └── checkpoints/
```

## Progress reporting

Every user-facing response states the current stage, completed work, blocker if any, the user's required action if any, and the next action. Do not expose internal routing choices unless needed to explain a failure.
