#!/usr/bin/env python3
"""
从 Markdown 新闻数据生成 News HTML 页面
"""

import sys
import os
from datetime import datetime, timezone, timedelta

def generate_html(news_md_path, template_path, output_path):
    """生成 News HTML"""
    
    # 读取模板
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 读取新闻数据
    with open(news_md_path, 'r', encoding='utf-8') as f:
        news_md = f.read()
    
    # 解析新闻数据
    news_items = {
        'world': [],      # 国际新闻
        'china': [],      # 中国新闻
        'ai': [],         # AI 新闻
        'tech': []        # 科技趋势
    }
    
    current_category = None
    current_item = {}
    
    # 分类映射（支持多种格式）
    category_map = {
        '### 【国际新闻】': 'world',
        '### 【中国新闻】': 'china',
        '### 【AI 新闻】': 'ai',
        '### 【科技趋势】': 'tech',
        '## 国际新闻': 'world',
        '## 中国新闻': 'china',
        '## AI 新闻': 'ai',
        '## 科技趋势': 'tech',
        '### 【🌍 国际新闻】': 'world',
        '### 【🇨🇳 中国新闻】': 'china',
        '### 【🤖 AI 新闻】': 'ai',
        '### 【📱 科技趋势】': 'tech',
    }
    
    for line in news_md.split('\n'):
        matched = False
        
        # 检查是否是分类标题
        for header, cat_key in category_map.items():
            if line.startswith(header):
                if current_item and current_category:
                    news_items[current_category].append(current_item)
                current_category = cat_key
                current_item = {}
                matched = True
                break
        
        if not matched:
            # 解析新闻条目
            if line.startswith('####') and current_category:
                if current_item:
                    news_items[current_category].append(current_item)
                current_item = {'title': line.replace('####', '').strip()}
            elif line.startswith('- **来源**:') and current_item:
                current_item['source'] = line.replace('- **来源**:', '').strip()
            elif line.startswith('- **信源**:') and current_item:
                current_item['source'] = line.replace('- **信源**:', '').strip()
            elif line.startswith('- **链接**:') and current_item:
                current_item['link'] = line.replace('- **链接**:', '').strip()
            elif line.startswith('- **内容摘要**:') and current_item:
                current_item['summary'] = line.replace('- **内容摘要**:', '').strip()
            elif line.startswith('- **摘要**:') and current_item:
                current_item['summary'] = line.replace('- **摘要**:', '').strip()
    
    # 添加最后一个条目
    if current_item and current_category:
        news_items[current_category].append(current_item)
    
    # 生成时间戳（上海时区）
    shanghai_tz = timezone(timedelta(hours=8))
    now_shanghai = datetime.now(shanghai_tz)
    date_str = now_shanghai.strftime('%Y年%m月%d日')
    time_str = f"{now_shanghai.strftime('%H:%M')} (Asia/Shanghai)"
    
    # 格式化新闻条目为 HTML
    def fmt_category(items, category_name, icon):
        """格式化一个分类的新闻"""
        import re
        html_parts = []
        for idx, item in enumerate(items[:5], 1):  # 最多 5 条
            title = item.get('title', 'Untitled')
            link = item.get('link', '#')
            source = item.get('source', 'Unknown')
            summary = item.get('summary', 'No description')
            
            # 移除标题中已有的序号前缀（如 "1. "、"#### 1. " 等）
            title_clean = re.sub(r'^[\d]+\.\s*', '', title.strip())
            
            html_parts.append(f'''<div class="news-item">
                <div class="news-title">
                    <a href="{link}" target="_blank" rel="noopener">{idx}. {title_clean}</a>
                </div>
                <div class="news-meta">
                    <span>📡 {source}</span>
                    <span>🕐 {time_str}</span>
                </div>
                <div class="news-description">{summary}</div>
            </div>''')
        
        return ''.join(html_parts)
    
    # 替换模板变量
    html = template
    html = html.replace('{{DATE}}', date_str)
    html = html.replace('{{TIME}}', time_str)
    html = html.replace('{{NEWS_WORLD}}', fmt_category(news_items['world'], '国际新闻', '🌍'))
    html = html.replace('{{NEWS_CHINA}}', fmt_category(news_items['china'], '中国新闻', '🇨🇳'))
    html = html.replace('{{NEWS_AI}}', fmt_category(news_items['ai'], 'AI 新闻', '🤖'))
    html = html.replace('{{NEWS_TECH}}', fmt_category(news_items['tech'], '科技趋势', '📱'))
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # 打印统计信息
    print(f"✅ News HTML 生成完成:")
    print(f"   国际新闻：{len(news_items['world'])} 条")
    print(f"   中国新闻：{len(news_items['china'])} 条")
    print(f"   AI 新闻：{len(news_items['ai'])} 条")
    print(f"   科技趋势：{len(news_items['tech'])} 条")
    print(f"   输出文件：{output_path}")


def main():
    if len(sys.argv) < 4:
        print("用法：generate-news-html.py <news_md_path> <template_path> <output_path>")
        print("示例：generate-news-html.py news.md news-template.html output.html")
        sys.exit(1)
    
    news_md_path = sys.argv[1]
    template_path = sys.argv[2]
    output_path = sys.argv[3]
    
    generate_html(news_md_path, template_path, output_path)


if __name__ == '__main__':
    main()
