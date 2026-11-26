// 非叔 SVG 助手 · 后台服务
// 负责：点击扩展图标直接开关侧边栏；感知活动标签页切换，向侧边栏同步当前是否在微信公众号编辑器。

chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch(() => {});

function isWechatMpUrl(url) {
  return typeof url === "string" && url.startsWith("https://mp.weixin.qq.com/");
}

function notifyTabContext(tab) {
  if (!tab) return;
  chrome.runtime
    .sendMessage({
      type: "FEIS_TAB_CONTEXT",
      tabId: tab.id,
      isWechat: isWechatMpUrl(tab.url),
      url: tab.url || ""
    })
    .catch(() => {
      // 侧边栏未打开时忽略
    });
}

chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  try {
    const tab = await chrome.tabs.get(tabId);
    notifyTabContext(tab);
  } catch {
    // ignore
  }
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (tab.active && (changeInfo.status === "complete" || changeInfo.url)) {
    notifyTabContext(tab);
  }
});
