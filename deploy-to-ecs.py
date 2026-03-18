#!/usr/bin/env python3
"""
部署脚本 - 将 HTML 文件上传到阿里云 ECS 服务器
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ECS 配置
ECS_HOST = "47.115.63.159"
ECS_USER = "root"
SSH_KEY = Path.home() / ".ssh/id_ed25519_news_worker"

# 部署目录
DEPLOY_DIRS = {
    "news": "/www/wwwroot/news",
    "ecommerce": "/www/wwwroot/ecommerce"
}

# SSH 选项
SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=10",
    "-i", str(SSH_KEY)
]


def log(message, level="INFO"):
    """记录日志"""
    shanghai_tz = timezone(timedelta(hours=8))
    timestamp = datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def test_connection():
    """测试 SSH 连接"""
    log("测试 ECS SSH 连接...")
    
    cmd = ["ssh"] + SSH_OPTS + [
        f"{ECS_USER}@{ECS_HOST}",
        "echo 'Connection successful'"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    
    if result.returncode != 0:
        log(f"SSH 连接失败：{result.stderr}", "ERROR")
        return False
    
    log("✅ SSH 连接成功")
    return True


def deploy_file(html_path, news_type):
    """部署单个 HTML 文件到 ECS"""
    if not Path(html_path).exists():
        log(f"HTML 文件不存在：{html_path}", "ERROR")
        return False
    
    deploy_dir = DEPLOY_DIRS.get(news_type)
    if not deploy_dir:
        log(f"未知的新闻类型：{news_type}", "ERROR")
        return False
    
    # 目标路径
    dest_path = f"{deploy_dir}/index.html"
    
    log(f"部署 {news_type} HTML: {html_path} → {ECS_HOST}:{dest_path}")
    
    # 使用 scp 上传
    scp_cmd = ["scp"] + SSH_OPTS + [
        str(html_path),
        f"{ECS_USER}@{ECS_HOST}:{dest_path}"
    ]
    
    log(f"执行：{' '.join(scp_cmd)}")
    result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=60)
    
    if result.returncode != 0:
        log(f"上传失败：{result.stderr}", "ERROR")
        return False
    
    log(f"✅ 上传成功")
    
    # 验证文件存在
    log("验证部署文件...")
    verify_cmd = ["ssh"] + SSH_OPTS + [
        f"{ECS_USER}@{ECS_HOST}",
        f"ls -lh {dest_path}"
    ]
    
    result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        log(f"✅ 文件验证成功：{result.stdout.strip()}")
        return True
    else:
        log(f"⚠️ 文件验证失败：{result.stderr}", "WARN")
        return True  # 上传成功，验证失败不影响整体


def backup_existing(news_type):
    """备份现有文件（可选）"""
    deploy_dir = DEPLOY_DIRS.get(news_type)
    if not deploy_dir:
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{deploy_dir}/index.html.bak.{timestamp}"
    
    log(f"备份现有文件：{deploy_dir}/index.html → {backup_path}")
    
    cmd = ["ssh"] + SSH_OPTS + [
        f"{ECS_USER}@{ECS_HOST}",
        f"cp {deploy_dir}/index.html {backup_path} 2>/dev/null || echo 'No existing file to backup'"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    
    if "No existing file" in result.stdout:
        log("ℹ️ 无现有文件，跳过备份")
        return True
    elif result.returncode == 0:
        log(f"✅ 备份成功：{backup_path}")
        return True
    else:
        log(f"⚠️ 备份失败：{result.stderr}", "WARN")
        return True  # 备份失败不影响部署


def deploy_to_ecs(html_path, news_type, backup=False):
    """
    完整部署流程
    
    Args:
        html_path: HTML 文件路径
        news_type: 新闻类型 (news / ecommerce)
        backup: 是否备份现有文件
    
    Returns:
        bool: 部署是否成功
    """
    log("=" * 60)
    log(f"开始部署 {news_type} 到 ECS")
    log("=" * 60)
    
    # 步骤 1: 测试连接
    if not test_connection():
        return False
    
    # 步骤 2: 备份现有文件（可选）
    if backup:
        backup_existing(news_type)
    
    # 步骤 3: 部署文件
    success = deploy_file(html_path, news_type)
    
    log("=" * 60)
    if success:
        log(f"✅ {news_type} 部署完成")
    else:
        log(f"❌ {news_type} 部署失败", "ERROR")
    log("=" * 60)
    
    return success


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="部署 HTML 到阿里云 ECS")
    parser.add_argument("html_path", nargs="?", help="HTML 文件路径")
    parser.add_argument("news_type", nargs="?", choices=["news", "ecommerce"], help="新闻类型")
    parser.add_argument("--backup", action="store_true", help="备份现有文件")
    parser.add_argument("--test", action="store_true", help="只测试连接，不部署")
    
    args = parser.parse_args()
    
    if args.test:
        success = test_connection()
        sys.exit(0 if success else 1)
    
    if not args.html_path or not args.news_type:
        print("用法：deploy-to-ecs.py <html_path> <news_type> [--backup]")
        print("示例：deploy-to-ecs.py /root/news-worker-tmp/index-news.html news")
        print("      deploy-to-ecs.py --test  # 只测试连接")
        sys.exit(1)
    
    success = deploy_to_ecs(args.html_path, args.news_type, args.backup)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
