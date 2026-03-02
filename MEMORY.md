# 长期记忆 - MEMORY.md

> 这是跨会话的核心记忆，每次主会话启动时加载。
> 只保留精华信息，定期从每日记录中提炼更新。

---

## 用户画像

### 基本信息
- **身份**: 研究生
- **目标**: 论文投稿 + 数据开发实习
- **核心痛点**: 需要快速掌握尚硅谷电商数仓6.0课程

### 偏好与习惯
- 使用 DanKoe 3-2-1 时间分配法
- 希望用结构化学习材料替代看视频
- 重视面试准备和项目实战

---

## 关键决策与约定

### Memory 管理策略 [2026-03-02]
- **短期记忆**: memory/YYYY-MM-DD.md - 每日原始记录
- **中期记忆**: memory/*.md (projects.md, system-config.md等) - 专题追踪
- **长期记忆**: MEMORY.md - 精华提炼
- **同步机制**: GitHub自动同步，确保不丢失

### 工作模式约定
- 重要任务先写文件再执行（防遗忘）
- 每30分钟自动保存进度到文件
- 完成后立即commit到GitHub

---

## 进行中的项目

### 尚硅谷电商数仓6.0文档加工 [进行中]
- **目标**: 将5个核心文档+12个辅助文档加工成结构化学习材料
- **标准模板**: doc1_用户行为数据采集.md 格式
- **输出位置**: learning_materials/processed_lessons/
- **GitHub**: https://github.com/VitoHawk35/Openclaw_learning

---

## 技术债务与改进点

### 已解决
- ✅ Gateway token问题：通过配置remote.token解决
- ✅ 文件传输问题：通过GitHub同步解决
- ✅ 任务遗忘问题：建立文件系统+persistence机制

### 待优化
- ⏳ Cron服务仍不可用（gateway token mismatch）
- ⏳ Sub-agent需要手动启动ssh-agent

---

## 常用资源

### 本地路径
- Workspace: /home/admin/.openclaw/workspace
- 学习资料: /learning_materials/vito-6.0-materials/
- 加工后文档: learning_materials/processed_lessons/

### 工具脚本
- memory_manager.py: 自动化memory管理
- process_docx_to_lesson.py: 文档批量加工

---

## 经验教训

1. **不要承诺无法保证的事**: 比如"9点给你结果"，因为会话可能中断
2. **文件系统比内存可靠**: 所有重要状态必须持久化到文件
3. **Git是最佳备份**: 定期commit防止数据丢失
4. **验证后再批量**: 先做一个样本验证质量，再批量处理

---

*最后更新: 2026-03-02*
