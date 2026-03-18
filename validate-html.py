#!/usr/bin/env python3
"""HTML Validation Script - Validates news HTML before deployment"""
import sys, re
from pathlib import Path

class HTMLValidator:
    def __init__(self, html_path, page_type='news'):
        self.html_path = Path(html_path)
        self.page_type = page_type
        self.errors = []
        self.warnings = []
        self.html_content = ""
        self.rules = {
            'news': {'min': 5, 'max': 5, 'cats': ['国际新闻', '中国新闻', 'AI 新闻', '科技趋势']},
            'ecommerce': {'min': 1, 'max': 10, 'cats': ['官方发布', '社区讨论', '行业媒体', '教程分析']}
        }
    
    def validate(self):
        if not self.html_path.exists():
            self.errors.append(f"File not found: {self.html_path}")
            return False
        
        with open(self.html_path, 'r', encoding='utf-8') as f:
            self.html_content = f.read()
        
        # Check for unescaped HTML tags (Reddit comments, etc.)
        self._check_unescaped_html()
        
        categories = self._extract_categories()
        rules = self.rules.get(self.page_type, {})
        
        if len(categories) != len(rules.get('cats', [])):
            self.errors.append(f"Category count: expected {len(rules.get('cats', []))}, got {len(categories)}")
        
        for cat_name, items in categories.items():
            count = len(items)
            if count < rules.get('min', 1):
                self.errors.append(f"'{cat_name}': {count} items (min: {rules.get('min', 1)})")
            if count > rules.get('max', 10):
                self.errors.append(f"'{cat_name}': {count} items (max: {rules.get('max', 10)})")
            
            numbers = [i['number'] for i in items]
            if numbers != list(range(1, count + 1)):
                self.errors.append(f"'{cat_name}': non-sequential numbering {numbers}")
        
        return len(self.errors) == 0
    
    def _extract_categories(self):
        categories = {}
        sections = re.split(r'<div class="section', self.html_content)
        
        for section in sections[1:]:
            cat_name = None
            
            # Pattern 1: <h2>分类名</h2> (ecommerce)
            h2_match = re.search(r'<h2[^>]*>([^<]+)</h2>', section)
            if h2_match:
                cat_name = h2_match.group(1).strip()
            
            # Pattern 2: <span class="section-icon">🌍</span>\n                国际新闻 (news)
            if not cat_name:
                match = re.search(r'section-icon">[^<]+</span>\s*([^\n<]+)', section)
                if match:
                    cat_name = match.group(1).strip()
            
            if cat_name:
                items = []
                for m in re.finditer(r'<a href="[^"]*"[^>]*>(\d+)\. ([^<]+)</a>', section):
                    items.append({'number': int(m.group(1)), 'title': m.group(2).strip()})
                categories[cat_name] = items
        
        return categories
    
    def _check_unescaped_html(self):
        """Check for unescaped HTML tags that could break page layout"""
        # Detect Reddit comment tags
        if '<!-- SC_OFF -->' in self.html_content:
            self.errors.append("Found unescaped Reddit comment tag: <!-- SC_OFF -->")
        if '<div class="md">' in self.html_content:
            self.errors.append("Found unescaped Reddit div tag: <div class=\"md\">")
        # Detect other potentially problematic HTML tags in content
        if re.search(r'<!--.*?-->', self.html_content):
            self.warnings.append("Found HTML comment in content (may be intentional)")
    
    def get_report(self):
        r = ["=" * 60, f"HTML Validation ({self.page_type})", "=" * 60, f"File: {self.html_path}", ""]
        if self.errors:
            r.append("❌ ERRORS:")
            for e in self.errors: r.append(f"  • {e}")
            r.append("")
        if self.warnings:
            r.append("⚠️ WARNINGS:")
            for w in self.warnings: r.append(f"  • {w}")
            r.append("")
        if not self.errors:
            cats = self._extract_categories()
            r.append("✅ Validation Passed!")
            r.append("\nCategory Summary:")
            for name, items in cats.items(): r.append(f"  {name}: {len(items)} items")
        r.append("=" * 60)
        return "\n".join(r)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: validate-html.py <file> [news|ecommerce]")
        sys.exit(1)
    v = HTMLValidator(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'news')
    print(v.get_report())
    sys.exit(0 if v.validate() else 1)

def validate_content_completeness(self):
    """Validate each news item has title, source, and summary"""
    categories = self._extract_categories()
    
    for cat_name, items in categories.items():
        for item in items:
            if not item.get('title'):
                self.errors.append(f"'{cat_name}': News item missing title")
            # Note: source and summary are in HTML as text, need different check
    
    return len(self.errors) == 0
