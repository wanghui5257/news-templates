#!/usr/bin/env python3
from datetime import datetime, timezone, timedelta
import sys, os, html

def generate_html(eco_md_path, template_path, output_path):
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    with open(eco_md_path, 'r', encoding='utf-8') as f:
        eco_md = f.read()
    
    news_items = {'official': [], 'community': [], 'media': [], 'knowledge': []}
    current_category = None
    current_item = {}
    
    category_map = {
        '### 【🏛️ 官方发布】': 'official',
        '### 【💬 社区讨论】': 'community',
        '### 【📰 行业媒体】': 'media',
        '### 【📚 教程分析】': 'knowledge'
    }
    
    for line in eco_md.split('\n'):
        matched = False
        for header, cat_key in category_map.items():
            if line.startswith(header):
                if current_item and current_category:
                    news_items[current_category].append(current_item)
                current_category = cat_key
                current_item = {}
                matched = True
                break
        
        if not matched:
            if line.startswith('####') and current_category:
                if current_item:
                    news_items[current_category].append(current_item)
                current_item = {'title': line.replace('####', '').strip()}
            elif line.startswith('- **信源**:') and current_item:
                current_item['source'] = line.replace('- **信源**:', '').strip()
            elif line.startswith('- **来源**:') and current_item:
                current_item['source'] = line.replace('- **来源**:', '').strip()
            elif line.startswith('- **链接**:') and current_item:
                current_item['link'] = line.replace('- **链接**:', '').strip()
            elif line.startswith('- **内容摘要**:') and current_item:
                current_item['summary'] = line.replace('- **内容摘要**:', '').strip()
            elif line.startswith('- **摘要**:') and current_item:
                current_item['summary'] = line.replace('- **摘要**:', '').strip()
    
    if current_item and current_category:
        news_items[current_category].append(current_item)
    
    shanghai_tz = timezone(timedelta(hours=8))
    now_shanghai = datetime.now(shanghai_tz)
    date_str = now_shanghai.strftime('%Y年%m月%d日')
    time_str = f"{now_shanghai.strftime('%H:%M')} (Asia/Shanghai)"
    
    def fmt(item):
        # Escape HTML tags in summary to prevent layout breaking
        summary = html.escape(item.get('summary', 'No description'))
        title = html.escape(item.get('title', 'Untitled'))
        source = html.escape(item.get('source', 'Unknown'))
        return f'''<div class="news-item">
                <div class="news-title">
                    <a href="{item.get('link','#')}" target="_blank" rel="noopener">{title}</a>
                </div>
                <div class="news-meta">
                    <span>📡 {source}</span>
                    <span>🕐 {time_str}</span>
                </div>
                <div class="news-description">{summary}</div>
            </div>'''
    
    html = template
    html = html.replace('{{DATE}}', date_str)
    html = html.replace('{{TIME}}', time_str)
    html = html.replace('{{NEWS_OFFICIAL}}', ''.join(fmt(i) for i in news_items['official'][:20]))
    html = html.replace('{{NEWS_COMMUNITY}}', ''.join(fmt(i) for i in news_items['community'][:20]))
    html = html.replace('{{NEWS_MEDIA}}', ''.join(fmt(i) for i in news_items['media'][:20]))
    html = html.replace('{{NEWS_KNOWLEDGE}}', ''.join(fmt(i) for i in news_items['knowledge'][:20]))
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Ecommerce HTML: Official={len(news_items['official'])}, Community={len(news_items['community'])}, Media={len(news_items['media'])}, Knowledge={len(news_items['knowledge'])}")

if __name__ == '__main__':
    generate_html(sys.argv[1], sys.argv[2], sys.argv[3])
