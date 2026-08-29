# Photoshop MCP 能力预检策略

优先复用当前机器已通过的能力，不每个项目重做完整 POC。

检查顺序：
1. 历史 `POC_REPORT.md` / checkpoint（若存在）
2. 本地 Codex MCP config 是否包含 Photoshop server
3. 保存当前会话真实 Photoshop MCP tool inventory
4. 调用 `ps_health` 并保存真实 JSON 返回
5. 运行 `scripts/capability_precheck.py <project> --tool-inventory-json <tools.json> --health-json <health.json>`
6. 使用 `scripts/run_production_canary.py` 对当前 Photoshop/MCP/Skill 版本组合运行或复用真实 production canary：临时文档、图层组、Smart Object、变换、文字、蒙版、JSX、高级视觉效果、PSD 保存、PNG 导出、尺寸/哈希验证及无保存关闭。Canary 结果必须由 `--canary-json` 提供且通过；工具存在但 canary 未通过仍为 FAIL。

判定：
- 基础工具必须包括 `ps_health`, `ps_create_document`, `ps_place_image`, `ps_transform_layer`, `ps_create_text`, `ps_get_state`, `ps_save_psd`, `ps_export_png`, `ps_close_document`
- v5.0 精确构建还必须包括 `ps_place_smart_object`, `ps_transform_layer_advanced`, `ps_apply_layer_mask`, `ps_list_fonts`；缺少任意一项不得宣称智能对象、完整变换、真实蒙版或项目字体验证可用
- 高级编辑必须具备 `ps_execute_jsx`，或同时具备分组、图层属性、排序、形状、蒙版、效果、调整层和完整文字属性等细粒度工具
- 上述生产工具全部满足且真实 `ps_health` pass → CAPABILITY_PRECHECK PASS
- server 已配置但 tools 不可见 → 提示完全重启 Codex，保存 checkpoint
- 只有旧版七工具 POC、缺少导出或高级编辑能力 → FAIL，进入 CAPABILITY_BOOTSTRAP
- 没 server / COM 不可用 → CAPABILITY_BOOTSTRAP

正式生产禁止 Computer Use fallback。

Canary 缓存键必须包含 Photoshop 版本、MCP server 标识、tool inventory SHA-256 和 Skill 版本。缓存键不变时可复用，避免每个项目重复完整测试。
