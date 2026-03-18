#!/usr/bin/env python3
"""验证新闻数据完整性和格式正确性"""
import sys
import os
from datetime import datetime, timedelta

def validate_news_data(news_md_path, expected_categories, expected_items_per_category=5):
    """验证新闻数据文件"""
    errors = []
    warnings = []
    
    # 1. 检查文件是否存在
    if not os.path.exists(news_md_path):
        return False, [f"❌ 数据文件不存在：{news_md_path}"], []
    
    # 2. 读取数据
    with open(news_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 2b. 检测未转义的 HTML 标签
    import re
    html_patterns = [
        (r'<!--.*?-->', 'HTML comment'),
        (r'<div[^>]*>', 'HTML div tag'),
        (r'</div>', 'HTML closing div tag'),
        (r'<span[^>]*>', 'HTML span tag'),
        (r'</span>', 'HTML closing span tag'),
    ]
    for pattern, desc in html_patterns:
        if re.search(pattern, content):
            errors.append(f"⚠️ 检测到 HTML 标签 ({desc}) - 可能需要在生成 HTML 时转义")
    
    if not content.strip():
        return False, ["❌ 数据文件为空"], []
    
    # 3. 验证分类数量
    categories_found = []
    for cat in expected_categories:
        if f'【{cat}】' in content or f'## {cat}' in content:
            categories_found.append(cat)
    
    if len(categories_found) != len(expected_categories):
        missing = set(expected_categories) - set(categories_found)
        errors.append(f"❌ 缺少分类：{missing}")
    
    # 4. 验证每个分类的新闻数量
    news_items = {cat: [] for cat in expected_categories}
    current_category = None
    
    for line in content.split('\n'):
        # 匹配分类标题
        for cat in expected_categories:
            if f'【{cat}】' in line or f'## {cat}' in line:
                current_category = cat
                break
        
        # 匹配新闻条目 (#### 开头)
        if line.startswith('####') and current_category:
            news_items[current_category].append(line)
    
    # 5. 验证每个分类的新闻数量
    for cat in expected_categories:
        count = len(news_items[cat])
        if count < expected_items_per_category:
            errors.append(f"❌ {cat} 分类只有{count}条新闻，期望{expected_items_per_category}条")
        elif count > expected_items_per_category:
            warnings.append(f"⚠️ {cat} 分类有{count}条新闻，超过期望{expected_items_per_category}条")
    
    # 6. 验证总新闻数量
    total = sum(len(items) for items in news_items.values())
    expected_total = len(expected_categories) * expected_items_per_category
    if total < expected_total:
        errors.append(f"❌ 总新闻数量{total}条，少于期望{expected_total}条")
    
    # 7. 输出验证报告
    print("=" * 60)
    print(f"📊 新闻数据验证报告 - {os.path.basename(news_md_path)}")
    print("=" * 60)
    print(f"📁 文件：{news_md_path}")
    print(f"📅 验证时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    for cat in expected_categories:
        count = len(news_items[cat])
        status = "✅" if count >= expected_items_per_category else "❌"
        print(f"{status} {cat}: {count}条")
    
    print("-" * 60)
    print(f"📊 总计：{total}条新闻")
    print("=" * 60)
    
    if errors:
        print("❌ 错误:")
        for err in errors:
            print(f"  {err}")
    
    if warnings:
        print("⚠️ 警告:")
        for warn in warnings:
            print(f"  {warn}")
    
    if not errors:
        print("✅ 验证通过！")
        print("=" * 60)
        return True, [], warnings
    else:
        print("=" * 60)
        return False, errors, warnings

def main():
    if len(sys.argv) < 3:
        print("用法：validate-news-data.py <news_md_path> <category1,category2,...> [expected_items_per_category]")
        print("示例：validate-news-data.py news.md 国际新闻，中国新闻,AI 新闻，科技趋势 5")
        sys.exit(1)
    
    news_md_path = sys.argv[1]
    categories = sys.argv[2].split(',')
    expected_items = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    success, errors, warnings = validate_news_data(news_md_path, categories, expected_items)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
