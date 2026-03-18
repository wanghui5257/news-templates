#!/usr/bin/env python3
"""
中文新闻抓取脚本
使用 Tavily API 搜索中文网站内容（无需 RSS）
带重试机制和超时处理
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path


# 配置 - 中文数据源
CHINESE_SOURCES = {
    '亿邦动力': {
        'domain': 'ebrun.com',
        'keywords': ['跨境电商', '亚马逊', 'FBA'],
        'category': '行业媒体',
        'max_results': 5
    },
    '雨果网': {
        'domain': 'cifnews.com',
        'keywords': ['跨境电商', '亚马逊运营', '独立站'],
        'category': '行业媒体',
        'max_results': 5
    },
    '卖家之家': {
        'domain': 'maijiazhijia.com',
        'keywords': ['亚马逊', '跨境电商', 'FBA 运营'],
        'category': '教程分析',
        'max_results': 5
    },
    '跨境知道': {
        'domain': 'kjzhidao.com',
        'keywords': ['跨境电商', '亚马逊', '出口电商'],
        'category': '教程分析',
        'max_results': 5
    }
}

# Tavily API 配置
TAVILY_API_URL = "https://api.tavily.com/search"
TAVILY_TIMEOUT = 10  # 超时时间（秒）
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试间隔（秒）


def load_tavily_config():
    """加载 Tavily API 配置"""
    config_paths = [
        '/root/hiclaw-fs/shared/mcp/tavily-config.json',
        '/tmp/tavily-config.json',
        os.path.expanduser('~/.copaw/tavily-config.json')
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    api_key = config.get('apiKey') or config.get('api_key')
                    if api_key:
                        return api_key
            except Exception as e:
                print(f"⚠️ 读取配置失败 {config_path}: {e}")
    
    # 尝试从环境变量获取
    api_key = os.getenv('TAVILY_API_KEY')
    if api_key:
        return api_key
    
    return None


def log(message, level="INFO"):
    """记录日志"""
    shanghai_tz = timezone(timedelta(hours=8))
    timestamp = datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def tavily_search_with_retry(query, max_results=5):
    """
    Tavily 搜索（带重试机制）
    
    Args:
        query: 搜索查询
        max_results: 最大结果数
    
    Returns:
        dict: 搜索结果，失败返回空字典
    """
    api_key = load_tavily_config()
    
    if not api_key:
        log("⚠️ Tavily API Key 未配置", "WARN")
        return {}
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    payload = {
        'query': query,
        'search_depth': 'basic',
        'max_results': max_results,
        'include_answer': True,
        'include_content': True
    }
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log(f"  尝试 {attempt}/{MAX_RETRIES}: {query}")
            
            response = requests.post(
                TAVILY_API_URL,
                headers=headers,
                json=payload,
                timeout=TAVILY_TIMEOUT
            )
            
            # 检查 HTTP 状态码
            if response.status_code == 200:
                result = response.json()
                log(f"  ✅ 搜索成功")
                return result
            elif response.status_code == 429:
                # 速率限制
                log(f"  ⚠️ 速率限制，等待 {RETRY_DELAY * 2}秒", "WARN")
                time.sleep(RETRY_DELAY * 2)
                continue
            elif response.status_code >= 500:
                # 服务器错误，重试
                log(f"  ⚠️ 服务器错误 {response.status_code}，重试...", "WARN")
                time.sleep(RETRY_DELAY)
                continue
            else:
                # 其他错误
                log(f"  ❌ HTTP {response.status_code}: {response.text}", "ERROR")
                return {}
        
        except requests.exceptions.Timeout:
            log(f"  ⚠️ 请求超时（{TAVILY_TIMEOUT}秒）", "WARN")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            continue
        
        except requests.exceptions.ConnectionError as e:
            log(f"  ⚠️ 网络连接错误：{e}", "WARN")
            if attempt < MAX_RETRIES:
                log(f"  等待 {RETRY_DELAY}秒后重试...", "INFO")
                time.sleep(RETRY_DELAY)
                continue
            else:
                log(f"  ❌ 网络连接失败，放弃", "ERROR")
                return {}
        
        except requests.exceptions.RequestException as e:
            log(f"  ❌ 请求失败：{e}", "ERROR")
            return {}
        
        except Exception as e:
            log(f"  ❌ 未知错误：{e}", "ERROR")
            return {}
    
    log(f"  ❌ 重试 {MAX_RETRIES} 次后仍失败", "ERROR")
    return {}


def fetch_source_news(source_name, source_config):
    """抓取单个中文数据源（带重试）"""
    items = []
    domain = source_config['domain']
    keywords = source_config['keywords']
    category = source_config['category']
    max_results = source_config['max_results']
    
    log(f"开始抓取 {source_name} ({domain})...")
    
    try:
        # 使用第一个关键词搜索（避免过度消耗 API 额度）
        keyword = keywords[0]
        query = f"site:{domain} {keyword}"
        
        # Tavily 搜索（带重试）
        response = tavily_search_with_retry(query, max_results=max_results)
        
        if not response or 'results' not in response:
            log(f"  ⚠️ {source_name} 无搜索结果", "WARN")
            return items
        
        for result in response['results']:
            title = result.get('title', 'No title')
            url = result.get('url', '#')
            content = result.get('content', '')
            
            # 跳过无效结果
            if not title or title == 'No title':
                continue
            
            # 提取摘要（截取前 200 字符）
            summary = content[:200] if content else 'Click to read more'
            
            item = {
                'title': title,
                'link': url,
                'source': source_name,
                'summary': summary,
                'category': category,
                'published': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            items.append(item)
        
        log(f"  ✅ {source_name}: {len(items)} 条")
    
    except Exception as e:
        log(f"  ❌ 抓取 {source_name} 失败：{e}", "ERROR")
    
    return items


def fetch_all_chinese_news():
    """抓取所有中文数据源"""
    api_key = load_tavily_config()
    
    if not api_key:
        log("Tavily API 未配置，返回空数据", "WARN")
        return {}
    
    all_data = {}
    
    log("=" * 60)
    log("📰 中文新闻抓取（Tavily 搜索 - 带重试）")
    log("=" * 60)
    
    for source_name, source_config in CHINESE_SOURCES.items():
        items = fetch_source_news(source_name, source_config)
        all_data[source_name] = {
            'items': items,
            'category': source_config['category']
        }
        
        # 每个源之间等待 1 秒，避免速率限制
        time.sleep(1)
    
    log("=" * 60)
    total = sum(len(data['items']) for data in all_data.values())
    log(f"📊 总计抓取：{total} 条中文新闻")
    log("=" * 60)
    
    return all_data


def map_to_categories(all_data):
    """将数据映射到标准分类"""
    categories = {
        '官方发布': [],
        '社区讨论': [],
        '行业媒体': [],
        '教程分析': []
    }
    
    for source_name, data in all_data.items():
        category = data['category']
        if category in categories:
            categories[category].extend(data['items'])
    
    # 每类限制 10 条（中文源）
    for category in categories:
        categories[category] = categories[category][:10]
    
    return categories


def generate_markdown(categories):
    """生成标准 Markdown 格式"""
    shanghai_tz = timezone(timedelta(hours=8))
    now = datetime.now(shanghai_tz)
    
    md = ["# 跨境电商新闻 (中文源)", ""]
    md.append(f"**抓取时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**数据来源**: Tavily AI Search")
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
            md.append(f"#### {idx}. {item['title']}")
            md.append("")
            md.append(f"- **来源**: {item['source']}")
            md.append(f"- **链接**: {item['link']}")
            md.append(f"- **摘要**: {item['summary']}")
            if item.get('published'):
                md.append(f"- **发布**: 📅 {item['published']}")
            md.append("")
    
    return "\n".join(md)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='中文新闻抓取（Tavily）')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--source', '-s', help='指定数据源名称')
    parser.add_argument('--test', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📰 中文新闻抓取（Tavily 搜索 - 带重试）")
    print("=" * 60)
    
    # 测试模式
    if args.test:
        print("\n⚠️ 测试模式，使用示例数据")
        categories = {
            '行业媒体': [{
                'title': '测试：亿邦动力跨境电商新闻',
                'link': 'https://www.ebrun.com/test',
                'source': '亿邦动力',
                'summary': '这是测试数据',
                'category': '行业媒体'
            }],
            '教程分析': [{
                'title': '测试：卖家之家亚马逊教程',
                'link': 'https://www.maijiazhijia.com/test',
                'source': '卖家之家',
                'summary': '这是测试数据',
                'category': '教程分析'
            }]
        }
        markdown = generate_markdown(categories)
        print("\n" + markdown)
        return
    
    # 抓取指定源
    if args.source:
        if args.source not in CHINESE_SOURCES:
            print(f"❌ 未知源：{args.source}")
            print(f"可用源：{', '.join(CHINESE_SOURCES.keys())}")
            sys.exit(1)
        
        items = fetch_source_news(args.source, CHINESE_SOURCES[args.source])
        print(f"\n抓取结果：{len(items)} 条")
        for item in items:
            print(f"  - {item['title']}")
        return
    
    # 抓取所有源
    all_data = fetch_all_chinese_news()
    
    # 映射到分类
    categories = map_to_categories(all_data)
    
    # 生成 Markdown
    print(f"\n📝 生成 Markdown...")
    markdown = generate_markdown(categories)
    
    # 保存
    if args.output:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        print(f"✅ 保存到：{output_file}")
    else:
        print("\n" + markdown)
    
    print("=" * 60)
    print("✅ 抓取完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
