# Agent Rules — Sci PS Skill v5.0

1. 所有用户可见自然语言统一使用简体中文。
2. 用户不应被要求理解内部文件结构；内部资源由 Skill 自动路由。
3. 每次开始/继续都先读 `project_state.json`，避免重复阶段。
4. 没有 Photoshop MCP 能力不得进入正式 Photoshop 构建。
5. 参考图只能出现在 `99_REFERENCE_OVERLAY`，不得参与最终成品导出。
6. 禁止正式构建使用 reference tile / reference patch / 整图拼块 baseline。
7. 组件包一旦验证通过，必须直接逐项导入真实组件并验证 transform。
8. 每一 Photoshop build step 必须至少新增一个可验证的背景层、组件层、文字层、路径层、效果层或图层组。
9. 连续两轮 build 没有新增 `VERIFIED_COMPONENT_PLACEMENT` 或 `VERIFIED_LAYER_INCREMENT`，立即 `BUILD_LOOP_DETECTED = TRUE` 并暂停。
10. 图片组件核心形态错误应返回组件阶段修复；轻微颜色/亮度/边缘/glow/位置问题可在 Photoshop 修复。
11. 文字、简单箭头、路径、虚线框、简单电路、基础 shape、渐变、常规 glow/shadow 优先 Photoshop 原生构建。
12. Web Image2 按通用 MD 从 STAGE 1 / 6 开始，先完成动态语义识别与 `CONTENT_SEMANTIC_LOCK`，再完成组件规划、分批生成、QA 与交接；Codex 不得预先执行语义锁定、拆分参考图或动态生成项目专用 MD。
13. 科研图语义问题必须动态从当前参考图生成，禁止继承历史案例固定问题。
14. Web Stage 1 必须先识别图像类型，并且无论置信度多高都要等待用户明确确认后才能设置 `CONTENT_SEMANTIC_LOCK = TRUE`。
15. 旧版七工具 Photoshop POC 不等于生产能力；缺少 PNG 导出或高级编辑能力时必须 fail closed，不得进入构建。
16. 组件变换必须把 Alpha 主体目标换算为整层 `tool_target_layer_bounds`，不得直接把 `target_bbox` 传给图层变换。
17. 最终交付必须同时有真实 Photoshop state、隐藏参考层证据、当前参考/导出文件哈希和像素比较证据；只填写报告布尔值无效。
18. Photoshop 最终 QA 必须执行参考图差异定位与修正闭环；存在任何已知实质差异时不得进入交付。
19. Web 组件统一使用 `ASSET_CROP`；不得因素材画布、素材内位置或素材内尺度不同于参考图而返修，最终缩放、定位、布局和视觉融合由 Photoshop 完成。
20. 图片组件必须优先采用用户有权使用的精确来源并记录 provenance；正式导入必须是 Smart Object。
21. 需要抠图与局部融合时必须使用真实图层蒙版；旋转、倾斜和透视不得用普通矩形缩放冒充。
22. 像素比较失败后必须生成区域级差异定位；只有唯一归因且白名单内的高置信度修正才可自动执行，每次执行后必须重新比较。
23. 所有分析和交接规则必须适用于任意参考图，禁止把历史案例中的品牌、文字、科研名词或组件写死。
24. 缺少准确字体/素材的艺术字、字标或 Logo 只有在用户明确接受不可编辑栅格重建后才能交给 Image2；普通文字仍须保持可编辑。
25. 缺少准确字体时，必须先从 Photoshop/系统已有字体中给出相近候选和差异，由用户决定是否替代；用户不接受后才询问是否检索开源字体。打包字体必须包含可信来源、许可证和 SHA-256。字体安装必须再次获得明确同意，并在 Photoshop 中按 PostScript 名称验证。
26. 对明显手绘/扁平矢量参考仅允许提示性询问一次 Illustrator 或现成矢量源；不可用时不得阻塞，Photoshop 无法稳定原生完成的复杂元素统一回退到 Image2。
27. Photoshop 是最终高级视觉处理中心，必须承担蒙版、遮挡、材质融合、光效、阴影、渐变、背景环境光场、局部调整与整体调色。
28. 局部修改必须按稳定 layer ID 与完整父路径定位；同名歧义、上层全画布遮挡和用户已锁定/延期的修改类别必须先处理。
29. `USER_REVIEW`、`FINAL_EXPORT`、`DONE` 必须通过状态一致性门禁；用户定向改编不得冒充参考图精确匹配。
30. Web 最终压缩前必须生成 `PHOTOSHOP_RECONSTRUCTION_MASTER_PROMPT_ZH.md`；Codex 构建前必须读取，并按明确的自底向上图层顺序执行逐层隔离对比、相邻层融合检查和三层级最终验收。
31. 轮廓完整清晰、无遮挡、分辨率足够且背景可分离的参考图元素可归入 `REFERENCE_EXTRACTION`；ZIP 交接闭合路径和证据，验证通过后 Photoshop 必须先完成抠取，再进入常规构建。
32. 普通文字不得以参考图抠取替代可编辑文字；标题、字标或 Logo 只有在用户明确接受不可编辑栅格结果后才可抠取。抠取失败必须按 manifest 回退，不得把污染边缘带入最终 PSD。
33. 最终 QA 后必须把所有 Image2 图片组件层和参考图抠取层逐项导出为裁紧画布的真透明 PNG，统一放入 `05_output/transparent_elements/`，生成来源索引并验证通过后才能交付。
