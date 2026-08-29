# Web Image2 Handoff Policy

Codex 接收并保存参考图后，不在本地执行语义锁定或组件拆分，不建立 component plan / batch plan，不动态生成 `PROJECT_IMAGE2_COMPONENT_TASK_ZH.md`。

保存参考图后只允许给出一次非阻塞生产路线提示。对明显手绘/扁平矢量风格仅询问用户是否已有 Illustrator 或 SVG/AI/PDF 源文件；Illustrator 不是依赖。用户没有、未回应或不希望使用时，所有 Photoshop 无法稳定原生制作的复杂元素默认由 Image2 生成透明组件，流程不得暂停。

组件边界必须同时考虑第三条路线 `REFERENCE_EXTRACTION`：若元素在参考图中轮廓完整清晰、没有实质遮挡、分辨率足够、背景可可靠分离，并且抠取不会带入相邻对象，可不让 Image2 重新生成。Web 只交接闭合路径/蒙版规格、目标 bbox、边缘处理参数、资格证据与失败回退路线；ZIP 中不为该元素生成 PNG。透明、毛发、烟雾等复杂边缘、遮挡元素、背景污染严重或低分辨率元素不得勉强抠取。

普通正文、数据和标签仍保持 Photoshop 可编辑文字。标题、艺术字、字标或 Logo 只有在用户明确接受“从参考图抠出的栅格结果不可编辑，且精度受参考图分辨率限制”后才允许进入 `REFERENCE_EXTRACTION`，并保存确认原文。

用户交给 Web GPT/Image2 的只有：
1. `reference_master.*`
2. `02_component_handoff/OUTBOUND/UNIVERSAL_IMAGE_COMPONENT_EXTRACTION_PROMPT_ZH_V2.md`

必须由 `scripts/copy_reference_to_outbound.py` 自动把参考图和通用 MD 一起准备到 OUTBOUND；不得要求用户寻找 Skill 安装目录。

网页版必须从 `STAGE 1 / 6 — REFERENCE ANALYSIS` 开始：先识别图像类型，再完成动态语义识别；无论置信度多高，都必须向用户展示图像类型、语义清单和“Image2 生成 / Photoshop 原生制作”的初步边界。只有用户明确确认后才能设置 `CONTENT_SEMANTIC_LOCK = TRUE`，再按通用 MD 完成组件分析、计划、分批生成、全局检查和 Codex 交接。

网页版只增加精确来源门禁：用户提供的 Logo、字体、SVG、照片、科研素材和其它可合法使用的原始文件优先直接交接；只有没有准确来源时才允许 Image2 重建。每个组件必须写入 `source_provenance`，但不得改变六阶段流程或重新要求组件保持最终画布位置与尺度。

所有规则必须面向任意参考图，禁止写入或继承特定品牌、标题、科研名词、产品名或历史案例组件。缺少准确字体时，先列出 Photoshop/系统现有字体中的相近候选及差异并让用户决定是否替代；不得静默替换。用户不接受现有字体后，才询问是否检索开源字体；用户同意后才能检索并打包许可证证据。现有字体与开源字体均不合适时，缺少准确素材/字体的艺术字、字标或 Logo 可在用户明确接受“不可编辑栅格重建”后作为 Image2 透明组件；普通正文和需编辑标签仍必须留给 Photoshop 文字层。

Image2 必须在最终压缩前，根据已锁定语义、组件计划、批次结果、组件 QA、原生元素清单和参考图，生成项目专用的 `PHOTOSHOP_RECONSTRUCTION_MASTER_PROMPT_ZH.md`。该文件必须总结完整视觉系统，并给出 Photoshop 自底向上的图层顺序、逐层隔离对比方法、遮挡与融合关系、蒙版/阴影/光效/虚化/透明度/混合模式/局部调整/整体调色方案，以及逐层、关系级和整体画布验收步骤。它是 Codex 后续执行的专业视觉简报，不得伪造未测量的精确参数，也不得覆盖 manifest、用户确认或真实 Photoshop 状态。

Image2 最终交回：包含上述主提示词的 `COMPONENT_HANDOFF.zip`。

Image2 组件应尽量是干净的主体基础。除非属于对象不可分离的固有特征，不要把全局环境光、接触阴影、背景渐变、整体 Bloom 或跨对象光照烘焙进组件；这些由 Photoshop 在最终排布后统一建立。
用户放入：`02_component_handoff/INBOX/COMPONENT_HANDOFF.zip`。
放入后返回 Codex，回复“组件包已放入”。
