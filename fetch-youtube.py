#!/usr/bin/env python3
"""
YouTube 新闻抓取脚本
使用 YouTube Data API v3 抓取新闻视频数据
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ 缺少依赖：pip install google-api-python-client")
    sys.exit(1)


# 配置 - 新闻频道 ID
NEWS_CHANNELS = {
    'Reuters': {
        'channel_id': 'UCIRYBXDze5krPDzAEOxFRVA',
        'category': '国际新闻'
    },
    'AP': {
        'channel_id': 'UCwO-UgquohXwoe7f4e6zKtOg',
        'category': '国际新闻'
    },
    'BBC': {
        'channel_id': 'UC16niRr50-MSBwiO3YDb3RA',
        'category': '国际新闻'
    },
    'TechCrunch': {
        'channel_id': 'UCCjyq_K1Xwfg8Lndy7lKMpA',
        'category': '科技趋势'
    },
    'Bloomberg': {
        'channel_id': 'UCIALMKvObZNtJ6AmdCLP7Lg',
        'category': '国际新闻'
    }
}

# 从环境变量读取 API 密钥
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')


def init_youtube():
    """初始化 YouTube API"""
    if not YOUTUBE_API_KEY:
        print("⚠️ 警告：未配置 YouTube API Key")
        print("请设置环境变量:")
        print("  export YOUTUBE_API_KEY='your_api_key'")
        print("\n获取 API Key: https://console.developers.google.com/")
        return None
    
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        print("✅ YouTube API 连接成功")
        return youtube
    except Exception as e:
        print(f"❌ YouTube API 连接失败：{e}")
        return None


def fetch_channel_videos(youtube, channel_name, limit=5):
    """抓取单个频道的视频"""
    channel_info = NEWS_CHANNELS.get(channel_name)
    if not channel_info:
        return []
    
    channel_id = channel_info['channel_id']
    videos = []
    
    try:
        # 搜索频道最新视频
        request = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            maxResults=limit,
            order='date',
            type='video'
        )
        
        response = request.execute()
        
        for item in response['items']:
            video_id = item['id']['videoId']
            snippet = item['snippet']
            
            # 获取视频详情（可选，用于获取更多统计信息）
            video = {
                'title': snippet['title'],
                'link': f"https://youtube.com/watch?v={video_id}",
                'source': f'YouTube {channel_name}',
                'summary': snippet['description'][:200] if snippet['description'] else 'Watch video',
                'published': snippet['publishedAt'],
                'channel': channel_name,
                'category': channel_info['category']
            }
            
            videos.append(video)
    
    except HttpError as e:
        print(f"⚠️ 抓取 {channel_name} 失败：{e}")
        if e.resp.status == 403:
            print("  ⚠️ API 配额已用尽")
    
    return videos


def fetch_all_channels(youtube, limit_per_channel=5):
    """抓取所有频道的视频"""
    all_videos = {}
    
    for channel_name in NEWS_CHANNELS.keys():
        print(f"  抓取 {channel_name}...")
        videos = fetch_channel_videos(youtube, channel_name, limit=limit_per_channel)
        all_videos[channel_name] = videos
        print(f"    ✅ {len(videos)} 条")
    
    return all_videos


def map_to_categories(all_videos):
    """将视频数据映射到标准分类"""
    categories = {
        '国际新闻': [],
        '中国新闻': [],
        'AI 新闻': [],
        '科技趋势': []
    }
    
    for channel_name, videos in all_videos.items():
        category = NEWS_CHANNELS[channel_name]['category']
        if category in categories:
            categories[category].extend(videos)
    
    # 每类限制 5 条
    for category in categories:
        categories[category] = categories[category][:5]
    
    return categories


def generate_markdown(categories):
    """生成标准 Markdown 格式"""
    shanghai_tz = timezone(timedelta(hours=8))
    now = datetime.now(shanghai_tz)
    
    md = ["# 时事新闻 (YouTube)", ""]
    md.append(f"**抓取时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**数据来源**: YouTube Data API")
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
        
        for idx, item in enumerate(items, 1):
            # 格式化发布时间
            try:
                published = datetime.fromisoformat(item['published'].replace('Z', '+00:00'))
                published_str = published.strftime('%Y-%m-%d %H:%M')
            except:
                published_str = item['published']
            
            md.append(f"#### {idx}. {item['title']}")
            md.append("")
            md.append(f"- **来源**: {item['source']}")
            md.append(f"- **链接**: {item['link']}")
            md.append(f"- **摘要**: {item['summary']}")
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
    minio_path = f"shared/news-data/youtube-news-{timestamp}.md"
    
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
    
    parser = argparse.ArgumentParser(description='YouTube 新闻抓取')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--limit', '-l', type=int, default=5, help='每频道视频数量')
    parser.add_argument('--channel', '-c', help='指定频道名称')
    parser.add_argument('--test', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📺 YouTube 新闻抓取")
    print("=" * 60)
    
    # 初始化 YouTube
    youtube = init_youtube()
    
    if not youtube:
        print("\n⚠️ 未配置 YouTube API，使用测试数据")
        if args.test:
            categories = {
                '国际新闻': [{
                    'title': 'Test Video from YouTube',
                    'link': 'https://youtube.com/watch?v=test',
                    'source': 'YouTube Reuters',
                    'summary': 'This is a test video',
                    'published': datetime.now().isoformat()
                }],
                '中国新闻': [],
                'AI 新闻': [],
                '科技趋势': []
            }
        else:
            sys.exit(1)
    else:
        # 抓取视频
        print(f"\n📥 抓取视频...")
        
        if args.channel:
            # 抓取指定频道
            if args.channel not in NEWS_CHANNELS:
                print(f"❌ 未知频道：{args.channel}")
                print(f"可用频道：{', '.join(NEWS_CHANNELS.keys())}")
                sys.exit(1)
            
            all_videos = {args.channel: fetch_channel_videos(youtube, args.channel, limit=args.limit)}
        else:
            # 抓取所有频道
            all_videos = fetch_all_channels(youtube, limit_per_channel=args.limit)
        
        # 映射到分类
        categories = map_to_categories(all_videos)
    
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
