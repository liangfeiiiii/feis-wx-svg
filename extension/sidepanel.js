// 非叔 SVG 助手 · Side Panel 核心交互与状态管理
// 遵循：复杂留给系统，不留给用户；按状态变化精细驱动苹果级微动效。

(() => {
  const STORAGE_KEY = "feis_wx_svg_state_v1";

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
    modules: [],
    previewBg: "light",
    wechatReady: false,
    activeTabId: null,
    undoSnapshot: null,
    clearArmTimer: null,
    toastTimer: null
  };

  // DOM 引用
  const $app = document.getElementById("app");
  const $statusPill = document.getElementById("statusPill");
  const $statusText = document.getElementById("statusText");
  const $packTitle = document.getElementById("packTitle");
  const $packStat = document.getElementById("packStat");
  const $dropzone = document.getElementById("dropzone");
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
  const $segBtns = Array.from(document.querySelectorAll(".seg-btn"));

  // ---------- 微信规则体检与一键净化 ----------

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

  function normalizeSvgSnippet(raw) {
    const trimmed = (raw || "").trim();
    if (!trimmed) return "";
    if (/^<section\b/i.test(trimmed)) return trimmed;
    if (/^<svg\b/i.test(trimmed)) {
      return `<section style="margin:24px 0;padding:0;line-height:0;font-size:0;border-radius:16px;overflow:hidden;">${trimmed}</section>`;
    }
    return trimmed;
  }

  // ---------- 轻提示（可打断、支持撤销） ----------

  function showToast(msg, { duration = 1800, onUndo = null } = {}) {
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

  // ---------- 存储持久化 ----------

  function saveState() {
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({
        [STORAGE_KEY]: {
          packTitle: state.packTitle,
          modules: state.modules,
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
      if (saved && Array.isArray(saved.modules) && saved.modules.length > 0) {
        state.packTitle = saved.packTitle || "已导入模块";
        state.modules = saved.modules;
        state.previewBg = saved.previewBg === "dark" ? "dark" : "light";
        applyPreviewBg(state.previewBg, false);
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
    // 同步所有卡片主按钮文案
    document.querySelectorAll(".act-primary").forEach((btn) => {
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
      if (msg && msg.type === "FEIS_TAB_CONTEXT") {
        probeActiveTab();
      }
    });
  }

  // ---------- 复制与插入核心动作 ----------

  async function copyRichHtml(html) {
    if (navigator.clipboard && window.ClipboardItem) {
      await navigator.clipboard.write([
        new ClipboardItem({
          "text/html": new Blob([html], { type: "text/html" }),
          "text/plain": new Blob([html], { type: "text/plain" })
        })
      ]);
      return true;
    }
    // 兜底隐藏选区复制
    const box = document.createElement("div");
    box.style.cssText = "position:fixed;left:-9999px;top:0;opacity:0;";
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

  async function triggerModuleAction(mod, cardEl, primaryBtn, forceCopyOnly = false) {
    let insertedDirect = false;

    if (!forceCopyOnly && state.wechatReady && state.activeTabId && typeof chrome !== "undefined" && chrome.tabs) {
      insertedDirect = await new Promise((resolve) => {
        chrome.tabs.sendMessage(
          state.activeTabId,
          { type: "FEIS_INSERT_HTML", html: mod.html },
          (res) => {
            if (chrome.runtime.lastError || !res || !res.ok) resolve(false);
            else resolve(true);
          }
        );
      });
    }

    if (!insertedDirect) {
      try {
        await copyRichHtml(mod.html);
      } catch {
        showToast("复制受限，请重试或检查剪贴板权限");
        return;
      }
    }

    // 标记已使用状态 + 按钮苹果级完成态微动效
    mod.used = true;
    cardEl.dataset.used = "true";
    saveState();

    const labelEl = primaryBtn.querySelector(".act-label");
    const iconEl = primaryBtn.querySelector(".act-icon");
    primaryBtn.dataset.state = "success";
    labelEl.textContent = insertedDirect ? "已插入正文" : "已复制";
    iconEl.innerHTML = `<svg viewBox="0 0 18 18" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path class="check-path" d="M3.8 9.4L7.4 13L14.2 5.4"/></svg>`;

    showToast(
      insertedDirect
        ? `已插入「${mod.name}」到编辑器`
        : `已复制「${mod.name}」，在公众号按 ⌘V 粘贴`
    );

    clearTimeout(primaryBtn._resetTimer);
    primaryBtn._resetTimer = setTimeout(() => {
      primaryBtn.dataset.state = "idle";
      labelEl.textContent = state.wechatReady ? "插入光标处" : "复制到公众号";
      iconEl.innerHTML = "";
    }, 1500);
  }

  // ---------- 文件解析（支持 feis-pack.json / 单文件 .html / .svg） ----------

  async function importFiles(fileList) {
    const files = Array.from(fileList || []);
    if (files.length === 0) return;

    const incoming = [];
    let newTitle = "";

    for (const file of files) {
      const text = await file.text();
      const lower = file.name.toLowerCase();

      if (lower.endsWith(".json")) {
        try {
          const parsed = JSON.parse(text);
          if (Array.isArray(parsed.modules)) {
            newTitle = parsed.title || file.name.replace(/\.json$/i, "");
            for (const m of parsed.modules) {
              const html = normalizeSvgSnippet(m.html || "");
              if (!html) continue;
              incoming.push({
                id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
                name: m.name || m.file || "未命名模块",
                type: m.type || "svg",
                html,
                lint: lintHtml(html),
                used: false
              });
            }
          }
        } catch {
          showToast(`无法解析 ${file.name}，请确认是有效的 feis-pack.json`);
        }
      } else if (lower.endsWith(".html") || lower.endsWith(".htm") || lower.endsWith(".svg")) {
        const html = normalizeSvgSnippet(text);
        if (html.includes("<svg")) {
          incoming.push({
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

    if (incoming.length === 0) {
      showToast("未识别到有效的 SVG 模块文件");
      return;
    }

    if (newTitle) {
      state.packTitle = newTitle;
      state.modules = incoming;
    } else {
      if (!state.packTitle) state.packTitle = incoming.length === 1 ? incoming[0].name : "自定义模块组";
      state.modules = [...state.modules, ...incoming];
    }

    saveState();
    render();
    showToast(`已导入 ${incoming.length} 个模块`);
  }

  async function importFromClipboard() {
    try {
      const text = await navigator.clipboard.readText();
      if (!text || !text.includes("<svg")) {
        showToast("剪贴板里没有检测到 SVG 代码");
        return;
      }
      const html = normalizeSvgSnippet(text);
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
      saveState();
      render();
      showToast("已从剪贴板导入 1 个模块");
    } catch {
      showToast("读取剪贴板失败，请直接拖入文件");
    }
  }

  // ---------- 视图渲染 ----------

  function applyPreviewBg(mode, persist = true) {
    state.previewBg = mode === "dark" ? "dark" : "light";
    $app.dataset.previewBg = state.previewBg;
    $segBtns.forEach((btn) => {
      btn.setAttribute("aria-checked", btn.dataset.bg === state.previewBg ? "true" : "false");
    });
    if (persist) saveState();
  }

  function render() {
    const hasItems = state.modules.length > 0;
    $app.dataset.hasItems = hasItems ? "true" : "false";
    $packTitle.textContent = state.packTitle || "未命名模块包";
    const totalKb = state.modules.reduce((acc, m) => acc + (m.lint?.bytes || 0), 0) / 1024;
    $packStat.textContent = `${state.modules.length} 个模块 · ${totalKb.toFixed(1)}KB`;

    $moduleList.innerHTML = "";
    if (!hasItems) return;

    state.modules.forEach((mod, idx) => {
      const card = document.createElement("article");
      card.className = "mod-card";
      card.dataset.used = mod.used ? "true" : "false";
      card.style.setProperty("--enter-delay", `${Math.min(idx * 50, 220)}ms`);

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

      // 点击已用徽章可收回标记
      card.querySelector(".done-badge").onclick = () => {
        mod.used = false;
        card.dataset.used = "false";
        saveState();
      };

      // 单卡平滑移除 + 4 秒撤销
      card.querySelector(".remove-btn").onclick = () => {
        const snapshot = {
          packTitle: state.packTitle,
          modules: state.modules.map((m) => ({ ...m }))
        };
        card.classList.add("is-removing");
        setTimeout(() => {
          state.modules = state.modules.filter((m) => m.id !== mod.id);
          if (state.modules.length === 0) state.packTitle = "";
          saveState();
          render();
          showToast(`已移除「${mod.name}」`, {
            duration: 4000,
            onUndo: () => {
              state.packTitle = snapshot.packTitle;
              state.modules = snapshot.modules;
              saveState();
              render();
              showToast("已恢复模块");
            }
          });
        }, 180);
      };

      // 一键净化微信禁用项（原地局部更新，避免整页重绘导致其他卡片闪烁）
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
          const newKb = (mod.lint.bytes / 1024).toFixed(1);
          card.querySelector(".mod-meta").textContent = `${newKb}KB · ${mod.type}`;
          const totalKbNow = state.modules.reduce((acc, m) => acc + (m.lint?.bytes || 0), 0) / 1024;
          $packStat.textContent = `${state.modules.length} 个模块 · ${totalKbNow.toFixed(1)}KB`;
          showToast(`已净化「${mod.name}」，现已符合微信规则`);
        };
      }

      // 主按钮（自动插入或复制）
      const primaryBtn = card.querySelector(".act-primary");
      primaryBtn.onclick = () => triggerModuleAction(mod, card, primaryBtn, false);

      // 纯复制按钮
      card.querySelector(".btn-copy-only").onclick = () => triggerModuleAction(mod, card, primaryBtn, true);

      // 单卡片重播
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

  $segBtns.forEach((btn) => {
    btn.onclick = () => applyPreviewBg(btn.dataset.bg);
  });

  $btnReplayAll.onclick = () => {
    $btnReplayAll.classList.remove("spinning");
    void $btnReplayAll.offsetWidth;
    $btnReplayAll.classList.add("spinning");
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

  // 两段式防误触清空 + 点击外部自动收回 + 4 秒撤销
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
      modules: state.modules.map((m) => ({ ...m }))
    };
    state.packTitle = "";
    state.modules = [];
    saveState();
    render();
    showToast("已清空模块列表", {
      duration: 4200,
      onUndo: () => {
        state.packTitle = snapshot.packTitle;
        state.modules = snapshot.modules;
        saveState();
        render();
        showToast("已恢复模块列表");
      }
    });
  };

  // 全局拖放感应
  let dragDepth = 0;
  window.addEventListener("dragenter", (e) => {
    e.preventDefault();
    dragDepth += 1;
    if (state.modules.length === 0) {
      $dropzone.classList.add("is-dragover");
    } else {
      $dragOverlay.classList.add("visible");
    }
  });
  window.addEventListener("dragover", (e) => {
    e.preventDefault();
  });
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
  restoreState();
  probeActiveTab();
})();
