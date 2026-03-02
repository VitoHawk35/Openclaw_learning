#!/bin/bash
# 会话结束时的自动保存脚本

echo "=== Session End Memory Sync ==="
echo "Time: $(date)"

# 1. 确保所有修改被记录
cd /home/admin/.openclaw/workspace

# 2. 启动 SSH agent
export SSH_AUTH_SOCK="/tmp/ssh-agent-$$.sock"
ssh-agent -a "$SSH_AUTH_SOCK" > /dev/null
ssh-add ~/.ssh/id_ed25519 2>/dev/null

# 3. Git 提交和推送
git add -A
git commit -m "Session sync: $(date '+%Y-%m-%d %H:%M')" --quiet

if git push origin master --quiet 2>/dev/null; then
    echo "✅ Synced to GitHub"
else
    echo "⚠️  Push failed, but changes are committed locally"
fi

# 4. 清理
rm -f "$SSH_AUTH_SOCK"

echo "=== Done ==="
