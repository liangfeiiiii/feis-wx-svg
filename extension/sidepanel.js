// 非叔 SVG 助手 · Side Panel 核心交互与状态管理（V1.1 整篇一键复制 + 内置示例画廊）

(() => {
  const STORAGE_KEY = "feis_wx_svg_state_v2";

  const FORBIDDEN_RULES = [
    { name: "id 属性", regex: /\bid\s*=\s*["'][^"']*["']/gi },
    { name: "fill-opacity 动画", regex: /attributeName\s*=\s*["']fill-opacity["']/gi },
    { name: "xlink:href", regex: /\bxlink:href\b/gi },
    { name: "滤镜 filter", regex: /<filter\b[\s\S]*?<\/filter>/gi },
    { name: "渐变标签", regex: /<(linearGradient|radialGradient)\b[\s\S]*?<\/\1>/gi },
    { name: "遮罩/裁切", regex: /<(mask|clipPath)\b[\s\S]*?<\/\1>/gi },
    { name: "style 标签", regex: /<style\b[\s\S]*?<\/style>/gi },
    { name: "script 脚本", regex: /<script\b[\s\S]*?<\/script>/gi }
  ];

  const state = {
    packTitle: "",
    articleHtml: "",
    articleLint: null,
    modules: [],
    view: "article",
    previewBg: "light",
    wechatReady: false,
    activeTabId: null,
    galleryOpen: false,
    clearArmTimer: null,
    toastTimer: null
  };

  // DOM 引用
  const $app = document.getElementById("app");
  const $statusPill = document.getElementById("statusPill");
  const $statusText = document.getElementById("statusText");
  const $btnToggleGallery = document.getElementById("btnToggleGallery");
  const $btnCloseGallery = document.getElementById("btnCloseGallery");
  const $galleryDrawerList = document.getElementById("galleryDrawerList");
  const $emptyGalleryList = document.getElementById("emptyGalleryList");
  const $packTitle = document.getElementById("packTitle");
  const $packStat = document.getElementById("packStat");
  const $btnWholeAction = document.getElementById("btnWholeAction");
  const $btnWholeCopyOnly = document.getElementById("btnWholeCopyOnly");
  const $dropzone = document.getElementById("dropzone");
  const $articleLintSlot = document.getElementById("articleLintSlot");
  const $articleCanvas = document.getElementById("articleCanvas");
  const $moduleList = document.getElementById("moduleList");
  const $dragOverlay = document.getElementById("dragOverlay");
  const $fileInput = document.getElementById("fileInput");
  const $btnPickFile = document.getElementById("btnPickFile");
  const $btnFromClipboard = document.getElementById("btnFromClipboard");
  const $btnReplayAll = document.getElementById("btnReplayAll");
  const $btnAddMore = document.getElementById("btnAddMore");
  const $btnClear = document.getElementById("btnClear");
  const $toast = document.getElementById("toast");
  const $toastMsg = document.getElementById("toastMsg");
  const $toastUndo = document.getElementById("toastUndo");
  const $viewBtns = Array.from(document.querySelectorAll(".view-btn"));
  const $bgBtns = Array.from(document.querySelectorAll(".bg-btn"));

  // ---------- 微信规则体检与净化 ----------

  function lintHtml(html) {
    const issues = [];
    for (const r of FORBIDDEN_RULES) {
      r.regex.lastIndex = 0;
      if (r.regex.test(html)) issues.push(r.name);
    }
    const bytes = new Blob([html]).size;
    if (bytes > 1000 * 1024) {
      issues.push(`体积偏大(${Math.round(bytes / 1024)}KB)`);
    }
    return { ok: issues.length === 0, issues, bytes };
  }

  function sanitizeWechatHtml(html) {
    let cleaned = html;
    cleaned = cleaned.replace(/<script\b[\s\S]*?<\/script>/gi, "");
    cleaned = cleaned.replace(/<style\b[\s\S]*?<\/style>/gi, "");
    cleaned = cleaned.replace(/<filter\b[\s\S]*?<\/filter>/gi, "");
    cleaned = cleaned.replace(/<(linearGradient|radialGradient|mask|clipPath)\b[\s\S]*?<\/\1>/gi, "");
    cleaned = cleaned.replace(/\s+id\s*=\s*["'][^"']*["']/gi, "");
    cleaned = cleaned.replace(/\bxlink:href\b/gi, "href");
    cleaned = cleaned.replace(/attributeName\s*=\s*["']fill-opacity["']/gi, 'attributeName="opacity"');
    return cleaned;
  }

  function normalizeSnippet(raw) {
    const trimmed = (raw || "").trim();
    if (!trimmed) return "";
    if (/^<section\b/i.test(trimmed)) return trimmed;
    if (/^<svg\b/i.test(trimmed)) {
      return `<section style="margin:24px 0;padding:0;line-height:0;font-size:0;border-radius:16px;overflow:hidden;">${trimmed}</section>`;
    }
    return trimmed;
  }

  // ---------- 轻提示 ----------

  function showToast(msg, { duration = 1900, onUndo = null } = {}) {
    clearTimeout(state.toastTimer);
    $toastMsg.textContent = msg;
    if (onUndo) {
      $toastUndo.hidden = false;
      $toastUndo.onclick = () => {
        $toast.classList.remove("show");
        onUndo();
      };
    } else {
      $toastUndo.hidden = true;
      $toastUndo.onclick = null;
    }
    $toast.classList.add("show");
    state.toastTimer = setTimeout(() => {
      $toast.classList.remove("show");
    }, duration);
  }

  // ---------- 持久化存储 ----------

  function saveState() {
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({
        [STORAGE_KEY]: {
          packTitle: state.packTitle,
          articleHtml: state.articleHtml,
          modules: state.modules,
          view: state.view,
          previewBg: state.previewBg
        }
      });
    }
  }

  async function restoreState() {
    if (typeof chrome === "undefined" || !chrome.storage || !chrome.storage.local) return;
    try {
      const data = await chrome.storage.local.get(STORAGE_KEY);
      const saved = data[STORAGE_KEY];
      if (saved && (saved.articleHtml || (Array.isArray(saved.modules) && saved.modules.length > 0))) {
        state.packTitle = saved.packTitle || "已导入内容";
        state.articleHtml = saved.articleHtml || "";
        state.articleLint = state.articleHtml ? lintHtml(state.articleHtml) : null;
        state.modules = Array.isArray(saved.modules) ? saved.modules : [];
        state.view = saved.view === "modules" ? "modules" : "article";
        applyPreviewBg(saved.previewBg === "dark" ? "dark" : "light", false);
        applyView(state.view, false);
        render();
      }
    } catch {
      // ignore
    }
  }

  // ---------- 公众号编辑器自动感知 ----------

  function setConnectionStatus(ready) {
    state.wechatReady = Boolean(ready);
    $app.dataset.wechat = state.wechatReady ? "true" : "false";
    $statusPill.dataset.state = state.wechatReady ? "connected" : "offline";
    $statusText.textContent = state.wechatReady ? "已连接公众号" : "复制模式";

    if ($btnWholeAction.dataset.state !== "success") {
      $btnWholeAction.querySelector(".act-label").textContent = state.wechatReady
        ? "一键插入整篇文章"
        : "一键复制整篇文章";
    }
    document.querySelectorAll(".mod-card .act-primary").forEach((btn) => {
      if (btn.dataset.state !== "success") {
        btn.querySelector(".act-label").textContent = state.wechatReady ? "插入光标处" : "复制到公众号";
      }
    });
  }

  async function probeActiveTab() {
    if (typeof chrome === "undefined" || !chrome.tabs) {
      setConnectionStatus(false);
      return;
    }
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.url || !tab.url.startsWith("https://mp.weixin.qq.com/")) {
        state.activeTabId = tab ? tab.id : null;
        setConnectionStatus(false);
        return;
      }
      state.activeTabId = tab.id;
      chrome.tabs.sendMessage(tab.id, { type: "FEIS_PING_EDITOR" }, (res) => {
        if (chrome.runtime.lastError || !res) {
          setConnectionStatus(false);
          return;
        }
        setConnectionStatus(Boolean(res.ready));
      });
    } catch {
      setConnectionStatus(false);
    }
  }

  if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((msg) => {
      if (msg && msg.type === "FEIS_TAB_CONTEXT") probeActiveTab();
    });
  }

  // ---------- 双保险富文本复制与公众号光标插入 ----------

  async function copyRichHtml(html) {
    // 方式 1：现代 ClipboardItem API（同时写入 text/html 与 text/plain）
    if (navigator.clipboard && window.ClipboardItem) {
      try {
        await navigator.clipboard.write([
          new ClipboardItem({
            "text/html": new Blob([html], { type: "text/html" }),
            "text/plain": new Blob([html], { type: "text/plain" })
          })
        ]);
        return true;
      } catch {
        // 降级到选区复制
      }
    }
    // 方式 2：隐藏富文本选区 execCommand('copy') 兜底
    const box = document.createElement("div");
    box.setAttribute("contenteditable", "true");
    box.style.cssText = "position:fixed;left:-9999px;top:0;opacity:0;pointer-events:none;";
    box.innerHTML = html;
    document.body.appendChild(box);
    const range = document.createRange();
    range.selectNodeContents(box);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    const ok = document.execCommand("copy");
    sel.removeAllRanges();
    box.remove();
    return ok;
  }

  async function deliverHtml({ html, label, buttonEl, forceCopyOnly = false, onSuccess = null }) {
    let insertedDirect = false;

    if (!forceCopyOnly && state.wechatReady && state.activeTabId && typeof chrome !== "undefined" && chrome.tabs) {
      insertedDirect = await new Promise((resolve) => {
        chrome.tabs.sendMessage(state.activeTabId, { type: "FEIS_INSERT_HTML", html }, (res) => {
          if (chrome.runtime.lastError || !res || !res.ok) resolve(false);
          else resolve(true);
        });
      });
    }

    if (!insertedDirect) {
      const ok = await copyRichHtml(html);
      if (!ok) {
        showToast("复制失败，请点击页面空白处后重试");
        return;
      }
    }

    if (onSuccess) onSuccess();

    const labelEl = buttonEl.querySelector(".act-label");
    const iconEl = buttonEl.querySelector(".act-icon");
    const prevIdleLabel = buttonEl === $btnWholeAction
      ? (state.wechatReady ? "一键插入整篇文章" : "一键复制整篇文章")
      : (state.wechatReady ? "插入光标处" : "复制到公众号");

    buttonEl.dataset.state = "success";
    labelEl.textContent = insertedDirect ? "已插入正文" : "已复制";
    iconEl.innerHTML = `<svg viewBox="0 0 18 18" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path class="check-path" d="M3.8 9.4L7.4 13L14.2 5.4"/></svg>`;

    showToast(
      insertedDirect
        ? `已将「${label}」插入公众号编辑器`
        : `已复制「${label}」，去公众号编辑器按 ⌘V 粘贴`
    );

    clearTimeout(buttonEl._resetTimer);
    buttonEl._resetTimer = setTimeout(() => {
      buttonEl.dataset.state = "idle";
      labelEl.textContent = prevIdleLabel;
      iconEl.innerHTML = "";
    }, 1500);
  }

  // ---------- 载入整包数据（支持用户文件与内置示例） ----------

  function loadPackObject(pack, toastLabel = "") {
    state.packTitle = pack.title || "未命名文章";
    state.articleHtml = pack.articleHtml || "";
    state.articleLint = state.articleHtml ? lintHtml(state.articleHtml) : null;
    state.modules = (pack.modules || []).map((m, idx) => {
      const html = normalizeSnippet(m.html || "");
      return {
        id: `${Date.now()}-${idx}-${Math.random().toString(36).slice(2, 6)}`,
        name: m.name || m.file || `模块 ${idx + 1}`,
        type: m.type || "svg",
        html,
        lint: lintHtml(html),
        used: false
      };
    });
    const nextView = state.articleHtml ? "article" : "modules";
    applyView(nextView, false);
    setGalleryOpen(false);
    saveState();
    render();
    if (toastLabel) showToast(toastLabel);
  }

  async function importFiles(fileList) {
    const files = Array.from(fileList || []);
    if (files.length === 0) return;

    const incomingModules = [];
    let importedPack = null;
    let importedWholeHtml = "";
    let importedWholeTitle = "";

    for (const file of files) {
      const text = await file.text();
      const lower = file.name.toLowerCase();

      if (lower.endsWith(".json")) {
        try {
          const parsed = JSON.parse(text);
          if (parsed.articleHtml || Array.isArray(parsed.modules)) {
            importedPack = parsed;
            if (!importedPack.title) importedPack.title = file.name.replace(/\.json$/i, "");
          }
        } catch {
          showToast(`无法解析 ${file.name}，请确认是有效的 feis-pack.json`);
        }
      } else if (lower.endsWith(".html") || lower.endsWith(".htm") || lower.endsWith(".svg")) {
        const html = normalizeSnippet(text);
        if (!html.includes("<svg") && !html.includes("<section") && !html.includes("<p")) continue;

        // 判断是整篇图文 HTML（含正文段落 <p>）还是单个 SVG 模块
        if (lower.endsWith(".html") && /<p\b/i.test(html) && files.length === 1) {
          importedWholeHtml = html;
          importedWholeTitle = file.name.replace(/\.html?$/i, "");
        } else {
          incomingModules.push({
            id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
            name: file.name.replace(/\.(html?|svg)$/i, ""),
            type: lower.endsWith(".svg") ? "svg" : "html",
            html,
            lint: lintHtml(html),
            used: false
          });
        }
      }
    }

    if (importedPack) {
      loadPackObject(importedPack, `已载入「${importedPack.title}」`);
      return;
    }

    if (importedWholeHtml) {
      state.packTitle = importedWholeTitle || "完整文章";
      state.articleHtml = importedWholeHtml;
      state.articleLint = lintHtml(importedWholeHtml);
      state.modules = [];
      applyView("article", false);
      saveState();
      render();
      showToast(`已导入完整文章「${state.packTitle}」`);
      return;
    }

    if (incomingModules.length === 0) {
      showToast("未识别到有效的文章包或 SVG 文件");
      return;
    }

    if (!state.packTitle) state.packTitle = incomingModules.length === 1 ? incomingModules[0].name : "自定义模块组";
    state.modules = [...state.modules, ...incomingModules];
    if (!state.articleHtml) applyView("modules", false);
    saveState();
    render();
    showToast(`已导入 ${incomingModules.length} 个模块`);
  }

  async function importFromClipboard() {
    try {
      const text = await navigator.clipboard.readText();
      if (!text || (!text.includes("<svg") && !text.includes("<section"))) {
        showToast("剪贴板里没有检测到 SVG 或公众号 HTML 代码");
        return;
      }
      const html = normalizeSnippet(text);
      if (/<p\b/i.test(html)) {
        state.packTitle = "剪贴板整篇文章";
        state.articleHtml = html;
        state.articleLint = lintHtml(html);
        applyView("article", false);
        saveState();
        render();
        showToast("已从剪贴板导入整篇文章");
        return;
      }
      const mod = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        name: `剪贴板模块 ${state.modules.length + 1}`,
        type: "clipboard",
        html,
        lint: lintHtml(html),
        used: false
      };
      if (!state.packTitle) state.packTitle = "剪贴板导入";
      state.modules = [mod, ...state.modules];
      if (!state.articleHtml) applyView("modules", false);
      saveState();
      render();
      showToast("已从剪贴板导入 1 个模块");
    } catch {
      showToast("读取剪贴板失败，请直接拖入文件");
    }
  }

  // ---------- 内置示例画廊渲染 ----------

  function setGalleryOpen(open) {
    state.galleryOpen = Boolean(open);
    $app.dataset.galleryOpen = state.galleryOpen ? "true" : "false";
    $btnToggleGallery.setAttribute("aria-expanded", state.galleryOpen ? "true" : "false");
  }

  function renderGalleryCards(container) {
    const samples = Array.isArray(window.FEIS_BUILTIN_SAMPLES) ? window.FEIS_BUILTIN_SAMPLES : [];
    container.innerHTML = "";
    samples.forEach((s) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "gallery-item";
      const kb = ((s.articleBytes || 0) / 1024).toFixed(1);
      btn.innerHTML = `
        <div class="gallery-item-top">
          <span class="gallery-tag"></span>
          <span class="gallery-kb">${(s.modules || []).length} 模块 · ${kb}KB</span>
        </div>
        <div class="gallery-title"></div>
        <div class="gallery-desc"></div>
      `;
      btn.querySelector(".gallery-tag").textContent = s.category || "示例";
      btn.querySelector(".gallery-title").textContent = s.title;
      btn.querySelector(".gallery-desc").textContent = s.summary || "";
      btn.onclick = () => loadPackObject(s, `已打开示例「${s.category || s.title}」`);
      container.appendChild(btn);
    });
  }

  // ---------- 视图与底色切换 ----------

  function applyPreviewBg(mode, persist = true) {
    state.previewBg = mode === "dark" ? "dark" : "light";
    $app.dataset.previewBg = state.previewBg;
    $bgBtns.forEach((btn) => {
      btn.setAttribute("aria-checked", btn.dataset.bg === state.previewBg ? "true" : "false");
    });
    if (persist) saveState();
  }

  function applyView(view, persist = true) {
    state.view = view === "modules" ? "modules" : "article";
    $app.dataset.view = state.view;
    $viewBtns.forEach((btn) => {
      btn.setAttribute("aria-checked", btn.dataset.view === state.view ? "true" : "false");
    });
    if (persist) saveState();
  }

  // ---------- 主渲染 ----------

  function renderArticlePane() {
    $articleLintSlot.innerHTML = "";
    $articleCanvas.innerHTML = "";
    if (!state.articleHtml) return;

    if (state.articleLint && !state.articleLint.ok) {
      const bar = document.createElement("div");
      bar.className = "lint-bar";
      bar.innerHTML = `<span>检测到微信禁用项：${state.articleLint.issues.join("、")}</span>
        <button class="lint-fix-btn" type="button">一键净化</button>`;
      bar.querySelector(".lint-fix-btn").onclick = () => {
        state.articleHtml = sanitizeWechatHtml(state.articleHtml);
        state.articleLint = lintHtml(state.articleHtml);
        saveState();
        bar.classList.add("is-resolved");
        setTimeout(() => bar.remove(), 220);
        $articleCanvas.innerHTML = state.articleHtml;
        showToast("已净化整篇文章，现已符合微信规则");
      };
      $articleLintSlot.appendChild(bar);
    }
    $articleCanvas.innerHTML = state.articleHtml;
  }

  function render() {
    const hasArticle = Boolean(state.articleHtml);
    const hasModules = state.modules.length > 0;
    const hasItems = hasArticle || hasModules;

    $app.dataset.hasItems = hasItems ? "true" : "false";
    $app.dataset.hasArticle = hasArticle ? "true" : "false";
    $packTitle.textContent = state.packTitle || "未命名文章";

    if (hasArticle) {
      const artKb = ((state.articleLint?.bytes || new Blob([state.articleHtml]).size) / 1024).toFixed(1);
      $packStat.textContent = hasModules ? `整篇 ${artKb}KB · ${state.modules.length} 模块` : `整篇 ${artKb}KB`;
    } else {
      const totalKb = state.modules.reduce((acc, m) => acc + (m.lint?.bytes || 0), 0) / 1024;
      $packStat.textContent = `${state.modules.length} 个模块 · ${totalKb.toFixed(1)}KB`;
    }

    renderArticlePane();

    $moduleList.innerHTML = "";
    if (!hasModules) return;

    state.modules.forEach((mod, idx) => {
      const card = document.createElement("article");
      card.className = "mod-card";
      card.dataset.used = mod.used ? "true" : "false";
      card.style.setProperty("--enter-delay", `${Math.min(idx * 45, 200)}ms`);

      const kb = ((mod.lint?.bytes || new Blob([mod.html]).size) / 1024).toFixed(1);
      const lintWarnHtml =
        mod.lint && !mod.lint.ok
          ? `<div class="lint-bar">
               <span>检测到微信禁用项：${mod.lint.issues.join("、")}</span>
               <button class="lint-fix-btn" type="button">一键净化</button>
             </div>`
          : "";

      card.innerHTML = `
        <div class="mod-head">
          <div class="mod-info">
            <div class="mod-title-row">
              <span class="mod-index">${String(idx + 1).padStart(2, "0")}</span>
              <span class="mod-name"></span>
            </div>
            <span class="mod-meta">${kb}KB · ${mod.type}</span>
          </div>
          <div class="mod-badges">
            <button class="done-badge" type="button" title="点击收回已用标记">✓ 已用</button>
            <button class="remove-btn" type="button" title="移除此模块" aria-label="移除此模块">
              <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                <path d="M4.5 4.5l7 7M11.5 4.5l-7 7"/>
              </svg>
            </button>
          </div>
        </div>
        ${lintWarnHtml}
        <div class="mod-stage"></div>
        <div class="mod-foot">
          <button class="act-primary" type="button" data-state="idle">
            <span class="act-icon" aria-hidden="true"></span>
            <span class="act-label">${state.wechatReady ? "插入光标处" : "复制到公众号"}</span>
          </button>
          <button class="act-secondary btn-copy-only" type="button" title="仅复制到剪贴板">复制</button>
          <button class="icon-btn btn-replay" type="button" title="重播此模块" aria-label="重播此模块">
            <svg viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M16.2 10a6.2 6.2 0 1 1-1.6-4.2"/>
              <path d="M16.2 3.8v3.1h-3.1"/>
            </svg>
          </button>
        </div>
      `;

      card.querySelector(".mod-name").textContent = mod.name;
      const stage = card.querySelector(".mod-stage");
      stage.innerHTML = mod.html;

      card.querySelector(".done-badge").onclick = () => {
        mod.used = false;
        card.dataset.used = "false";
        saveState();
      };

      card.querySelector(".remove-btn").onclick = () => {
        const snapshot = {
          packTitle: state.packTitle,
          articleHtml: state.articleHtml,
          modules: state.modules.map((m) => ({ ...m }))
        };
        card.classList.add("is-removing");
        setTimeout(() => {
          state.modules = state.modules.filter((m) => m.id !== mod.id);
          if (state.modules.length === 0 && !state.articleHtml) state.packTitle = "";
          saveState();
          render();
          showToast(`已移除「${mod.name}」`, {
            duration: 4000,
            onUndo: () => {
              state.packTitle = snapshot.packTitle;
              state.articleHtml = snapshot.articleHtml;
              state.articleLint = state.articleHtml ? lintHtml(state.articleHtml) : null;
              state.modules = snapshot.modules;
              saveState();
              render();
              showToast("已恢复模块");
            }
          });
        }, 180);
      };

      const fixBtn = card.querySelector(".lint-fix-btn");
      if (fixBtn) {
        fixBtn.onclick = () => {
          mod.html = sanitizeWechatHtml(mod.html);
          mod.lint = lintHtml(mod.html);
          saveState();
          const bar = card.querySelector(".lint-bar");
          if (bar) {
            bar.classList.add("is-resolved");
            setTimeout(() => bar.remove(), 220);
          }
          stage.innerHTML = mod.html;
          card.querySelector(".mod-meta").textContent = `${(mod.lint.bytes / 1024).toFixed(1)}KB · ${mod.type}`;
          showToast(`已净化「${mod.name}」`);
        };
      }

      const primaryBtn = card.querySelector(".act-primary");
      primaryBtn.onclick = () =>
        deliverHtml({
          html: mod.html,
          label: mod.name,
          buttonEl: primaryBtn,
          forceCopyOnly: false,
          onSuccess: () => {
            mod.used = true;
            card.dataset.used = "true";
            saveState();
          }
        });

      card.querySelector(".btn-copy-only").onclick = () =>
        deliverHtml({
          html: mod.html,
          label: mod.name,
          buttonEl: primaryBtn,
          forceCopyOnly: true,
          onSuccess: () => {
            mod.used = true;
            card.dataset.used = "true";
            saveState();
          }
        });

      const replayBtn = card.querySelector(".btn-replay");
      replayBtn.onclick = () => {
        replayBtn.classList.remove("spinning");
        void replayBtn.offsetWidth;
        replayBtn.classList.add("spinning");
        stage.innerHTML = "";
        requestAnimationFrame(() => {
          stage.innerHTML = mod.html;
        });
      };

      $moduleList.appendChild(card);
    });
  }

  // ---------- 事件绑定 ----------

  $btnToggleGallery.onclick = () => setGalleryOpen(!state.galleryOpen);
  $btnCloseGallery.onclick = () => setGalleryOpen(false);

  $btnWholeAction.onclick = () => {
    if (!state.articleHtml) return;
    deliverHtml({
      html: state.articleHtml,
      label: state.packTitle || "整篇文章",
      buttonEl: $btnWholeAction,
      forceCopyOnly: false
    });
  };

  $btnWholeCopyOnly.onclick = () => {
    if (!state.articleHtml) return;
    deliverHtml({
      html: state.articleHtml,
      label: state.packTitle || "整篇文章",
      buttonEl: $btnWholeAction,
      forceCopyOnly: true
    });
  };

  $btnPickFile.onclick = (e) => {
    e.stopPropagation();
    $fileInput.click();
  };
  $btnAddMore.onclick = () => $fileInput.click();
  $dropzone.onclick = () => $fileInput.click();
  $dropzone.onkeydown = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      $fileInput.click();
    }
  };
  $fileInput.onchange = (e) => {
    importFiles(e.target.files);
    $fileInput.value = "";
  };
  $btnFromClipboard.onclick = (e) => {
    e.stopPropagation();
    importFromClipboard();
  };

  $viewBtns.forEach((btn) => {
    btn.onclick = () => applyView(btn.dataset.view);
  });
  $bgBtns.forEach((btn) => {
    btn.onclick = () => applyPreviewBg(btn.dataset.bg);
  });

  $btnReplayAll.onclick = () => {
    $btnReplayAll.classList.remove("spinning");
    void $btnReplayAll.offsetWidth;
    $btnReplayAll.classList.add("spinning");
    if (state.view === "article" && state.articleHtml) {
      $articleCanvas.innerHTML = "";
      requestAnimationFrame(() => {
        $articleCanvas.innerHTML = state.articleHtml;
      });
      return;
    }
    document.querySelectorAll(".mod-card").forEach((card, idx) => {
      const stage = card.querySelector(".mod-stage");
      const mod = state.modules[idx];
      if (!stage || !mod) return;
      stage.innerHTML = "";
      requestAnimationFrame(() => {
        stage.innerHTML = mod.html;
      });
    });
  };

  function disarmClear() {
    clearTimeout(state.clearArmTimer);
    $btnClear.dataset.armed = "false";
    $btnClear.querySelector(".danger-label").textContent = "清空";
  }

  document.addEventListener("click", (e) => {
    if ($btnClear.dataset.armed === "true" && !$btnClear.contains(e.target)) {
      disarmClear();
    }
  });

  $btnClear.onclick = () => {
    if ($btnClear.dataset.armed !== "true") {
      $btnClear.dataset.armed = "true";
      $btnClear.querySelector(".danger-label").textContent = "确认清空";
      clearTimeout(state.clearArmTimer);
      state.clearArmTimer = setTimeout(disarmClear, 2800);
      return;
    }
    disarmClear();
    const snapshot = {
      packTitle: state.packTitle,
      articleHtml: state.articleHtml,
      modules: state.modules.map((m) => ({ ...m })),
      view: state.view
    };
    state.packTitle = "";
    state.articleHtml = "";
    state.articleLint = null;
    state.modules = [];
    saveState();
    render();
    showToast("已清空当前内容", {
      duration: 4200,
      onUndo: () => {
        state.packTitle = snapshot.packTitle;
        state.articleHtml = snapshot.articleHtml;
        state.articleLint = state.articleHtml ? lintHtml(state.articleHtml) : null;
        state.modules = snapshot.modules;
        applyView(snapshot.view, false);
        saveState();
        render();
        showToast("已恢复内容");
      }
    });
  };

  // 全局拖放感应
  let dragDepth = 0;
  window.addEventListener("dragenter", (e) => {
    e.preventDefault();
    dragDepth += 1;
    if (!state.articleHtml && state.modules.length === 0) {
      $dropzone.classList.add("is-dragover");
    } else {
      $dragOverlay.classList.add("visible");
    }
  });
  window.addEventListener("dragover", (e) => e.preventDefault());
  window.addEventListener("dragleave", (e) => {
    e.preventDefault();
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) {
      $dropzone.classList.remove("is-dragover");
      $dragOverlay.classList.remove("visible");
    }
  });
  window.addEventListener("drop", (e) => {
    e.preventDefault();
    dragDepth = 0;
    $dropzone.classList.remove("is-dragover");
    $dragOverlay.classList.remove("visible");
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      importFiles(e.dataTransfer.files);
    }
  });

  // 初始化
  renderGalleryCards($emptyGalleryList);
  renderGalleryCards($galleryDrawerList);
  restoreState();
  probeActiveTab();
})();
