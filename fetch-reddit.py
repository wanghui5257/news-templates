#!/usr/bin/env python3
"""
Reddit 新闻抓取脚本
使用 Reddit 官方 API (PRAW) 抓取新闻数据
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import praw
except ImportError:
    print("❌ 缺少依赖：pip install praw")
    sys.exit(1)


# 配置
SUBREDDITS = {
    'worldnews': '国际新闻',
    'technology': '科技趋势',
    'artificial': 'AI 新闻',
    'science': '科技趋势'
}

# 从环境变量读取 API 密钥
REDDIT_CONFIG = {
    'client_id': os.getenv('REDDIT_CLIENT_ID', ''),
    'client_secret': os.getenv('REDDIT_CLIENT_SECRET', ''),
    'user_agent': os.getenv('REDDIT_USER_AGENT', 'news-worker/1.0 by news-worker')
}


def init_reddit():
    """初始化 Reddit API"""
    if not REDDIT_CONFIG['client_id'] or not REDDIT_CONFIG['client_secret']:
        print("⚠️ 警告：未配置 Reddit API 密钥")
        print("请设置环境变量:")
        print("  export REDDIT_CLIENT_ID='your_client_id'")
        print("  export REDDIT_CLIENT_SECRET='your_client_secret'")
        return None
    
    try:
        reddit = praw.Reddit(**REDDIT_CONFIG)
        reddit.user.me()  # 测试连接
        print("✅ Reddit API 连接成功")
        return reddit
    except Exception as e:
        print(f"❌ Reddit API 连接失败：{e}")
        return None


def fetch_subreddit_news(subreddit_name, category_name, limit=5):
    """抓取单个 Subreddit 的新闻"""
    news_items = []
    
    try:
        subreddit = reddit.subreddit(subreddit_name)
        
        for post in subreddit.hot(limit=limit):
            # 过滤低质量帖子
            if post.score < 10:
                continue
            
            # 跳过置顶帖
            if post.stickied:
                continue
            
            # 创建新闻条目
            item = {
                'title': post.title,
                'link': f'https://reddit.com{post.permalink}',
                'source': f'Reddit r/{subreddit_name}',
                'summary': post.selftext[:200] if post.selftext else 'Click to read discussion',
                'score': post.score,
                'num_comments': post.num_comments,
                'created': datetime.fromtimestamp(post.created_utc)
            }
            
            news_items.append(item)
    
    except Exception as e:
        print(f"⚠️ 抓取 r/{subreddit_name} 失败：{e}")
    
    return news_items


def map_to_categories(all_news):
    """将抓取的数据映射到标准分类"""
    categories = {
        '国际新闻': [],
        '中国新闻': [],
        'AI 新闻': [],
        '科技趋势': []
    }
    
    for subreddit_name, category_name in SUBREDDITS.items():
        if category_name in categories:
            news_items = fetch_subreddit_news(subreddit_name, category_name, limit=5)
            categories[category_name].extend(news_items[:5])
    
    return categories


def generate_markdown(categories):
    """生成标准 Markdown 格式"""
    shanghai_tz = timezone(timedelta(hours=8))
    now = datetime.now(shanghai_tz)
    
    md = ["# 时事新闻 (Reddit)", ""]
    md.append(f"**抓取时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**数据来源**: Reddit API")
    md.append("")
    
    category_icons = {
        '国际新闻': '🌍',
        '中国新闻': '🇨🇳',
        'AI 新闻': '🤖',
        '科技趋势': '📱'
    }
    
    for category_name, items in categories.items():
        if not items:
            continue
        
        icon = category_icons.get(category_name, '')
        md.append(f"### 【{icon} {category_name}】")
        md.append("")
        
        for idx, item in enumerate(items[:5], 1):
            md.append(f"#### {idx}. {item['title']}")
            md.append("")
            md.append(f"- **来源**: {item['source']}")
            md.append(f"- **链接**: {item['link']}")
            md.append(f"- **摘要**: {item['summary']}")
            md.append(f"- **热度**: 🔼 {item['score']} | 💬 {item['num_comments']}")
            md.append("")
    
    return "\n".join(md)


def save_to_minio(markdown_content, output_path=None):
    """保存到 MinIO 或本地"""
    if output_path:
        # 保存到本地
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ 保存到：{output_file}")
        return str(output_file)
    
    # 保存到 MinIO (需要 mc 命令)
    import subprocess
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(markdown_content)
        temp_path = f.name
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    minio_path = f"shared/news-data/reddit-news-{timestamp}.md"
    
    cmd = ['mc', 'cp', temp_path, f'hiclaw/hiclaw-storage/{minio_path}']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    os.unlink(temp_path)
    
    if result.returncode == 0:
        print(f"✅ 保存到 MinIO: {minio_path}")
        return minio_path
    else:
        print(f"❌ MinIO 保存失败：{result.stderr}")
        return None


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Reddit 新闻抓取')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--limit', '-l', type=int, default=5, help='每类新闻数量')
    parser.add_argument('--test', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📰 Reddit 新闻抓取")
    print("=" * 60)
    
    # 初始化 Reddit
    global reddit
    reddit = init_reddit()
    
    if not reddit:
        print("\n⚠️ 未配置 Reddit API，使用测试数据")
        if args.test:
            # 测试数据
            categories = {
                '国际新闻': [{
                    'title': 'Test News from Reddit',
                    'link': 'https://reddit.com/test',
                    'source': 'Reddit r/worldnews',
                    'summary': 'This is a test news item',
                    'score': 100,
                    'num_comments': 20
                }],
                '中国新闻': [],
                'AI 新闻': [],
                '科技趋势': []
            }
        else:
            sys.exit(1)
    else:
        # 抓取新闻
        print(f"\n📥 抓取新闻...")
        categories = {}
        
        for subreddit_name, category_name in SUBREDDITS.items():
            print(f"  抓取 r/{subreddit_name} → {category_name}")
            items = fetch_subreddit_news(subreddit_name, category_name, limit=args.limit)
            categories[category_name] = items
            print(f"    ✅ {len(items)} 条")
    
    # 生成 Markdown
    print(f"\n📝 生成 Markdown...")
    markdown = generate_markdown(categories)
    
    # 保存
    if args.output:
        save_to_minio(markdown, args.output)
    else:
        # 输出到 stdout
        print("\n" + markdown)
    
    print("=" * 60)
    print("✅ 抓取完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
