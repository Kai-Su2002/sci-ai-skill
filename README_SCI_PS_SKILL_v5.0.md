# SCI PS SKILL v5.0

> **High-Fidelity Scientific Figure Reconstruction with Photoshop**  
> 从参考图分析、组件拆解与生成，到 Photoshop 逐层重建、终审 QA 与透明元素交付的一套科研绘图自动化工作流。

**Version:** 5.0  
**Manual:** 2026-08-29  
**License:** Proprietary / Source-Available — Authorization Required

---

## 这是什么？

**SCI PS SKILL** 是一套面向科研绘图、期刊封面、机制示意图与复杂视觉参考图复刻的自动化工作流。

它的目标不是“让 AI 随便生成一张看起来类似的图”，而是把参考图拆解为可管理的视觉组件，并通过 **Codex + GPT/Image2 + Photoshop** 完成：

- 参考图结构与语义分析
- 组件拆解与路线规划
- Image2 组件生成
- 参考图精确抠取
- Photoshop 原生文字 / 形状 / 渐变重建
- 组件包校验
- Photoshop 逐层构建
- Overlay / Difference / Blink 对照
- 遮挡、阴影、透明度、虚化与色调修复
- 最终人工复核
- 分层 PSD、最终 PNG 与透明元素库交付

最终重点不是“风格像”，而是尽可能做到：

> **位置一致、比例一致、轮廓一致、透视一致、层级一致、遮挡一致、色调一致、光影一致、透明度一致、局部过渡一致。**

---

## 适合做什么？

SCI PS SKILL 适合处理以下类型的视觉任务：

- 科研机制示意图
- Science / Nature 风格期刊视觉图
- 复杂科研封面复刻
- 3D 半写实科研元素拼装
- 多组件科研示意图
- 高保真参考图复现
- 需要最终保留可编辑 PSD 的科研图
- 需要把 AI 生成组件进一步做 Photoshop 精修的项目

对于规则化元素，优先使用 Photoshop 原生方式保留可编辑性，例如：

- 标题与普通文字
- 箭头
- 线条
- 几何形状
- 渐变
- 部分 Logo / 矢量元素

对于复杂材质或难以原生绘制的科研主体，则可交由 Image2 生成；对于轮廓完整、无遮挡且分辨率足够的元素，也可采用参考图精确抠取路线。

---

## 最终会得到什么？

完成一次完整项目后，目标交付包括：

### 1. 分层 PSD

背景、组件、文字、光效、阴影、蒙版等尽可能保留为独立、可继续编辑的 Photoshop 图层。

### 2. 最终 PNG

关闭参考图与检查图层后的干净成品。

### 3. 透明元素库

将批准的 Image2 组件与参考图精确抠取组件统一整理为透明 PNG。

默认输出目录：

```text
05_output/
└── transparent_elements/
```

### 4. 透明元素清单

生成：

```text
transparent_elements_manifest.json
```

用于记录元素来源、文件名、数量与校验信息。

### 5. QA / 复核证据

用于证明图层结构、像素差异、透明通道、遮挡关系和最终视觉结果已经经过检查。

---

# 工作流概览

```text
参考图 + 文案 + Logo/字体要求
              │
              ▼
      [A] Codex 项目启动
      Photoshop 能力预检
              │
              ▼
      [B] GPT/Image2 网页阶段
      参考图分析
          ↓
      语义锁定
          ↓
      路线规划
          ↓
      批次生成
          ↓
      组件复核
          ↓
      COMPONENT_HANDOFF.zip
              │
              ▼
      [C] 组件包交回 Codex
      清单 / Alpha / 路径 / 字体
      / Logo / 组件批准状态校验
              │
              ▼
      [D] Photoshop 逐层构建
      Background
          ↓
      Rear Elements
          ↓
      Main Objects
          ↓
      Foreground
          ↓
      Text / Vector
          ↓
      Light / Shadow / Mask
              │
              ▼
      [E] 最终人工复核
      Side-by-Side
      Overlay
      Difference
      Blink
      局部接触区 QA
              │
              ▼
      [F] 最终交付
      PSD + PNG + 透明元素库
```

---

# 开始前准备

建议提前准备：

| 项目 | 建议 |
|---|---|
| 参考图 | 尽量使用高清原图，不要先截图压缩 |
| 成品尺寸 | 提供像素宽 × 高；不确定时可由 Codex 读取 |
| 最终文案 | 标题、正文、数字、标签，并注明哪些必须可编辑 |
| Logo | 优先提供官方 PNG / SVG / AI |
| 字体 | 提供字体名或字体文件；缺失时由系统列候选并由用户确认 |
| Photoshop | 保持已安装且可正常启动 |
| Codex | 已安装本 Skill，并可正常执行项目工作流 |

---

# 快速开始

## Step 1：安装 Skill

按照项目提供的：

```text
INSTALL_PROMPT_ZH
```

在 Codex 中完成 Skill 安装。

安装成功后，启动项目时会先执行能力预检。

---

## Step 2：在 Codex 中启动项目

推荐输入：

```text
开始一个新的高保真复刻项目。
参考图在【路径】，
尺寸为【宽×高】，
最终文案为【内容】；
Logo 和字体要求为【说明】。
```

示例：

```text
开始一个新的高保真复刻项目。
参考图在 F:\Project\reference.png，
尺寸 3000×2000。
标题必须保持可编辑。
```

Codex 首先检查 Photoshop 生产能力。

如果能力检查失败，应根据 Codex 返回的安装、修复或重启提示处理，**不要绕过能力检查继续生产**。

---

# GPT / Image2 网页阶段

Codex 会准备一个 `OUTBOUND` 文件夹。

在新的网页版 GPT / Image2 对话中上传：

- 参考图
- 系统准备的通用 MD 文件

然后按照六阶段逐步执行。

## 六阶段

### 1. 参考图分析

确认：

- 图像类型判断
- 语义清单
- 元素边界
- 图层关系
- 视觉结构

如果语义错误，应在锁定前纠正。

### 2. 语义锁定

明确“每个元素到底是什么”。

只有用户确认后才能锁定。

### 3. 路线规划

每个元素选择最适合的制作路线：

| 路线 | 适合内容 |
|---|---|
| Image2 生成 | 复杂科研主体、材质、难以 Photoshop 原生绘制的视觉元素 |
| 参考图精确抠取 | 轮廓完整、无遮挡、分辨率足够的元素 |
| Photoshop 原生 | 文字、箭头、线条、几何形状、渐变等 |
| 官方素材 | Logo、字体、SVG、AI 或其他可信源文件 |
| 可选矢量路线 | 可结合 cell lct 等矢量绘图能力 |

### 4. 批次生成

逐批生成组件。

重点检查：

- 形状
- 视角
- 材质
- 透明背景
- Alpha
- 边缘质量

不合格组件应单独返修，不应整包重做。

### 5. 组件复核

组件只有经过批准，才允许进入最终交接包。

### 6. 打包

下载：

```text
COMPONENT_HANDOFF.zip
```

交接包应包含：

- 组件文件
- 组件清单
- 批准状态
- Photoshop 重建信息
- 字体 / Logo 说明
- 抠取规范
- 必要的重建提示

---

# 元素路线原则

## Image2 生成

适合：

- 复杂科研主体
- 半写实材质
- 复杂 3D 结构
- 难以 Photoshop 原生制作的视觉组件

检查重点：

- 结构是否正确
- 视角是否正确
- 背景是否真实透明
- 边缘是否存在黑边 / 白边
- 是否存在明显 AI 伪影

---

## 参考图精确抠取

适合：

- 边缘清晰
- 无明显遮挡
- 分辨率足够
- 可从背景分离

注意：

对于标题、艺术字、Logo 等内容，如果采用抠取路线，会成为 **栅格且不可编辑** 的元素。

因此必须经过用户明确同意。

---

## Photoshop 原生元素

优先用于：

- 正文
- 数字
- 标签
- 标题
- 箭头
- 规则线条
- 几何图形
- 渐变
- 可编辑的设计元素

目标是尽可能保留后期编辑能力。

---

# 标题、文字和 Logo 的处理规则

- 普通正文、数字和标签默认保留为 Photoshop 可编辑文字。
- 标题、艺术字、字标、Logo 只有在用户明确接受不可编辑栅格时，才可从参考图抠取。
- 对 Logo 精度要求较高时，优先提供官方文件。
- 字体缺失时，不允许系统擅自替换。
- 系统应列出已安装候选字体及差异，由用户确认后再使用。
- 如需安装新的开放字体，应先确认来源和许可。

---

# 组件包交回 Codex

将网页阶段下载的文件确认或重命名为：

```text
COMPONENT_HANDOFF.zip
```

然后放入：

```text
02_component_handoff/
└── INBOX/
```

回到原 Codex 项目对话，发送：

```text
组件包已放入
```

Codex 将检查：

- ZIP 路径安全
- 组件清单
- 组件批准状态
- Alpha / 透明通道
- 字体说明
- Logo 说明
- 抠取规范
- 文件完整性

如果验证失败，应只修复明确失败的组件。

例如：

```text
C007 透明通道不可用
```

则只回网页阶段修复 `C007`，不要重新生成已通过组件。

---

# Photoshop 逐层构建

当组件包验证通过后，进入 Photoshop 构建阶段。

此时使用项目配套的：

```text
PS 开始执行提示词.txt
```

推荐在 Codex 中输入：

```text
请进入 Photoshop 逐层构建阶段，并完整遵循以下辅助提示词：

【粘贴 PS 开始执行提示词.txt 全文】
```

## 构建核心原则

### 1. 从后到前

推荐顺序：

```text
Background
↓
Rear Atmospheric Effects
↓
Rear Objects
↓
Main Objects
↓
Secondary Objects
↓
Foreground
↓
Contact Shadow / AO
↓
Glow / Highlight
↓
Text / Vector
↓
Finishing
```

### 2. 每次只校准一个组件

每新增一个组件，应立即与参考图进行单独比对。

必要时临时关闭其它无关图层，只保留：

- 当前组件
- 必要定位对象
- 参考图

### 3. 必查项目

每个组件至少检查：

- Position
- Scale
- Shape
- Rotation
- Perspective
- Crop / Visible Area
- Opacity
- Blur
- Hue
- Saturation
- Brightness
- Contrast
- Highlight
- Shadow
- Glow
- Occlusion
- Transition

### 4. 对照方法

构建过程中推荐反复使用：

- `Side-by-Side`
- `50% Overlay`
- `Difference`
- `Blink Comparison`

### 5. 不通过不继续

当前组件与参考图之间仍存在明显偏差时，不应直接继续堆叠后续组件。

---

# 背景不是简单底色

背景应被视为一个需要独立 QA 的正式视觉层。

重点检查：

- 主色
- 渐变方向
- 渐变起点与终点
- 局部明暗
- 左上 / 右上 / 中央 / 下部区域色差
- haze
- vignette
- bloom
- 背景与主体的环境色关系
- 是否存在机械滤镜感
- 是否存在灰雾感
- 是否存在渐变断层

禁止仅使用一个简单全局滤镜掩盖背景问题。

---

# 遮挡与融合

最终图不能只是“把所有组件摆在正确位置”。

还必须建立正确的空间关系。

重点包括：

- 谁在前
- 谁在后
- 哪个部分被遮挡
- 哪个部分露出
- 接触阴影
- Ambient Occlusion
- 环境色
- 边缘软硬
- 透明度过渡
- 发光对邻近对象的影响
- 前后景虚化

必要时允许使用：

```text
Layer Mask
Vector Mask
Clipping Mask
Gradient Mask
Warp
Perspective
Distort
Curves
Levels
Hue/Saturation
Color Balance
Gaussian Blur
Blend If
Drop Shadow
Inner Shadow
Outer Glow
```

复杂遮挡关系允许拆分为：

```text
OBJECT_BACK
OBJECT_FRONT
```

以实现局部前后穿插。

---

# 最终人工复核

初版 PSD 已完成并输出预览后，再使用：

```text
最终人工复核提示词.txt
```

推荐输入：

```text
请基于当前 PSD 进入最终人工复核阶段，并完整遵循以下辅助提示词：

【粘贴 最终人工复核提示词.txt 全文】
```

## 最终 QA 重点

### 单层 QA

逐层检查：

- 位置
- 比例
- 角度
- 透视
- 轮廓
- 透明度
- 虚化
- 颜色
- 高光
- 阴影
- 辉光

### 元素关系 QA

重点检查：

- 遮挡
- 接触
- 接触阴影
- 环境色
- 局部 Alpha
- 边缘融合
- 拼贴感

### 区域 QA

将整图划分区域逐块检查。

### Overlay / Difference QA

最终至少执行：

1. Side-by-Side
2. 50% Overlay
3. Difference
4. Blink Comparison
5. 100% / 200% 接触区域检查

---

# 两个关键提示词的使用边界

| 当前状态 | PS 开始执行提示词 | 最终人工复核提示词 |
|---|---:|---:|
| 刚开始项目 | ❌ | ❌ |
| 网页分析 / 生成中 | ❌ | ❌ |
| ZIP 尚未验证 | ❌ | ❌ |
| ZIP 已验证，准备建 PSD | ✅ | ❌ |
| 初版 PSD 已完成 | 通常不重复 | ✅ |
| 只修改一个已知局部 | 通常不需要 | 通常不需要 |
| 大量组件更换并重建 | ✅ | 新初版完成后 ✅ |

> **不要把两个 TXT 一次性发送。**  
> 它们属于两个不同阶段：先构建，再终审。

---

# 透明元素最终整理

最终 QA 通过后，从最终 Photoshop 状态导出透明元素。

目录：

```text
05_output/
└── transparent_elements/
```

要求：

- 每个元素一个紧边界透明 PNG
- 保留来源类别
- 不将无关阴影或光效错误烘焙进元素
- 验证 PNG 可解码
- 验证 Alpha 可用
- 验证数量一致
- 验证 SHA-256
- 生成 `transparent_elements_manifest.json`

---

# 常见问题

## Photoshop 能力检查失败

按照 Codex 给出的安装 / 修复 / 重启方案处理。

不要跳过能力预检。

---

## 组件透明背景是假透明

只退回该组件。

要求重新生成真实 Alpha。

---

## 抠取元素存在遮挡或边缘不完整

不要强行抠取。

改为：

- Image2 重新生成
- Photoshop 原生重建
- 或其它更适合的路线

---

## Logo 不够精确

优先提供官方素材。

如果没有官方素材，则由用户明确决定是否接受栅格抠取。

---

## 字体缺失

从已安装候选中选择，或明确批准安装已验证的开放字体。

---

## 初版有明显拼贴感

重点检查：

- 图层顺序
- 遮挡
- Contact Shadow
- Ambient Occlusion
- 环境色
- 边缘软硬
- Blur
- Alpha
- Glow
- 背景融合

不要简单加一层全局 haze 解决。

---

## 两轮修正没有改善

停止盲调。

要求系统明确列出：

```text
BLOCKING_COMPONENT
CAUSE
CURRENT_LIMITATION
RECOMMENDED_ROUTE
```

只有核心结构确实无法通过 Photoshop 修复时，才返回组件重新生成。

---

# 最终验收清单

完成项应全部满足：

- [ ] 参考图没有出现在最终成品中
- [ ] PSD 为真实分层，没有被扁平化
- [ ] 普通文字保持可编辑
- [ ] 栅格标题 / Logo 已获得用户明确同意
- [ ] 主要元素位置接近参考图
- [ ] 主要元素比例接近参考图
- [ ] 主要元素角度与透视接近参考图
- [ ] 主要轮廓接近参考图
- [ ] 图层顺序正确
- [ ] 遮挡关系正确
- [ ] 接触区域不存在明显白边 / 黑边
- [ ] 不存在明显错误空隙或重叠
- [ ] 阴影与辉光方向合理
- [ ] 透明度与虚化匹配参考图
- [ ] 背景渐变与色差已经校准
- [ ] 元素与背景不存在明显拼贴感
- [ ] 最终 PSD 存在
- [ ] 最终 PNG 存在
- [ ] 透明元素库存在
- [ ] 透明元素清单与实际文件数量一致

---

# 推荐项目结构

实际项目可根据 Skill 当前版本调整，但建议保持类似结构：

```text
project/
├── 00_reference/
│   └── reference.png
│
├── 01_outbound/
│   └── web_handoff/
│
├── 02_component_handoff/
│   ├── INBOX/
│   │   └── COMPONENT_HANDOFF.zip
│   └── validated/
│
├── 03_photoshop/
│   └── working.psd
│
├── 04_qa/
│   ├── previews/
│   ├── difference/
│   └── reports/
│
└── 05_output/
    ├── final.psd
    ├── final.png
    ├── transparent_elements/
    └── transparent_elements_manifest.json
```

---

# 核心设计哲学

SCI PS SKILL 的目标不是让 AI “自由设计”，而是建立一个可控的科研绘图生产过程。

核心原则：

> **Reference is Ground Truth.**

任何时候都优先回答：

- 它和参考图的位置是否一致？
- 它和参考图的大小是否一致？
- 它和参考图的形状是否一致？
- 它的透明度是否一致？
- 它的阴影是否一致？
- 它的光效是否一致？
- 它和周围元素的遮挡关系是否一致？
- 它和背景之间是否真正融合？

而不是：

> “现在是不是更好看？”

---

# License & Usage

## Important

This repository is **not released under an open-source license**.

Unless you have obtained prior written authorization from the copyright holder, the source code, prompts, workflows, skills, documentation, assets, and derivative materials in this project are provided for **viewing and evaluation only**.

Without authorization, you may not:

- use the Skill in production
- redistribute it
- modify and redistribute it
- repackage it
- sell it
- provide it as a paid service
- integrate it into commercial software
- expose it through SaaS / API services
- create commercial derivative products
- sublicense it to third parties

Academic, educational, internal enterprise, collaborative, and commercial use should obtain authorization from the copyright holder first.

> **Commercial use requires a separate commercial license.**

Please see the repository `LICENSE` file for the complete terms.

---

## 中文授权说明

本项目**不是传统意义上的开源项目**。

仓库中的源码、Prompt、工作流、Skill、文档、资产及相关衍生材料公开的主要目的为：

- 项目展示
- 技术交流
- 功能评估

未经版权所有者事先书面授权，不得：

- 实际部署使用
- 复制传播
- 修改后二次发布
- 重新打包
- 出售
- 商业化使用
- 集成到其它软件
- 作为 SaaS / API 服务提供
- 制作商业衍生产品
- 向第三方再次授权

科研、教学、企业内部、合作项目及商业用途，均建议先联系作者获得授权。

**商业使用需单独取得商业许可。**

完整授权条款请以仓库根目录中的 `LICENSE` 文件为准。

---

# Version

Current documented version:

```text
SCI PS SKILL v5.0
2026-08-29
```

---

# Notes

- 本项目依赖不同阶段的 AI、Photoshop 与外部工具能力，具体可用性取决于实际运行环境。
- Photoshop、Science、Nature 等名称及商标归各自权利人所有。
- 本项目与上述第三方品牌不存在官方隶属或背书关系。
- 使用外部字体、Logo、图片与其它受版权保护素材时，请确保拥有合法使用权。

---

## 一句话总结

> **给 SCI PS SKILL 一张参考图，不是让 AI 猜着画，而是让它拆、生成、验证、进 Photoshop、逐层对齐、逐层修复，最后交付真正可继续编辑的高保真 PSD。**
