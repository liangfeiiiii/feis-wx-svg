# 微信公众号原生 SVG 安全规矩

微信公众号后台在保存和发布时会对 HTML / SVG 进行静默清洗（直接删掉不支持的标签和属性，不会报错）。本引擎与 Chrome 插件内置的规则体检均严格遵循以下清单。

## 安全保留（可使用）

- `<animate>`：支持 `opacity`、`stroke-dashoffset`、`width`、`height`、`x`、`y`、`cx`、`cy`、`r`、`fill` 等属性动画
- `<animateTransform>`：支持 `translate`、`scale`、`rotate`
- `<set>`：离散状态切换
- 缓动控制：`calcMode="spline"`、`keyTimes`、`keySplines`、`fill="freeze"`、`repeatCount`
- 交互触发：`begin="click"`、`touchstart`（仅限元素自身触发）
- 内联样式：`style` 属性（仅限基础盒模型、背景色、圆角、overflow、line-height 等）

## 会被静默删除或拒收（严禁使用）

- 所有 `id` 属性（跨元素引用会全部失效）
- `fill-opacity` 动画（用元素级 `opacity` 动画替代）
- `xlink:href`（统一改用 `href`）
- `<filter>` 滤镜（模糊、阴影等）
- `<linearGradient>` / `<radialGradient>` 渐变
- `<mask>` 与 `<clipPath>`
- `<style>` 标签与外部 CSS
- `<script>` 与所有 JS 事件属性（`onclick` 等）
- `@font-face` 自定义字体（统一使用系统无衬线字体栈 `-apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", sans-serif`）
- `<mpvoice>` 音频嵌入到 SVG 结构中

## 体积与体验建议

- 单篇文章总 HTML 体积控制在 1MB 以内；模块化 B 路线单个模块控制在 5KB 到 30KB，加载极快。
- 动画从读者打开文章时开始计时，建议单模块入场动画控制在 2.5 到 4.5 秒内完成定格，避免读者划到时仍在剧烈晃动。
- 为适配微信深色模式，模块外层显式声明背景色，避免透明底导致深色模式下文字看不清。
