#!/usr/bin/env python3
"""
亚马逊官方 RSS 抓取脚本
抓取 Amazon Seller Central、Advertising 等官方博客
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import feedparser
except ImportError:
    print("❌ 缺少依赖：pip install feedparser")
    sys.exit(1)


# 配置 - RSS 源（亚马逊官方 + 跨境电商 + 科技媒体）
RSS_FEEDS = {
    # 亚马逊官方 - 官方发布
    'AWS': {
        'url': 'https://aws.amazon.com/blogs/aws/feed/',
        'category': '官方发布'
    },
    'GitHub Blog': {
        'url': 'https://github.blog/feed/',
        'category': '官方发布'
    },
    
    # 科技媒体 - 行业媒体
    'TechCrunch': {
        'url': 'https://techcrunch.com/feed/',
        'category': '行业媒体'
    },
    'The Verge': {
        'url': 'https://www.theverge.com/rss/index.xml',
        'category': '行业媒体'
    },
    
    # 跨境电商 - 行业媒体
    '亿邦动力': {
        'url': 'https://www.ebrun.com/feed/',
        'category': '行业媒体'
    },
    '雨果网': {
        'url': 'https://www.cifnews.com/feed',
        'category': '行业媒体'
    },
    
# 教程分析 - 添加更多数据源
    '卖家之家': {
        'url': 'https://www.maijiazhijia.com/feed',
        'category': '教程分析'
    },
    '跨境知道': {
        'url': 'https://www.kjzhidao.com/feed',
        'category': '教程分析'
    },
    'YouTube Creators': {
        'url': 'https://blog.youtube/feeds/posts/default?alt=rss',
        'category': '教程分析'
    },
    'Shopify Blog': {
        'url': 'https://www.shopify.com/blog/rss.xml',
        'category': '教程分析'
    },
    'AMZScout': {
        'url': 'https://amzscout.net/blog/feed/',
        'category': '教程分析'
    },
    'Jungle Scout': {
        'url': 'https://www.junglescout.com/blog/feed/',
        'category': '教程分析'
    }
}

# 论坛源 - 社区讨论
FORUM_FEEDS = {
    'Hacker News': {
        'url': 'https://news.ycombinator.com/rss',
        'category': '社区讨论'
    },
    'Reddit Technology': {
        'url': 'https://www.reddit.com/r/technology/.rss',
        'category': '社区讨论'
    },
    'Reddit World News': {
        'url': 'https://www.reddit.com/r/worldnews/.rss',
        'category': '社区讨论'
    },
    'Reddit FBA': {
        'url': 'https://www.reddit.com/r/FulfillmentByAmazon/.rss',
        'category': '社区讨论'
    },
    'Reddit Ecommerce': {
        'url': 'https://www.reddit.com/r/ecommerce/.rss',
        'category': '社区讨论'
    }
}


def log(message, level="INFO"):
    """记录日志"""
    shanghai_tz = timezone(timedelta(hours=8))
    timestamp = datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def fetch_rss_feed(feed_name, feed_url, limit=5):
    """抓取单个 RSS 源"""
    items = []
    
    try:
        # Reddit 需要特殊处理
        if 'reddit.com' in feed_url:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml',
            }
            response = requests.get(feed_url, headers=headers, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
            else:
                log(f"⚠️ {feed_name} HTTP {response.status_code}", "WARN")
                return items
        else:
            feed = feedparser.parse(feed_url, request_headers={'User-Agent': 'Mozilla/5.0 (compatible; news-worker/1.0)'})
        
        if not feed.entries:
            log(f"⚠️ {feed_name} 无数据或 RSS 不可用", "WARN")
            return items
        
        for entry in feed.entries[:limit]:
            # 提取摘要（不同 RSS 源字段不同）
            summary = ''
            if hasattr(entry, 'summary'):
                summary = entry.summary[:200]
            elif hasattr(entry, 'description'):
                summary = entry.description[:200]
            elif hasattr(entry, 'content') and len(entry.content) > 0:
                summary = entry.content[0].value[:200]
            else:
                summary = 'Click to read more'
            
            # 提取发布时间
            published = 'N/A'
            if hasattr(entry, 'published'):
                published = entry.published[:19] if entry.published else 'N/A'
            elif hasattr(entry, 'updated'):
                published = entry.updated[:19] if entry.updated else 'N/A'
            
            item = {
                'title': entry.title if hasattr(entry, 'title') else 'No title',
                'link': entry.link if hasattr(entry, 'link') else '#',
                'source': f'{feed_name}',
                'summary': summary,
                'published': published
            }
            
            items.append(item)
        
        log(f"✅ {feed_name}: {len(items)} 条")
    
    except Exception as e:
        log(f"⚠️ 抓取 {feed_name} 失败：{e}", "WARN")
    
    return items


def fetch_all_feeds():
    """抓取所有 RSS 源"""
    all_items = {}
    
    print("抓取官方博客...")
    for feed_name, feed_info in RSS_FEEDS.items():
        print(f"  抓取 {feed_name}...")
        items = fetch_rss_feed(feed_name, feed_info['url'], limit=20)
        all_items[feed_name] = {
            'items': items,
            'category': feed_info['category']
        }
        print(f"    ✅ {len(items)} 条")
    
    print("抓取论坛...")
    for feed_name, feed_info in FORUM_FEEDS.items():
        print(f"  抓取 {feed_name}...")
        items = fetch_rss_feed(feed_name, feed_info['url'], limit=20)
        all_items[feed_name] = {
            'items': items,
            'category': feed_info['category']
        }
        print(f"    ✅ {len(items)} 条")
    
    return all_items


def map_to_categories(all_items):
    """将数据映射到 ecommerce 标准分类"""
    categories = {
        '官方发布': [],
        '社区讨论': [],
        '行业媒体': [],
        '教程分析': []
    }
    
    for feed_name, data in all_items.items():
        category = data['category']
        if category in categories:
            categories[category].extend(data['items'])
    
    # 每类限制 20 条
    for category in categories:
        categories[category] = categories[category][:20]
    
    return categories


def generate_markdown(categories):
    """生成标准 Markdown 格式"""
    shanghai_tz = timezone(timedelta(hours=8))
    now = datetime.now(shanghai_tz)
    
    md = ["# 跨境电商新闻 (Amazon)", ""]
    md.append(f"**抓取时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**数据来源**: Amazon RSS Feeds")
    md.append("")
    
    category_icons = {
        '官方发布': '🏛️',
        '社区讨论': '💬',
        '行业媒体': '📰',
        '教程分析': '📚'
    }
    
    for category_name, items in categories.items():
        if not items:
            continue
        
        icon = category_icons.get(category_name, '')
        md.append(f"### 【{icon} {category_name}】")
        md.append("")
        
        for idx, item in enumerate(items, 1):
            # 格式化发布时间
            published_str = item.get('published', 'N/A')
            if published_str and published_str != 'N/A':
                try:
                    # 尝试解析并格式化
                    published_str = published_str[:19]  # 截取日期部分
                except:
                    pass
            
            md.append(f"#### {idx}. {item['title']}")
            md.append("")
            md.append(f"- **来源**: {item['source']}")
            md.append(f"- **链接**: {item['link']}")
            md.append(f"- **摘要**: {item['summary']}")
            if published_str:
                md.append(f"- **发布**: 📅 {published_str}")
            md.append("")
    
    return "\n".join(md)


def save_to_minio(markdown_content, output_path=None):
    """保存到 MinIO 或本地"""
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ 保存到：{output_file}")
        return str(output_file)
    
    import subprocess
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(markdown_content)
        temp_path = f.name
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    minio_path = f"shared/ecommerce-data/amazon-{timestamp}.md"
    
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
    
    parser = argparse.ArgumentParser(description='亚马逊 RSS 抓取')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--limit', '-l', type=int, default=5, help='每源文章数量')
    parser.add_argument('--feed', '-f', help='指定 RSS 源名称')
    parser.add_argument('--test', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📦 亚马逊 RSS 抓取")
    print("=" * 60)
    
    # 测试模式
    if args.test:
        print("\n⚠️ 测试模式，使用示例数据")
        categories = {
            '官方发布': [{
                'title': 'Test Announcement from Amazon',
                'link': 'https://sellercentral.amazon.com/test',
                'source': 'Amazon Seller Central',
                'summary': 'This is a test announcement'
            }],
            '社区讨论': [],
            '行业媒体': [],
            '教程分析': []
        }
    else:
        # 抓取数据
        print(f"\n📥 抓取数据...")
        
        if args.feed:
            # 抓取指定源
            if args.feed not in RSS_FEEDS and args.feed not in FORUM_FEEDS:
                print(f"❌ 未知源：{args.feed}")
                all_feeds = {**RSS_FEEDS, **FORUM_FEEDS}
                print(f"可用源：{', '.join(all_feeds.keys())}")
                sys.exit(1)
            
            all_feeds = {}
            if args.feed in RSS_FEEDS:
                feed_info = RSS_FEEDS[args.feed]
                items = fetch_rss_feed(args.feed, feed_info['url'], limit=args.limit)
                all_feeds[args.feed] = {'items': items, 'category': feed_info['category']}
            else:
                feed_info = FORUM_FEEDS[args.feed]
                items = fetch_rss_feed(args.feed, feed_info['url'], limit=args.limit)
                all_feeds[args.feed] = {'items': items, 'category': feed_info['category']}
        else:
            # 抓取所有源
            all_feeds = fetch_all_feeds()
        
        # 映射到分类
        categories = map_to_categories(all_feeds)
    
    # 生成 Markdown
    print(f"\n📝 生成 Markdown...")
    markdown = generate_markdown(categories)
    
    # 保存
    if args.output:
        save_to_minio(markdown, args.output)
    else:
        print("\n" + markdown)
    
    print("=" * 60)
    print("✅ 抓取完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
