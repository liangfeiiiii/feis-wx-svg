<div align="center">

# 非叔 SVG 助手 · feis-wx-svg

> *把苹果发布会式的极简 SVG 动效，顺手插进公众号正文*

[![Chrome](https://img.shields.io/badge/Chrome-Side%20Panel%20MV3-4285F4)](#快速开始)
[![Version](https://img.shields.io/badge/版本-1.0.0-1D1D1F)](#功能特性)
[![License](https://img.shields.io/badge/License-MIT-FF8C00)](LICENSE)

<br>

**一套纯 Python 零依赖的公众号 SVG 模块生成引擎，配一个常驻浏览器侧边栏的 Chrome 插件。**

正文照常排版，只在关键观点处插入轻巧克制的纯 SVG 动效卡片，无视频、无 GIF、无 JS。
拖进侧边栏自动体检微信规则，深浅底实时预览，在公众号后台点一下直接落入光标处，全程本地运行不上传。

[为什么做这个](#为什么做这个) · [快速开始](#快速开始) · [功能特性](#功能特性) · [技术栈](#技术栈) · [项目结构](#项目结构) · [能改什么](#能改什么) · [许可证](#许可证)

</div>

---

## 为什么做这个

公众号排版做到最后，常常落进两个极端。一边是白底黑字一拉到底，读起来省心，但重点压不住视线，滑完就忘了。另一边是整篇做成动效长图，从头到尾全在动，文字既选不中也不能复制，看长文眼睛很累。

我想要中间那条路。正文老老实实保持原生排版，让读者舒服地阅读和划词，只在需要停顿、对比或者交代流程的地方，插进一块安静、干净、自己会轻轻动起来的纯 SVG 卡片。

以前做完 SVG 还要找外部粘贴网页中转，切来切去很打断写稿节奏。干脆把生成引擎和 Chrome 侧边栏插件合在一块。写完文章把打包好的模块拖进侧边栏，插件自动检查有没有触发微信的静默清洗规则，光标停在哪，点一下直接进正文。

---

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/liangfeiiiii/feis-wx-svg.git
cd feis-wx-svg

# 试跑内置样板，生成 5 个苹果风 SVG 模块与模块包
python3 engine/apple_modules.py samples/intro-feis-wx-svg/modules.json -o samples/intro-feis-wx-svg/dist
```

然后在 Chrome 里加载侧边栏插件。地址栏输入 `chrome://extensions` 回车，打开右上角的**开发者模式**，点**加载已解压的扩展程序**，选中仓库里的 `extension/` 文件夹。

打开微信公众号编辑页，点击浏览器工具栏上的「非叔 SVG 助手」图标滑出侧边栏，把刚生成的 `feis-pack.json`（或任意单个 `.html` / `.svg`）拖进去即可预览并一键插入正文。

改了插件代码也一样，回扩展页点刷新按钮，重新打开侧边栏就能看到变化。

---

## 功能特性

### 模块引擎与侧边栏协同

| 你会看到 | 它解决什么 |
|---------|-----------|
| 5 种苹果风极简 SVG 组件 | 覆盖数据冲击卡、双栏对比、步骤链路、Bento 网格与金句落版，单块仅几 KB |
| 自动感知公众号编辑器状态 | 在 `mp.weixin.qq.com` 直接显示「插入光标处」，其他网页自动切为「复制到公众号」 |
| 整篇模块包一键拖入 | 支持 `feis-pack.json` 一次导入整篇文章的全部模块，也支持单文件与剪贴板导入 |
| 微信规则静默体检与一键净化 | 自动排查 `id`、滤镜、渐变、`fill-opacity` 动画、脚本等禁用项，发现问题一键清理 |
| 深浅底预览与单卡重播 | 物理滑块切换浅底与深底，提前看清微信深色模式下的呈现效果 |
| 已用标记与防误触撤销 | 插过的模块自动打标（点徽章可收回），单卡移除与两段式清空均提供 4 秒撤销 |

### 微信原生 SVG 规矩

公众号后台保存文章时会悄悄删掉所有 `id`、滤镜、渐变、`mask`、`clipPath`、`fill-opacity` 动画、`<style>` 和脚本，而且不会报错。本引擎产出的模块从底层只使用微信稳定保留的 `<animate>`、`<animateTransform>` 和贝塞尔缓动曲线，完整规则记录在 [docs/wechat-svg-rules.md](docs/wechat-svg-rules.md)。

### 其余的

所有模块数据和已用状态只存在本机 `chrome.storage.local`，关掉侧边栏下次打开进度还在，不经过任何第三方服务器。界面遵循系统深浅色自动切换，并完整尊重系统的「减少动态效果」设置。

---

## 技术栈

生成引擎采用纯 Python 3 标准库编写，零外部依赖，直接读取 JSON 配置输出微信安全 HTML 片段、`feis-pack.json` 模块包与本地预览页。Chrome 插件采用 Manifest V3，通过 `sidePanel` API 常驻侧边栏，借助注入在 `mp.weixin.qq.com` 的轻量 Content Script 兼容新版 ProseMirror 与经典 UEditor 光标插入，插入失败时自动降级为富文本剪贴板写入。前端全部为原生 HTML、CSS 与 JavaScript，无框架无构建步骤，全部过渡动效仅操作 `transform`、`opacity` 与 `stroke-dashoffset`。

---

## 项目结构

```
feis-wx-svg/
├── docs/
│   └── wechat-svg-rules.md    # 微信公众号原生 SVG 保留与清洗规矩
├── engine/
│   └── apple_modules.py       # 苹果发布会极简风 SVG 模块生成引擎（零依赖）
├── extension/
│   ├── icons/                 # 扩展图标 16 / 32 / 48 / 128
│   ├── manifest.json          # MV3 清单（侧边栏、公众号内容脚本、本地存储）
│   ├── background.js          # 侧边栏开关与活动标签页感知
│   ├── content.js             # 公众号编辑器探测与光标处富文本注入
│   ├── sidepanel.html         # 侧边栏页面结构
│   ├── sidepanel.css          # 浅深色主题变量与全状态苹果级动效
│   └── sidepanel.js           # 拖放解析、微信规则体检净化、插入复制与撤销栈
├── samples/
│   └── intro-feis-wx-svg/     # 首篇样板文章、模块配置与生成产物
├── README.md
└── LICENSE
```

---

## 能改什么

想调整模块配色或新增一套自己的主题，打开 `engine/apple_modules.py` 顶部的 `THEMES` 字典改色值即可。想微调动画节奏与缓动曲线，改同文件顶部的 `EASE` 和各 `render_*` 函数里的 `begin` 延迟秒数。想新增一种排版组件，写一个 `render_xxx(mod, th)` 函数并注册进 `RENDERERS`。

想调整 Chrome 侧边栏的视觉色值、圆角或动效时长，打开 `extension/sidepanel.css` 顶部的 `:root` 变量区修改后刷新扩展即可生效。

---

## 许可证

本项目基于 [MIT License](LICENSE) 开源，允许自由使用、修改和分发（包括商业用途），前提是保留原始版权声明与许可声明。完整条款请参阅 [LICENSE](LICENSE) 文件。
