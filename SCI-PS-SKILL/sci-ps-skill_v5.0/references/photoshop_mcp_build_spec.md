# Photoshop MCP Build Spec

## 目标
组件包通过后直接真实构建，不做 reference baseline 拼块。

Photoshop 是最终视觉合成与高级效果中心。Image2 提供基础组件，Photoshop 必须负责最终缩放定位、前后层级、真实蒙版、遮挡、材质融合、接触阴影、反射、高光、外/内发光、渐变、背景环境光场、局部调整和整体调色，而不是只完成素材拼装。

## 组件规则
- `REFERENCE_EXTRACTION`：组件包验证后、其它正式图层构建前，从参考图原始像素工作副本按已验证闭合路径复制为独立透明图层；完成后不得在生产组保留整幅参考图副本。
- 抠取层必须保留参考图 SHA-256、闭合路径、边缘处理参数、资格证据和失败回退路线。规格不完整时 fail closed，不允许临场随意框选。
- 抠取后先在 100% 与 200%–400% 核对轮廓、背景残留、锯齿、白边/黑边、缺口和相邻像素污染；失败时按 manifest 回退到 Photoshop 原生或 Image2。
- 真透明 `ASSET_CROP` PNG：直接 Place/Import，验证 alpha，不要求素材画布与参考图同尺寸，也不要求素材内位置/尺度与最终画面一致。
- Alpha 失败：才做 mask/defringe/cleanup。
- 核心形态错误：退回组件阶段。
- 轻微颜色、亮度、边缘、glow、位置：Photoshop 修。

## 背景规则
优先 Photoshop 原生：solid/gradient/radial glow/noise/vignette/local atmosphere。
不得自由再生成一张新背景冒充。

## Transform
目标坐标统一 document pixels top-left。`target_bbox` 是 Photoshop 最终布局目标；`source_content_bbox` 只描述 PNG 内有效主体。通过这两个 bbox 计算缩放和位移，不得把素材图中的初始位置或尺度当成最终位置。
每个组件：
1. 以 Smart Object place，保留原始组件来源与可替换性
2. read bounds
3. compute scale
4. transform
5. read bounds
6. translate
7. read bounds
8. correction pass（最多一次）
9. tolerance pass → `PLACEMENT_VERIFIED=TRUE`

所有运行期修改使用稳定 layer ID + full parent path；名称仅用于显示。发现同名图层时禁止仅按名称修改。修改前检查目标与父组可见性，并检测目标上方是否存在可见的全画布不透明层。

缩放策略：

- `allow_warp = false`：使用 `UNIFORM_FIT_TARGET_BBOX`，保持宽高比并在目标框内居中；
- `allow_warp = true`：使用 `FREE_TRANSFORM_TO_TARGET`，允许分别调整横纵比例，并执行 manifest 明确记录的 rotation/skew/perspective；禁止把非等比缩放冒充透视或 warp；
- `build_manifest.json` 必须记录 `transform_plan`、`placement_expected_bounds`、`source_pixel_size` 和 `tool_target_layer_bounds`；只有 `tool_target_layer_bounds` 可直接传给矩形变换工具，避免透明留白导致主体错位；
- Photoshop 执行与 bounds 验证必须读取同一份 transform plan，禁止各自重新猜测。
- 运行 `generate_mcp_action_queue.py` 生成确定性执行队列；每个实质动作后读取真实 Photoshop state，失败即停，不得跳步。
- 每个 native spec 必须先由 `compile_native_element.py` 编译成具有完整参数的 `ps_execute_jsx` 动作；出现不支持的类型或缺少参数时生成队列必须失败，禁止保留占位动作。
- 使用 `execute_mcp_action_queue.py` 通过 stdio MCP 顺序执行全部动作并写入 `06_logs/mcp_execution_log.json`；队列未完整执行不得进入 QA。
- 需要抠图或局部融合时使用真实 layer mask；mask 文件、feather、density、invert 必须进入 `mask_plan` 并由 `ps_apply_layer_mask` 执行，不得擦除像素冒充蒙版。
- 曲线和曲线箭头必须保留 Photoshop PathItem。组件必须保留 `source_provenance`；有准确素材时禁止生成式替代。
- 缺少准确字体时，先调用 `ps_list_fonts`，按字形类别、字重、宽度和风格给出最接近的已安装候选及差异，等待用户选择；不得静默替换。用户不接受后才进入开源字体检索。项目字体必须先通过文件头、SHA-256、来源和许可证验证；只有用户明确同意后才可安装到当前 Windows 用户。安装后再次调用 `ps_list_fonts` 并运行 `verify_project_fonts.py`，缺少任一选定 PostScript 名称不得开始对应文字层构建。
- 经用户明确接受的艺术字、字标或 Logo 栅格重建按普通 Smart Object 图片组件处理，并保留 `editable_text=false` 证据；普通正文和标签不得栅格化。

## 参考图
只在 `99_REFERENCE_OVERLAY`：Normal 35% + Difference copy。
最终 QA/导出必须隐藏。

## 自底向上的逐层隔离校准

构建前必须读取已验证组件包中的 `PHOTOSHOP_RECONSTRUCTION_MASTER_PROMPT_ZH.md`，结合 manifest 建立唯一、明确的自底向上图层栈。主提示词用于补充视觉判断和高级处理方法，不得覆盖 manifest 的确定性字段、用户决定、能力门禁或真实 Photoshop 状态。

每个生产图层或具有独立视觉职责的效果层都必须完成以下闭环后，才能继续下一层：

1. 确认目标 layer ID、完整父路径、预期上下层和遮挡关系；
2. 暂时隐藏无关生产图层，只保留当前层、参考图，以及判断接触/遮挡所必需的相邻层；
3. 在 Normal overlay、Difference 和轮廓对齐视图中核对形状、大小、位置、旋转、透视和边缘；
4. 核对颜色、亮度、饱和度、透明度、混合模式、模糊、光效、阴影、反射和材质；
5. 不一致时使用 transform、warp、mask、opacity、blend mode、blur、shadow、glow 或 clipped adjustment 修正，并重新对比参考图；
6. 恢复必要的上下层，检查遮挡、接触边缘、重叠、反射、投影和过渡，不得只凭孤立图层正确就判定通过；
7. 记录该层的比较结果与修正，读取真实 Photoshop state，确认当前层仍处于正确层级后再进入下一层。

几何校准时应尽可能隔离当前层；关系校准时必须恢复相关相邻层。用于对比而临时改变的可见性必须在检查后恢复，参考图仍只能位于 `99_REFERENCE_OVERLAY`。

## 最终一致性修正闭环

构建完成后不得直接交付。必须循环执行：

1. 在完整画布下比较整体构图、比例、位置、层级和色调；
2. 使用 Normal overlay 与 Difference 对照定位偏差；
3. 在 100% 检查清晰度和边缘，在 200%–400% 检查细节、蒙版、光晕和微结构；
4. 把每处差异归类并采用对应修正：
   - 位置、尺寸、透视、形变 → transform / warp / perspective correction；
   - 透明度、叠加关系 → opacity / blend mode / layer order；
   - 模糊、景深、柔化 → blur radius / mask feather / depth treatment；
   - 光效、反射、阴影 → glow / highlight / shadow / local dodge-burn；
   - 色相、饱和度、亮度、对比度 → clipped adjustment layers / curves / levels / color balance；
   - 边缘、抠图、透明杂边 → mask cleanup / defringe / edge color correction；
   - 文字 → 内容、字体、字号、字距、行距、对齐逐项修正；
   - 遗漏或核心形态错误 → 补建 Photoshop 原生元素，或退回 Web 组件阶段返修；
5. 每次修正后重新比较，不得凭记忆判断；
6. 隐藏参考图层，确认成品自身完整；
7. 用 `ps_export_png` 导出无参考图层的最终渲染，运行 `compare_rendered_output.py` 生成带文件 SHA-256 和像素指标的证据；默认阈值为像素精确一致。只有用户明确接受视觉容差时才能传入非零阈值，并把该决定写入报告；
8. 用 `verify_photoshop_build_state.py --final` 证明参考图层在真实 Photoshop 状态中不可见；
9. 仍有已知可见差异、像素证据失败或证据哈希不一致时，`FINAL_VISUAL_MATCH = FALSE`，不得交付；
10. 只有目标尺寸、细节检查、实际状态和像素证据同时通过时，才能设置 `FINAL_VISUAL_MATCH = TRUE`。

最终验收必须把每个主要图层和形状逐项对应回参考图，并同时检查三个层级：单图层几何与质感、相邻图层之间的遮挡/接触/过渡、完整画布的色调与空间融合。重点筛查元素交叠处、接触处、透明边缘、背景过渡和景深关系；发现生硬拼贴、错误遮挡或不自然过渡时，必须判断是否需要抠图裁剪、真实蒙版遮盖、局部阴影/光效、模糊、透明度、混合模式或局部曲线调整，修正后重新比较。

每次像素比较失败后必须运行 `localize_visual_differences.py`，生成带区域 bbox、候选图层、差异类别和置信度的 `difference_localization.json`。只有目标图层唯一且修正类型属于确定性白名单时，`generate_correction_queue.py` 才可生成自动修正；模糊归因、核心形态、文字内容、Logo 或科研语义差异必须进入模型/人工诊断，不得盲改。执行修正队列后重新导出、比较和定位；连续两轮指标无改善时暂停。

“完全一致”指在目标输出和上述细节检查中不存在已知的、肉眼可辨或影响语义/结构/视觉效果的差异。不得在仍能指出差异时声称完全一致或完成交付。

如果用户明确要求偏离参考图进行艺术指导，记录 `FINAL_USER_DIRECTED_RESULT`、批准原文和允许偏离范围。该结果与 `FINAL_VISUAL_MATCH` 分开；不得用艺术指导通过替代参考图一致性结论。

每个发现过的差异及其修正方式必须记录到 `04_photoshop/qa/VISUAL_DIFFERENCE_REPORT.json`。完成后运行 `scripts/validate_final_qa.py`；脚本未通过时不得设置 `FINAL_VISUAL_MATCH = TRUE`。

## 统一透明元素资产库

最终 QA 通过后，从最终 Photoshop 图层状态导出所有 `component` 与 `reference_extraction` 图层。每个元素单独裁紧透明画布，输出到 `05_output/transparent_elements/`；文件名必须包含来源类别和稳定 ID。生成 `transparent_elements_manifest.json`，记录 layer name、source class、原始 provenance、文件名、像素尺寸和 SHA-256。导出不得混入参考图、背景或无关相邻层。运行 `validate_transparent_asset_library.py`，元素数、PNG 解码或有效 Alpha 任一失败时不得最终交付。

## 进度计数
必须维护：
- background_verified / total
- image_components_verified / total
- text_verified / total
- paths_verified / total
- effects_verified / total
- verified_layer_count
