from pathlib import Path
import hashlib
import json
import sys


root = Path(__file__).resolve().parents[1]
required = [
    "SKILL.md",
    "AGENTS.md",
    "agents/openai.yaml",
    "INSTALL_PROMPT_ZH.txt",
    "START_PROMPT_ZH.txt",
    "CONTINUE_PROMPT_ZH.txt",
    "COMPONENT_RETURN_PROMPT_ZH.txt",
    "VERSION.json",
    "requirements.txt",
    "references/state_machine.md",
    "references/reference_production_routing.md",
    "references/revision_transaction_policy.md",
    "references/capability_precheck_policy.md",
    "references/image2_handoff_policy.md",
    "references/photoshop_mcp_build_spec.md",
    "references/advanced_native_elements.md",
    "references/qa_checklist.md",
    "references/phase_interaction_templates_zh.md",
    "templates/UNIVERSAL_IMAGE_COMPONENT_EXTRACTION_PROMPT_ZH_V2.md",
    "templates/project_state.template.json",
    "templates/production_canary.template.json",
    "schemas/project_state.schema.json",
    "schemas/component_manifest.schema.json",
    "schemas/build_manifest.schema.json",
    "schemas/visual_difference_report.schema.json",
    "scripts/init_project.py",
    "scripts/create_project_manifest.py",
    "scripts/capability_precheck.py",
    "scripts/run_production_canary.py",
    "scripts/copy_reference_to_outbound.py",
    "scripts/validate_component_handoff.py",
    "scripts/generate_build_manifest.py",
    "scripts/generate_mcp_action_queue.py",
    "scripts/generate_transparent_asset_export_queue.py",
    "scripts/validate_transparent_asset_library.py",
    "scripts/compile_native_element.py",
    "scripts/execute_mcp_action_queue.py",
    "scripts/route_next_action.py",
    "scripts/install_local.py",
    "scripts/mcp_queue_integration_test.py",
    "scripts/reference_extraction_integration_test.py",
    "scripts/finalize_delivery.py",
    "scripts/advanced_native_integration_test.py",
    "scripts/compare_rendered_output.py",
    "scripts/localize_visual_differences.py",
    "scripts/generate_correction_queue.py",
    "scripts/visual_correction_integration_test.py",
    "scripts/install_project_fonts.py",
    "scripts/verify_project_fonts.py",
    "scripts/font_workflow_integration_test.py",
    "scripts/self_test.py",
    "scripts/verify_photoshop_build_state.py",
    "scripts/validate_final_qa.py",
    "scripts/resume_project.py",
    "scripts/update_build_progress.py",
    "scripts/validate_state_consistency.py",
    "templates/visual_difference_report.template.json",
    "bootstrap/photoshop_mcp/BOOTSTRAP_PROMPT_ZH.md",
    "bootstrap/photoshop_mcp/server.py",
    "bootstrap/photoshop_mcp/photoshop_com.py",
    "bootstrap/photoshop_mcp/integration_test.py",
    "bootstrap/photoshop_mcp/mcp_stdio_integration_test.py",
    "assets/masked_smart_object_template.psd",
]
missing = [path for path in required if not (root / path).exists()]
hash_issues=[]
hash_path=root/"SHA256.json"
if hash_path.exists():
    recorded=json.loads(hash_path.read_text(encoding="utf-8"))
    actual={str(path.relative_to(root)).replace("\\","/"):hashlib.sha256(path.read_bytes()).hexdigest() for path in root.rglob("*") if path.is_file() and path.name!="SHA256.json" and path.suffix!='.pyc' and '__pycache__' not in path.parts}
    if set(recorded)!=set(actual): hash_issues.append("SHA256.json 文件清单与实际包不一致")
    for name in set(recorded)&set(actual):
        if recorded[name]!=actual[name]: hash_issues.append(f"哈希不一致: {name}")
else: hash_issues.append("缺少 SHA256.json")
result = {"package_ok": not missing and not hash_issues, "missing": missing, "hash_issues":hash_issues}
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if result["package_ok"] else 2)
