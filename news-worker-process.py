#!/usr/bin/env python3
"""
news-worker 核心处理脚本
功能：读取 MinIO 新闻数据 → 验证 → 生成 HTML → 验证 HTML → 推送通知
"""

import os
import sys
import subprocess
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 配置
MINIO_ALIAS = "hiclaw"
MINIO_BUCKET = "hiclaw-storage"
WORK_DIR = Path.home() / "news-worker-tmp"
NEWS_CATEGORIES = ["国际新闻", "中国新闻", "AI 新闻", "科技趋势"]
ECOMMERCE_CATEGORIES = ["官方发布", "社区讨论", "行业媒体", "教程分析"]

# news-worker 技能脚本路径（所有脚本在同一目录）
SKILL_SCRIPTS_DIR = Path(__file__).parent
VALIDATE_NEWS_SCRIPT = SKILL_SCRIPTS_DIR / "validate-news-sources.py"
VALIDATE_HTML_SCRIPT = SKILL_SCRIPTS_DIR / "validate-html.py"
GENERATE_ECOMMERCE_SCRIPT = SKILL_SCRIPTS_DIR / "generate-ecommerce-html.py"
GENERATE_NEWS_SCRIPT = SKILL_SCRIPTS_DIR / "generate-news-html.py"
SEND_NOTIFICATIONS_SCRIPT = SKILL_SCRIPTS_DIR / "send-notifications.py"
DEPLOY_TO_ECS_SCRIPT = SKILL_SCRIPTS_DIR / "deploy-to-ecs.py"

# 模板路径（从 MinIO 同步到本地）
NEWS_TEMPLATES_DIR = SKILL_SCRIPTS_DIR / "templates"
NEWS_TEMPLATE = NEWS_TEMPLATES_DIR / "news-template.html"
ECOMMERCE_TEMPLATE = NEWS_TEMPLATES_DIR / "ecommerce-template.html"


class NewsWorker:
    def __init__(self, news_type="news"):
        self.news_type = news_type
        self.categories = NEWS_CATEGORIES if news_type == "news" else ECOMMERCE_CATEGORIES
        self.errors = []
        self.warnings = []
        self.info = []
        
    def log(self, level, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if level == "ERROR":
            self.errors.append(message)
        elif level == "WARN":
            self.warnings.append(message)
        else:
            self.info.append(message)
        print(f"[{timestamp}] [{level}] {message}")
    
    def pull_from_minio(self, minio_path, local_path):
        """从 MinIO 拉取文件"""
        # 移除 minio_path 开头的 '/' 避免双斜杠
        if minio_path.startswith('/'):
            minio_path = minio_path.lstrip('/')
        
        self.log("INFO", f"从 MinIO 拉取：{minio_path} → {local_path}")
        
        cmd = ["mc", "cp", f"{MINIO_ALIAS}/{MINIO_BUCKET}/{minio_path}", str(local_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.log("ERROR", f"MinIO 拉取失败：{result.stderr}")
            return False
        
        self.log("INFO", "✅ MinIO 拉取成功")
        
        # 检查数据新鲜度
        filename = Path(minio_path).name
        shanghai_tz = timezone(timedelta(hours=8))
        today = datetime.now(shanghai_tz).strftime('%Y%m%d')
        
        if today not in filename:
            self.log("WARN", f"⚠️ 数据不是今天的：{filename} (期望包含 {today})")
            self.log("WARN", "⚠️ 跳过处理旧数据，避免重复处理")
            return False
        
        return True
    
    def validate_news_data(self, news_md_path):
        """验证新闻数据"""
        self.log("INFO", f"验证新闻数据：{news_md_path}")
        
        if not Path(news_md_path).exists():
            self.log("ERROR", f"数据文件不存在：{news_md_path}")
            return False
        
        categories_str = ",".join(self.categories)
        cmd = [
            "python3", str(VALIDATE_NEWS_SCRIPT),
            str(news_md_path),
            categories_str,
            "5"  # 期望每个分类 5 条
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        
        if result.returncode != 0:
            self.log("ERROR", "❌ 新闻数据验证失败")
            if result.stderr:
                self.log("ERROR", result.stderr)
            return False
        
        self.log("INFO", "✅ 新闻数据验证通过")
        return True
    
    def generate_news_html(self, news_md_path, output_path):
        """生成 News HTML"""
        self.log("INFO", f"生成 News HTML: {news_md_path} → {output_path}")
        
        if not GENERATE_NEWS_SCRIPT.exists():
            self.log("ERROR", f"生成脚本不存在：{GENERATE_NEWS_SCRIPT}")
            return False
        
        if not NEWS_TEMPLATE.exists():
            self.log("ERROR", f"模板文件不存在：{NEWS_TEMPLATE}")
            return False
        
        cmd = [
            "python3", str(GENERATE_NEWS_SCRIPT),
            str(news_md_path),
            str(NEWS_TEMPLATE),
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        
        if result.returncode != 0:
            self.log("ERROR", f"HTML 生成失败：{result.stderr}")
            return False
        
        self.log("INFO", "✅ HTML 生成成功")
        return True
    
    def generate_ecommerce_html(self, eco_md_path, output_path):
        """生成 Ecommerce HTML"""
        self.log("INFO", f"生成 Ecommerce HTML: {eco_md_path} → {output_path}")
        
        if not GENERATE_ECOMMERCE_SCRIPT.exists():
            self.log("ERROR", f"生成脚本不存在：{GENERATE_ECOMMERCE_SCRIPT}")
            return False
        
        if not ECOMMERCE_TEMPLATE.exists():
            self.log("ERROR", f"模板文件不存在：{ECOMMERCE_TEMPLATE}")
            return False
        
        cmd = [
            "python3", str(GENERATE_ECOMMERCE_SCRIPT),
            str(eco_md_path),
            str(ECOMMERCE_TEMPLATE),
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        
        if result.returncode != 0:
            self.log("ERROR", f"HTML 生成失败：{result.stderr}")
            return False
        
        self.log("INFO", "✅ HTML 生成成功")
        return True
    
    def validate_html(self, html_path):
        """验证 HTML"""
        self.log("INFO", f"验证 HTML: {html_path}")
        
        if not Path(html_path).exists():
            self.log("ERROR", f"HTML 文件不存在：{html_path}")
            return False
        
        cmd = [
            "python3", str(VALIDATE_HTML_SCRIPT),
            str(html_path),
            self.news_type
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        
        if result.returncode != 0:
            self.log("ERROR", "❌ HTML 验证失败")
            if result.stderr:
                self.log("ERROR", result.stderr)
            return False
        
        self.log("INFO", "✅ HTML 验证通过")
        return True
    
    def send_notifications(self):
        """发送推送通知"""
        self.log("INFO", "发送推送通知")
        
        if not SEND_NOTIFICATIONS_SCRIPT.exists():
            self.log("ERROR", f"推送脚本不存在：{SEND_NOTIFICATIONS_SCRIPT}")
            return False
        
        cmd = ["python3", str(SEND_NOTIFICATIONS_SCRIPT)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        
        if result.returncode != 0:
            self.log("ERROR", f"推送失败：{result.stderr}")
            return False
        
        self.log("INFO", "✅ 推送通知发送成功")
        return True
    
    def push_to_minio(self, local_path, minio_path):
        """推送文件到 MinIO"""
        self.log("INFO", f"推送到 MinIO: {local_path} → {minio_path}")
        
        cmd = ["mc", "cp", str(local_path), f"{MINIO_ALIAS}/{MINIO_BUCKET}/{minio_path}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.log("ERROR", f"MinIO 推送失败：{result.stderr}")
            return False
        
        self.log("INFO", "✅ MinIO 推送成功")
        return True
    
    def deploy_to_ecs(self, local_html_path, news_type):
        """部署 HTML 到 ECS 服务器"""
        self.log("INFO", f"部署到 ECS: {local_html_path} → {news_type}")
        
        if not DEPLOY_TO_ECS_SCRIPT.exists():
            self.log("ERROR", f"部署脚本不存在：{DEPLOY_TO_ECS_SCRIPT}")
            return False
        
        cmd = [
            "python3", str(DEPLOY_TO_ECS_SCRIPT),
            str(local_html_path),
            news_type,
            "--backup"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print(result.stdout)
        
        if result.returncode != 0:
            self.log("ERROR", f"ECS 部署失败：{result.stderr}")
            return False
        
        self.log("INFO", "✅ ECS 部署成功")
        return True
    
    def process(self, minio_input_path, minio_output_dir=None):
        """
        完整处理流程
        minio_input_path: MinIO 输入路径 (如: shared/news-data/news-20260309.md)
        minio_output_dir: MinIO 输出目录 (可选，如: shared/news-html/)
        """
        self.log("INFO", "=" * 60)
        self.log("INFO", f"开始处理 {self.news_type} 新闻")
        self.log("INFO", "=" * 60)
        
        # 创建工作目录
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        
        # 步骤 1: 从 MinIO 拉取数据
        local_data = WORK_DIR / f"news-{self.news_type}.md"
        if not self.pull_from_minio(minio_input_path, local_data):
            return self.get_report()
        
        # 步骤 2: 验证数据
        if not self.validate_news_data(local_data):
            return self.get_report()
        
        # 步骤 3: 生成 HTML
        local_html = WORK_DIR / f"index-{self.news_type}.html"
        if self.news_type == "ecommerce":
            if not self.generate_ecommerce_html(local_data, local_html):
                return self.get_report()
        else:
            if not self.generate_news_html(local_data, local_html):
                return self.get_report()
        
        # 步骤 4: 验证 HTML
        if not self.validate_html(local_html):
            return self.get_report()
        
        # 步骤 5: 推送到 MinIO (如果指定了输出目录)
        if minio_output_dir:
            minio_output_path = f"{minio_output_dir}index-{self.news_type}.html"
            if not self.push_to_minio(local_html, minio_output_path):
                return self.get_report()
        
        # 步骤 6: 部署到 ECS
        if not self.deploy_to_ecs(local_html, self.news_type):
            self.log("WARN", "⚠️ ECS 部署失败，但 HTML 已生成")
        
        # 步骤 7: 发送推送通知
        if not self.send_notifications():
            self.log("WARN", "⚠️ 推送通知发送失败，但 HTML 已生成")
        
        self.log("INFO", "=" * 60)
        self.log("INFO", "✅ 处理完成")
        self.log("INFO", "=" * 60)
        
        return self.get_report()
    
    def get_report(self):
        """生成处理报告"""
        report = []
        report.append("=" * 60)
        report.append(f"news-worker 处理报告 - {self.news_type}")
        report.append("=" * 60)
        report.append(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        if self.info:
            report.append("📋 处理日志:")
            for msg in self.info:
                report.append(f"  {msg}")
            report.append("")
        
        if self.warnings:
            report.append("⚠️ 警告:")
            for msg in self.warnings:
                report.append(f"  {msg}")
            report.append("")
        
        if self.errors:
            report.append("❌ 错误:")
            for msg in self.errors:
                report.append(f"  {msg}")
            report.append("")
            report.append("🛑 处理失败 - 需要人工干预")
        else:
            report.append("✅ 处理成功")
        
        report.append("=" * 60)
        return "\n".join(report)


def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        print("用法：news-worker-process.py <news|ecommerce> <minio_input_path> [minio_output_dir]")
        print("示例：news-worker-process.py news shared/news-data/news-20260309.md shared/news-html/")
        print("      news-worker-process.py ecommerce shared/ecommerce-data/eco-20260309.md shared/ecommerce-html/")
        sys.exit(1)
    
    news_type = sys.argv[1]
    minio_input = sys.argv[2]
    minio_output = sys.argv[3] if len(sys.argv) > 3 else None
    
    if news_type not in ["news", "ecommerce"]:
        print(f"错误：新闻类型必须是 'news' 或 'ecommerce'，当前：{news_type}")
        sys.exit(1)
    
    worker = NewsWorker(news_type)
    report = worker.process(minio_input, minio_output)
    print(report)
    
    if worker.errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
