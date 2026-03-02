#!/usr/bin/env python3
"""
OpenClaw Memory 管理工具
自动化维护短期/中期/长期记忆
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/home/admin/.openclaw/workspace"
MEMORY_DIR = os.path.join(WORKSPACE, "memory")

def get_today_file():
    """获取今天的记忆文件路径"""
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(MEMORY_DIR, f"{today}.md")

def ensure_memory_dir():
    """确保 memory 目录存在"""
    os.makedirs(MEMORY_DIR, exist_ok=True)

def append_to_today(content, category="general"):
    """追加内容到今日记忆"""
    ensure_memory_dir()
    filepath = get_today_file()
    
    timestamp = datetime.now().strftime("%H:%M")
    entry = f"\n## [{timestamp}] {category}\n\n{content}\n"
    
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(entry)
    
    return filepath

def create_daily_summary(date_str=None):
    """
    将某天的记忆整理为摘要
    用于定期归档到 MEMORY.md
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    filepath = os.path.join(MEMORY_DIR, f"{date_str}.md")
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取关键信息
    summary = {
        "date": date_str,
        "raw_size": len(content),
        "key_decisions": [],
        "action_items": [],
        "lessons_learned": []
    }
    
    # 简单规则提取（可扩展为LLM调用）
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if '[决策]' in line or '决定' in line or '确定' in line:
            summary["key_decisions"].append(line)
        elif '[行动]' in line or 'TODO' in line or '待办' in line:
            summary["action_items"].append(line)
        elif '[教训]' in line or '问题' in line or '错误' in line:
            summary["lessons_learned"].append(line)
    
    return summary

def update_long_term_memory(summaries):
    """
    更新 MEMORY.md
    summaries: list of daily summaries
    """
    memory_path = os.path.join(WORKSPACE, "MEMORY.md")
    
    # 读取现有内容
    existing = ""
    if os.path.exists(memory_path):
        with open(memory_path, 'r', encoding='utf-8') as f:
            existing = f.read()
    
    # 生成新内容
    new_section = f"\n\n## 记忆更新 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    for summary in summaries:
        new_section += f"\n### {summary['date']}\n"
        
        if summary["key_decisions"]:
            new_section += "\n**关键决策**:\n"
            for d in summary["key_decisions"][:5]:  # 最多5条
                new_section += f"- {d}\n"
        
        if summary["action_items"]:
            new_section += "\n**待办事项**:\n"
            for a in summary["action_items"][:5]:
                new_section += f"- [ ] {a}\n"
        
        if summary["lessons_learned"]:
            new_section += "\n**经验教训**:\n"
            for l in summary["lessons_learned"][:3]:
                new_section += f"- {l}\n"
    
    # 写入文件
    with open(memory_path, 'w', encoding='utf-8') as f:
        f.write(existing + new_section)
    
    return memory_path

def cleanup_old_memories(days=30):
    """
    清理旧的记忆文件
    超过days天的文件会被归档压缩
    """
    cutoff = datetime.now() - timedelta(days=days)
    
    archived = []
    for filename in os.listdir(MEMORY_DIR):
        if not filename.endswith('.md'):
            continue
        
        # 尝试解析日期
        try:
            date_str = filename.replace('.md', '')
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            if file_date < cutoff:
                # 归档处理：移动到 archive 子目录
                archive_dir = os.path.join(MEMORY_DIR, "archive")
                os.makedirs(archive_dir, exist_ok=True)
                
                src = os.path.join(MEMORY_DIR, filename)
                dst = os.path.join(archive_dir, filename)
                os.rename(src, dst)
                archived.append(filename)
        except ValueError:
            # 不是日期命名的文件，跳过
            pass
    
    return archived

def get_recent_context(days=3):
    """
    获取最近几天的记忆作为上下文
    用于会话开始时加载
    """
    context = []
    
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        filepath = os.path.join(MEMORY_DIR, f"{date_str}.md")
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                context.append({
                    "date": date_str,
                    "content": content[:2000]  # 限制长度
                })
    
    return context

def sync_to_github():
    """
    自动同步到 GitHub
    """
    import subprocess
    
    try:
        # 启动 ssh-agent
        eval_cmd = 'eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519'
        subprocess.run(eval_cmd, shell=True, capture_output=True)
        
        # git 操作
        cmds = [
            "cd /home/admin/.openclaw/workspace",
            "git add -A",
            f'git commit -m "Memory sync: {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
            "git push origin master"
        ]
        
        result = subprocess.run(" && ".join(cmds), shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout + result.stderr
        
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    import sys
    
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    
    if command == "append":
        content = sys.argv[2] if len(sys.argv) > 2 else ""
        category = sys.argv[3] if len(sys.argv) > 3 else "general"
        path = append_to_today(content, category)
        print(f"Appended to: {path}")
    
    elif command == "summary":
        date = sys.argv[2] if len(sys.argv) > 2 else None
        summary = create_daily_summary(date)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    elif command == "update-long-term":
        # 获取最近7天的摘要
        summaries = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            s = create_daily_summary(date)
            if s:
                summaries.append(s)
        
        path = update_long_term_memory(summaries)
        print(f"Updated: {path}")
    
    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        archived = cleanup_old_memories(days)
        print(f"Archived {len(archived)} files: {archived}")
    
    elif command == "sync":
        success, msg = sync_to_github()
        print(f"Sync {'success' if success else 'failed'}: {msg}")
    
    elif command == "context":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        context = get_recent_context(days)
        print(json.dumps(context, indent=2, ensure_ascii=False))
    
    else:
        print("""
Usage: python memory_manager.py <command> [args]

Commands:
  append <content> [category]  - 追加到今日记忆
  summary [date]               - 生成某日摘要
  update-long-term             - 更新长期记忆
  cleanup [days]               - 清理旧记忆（默认30天）
  sync                         - 同步到 GitHub
  context [days]               - 获取近期上下文
        """)
