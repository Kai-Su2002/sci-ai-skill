# Photoshop MCP 首次能力安装 / 恢复 Prompt

仅当 `CAPABILITY_PRECHECK` 未通过时使用。

目标控制链：
`Codex → local stdio MCP → Python → Windows COM → Photoshop`

优先级：
1. 如果当前机器已有 server，先检查完整生产工具清单；缺少 `ps_place_smart_object`、`ps_transform_layer_advanced`、`ps_apply_layer_mask` 或 `ps_list_fonts` 时不得复用为当前生产能力。
2. 如果 config 已有 server 但当前会话看不到 tools：保存 checkpoint，要求完全重启 Codex；重启后用户只说“继续”。
3. 如果没有生产 server：使用本目录自带的 `server.py`、`photoshop_com.py` 和 `requirements.txt` 建立 `photoshop-production` server，再按 `POC_FULL_PROMPT_ZH.md` 验证。
4. POC 必须通过 MCP 真调用，不允许仅 Python 直调冒充。
5. 注册 MCP 前可运行 `integration_test.py` 验证 COM backend；注册并重启后仍必须再通过 MCP 真调用同等动作。
6. 禁止 Computer Use fallback。

通过标准：
PHOTOSHOP_COM_AVAILABLE=YES
MCP_SERVER_STARTED=YES
CODEX_CAN_SEE_MCP_TOOLS=YES
PS_HEALTH_VERIFIED=YES
DOCUMENT_CREATE_VERIFIED=YES
IMAGE_PLACE_VERIFIED=YES
TRANSFORM_VERIFIED=YES
PLACEMENT_VERIFIED=YES
EDITABLE_TEXT_VERIFIED=YES
PSD_SAVE_VERIFIED=YES
PNG_EXPORT_VERIFIED=YES
SMART_OBJECT_VERIFIED=YES
GROUP_CREATE_VERIFIED=YES
REAL_LAYER_MASK_VERIFIED=YES
EXPORT_HASH_AND_SIZE_VERIFIED=YES
TEMP_DOCUMENT_CLOSED_WITHOUT_SAVE=YES
ADVANCED_EDIT_JSX_OR_GRANULAR_TOOLS_VERIFIED=YES
RECURSIVE_LAYER_STATE_AND_VISIBILITY_VERIFIED=YES
COMPUTER_USE_USED=NO

把上述真实测试结果写入 production canary JSON；工具清单和 `ps_health` 通过但 canary 不完整时仍不得进入生产构建。
