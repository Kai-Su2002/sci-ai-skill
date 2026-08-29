# Advanced Photoshop Native Elements

All items require `bbox`, `opacity`, `blend_mode`, and `parameters`.

- `TEXT`: `text`, `font`, `font_size`, `color`, `alignment`, `tracking`, `leading`; optional `direction`, `anti_alias`, `horizontal_scale`, `vertical_scale`, `baseline_shift`, `faux_bold`, `faux_italic`, and `[width,height]` `text_box`.
- `GLOW`: `source_layer`, `radius`, `color`; optional offsets. Use SCREEN/LINEARDODGE where appropriate.
- `SHADOW`: `source_layer`, `radius`, `color`, `offset_x`, `offset_y`; normally MULTIPLY.
- `BLUR`: `source_layer`, `radius`.
- `GRADIENT_LINEAR` / `GRADIENT_RADIAL`: `start_color`, `end_color`, `steps`.
- `ADJUSTMENT_LEVELS`: input/output black and white, gamma, clipped.
- `ADJUSTMENT_HUE_SATURATION`: hue, saturation, lightness, clipped.
- `ADJUSTMENT_BRIGHTNESS_CONTRAST`: brightness, contrast, clipped.
- `COMPLEX_PATH`: retained Photoshop path plus stroke layer; `stroke_color`, `stroke_width`, `closed`, and Bezier points containing `anchor` with optional `left` / `right` handles.
- `CURVED_ARROW`: the same retained Bezier path plus a tangent-aligned arrowhead; optional `head_size`.
- `VECTOR_SHAPE`: retained closed Photoshop path with `fill_color` and optional stroke.

Image components are placed as Smart Objects. Optional masks are real layer masks with feather, density, and invert settings. Component transform plans may include rotation, skew, and horizontal/vertical perspective in addition to target bounds.

Effects reference an already-created layer by its exact unique name. Generation fails closed for missing parameters, missing source layers, unsupported types, or invalid colors. Every effect remains on a separately named Photoshop layer; adjustment items use Photoshop adjustment layers where supported.
