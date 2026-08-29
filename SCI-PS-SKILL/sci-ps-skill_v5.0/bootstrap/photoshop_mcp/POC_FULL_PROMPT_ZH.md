# Photoshop MCP / COM 生产能力 POC — 完整验收版

必须证明：Codex → MCP stdio server → Python/pywin32 → Windows COM → Photoshop。
禁止 Computer Use、pyautogui、AutoHotkey、鼠标键盘模拟。

阶段 1/5 环境：Windows / Python / Photoshop / pywin32 / Codex MCP config。
阶段 2/5 COM 直连：创建 1200×800/72ppi 文档；导入 400×300 test PNG；精确 transform 到 x=150,y=180,w=500,h=375，误差≤1px；创建可编辑文字 `MCP CONTROL VERIFIED` 36pt；保存未扁平化 PSD；反向读取验证。
阶段 3/5 建 stdio MCP server，tools 至少：ps_health, ps_list_fonts, ps_create_document, ps_place_image, ps_place_smart_object, ps_transform_layer, ps_transform_layer_advanced, ps_apply_layer_mask, ps_create_text, ps_execute_jsx, ps_get_state, ps_save_psd, ps_export_png, ps_close_document。必须使用本目录附带的生产版 server/backend，或功能等价且经过验证的实现。
阶段 4/5 重启/刷新后，必须由 Codex 真调用这些 MCP tools 重新创建 `MCP_PHOTOSHOP_POC_FINAL`；通过 `ps_execute_jsx` 创建组、修改透明度/可见性、设置文字颜色并读取递归状态，再真实导出 PNG。禁止绕过 MCP。
阶段 5/5 只有所有 VERIFIED=YES 且 COMPUTER_USE_USED=NO 才可 PASS。

兼容提示：
- Photoshop early-bound typelib 可能使用 `layer.id` 而 dynamic binding 使用 `layer.ID`，统一做兼容 getter。
- create_document 验证必须直接读 Document 宽高/分辨率，不得依赖 layer id。
- `RulerUnits` pixels 值通常为 1；不要误把 `TypeUnits=2`。文字单位优先保持当前有效值并以可编辑文本验收为准。
