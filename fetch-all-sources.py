#!/usr/bin/env python3
"""
统一数据抓取入口
整合 Reddit、YouTube、Amazon 等数据源
"""

import os
import sys
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 脚本路径
SCRIPT_DIR = Path(__file__).parent
REDDIT_SCRIPT = SCRIPT_DIR / "fetch-reddit.py"
YOUTUBE_SCRIPT = SCRIPT_DIR / "fetch-youtube.py"
AMAZON_SCRIPT = SCRIPT_DIR / "fetch-amazon-rss.py"

# 输出目录
OUTPUT_DIR = Path.home() / "news-worker-tmp" / "fetched-data"


def log(message, level="INFO"):
    """记录日志"""
    shanghai_tz = timezone(timedelta(hours=8))
    timestamp = datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def run_script(script_path, output_file, news_type):
    """运行抓取脚本"""
    if not script_path.exists():
        log(f"脚本不存在：{script_path}", "ERROR")
        return False
    
    cmd = [
        "python3", str(script_path),
        "--output", str(output_file)
    ]
    
    log(f"执行：{' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        log(f"错误：{result.stderr}", "ERROR")
    
    return result.returncode == 0


def fetch_all_sources():
    """抓取所有数据源"""
    log("=" * 60)
    log("📊 统一数据抓取")
    log("=" * 60)
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    results = {}
    
    # 1. Reddit
    log("\n--- Reddit ---")
    reddit_output = OUTPUT_DIR / f"reddit-{timestamp}.md"
    results['reddit'] = run_script(REDDIT_SCRIPT, reddit_output, 'news')
    
    # 2. YouTube
    log("\n--- YouTube ---")
    youtube_output = OUTPUT_DIR / f"youtube-{timestamp}.md"
    results['youtube'] = run_script(YOUTUBE_SCRIPT, youtube_output, 'news')
    
    # 3. Amazon RSS
    log("\n--- Amazon RSS ---")
    amazon_output = OUTPUT_DIR / f"amazon-{timestamp}.md"
    results['amazon'] = run_script(AMAZON_SCRIPT, amazon_output, 'ecommerce')
    
    # 总结
    log("\n" + "=" * 60)
    log("📊 抓取总结:")
    for source, success in results.items():
        status = "✅" if success else "❌"
        log(f"  {status} {source}")
    log("=" * 60)
    
    return all(results.values())


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='统一数据抓取入口')
    parser.add_argument('--source', '-s', choices=['reddit', 'youtube', 'amazon', 'all'],
                       default='all', help='数据源')
    parser.add_argument('--test', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    if args.test:
        log("测试模式：检查脚本依赖")
        
        # 检查依赖
        log("检查 Python 依赖...")
        try:
            import praw
            log("✅ praw (Reddit)")
        except ImportError:
            log("❌ praw 未安装：pip install praw")
        
        try:
            from googleapiclient.discovery import build
            log("✅ google-api-python-client (YouTube)")
        except ImportError:
            log("❌ google-api-python-client 未安装：pip install google-api-python-client")
        
        try:
            import feedparser
            log("✅ feedparser (RSS)")
        except ImportError:
            log("❌ feedparser 未安装：pip install feedparser")
        
        # 检查环境变量
        log("\n检查环境变量...")
        if os.getenv('REDDIT_CLIENT_ID'):
            log("✅ REDDIT_CLIENT_ID 已配置")
        else:
            log("⚠️ REDDIT_CLIENT_ID 未配置")
        
        if os.getenv('YOUTUBE_API_KEY'):
            log("✅ YOUTUBE_API_KEY 已配置")
        else:
            log("⚠️ YOUTUBE_API_KEY 未配置")
        
        return 0
    
    if args.source == 'all':
        success = fetch_all_sources()
    else:
        log(f"抓取 {args.source}...")
        # 实现单个源抓取
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
