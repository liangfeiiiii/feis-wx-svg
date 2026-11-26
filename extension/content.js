// 非叔 SVG 助手 · 微信公众号编辑器桥接脚本
// 仅运行在 https://mp.weixin.qq.com/*，不主动修改页面 DOM，只在用户点击「插入」时把干净的 SVG 片段插入光标处。

(() => {
  function findEditorTarget() {
    // 1. 新版公众号图文编辑器（ProseMirror / contenteditable）
    const pm = document.querySelector(".ProseMirror[contenteditable='true']");
    if (pm) return { kind: "contenteditable", el: pm, doc: document, win: window };

    // 2. 经典 UEditor iframe 编辑器
    const iframes = Array.from(document.querySelectorAll("iframe"));
    for (const frame of iframes) {
      try {
        const fdoc = frame.contentDocument;
        if (!fdoc || !fdoc.body) continue;
        if (
          fdoc.body.isContentEditable ||
          fdoc.body.classList.contains("view") ||
          fdoc.designMode === "on"
        ) {
          return { kind: "iframe", el: fdoc.body, doc: fdoc, win: frame.contentWindow };
        }
      } catch {
        // 跨域 iframe 跳过
      }
    }

    // 3. 兜底查找页面上可见的大型 contenteditable 区域
    const editables = Array.from(document.querySelectorAll("[contenteditable='true']")).filter(
      (el) => el.getBoundingClientRect().height > 120
    );
    if (editables.length > 0) {
      return { kind: "contenteditable", el: editables[0], doc: document, win: window };
    }
    return null;
  }

  function insertHtmlIntoTarget(target, html) {
    const { el, doc, win } = target;
    el.focus();

    // 优先通过模拟 ClipboardEvent paste，让微信编辑器原生接管结构与撤销栈（⌘Z 可直接撤销）
    try {
      const dt = new DataTransfer();
      dt.setData("text/html", html);
      dt.setData("text/plain", " ");
      const pasteEvent = new ClipboardEvent("paste", {
        bubbles: true,
        cancelable: true,
        clipboardData: dt
      });
      const handled = !el.dispatchEvent(pasteEvent);
      if (handled) {
        return { ok: true, method: "paste-event" };
      }
    } catch {
      // 降级到 execCommand
    }

    // 次选：execCommand insertHTML（同样支持编辑器撤销栈）
    try {
      const sel = win.getSelection();
      if (sel && sel.rangeCount === 0) {
        const range = doc.createRange();
        range.selectNodeContents(el);
        range.collapse(false);
        sel.removeAllRanges();
        sel.addRange(range);
      }
      const ok = doc.execCommand("insertHTML", false, html);
      if (ok) {
        return { ok: true, method: "execCommand" };
      }
    } catch {
      // 忽略，交由侧边栏降级为剪贴板复制
    }

    return { ok: false, reason: "editor-rejected" };
  }

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (!msg || !msg.type) return;

    if (msg.type === "FEIS_PING_EDITOR") {
      const target = findEditorTarget();
      sendResponse({ ready: Boolean(target), kind: target ? target.kind : null });
      return;
    }

    if (msg.type === "FEIS_INSERT_HTML") {
      const target = findEditorTarget();
      if (!target) {
        sendResponse({ ok: false, reason: "no-editor" });
        return;
      }
      const res = insertHtmlIntoTarget(target, msg.html || "");
      sendResponse(res);
    }
  });
})();
