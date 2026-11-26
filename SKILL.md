---
name: feis-wx-svg
description: 非叔公众号 SVG 动效工具（feis-wx-svg）——为微信公众号打造苹果发布会极简风格的纯 SVG 动效与互动模块（支持数据卡、双栏对比、步骤链路、Bento 网格、金句落版、横向滑动画廊与点击揭晓互动）。主打“正文正常排版 + 关键节点插入高定 SVG 模块”的混排路线，无视频、无 GIF、无 JS，公众号原生支持。配套 Chrome 侧边栏插件，内置示例画廊，支持整篇一键复制与插入公众号编辑器。触发词：公众号SVG、公众号动效、SVG模块、苹果风SVG、非叔SVG、feis-wx-svg、横滑画廊、点击揭晓。
---

# 非叔公众号 SVG 动效工具（feis-wx-svg）

你（Agent）要帮用户为微信公众号制作苹果发布会极简风格的纯 SVG 动效与互动模块，并支持把正文 Markdown 与 SVG 合并编译成可直接一键贴进公众号的完整图文。

- **主仓库路径**：`/Users/macbook/Documents/vibe coding/feis-wx-svg`（公开仓库：`https://github.com/liangfeiiiii/feis-wx-svg`）
- **引擎入口**：`engine/apple_modules.py`（仅需 Python 3 标准库，零外部依赖）
- **示例库打包**：`engine/build_samples.py`（编译全部 `samples/` 示例并同步到 Chrome 插件内置画廊）
- **Chrome 插件目录**：`extension/`（Manifest V3，原生 Side Panel）

## 0. 维护同步铁律（必守）

凡是需要修改或升级本技能说明时，**永远先修改本地技能文件 `~/.gemini/config/skills/feis-wx-svg/SKILL.md`，然后立刻执行同步脚本 `bash "/Users/macbook/Documents/vibe coding/feis-wx-svg/scripts/sync_skill.sh"` 同步覆盖到 Git 仓库根目录的 `SKILL.md` 并提交推送**，严禁本地与 Git 仓库脱节。

## 1. 核心工作模式（正文 + 模块化 SVG 混排）

采用「正常公众号正文排版 + 关键节点插入 2 到 5 个高定 SVG 动效/互动模块」的阅读形态：
- 正文保持可阅读、可划词、有呼吸感，遵循非叔写作风格（具体实在、无 AI 味、无破折号、无互联网黑话）。
- 正文 Markdown 中使用 `[插入 SVG 模块 1：模块名]` 或 `{{module:1}}` 标注模块位置，在配置 JSON 中通过 `"article_md": "article.md"` 关联。
- 运行引擎后自动输出：
  - `article.html`：可直接一键贴进公众号的完整图文 + SVG HTML
  - `preview.html`：手机宽度完整文章预览页（支持重播、深浅底、一键复制整篇）
  - `feis-pack.json`：V2 打包文件（含整篇 `articleHtml` 与全部单模块 `modules`，直接拖进 Chrome 侧边栏插件即可整篇一键复制/插入或分块单插）

## 2. 内置 7 种苹果风与互动组件

运行命令：

```bash
python3 "/Users/macbook/Documents/vibe coding/feis-wx-svg/engine/apple_modules.py" <modules.json> -o <输出目录>
```

可选配色 `theme`：`apple-light`（极净白灰 + 墨黑 + 苹果蓝/朱红点缀）或 `apple-dark`（深空黑 + 炭灰卡片 + 纯白）。每个模块可单独覆盖 `theme` 或 `accent`。

支持 7 种组件 `type`：
1. `hero-metric`：核心数据或关键词冲击卡（字段：`kicker`, `metric`, `unit`, `title`, `subtitle`）
2. `compare-split`：左右双栏高对比卡（字段：`kicker`, `title`, `left`: `{tag, items}`, `right`: `{tag, items}`）
3. `flow-strip`：步骤链路卡，细线绘制与光点流转（字段：`kicker`, `title`, `steps`: `[{num, title, desc}]`, `footnote?`）
4. `bento-grid`：苹果经典 Bento 圆角网格，支持 1+2 或 2x2（字段：`kicker`, `title`, `cards`: `[{label, value, desc, highlight?}]`）
5. `quote-seal`：极简留白金句落版卡（字段：`kicker?`, `quote`, `subquote?`, `author`）
6. `swipe-gallery`：横向左右滑动高定杂志画廊（字段：`kicker`, `title`, `hint?`, `cards`: `[{num, tag, title, desc, highlight?, foot?}]`）
7. `click-reveal`：点击揭晓互动卡片，微信原生 `begin="click"` 零 id 揭幕（字段：`kicker`, `prompt`, `cta`, `reveal_tag`, `reveal_title`, `reveal_desc`）

## 3. 微信原生 SVG 铁律

严格遵守微信编辑器安全白名单（详见 `docs/wechat-svg-rules.md`）：
- **绝对禁止**：所有 `id` 属性、`fill-opacity` 动画、`xlink:href`、`<filter>`、`<linearGradient>` / `<radialGradient>`、`<mask>`、`<clipPath>`、`<style>`、`<script>`。
- **安全可用**：`<animate>`、`<animateTransform>`、`<set>`、`begin="click"`（仅限点击元素自身触发）、内联 `overflow-x:auto` 横向滚动容器。
- **事实核对**：模块里的数字、案例和结论必须来自用户资料，绝不编造；生成后向用户核对关键事实。

## 4. Chrome 插件闭环交付

1. 打开微信公众号编辑页，点击浏览器工具栏「非叔 SVG 助手」打开侧边栏。
2. 拖入 `feis-pack.json`（或点击顶栏「示例」直接体验内置 3 套完整样板）。
3. 在「整篇」视图下点击「一键插入整篇文章」或「一键复制整篇文章」，即可直接把正文与所有动效/互动模块完整贴入公众号；也可以切到「分块」视图逐个插入。
