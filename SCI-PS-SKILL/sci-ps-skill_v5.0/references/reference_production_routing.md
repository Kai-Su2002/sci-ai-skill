# Reference Production Routing

This is a non-blocking hint after the reference is saved. It does not perform semantic locking, component planning, or extraction in Codex and does not add a new state.

## Route hint

- Predominantly 3D render, photography, complex material, transparent liquid, dense particles, or microstructure: recommend Web GPT/Image2 for clean transparent base components.
- Predominantly hand-drawn, flat illustration, closed outlined shapes, or node-editable vector art: ask once whether the user already has Illustrator or usable SVG/AI/PDF assets.
- Mixed reference: divide by production suitability. Photoshop-native items remain native; complex objects go to Image2 unless an accurate user-owned vector source is supplied.

Use this short Chinese prompt when relevant:

> 检测到部分元素更适合使用矢量工具制作。你是否已有 Illustrator 工具或可用的 SVG/AI/PDF 矢量素材？如果没有，这些 Photoshop 不适合稳定原生绘制的元素将默认交给 Image2 生成透明组件，不影响后续流程。

Do not require Illustrator, do not request installation, and do not pause waiting for it. No answer means `VECTOR_TOOL_AVAILABLE = FALSE` and the fallback is Image2.

## Default ownership

Photoshop-native: editable text, simple geometry, ordinary paths/arrows, dashed frames, simple circuits, gradients, masks, shadows, glows, background light fields, local adjustments, and final grading.

Image2 fallback: complex hand-drawn subjects, irregular cartoon forms, dense line art, high-complexity vector-like illustration without a source file, 3D rendered subjects, liquids, complex materials, microstructures, and anything the available Photoshop production tools cannot build reliably.

Image2 should normally deliver clean base components. Global lighting, contact shadows, environmental color, background gradients, and cross-object integration belong to Photoshop unless they are inseparable intrinsic properties of the component.
