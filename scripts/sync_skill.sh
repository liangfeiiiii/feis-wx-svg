#!/usr/bin/env bash
# 同步纪律：永远先改本地 ~/.gemini/config/skills/feis-wx-svg/SKILL.md，再运行本脚本同步到 Git 仓库根目录。
set -euo pipefail

LOCAL_SKILL="$HOME/.gemini/config/skills/feis-wx-svg/SKILL.md"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_SKILL="$REPO_ROOT/SKILL.md"

if [ ! -f "$LOCAL_SKILL" ]; then
  echo "❌ 未找到本地技能文件：$LOCAL_SKILL"
  exit 1
fi

cp "$LOCAL_SKILL" "$TARGET_SKILL"
echo "✅ 已同步本地 SKILL.md → $TARGET_SKILL"
