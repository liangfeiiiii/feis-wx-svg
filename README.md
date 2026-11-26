<div align="center">

# 非叔 SVG 助手 · feis-wx-svg

> *一套拿来就能用的公众号苹果风 SVG 动效产品：AI 排版 Skill + Chrome 侧边栏插件 + 交互示例画廊*

[![Chrome](https://img.shields.io/badge/Chrome-Side%20Panel%20MV3-4285F4)](#快速开始)
[![Version](https://img.shields.io/badge/版本-1.2.0-1D1D1F)](#示例画廊)
[![Agent Skill](https://img.shields.io/badge/AI-Agent%20Skill-0071E3)](SKILL.md)
[![License](https://img.shields.io/badge/License-MIT-FF8C00)](LICENSE)

<br>

**克隆这一个仓库，直接带走三件套：让 AI 帮你写公众号动效排版的 SKILL、一键整篇复制到公众号的 Chrome 插件、以及 3 套可直接打开体验的高级示例。**

正文照常排版，只在关键节点插入轻巧克制的纯 SVG 动效与互动卡片，无视频、无 GIF、无 JS。
所有数据与文件全在本机处理，不经过任何外部服务器。

[示例画廊](#示例画廊) · [为什么做这个](#为什么做这个) · [快速开始](#快速开始) · [AI 技能用法](#ai-技能用法) · [功能特性](#功能特性) · [项目结构](#项目结构) · [许可证](#许可证)

</div>

---

## 示例画廊

不知道它能做出什么效果？这里放了 3 套完整样板，既可以在克隆后直接双击对应的 `preview.html` 看效果，也可以装好 Chrome 插件后在侧边栏「示例」里一键点开体验、直接复制到自己公众号试用。

> 如果开启了本仓库的 GitHub Pages，可直接访问在线展厅：`https://liangfeiiiii.github.io/feis-wx-svg/`

| 编号 | 示例类型 | 你能看到什么 | 完整预览与源码 |
|---|---|---|---|
| **01** | **苹果风混排样板** | 正文原生排版 + 5 个苹果发布会极简动效模块（数据冲击卡、规则双栏对比、Bento 网格、步骤链路、金句落版），支持一键整篇复制 | [预览页](samples/01-intro-feis-wx-svg/dist/preview.html) · [正文](samples/01-intro-feis-wx-svg/article.md) · [配置](samples/01-intro-feis-wx-svg/modules.json) |
| **02** | **横向滑动画廊** | 复刻苹果官网特性展板与杂志横滑画册，手机微信里手指左右滑动翻看一组高定卡片 | [预览页](samples/02-swipe-gallery/dist/preview.html) · [正文](samples/02-swipe-gallery/article.md) · [配置](samples/02-swipe-gallery/modules.json) |
| **03** | **点击揭晓互动** | 复刻头部大号爆款「点击揭幕」卡片，零 JS、零 id，读者轻点盖板后优雅滑走露出底层答案 | [预览页](samples/03-click-reveal/dist/preview.html) · [正文](samples/03-click-reveal/article.md) · [配置](samples/03-click-reveal/modules.json) |

---

## 为什么做这个

公众号排版做到最后，常常落进两个极端。一边是白底黑字一拉到底，读起来省心，但重点压不住视线，滑完就忘了。另一边是整篇做成动效长图，从头到尾全在动，文字既选不中也不能复制，看长文眼睛很累。

我想要中间那条路。正文老老实实保持原生排版，让读者舒服地阅读和划词，只在需要停顿、对比、横滑翻看或者点击揭晓的地方，插进一块安静、干净、自己会轻轻动起来的纯 SVG 卡片。

以前做完 SVG 还要找外部粘贴网页中转，切来切去很打断写稿节奏。干脆把 AI 排版 Skill、生成引擎、示例画廊和 Chrome 侧边栏插件合在一起做成一套完整工具。写完文章把打包好的 `feis-pack.json` 拖进侧边栏，插件自动体检微信规则，点一下就能把整篇文章或者单个模块直接插进公众号编辑器。

---

## 快速开始

### 1. 下载仓库

```bash
git clone https://github.com/liangfeiiiii/feis-wx-svg.git
cd feis-wx-svg
```

### 2. 加载 Chrome 插件（30 秒）

地址栏输入 `chrome://extensions` 回车，打开右上角的**开发者模式**，点**加载已解压的扩展程序**，选中仓库里的 `extension/` 文件夹。

点击浏览器工具栏上的「非叔 SVG 助手」图标滑出侧边栏。不用跑任何命令，直接点面板里的**内置示例**，就能立刻看到 3 套样板的动效和互动效果，点「一键复制整篇文章」就能贴进自己的公众号草稿箱测试。

### 3. 自己生成新文章

```bash
# 编译单篇文章（同时输出完整 article.html、preview.html 与 feis-pack.json）
python3 engine/apple_modules.py samples/01-intro-feis-wx-svg/modules.json -o samples/01-intro-feis-wx-svg/dist

# 一键重编所有示例并同步更新插件内置示例库
python3 engine/build_samples.py
```

把生成出来的 `feis-pack.json` 拖进 Chrome 侧边栏，即可预览整篇文章并一键插入或复制到公众号。

---

## AI 技能用法

本仓库根目录自带完整规范的 [SKILL.md](SKILL.md)，支持 Antigravity、Claude Code、Cursor、Codex 等 AI Agent 直接使用。

把仓库里的 `SKILL.md` 放到你的 AI Agent 技能目录（例如 `~/.gemini/config/skills/feis-wx-svg/SKILL.md`），以后只要直接跟 AI 说：

> 用 feis-wx-svg 帮我把这篇文章做成公众号苹果风 SVG 混排，加上一个横滑画廊和一个点击揭晓。

AI 会自动帮你挑选合适的组件、写出正文与模块配置 JSON、调用 `engine/apple_modules.py` 编译成 `feis-pack.json`，你直接拖进 Chrome 插件一键发稿即可。

---

## 功能特性

### 引擎与插件协同

| 你会看到 | 它解决什么 |
|---|---|
| 7 种苹果风与互动 SVG 组件 | 数据冲击卡、双栏对比、步骤链路、Bento 网格、金句落版（9 秒循环 0→1 完整生长 + 6 秒清晰停留），外加横向滑动画廊与点击揭晓互动 |
| 真实 iPhone 16 Pro 样机预览 | 钛金属边框、灵动岛、9:41 状态栏与内屏独立滚动，所见即所得，顶部控制坞永不滚走 |
| 直接导入 Markdown 文章 | 拖入 `.md` 自动转为微信安全苹果风排版，也支持 `feis-pack.json`、`article.html` 与单模块 `.svg` |
| 可折叠排版滑块与 4 套极简标题 | 实时调页面两侧留白（默认 18px）、字号、行距、段距、字距，一键切换极简黑字 / 左竖线 / 底短线 / 细圆点 |
| 整篇一键复制与插件内置示例库 | 装完插件点「示例库」直接预览 3 套样板，一键把整篇正文加动效贴进公众号，也支持分块单插 |
| 微信规则静默体检与一键净化 | 自动排查 `id`、滤镜、渐变、`fill-opacity` 动画、脚本等微信禁用项，发现问题原地净化不闪烁 |

### 微信原生 SVG 规矩

公众号后台保存文章时会悄悄删掉所有 `id`、滤镜、渐变、`mask`、`clipPath`、`fill-opacity` 动画、`<style>` 和脚本，而且不会报错。本引擎产出的所有模块（含横滑画廊与点击揭晓）严格遵守微信原生白名单，完整实测清单见 [docs/wechat-svg-rules.md](docs/wechat-svg-rules.md)。

---

## 技术栈

生成引擎采用纯 Python 3 标准库编写，零外部依赖，支持将 Markdown 正文与 SVG 模块合并编译为微信安全内联 HTML、`feis-pack.json` 模块包与本地预览页。Chrome 插件采用 Manifest V3，通过 `sidePanel` API 常驻侧边栏，借助注入在 `mp.weixin.qq.com` 的轻量 Content Script 兼容新版 ProseMirror 与经典 UEditor 光标插入，失败时双保险自动降级为富文本剪贴板写入。前端全部为原生 HTML、CSS 与 JavaScript，无框架无构建步骤，全部状态动效仅操作 `transform`、`opacity` 与 `stroke-dashoffset`。

---

## 项目结构

```
feis-wx-svg/
├── SKILL.md                   # AI Agent 技能入口（与本地技能保持同步）
├── index.html                 # 在线示例画廊展厅页（支持 GitHub Pages）
├── docs/
│   └── wechat-svg-rules.md    # 微信公众号原生 SVG 保留与清洗规矩
├── engine/
│   ├── apple_modules.py       # 苹果风 SVG 模块与整篇混排生成引擎（零依赖）
│   └── build_samples.py       # 一键编译全部示例并更新插件内置示例库
├── scripts/
│   └── sync_skill.sh          # 从本地技能目录同步 SKILL.md 到 Git 仓库
├── extension/
│   ├── icons/                 # 扩展图标 16 / 32 / 48 / 128
│   ├── manifest.json          # MV3 清单（侧边栏、公众号内容脚本、本地存储）
│   ├── background.js          # 侧边栏开关与活动标签页感知
│   ├── content.js             # 公众号编辑器探测与光标处富文本注入
│   ├── samples_bundle.js      # 插件内置示例画廊数据（离线秒开）
│   ├── sidepanel.html         # 侧边栏页面结构
│   ├── sidepanel.css          # 浅深色主题变量与全状态苹果级动效
│   └── sidepanel.js           # 整篇/分块双模式、示例画廊、规则净化与撤销栈
├── samples/
│   ├── 01-intro-feis-wx-svg/  # 示例 01：首篇苹果风混排完整样板
│   ├── 02-swipe-gallery/      # 示例 02：横向滑动杂志画廊完整样板
│   └── 03-click-reveal/       # 示例 03：点击揭晓互动卡片完整样板
├── README.md
└── LICENSE
```

---

## 能改什么

想调整模块配色或新增一套自己的主题，打开 `engine/apple_modules.py` 顶部的 `THEMES` 字典改色值即可。想新增一种排版组件，写一个 `render_xxx(mod, th)` 函数并注册进 `RENDERERS`。在 `samples/` 下新增示例目录后，跑一遍 `python3 engine/build_samples.py`，插件内置示例库会自动同步更新。

想调整 Chrome 侧边栏的视觉色值、圆角或动效时长，打开 `extension/sidepanel.css` 顶部的 `:root` 变量区修改后刷新扩展即可生效。

---

## 许可证

本项目基于 [MIT License](LICENSE) 开源，允许自由使用、修改和分发（包括商业用途），前提是保留原始版权声明与许可声明。完整条款请参阅 [LICENSE](LICENSE) 文件。
