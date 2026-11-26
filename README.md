# feis-wx-svg

非叔专属的微信公众号 SVG 动效模块工具与 Chrome 侧边栏插件。

采用「正常公众号正文 + 关键节点插入苹果发布会极简风 SVG 动效模块」的混排路线。不依赖视频、GIF 或 JS，严格遵守微信公众号原生 SVG 白名单，单个模块轻至几 KB。

## 目录结构

- `engine/apple_modules.py`：纯 Python 3 标准库 SVG 模块生成引擎（零外部依赖）
- `extension/`：Google Chrome 侧边栏插件（Manifest V3），支持拖拽导入、微信规则自动体检、深浅色预览与一键插入公众号编辑器
- `samples/intro-feis-wx-svg/`：首篇样板文章（介绍 `feis-wx-svg` 的正文与 4 个苹果风 SVG 动效模块）
- `docs/wechat-svg-rules.md`：微信公众号原生 SVG 保留与过滤规矩

## 快速开始

### 1. 生成 SVG 模块包

```bash
python3 engine/apple_modules.py samples/intro-feis-wx-svg/modules.json -o samples/intro-feis-wx-svg/dist
```

会在输出目录生成单模块 `.html`、`preview.html` 以及整篇模块包 `feis-pack.json`。

### 2. 加载 Chrome 插件

1. 打开 Chrome 浏览器，地址栏输入 `chrome://extensions/`
2. 打开右上角「开发者模式」
3. 点击「加载已解压的扩展程序」，选择本仓库下的 `extension/` 文件夹
4. 打开微信公众号编辑页，点击浏览器工具栏的「非叔 SVG 助手」图标即可呼出侧边栏，把 `feis-pack.json` 拖进去一键插入文章
