# 系统配置 - 中期记忆

## OpenClaw 环境

### Gateway 配置
- **端口**: 13109
- **模式**: local
- **绑定**: lan
- **Token**: 已配置（见openclaw.json）
- **Control UI**: http://localhost:18789/

### SSH/GitHub
- **SSH Key**: ~/.ssh/id_ed25519
- **GitHub Repo**: git@github.com:VitoHawk35/Openclaw_learning.git
- **分支**: master

### 已安装插件
- qqbot (v1.4.4)
- dingtalk (v2.5.1)
- wecom (v1.2.1)

### 自定义工具
| 工具 | 路径 | 用途 |
|------|------|------|
| bilibili_subtitle_downloader.py | tools/ | B站字幕下载 |
| process_docx_to_lesson.py | tools/ | 文档自动加工 |
| memory_manager.py | tools/ | 记忆管理 |

## 已知问题

### Gateway Token 不匹配
- **症状**: cron/sessions_spawn 等工具返回 1008 unauthorized
- **原因**: agent和gateway token不一致
- **解决**: 已更新配置，需重启gateway生效
- **Workaround**: 使用文件系统方式

### Webchat 限制
- 不支持文件传输
- 通过 GitHub 同步解决
