#!/usr/bin/env python3
"""
B站课程字幕批量下载器
支持：尚硅谷大数据项目【电商数仓6.0】
用法：python3 bilibili_subtitle_downloader.py <课程URL或BV号>
"""

import sys
import os
import re
import json
import requests
import subprocess
from urllib.parse import urlencode
from pathlib import Path

class BilibiliSubtitleDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com'
        })
        self.output_dir = Path.home() / '.openclaw' / 'workspace' / 'learning_materials' / 'bilibili_subtitles'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_bvid(self, url_or_bvid):
        """从URL中提取BV号"""
        if url_or_bvid.startswith('BV'):
            return url_or_bvid
        match = re.search(r'BV([a-zA-Z0-9]+)', url_or_bvid)
        if match:
            return 'BV' + match.group(1)
        return None
    
    def get_video_info(self, bvid):
        """获取视频基本信息"""
        api_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
        try:
            response = self.session.get(api_url, timeout=10)
            data = response.json()
            if data.get('code') == 0:
                return data['data']
            else:
                print(f"获取视频信息失败: {data.get('message', '未知错误')}")
                return None
        except Exception as e:
            print(f"请求失败: {e}")
            return None
    
    def get_subtitle_url(self, cid, bvid):
        """获取字幕URL"""
        api_url = f'https://api.bilibili.com/x/player/wbi/v2?cid={cid}&bvid={bvid}'
        try:
            response = self.session.get(api_url, timeout=10)
            data = response.json()
            if data.get('code') == 0:
                subtitle_list = data['data'].get('subtitle', {}).get('subtitles', [])
                if subtitle_list:
                    # 优先选中文AI字幕，其次普通中文字幕
                    for sub in subtitle_list:
                        if 'ai' in sub.get('lan', '').lower():
                            return 'https:' + sub['subtitle_url']
                    return 'https:' + subtitle_list[0]['subtitle_url']
            return None
        except Exception as e:
            print(f"获取字幕URL失败: {e}")
            return None
    
    def download_subtitle(self, subtitle_url, output_path):
        """下载并转换字幕"""
        try:
            response = self.session.get(subtitle_url, timeout=10)
            subtitle_data = response.json()
            
            # 转换为纯文本
            text_lines = []
            for item in subtitle_data.get('body', []):
                content = item.get('content', '').strip()
                if content:
                    text_lines.append(content)
            
            # 保存为文本文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(text_lines))
            
            return True
        except Exception as e:
            print(f"下载字幕失败: {e}")
            return False
    
    def process_single_video(self, bvid, index=None):
        """处理单个视频"""
        prefix = f"[{index:03d}] " if index else ""
        print(f"{prefix}正在处理: {bvid}")
        
        # 获取视频信息
        info = self.get_video_info(bvid)
        if not info:
            return False
        
        title = info['title']
        cid = info['cid']
        
        # 清理文件名
        safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:80]
        output_file = self.output_dir / f"{prefix}{safe_title}.txt"
        
        print(f"  标题: {title}")
        
        # 获取字幕URL
        subtitle_url = self.get_subtitle_url(cid, bvid)
        if not subtitle_url:
            print(f"  ⚠️ 该视频没有字幕")
            return False
        
        # 下载字幕
        if self.download_subtitle(subtitle_url, output_file):
            print(f"  ✅ 已保存: {output_file.name}")
            return True
        else:
            return False
    
    def search_course_videos(self, keyword="尚硅谷大数据项目之电商数仓"):
        """搜索课程相关视频"""
        search_api = 'https://api.bilibili.com/x/web-interface/search/type'
        params = {
            'search_type': 'video',
            'keyword': keyword,
            'page': 1,
            'pagesize': 50
        }
        
        try:
            response = self.session.get(search_api, params=params, timeout=10)
            data = response.json()
            if data.get('code') == 0:
                videos = data['data'].get('result', [])
                bvids = []
                for v in videos:
                    bvid = v.get('bvid')
                    title = v.get('title', '')
                    if bvid and ('电商数仓' in title or '尚硅谷' in title):
                        bvids.append((bvid, title))
                return bvids
            return []
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def batch_download(self, bvids):
        """批量下载"""
        success_count = 0
        for i, (bvid, title) in enumerate(bvids, 1):
            if self.process_single_video(bvid, i):
                success_count += 1
        
        print(f"\n{'='*50}")
        print(f"下载完成: {success_count}/{len(bvids)} 个视频")
        print(f"保存位置: {self.output_dir}")
        return success_count


def main():
    downloader = BilibiliSubtitleDownloader()
    
    if len(sys.argv) > 1:
        # 从命令行参数获取BV号或URL
        input_arg = sys.argv[1]
        bvid = downloader.extract_bvid(input_arg)
        if bvid:
            downloader.process_single_video(bvid)
        else:
            print("无法识别BV号，请提供正确的B站链接或BV号")
    else:
        # 交互模式
        print("=" * 60)
        print("B站课程字幕批量下载器")
        print("=" * 60)
        print("\n选项:")
        print("1. 搜索尚硅谷电商数仓课程")
        print("2. 输入单个视频链接/BV号")
        print("3. 从文件批量导入BV号列表")
        
        choice = input("\n请选择 (1/2/3): ").strip()
        
        if choice == '1':
            print("\n正在搜索课程视频...")
            videos = downloader.search_course_videos()
            if videos:
                print(f"找到 {len(videos)} 个相关视频")
                for i, (bvid, title) in enumerate(videos[:10], 1):
                    print(f"{i}. {title} ({bvid})")
                
                confirm = input(f"\n是否下载全部 {len(videos)} 个视频的字幕? (y/n): ")
                if confirm.lower() == 'y':
                    downloader.batch_download(videos)
            else:
                print("未找到相关视频")
                
        elif choice == '2':
            url = input("请输入B站视频链接或BV号: ").strip()
            bvid = downloader.extract_bvid(url)
            if bvid:
                downloader.process_single_video(bvid)
            else:
                print("无法识别BV号")
                
        elif choice == '3':
            file_path = input("请输入BV号列表文件路径: ").strip()
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    lines = [line.strip() for line in f if line.strip()]
                bvids = [(downloader.extract_bvid(line), line) for line in lines]
                bvids = [(b, t) for b, t in bvids if b]
                print(f"从文件读取了 {len(bvids)} 个BV号")
                downloader.batch_download(bvids)
            else:
                print("文件不存在")
        else:
            print("无效选择")


if __name__ == '__main__':
    main()
