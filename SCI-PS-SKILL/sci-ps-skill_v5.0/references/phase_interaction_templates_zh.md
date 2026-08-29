# 阶段交互模板

每次回复开头统一：
```text
【当前任务状态】
阶段：{STATE}
进度：{CURRENT}/{TOTAL 或阶段描述}
已完成：{摘要}
当前阻塞：{无 / 具体阻塞}
下一动作：{唯一下一步}
```

同一连续执行回合只需在阶段变化、出现阻塞或完成实质批次时输出一次完整状态块；局部工具调用之间使用简短进度更新，避免重复模板淹没用户。

如果需要用户动作，再追加：
```text
【你现在只需要做】
1. ...
2. ...
完成后回来告诉我： “继续” / “组件包已放入”
```

Photoshop build 阶段必须额外显示：
```text
背景：x/y
图片组件：x/y
文字：x/y
路径/箭头：x/y
效果：x/y
已验证真实 Photoshop 图层：x/y
```

## 全场景回复模板

以下模板用于保持用户体验一致；只显示当前相关的一种，不要一次向用户倾倒全部内部状态。

### 新项目：能力通过

```text
【当前任务状态】
阶段：PROJECT_INIT
能力状态：生产能力 PASS
已完成：真实工具清单、ps_health 与 production canary 已验证
当前阻塞：无
下一动作：接收并保存参考图与项目要求

【你现在只需要做】
上传参考图，并告诉我目标尺寸、最终文案、Logo 和字体要求；没有的项目可以直接说“无”。
```

### 能力缺失或 Codex 重启

```text
【当前任务状态】
阶段：CAPABILITY_BOOTSTRAP
能力状态：FAIL / TOOLS_NOT_VISIBLE
当前阻塞：{缺失工具或 canary 失败项}
下一动作：{安装生产 MCP / 完全重启 Codex}

【你现在只需要做】
{唯一手动步骤}
完成后回来告诉我：“继续”
```

### 可选矢量路线提示

```text
检测到部分元素更适合使用矢量工具制作。你是否已有 Illustrator 工具或可用的 SVG/AI/PDF 矢量素材？如果没有，这些 Photoshop 不适合稳定原生绘制的元素将默认交给 Image2 生成透明组件，不影响后续流程。
```

此问题只出现一次且不阻塞；用户未回答时按“没有”继续。

### Web/Image2 交接准备完成

```text
【当前任务状态】
阶段：WAIT_IMAGE2_HANDOFF
已完成：参考图和 Skill 内置通用 MD 已准备
当前阻塞：等待网页版完成六阶段组件交接
下一动作：上传以下两个文件到新的 Web GPT/Image2 对话

1. {reference_path}
2. {universal_prompt_path}

网页版必须从 STAGE 1 / 6 — REFERENCE ANALYSIS 开始，并在最终压缩前生成项目专用的 `PHOTOSHOP_RECONSTRUCTION_MASTER_PROMPT_ZH.md`。完成后把 COMPONENT_HANDOFF.zip 放到：
{inbox_path}

回来只需要告诉我：“组件包已放入”
```

### 纯 Photoshop 原生项目

```text
【当前任务状态】
阶段：PHOTOSHOP_BUILD_PRECHECK
已完成：语义与原生元素计划已确认；图片组件 0 个
当前阻塞：无
下一动作：直接生成 Photoshop 原生构建清单和动作队列
```

### 重复提交同一组件包

```text
组件包 SHA-256 与已验证版本一致，无需重复解压或验证。我会从当前第一个未完成动作继续。
```

### 组件包通过

```text
【当前任务状态】
阶段：PHOTOSHOP_BUILD_PRECHECK
已完成：组件包完整性、Alpha、manifest、批次状态和来源验证通过
当前阻塞：无
下一动作：生成 build manifest 与 MCP action queue
```

### 组件包失败

```text
【当前任务状态】
阶段：COMPONENT_PACKAGE_VALIDATION
当前阻塞：{Cxxx / 文件名 / manifest 字段} 未通过
下一动作：只修复该项，不修改已批准组件

【你现在只需要做】
回到原 Web/Image2 对话，修复：{明确修复要求}
重新打包后覆盖 {inbox_path}，回来告诉我：“组件包已放入”
```

### 字体需要决定

```text
当前缺少准确字体。Photoshop 已安装候选为：{候选与差异}。
请选择是否接受其中一个；我不会静默替换。若都不接受，我再询问是否检索有许可证的开源字体。
```

### Photoshop 构建进行中

```text
【当前任务状态】
阶段：PHOTOSHOP_REAL_BUILD
背景：x/y
图片组件：x/y
文字：x/y
路径/箭头：x/y
效果：x/y
已验证真实 Photoshop 图层：x/y
当前阻塞：无
下一动作：{唯一构建批次}
```

### 修改被上层遮挡

```text
目标图层已定位，但其上方存在可见的全画布不透明层 `{layer_path}`，当前修改不会在画布中显示。我会先保持目标效果参数不变，处理图层顺序或遮挡关系，而不是盲目加深颜色。
```

### 同名图层歧义

```text
检测到多个同名图层 `{name}`，无法安全判断目标。已停止修改，未改变 PSD。需要依据图层 ID、完整父组路径或用户当前选择确认唯一目标。
```

### Bad Request / 请求过大

```text
本次 Photoshop 请求未执行，分类为：{REQUEST_PAYLOAD_OR_ARGUMENT_INVALID / JSX_REQUEST_TOO_LARGE / TIMEOUT / TARGET_LAYER_NOT_FOUND}。
已完成动作：x/y；未重复执行已提交动作。
下一动作：{拆分请求 / 修正参数 / 恢复活动文档 / 重新定位图层}
```

### 构建循环保护

```text
【当前任务状态】
阶段：PHOTOSHOP_REAL_BUILD
当前阻塞：连续两轮没有新增已验证图层或组件位置
状态：BUILD_LOOP_DETECTED = TRUE
下一动作：检查目标图层、活动文档和失败动作；不会继续盲目重试
```

### QA 未通过

```text
【当前任务状态】
阶段：BUILD_QA
FINAL_VISUAL_MATCH = FALSE
已定位差异：{区域、类别、候选图层、置信度}
下一动作：{高置信度确定性修正 / 暂停等待语义或素材决定}
```

### 用户定向艺术调整

```text
本轮属于用户定向视觉调整，不再宣称与原参考图逐像素一致。我会保留参考图作为结构与内容基线，记录允许偏离范围，并继续验证尺寸、图层结构、参考层隐藏、真实 Photoshop 导出和用户指定视觉目标。
```

### 用户要求暂停某类修改

```text
已记录 `{CATEGORY} = DEFERRED_BY_USER`。后续自动 QA 不会继续修改该类别，除非你明确解除。
```

### 用户局部修订

```text
已锁定本轮范围：{目标组/图层/属性}。
不会修改：{受保护区域或类别}。
我会先保存局部 checkpoint，完成修改后验证真实图层变化和新导出结果；若结果变差，只回退本轮修改。
```

### QA 通过并请求验收

```text
【当前任务状态】
阶段：USER_REVIEW
状态：{FINAL_VISUAL_MATCH = TRUE / FINAL_USER_DIRECTED_RESULT = TRUE}
已完成：真实 Photoshop 导出、文件哈希、参考层隐藏、图层状态与对应 QA 门禁
下一动作：请检查最终预览并决定是否验收或提出局部修改
```

### 最终交付

```text
【当前任务状态】
阶段：DONE
已完成：用户验收、最终 PSD 与 PNG 导出
参考图层：已隐藏
PSD：{path}
PNG：{path}
```

### 暂停、恢复与查看进度

```text
暂停：已保存当前状态和最近 checkpoint，不推进阶段。恢复时说“继续”。
恢复：已读取 project_state、日志和文件哈希，将从第一个未完成合法动作继续。
查看进度：只显示当前阶段、完成数量、阻塞和唯一下一步，不执行 Photoshop 修改。
```
