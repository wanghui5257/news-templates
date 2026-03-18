#!/usr/bin/env python3
"""
新闻处理定时任务触发脚本
功能：检查 MinIO 中的新闻数据并触发 news-worker 处理
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
NEWS_DATA_DIR = "shared/news-data"
NEWS_HTML_DIR = "shared/news-html"
WORKER_SCRIPT = Path.home() / ".copaw-worker/news-worker/.copaw/active_skills/news-worker/scripts/news-worker-process.py"

# 新闻类型和数据文件映射
NEWS_TYPES = {
    "news": "news-*.md",
    "ecommerce": "ecommerce-*.md"
}


def get_shanghai_time():
    """获取当前上海时间"""
    shanghai_tz = timezone(timedelta(hours=8))
    return datetime.now(shanghai_tz)


def log(message, level="INFO"):
    """记录日志"""
    timestamp = get_shanghai_time().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def fetch_news_data(news_type):
    """抓取新闻数据（news-worker 直接抓取）"""
    log(f"开始抓取 {news_type} 新闻...")
    
    # 使用新的抓取脚本
    if news_type == "ecommerce":
        # 运行 RSS 抓取
        fetch_script = Path(__file__).parent / "fetch-amazon-rss.py"
        if not fetch_script.exists():
            log(f"抓取脚本不存在：{fetch_script}", "WARN")
            return None
        
        # 执行抓取
        cmd = ["python3", str(fetch_script), "--output", "/tmp/ecommerce-rss.md"]
        log("执行 RSS 抓取...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        print(result.stdout)
        if result.returncode != 0:
            log(f"RSS 抓取失败：{result.stderr}", "ERROR")
            return None
        
        # 运行中文抓取
        chinese_script = Path(__file__).parent / "fetch-chinese-news.py"
        if chinese_script.exists():
            log("执行中文抓取...")
            # 设置环境变量
            env = os.environ.copy()
            config_path = '/root/hiclaw-fs/shared/mcp/tavily-config.json'
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        env['TAVILY_API_KEY'] = config.get('apiKey', '')
                except:
                    pass
            
            cmd = ["python3", str(chinese_script), "--output", "/tmp/ecommerce-chinese.md"]
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=90)
            print(result.stdout)
            if result.returncode == 0:
                log("✅ 中文抓取完成")
            else:
                log(f"⚠️ 中文抓取失败：{result.stderr}", "WARN")
        
        # 合并两个文件
        rss_file = Path("/tmp/ecommerce-rss.md")
        chinese_file = Path("/tmp/ecommerce-chinese.md")
        
        if rss_file.exists():
            # 读取两个文件并合并
            rss_content = rss_file.read_text(encoding='utf-8')
            chinese_content = chinese_file.read_text(encoding='utf-8') if chinese_file.exists() else ""
            
            # 合并内容（去掉第二个文件的标题行）
            lines = chinese_content.split('\n')
            if lines and lines[0].startswith('#'):
                lines = lines[1:]  # 去掉标题
                if lines and lines[0].startswith('**'):
                    lines = lines[1:]  # 去掉抓取时间行
                if lines and lines[0].startswith('**'):
                    lines = lines[1:]  # 去掉数据来源行
                if lines and lines[0] == '':
                    lines = lines[1:]  # 去掉空行
            
            merged_content = rss_content + '\n\n' + '\n'.join(lines)
            
            # 保存合并后的文件
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            output_file = Path(f"/tmp/ecommerce-{timestamp}.md")
            output_file.write_text(merged_content, encoding='utf-8')
            
            log(f"✅ 数据抓取完成：{output_file}")
            return str(output_file)
        else:
            log("RSS 文件不存在", "ERROR")
            return None
    
    else:  # news
        # 使用原有逻辑
        fetch_script = Path(__file__).parent / "fetch-all-sources.py"
        
        if not fetch_script.exists():
            log(f"抓取脚本不存在：{fetch_script}", "WARN")
            return None
        
        # 执行抓取
        cmd = ["python3", str(fetch_script), "--source", "all"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(result.stdout)
        if result.returncode != 0:
            log(f"抓取失败：{result.stderr}", "ERROR")
            return None
        
        # 查找最新抓取的文件
        output_dir = Path.home() / "news-worker-tmp" / "fetched-data"
        if output_dir.exists():
            files = sorted(output_dir.glob(f"{news_type}*.md"))
            if files:
                latest_file = files[-1]
                log(f"抓取成功：{latest_file}")
                return str(latest_file)
        
        log("未找到抓取的文件", "WARN")
        return None


def check_data_freshness(data_file):
    """检查数据新鲜度（只处理今天的数据）"""
    if not data_file:
        return False
    
    filename = Path(data_file).name
    shanghai_tz = timezone(timedelta(hours=8))
    today = datetime.now(shanghai_tz).strftime('%Y%m%d')
    
    # 检查文件名中是否包含今天的日期
    if today in filename:
        log(f"✅ 数据新鲜度检查通过：{filename} (今日数据)")
        return True
    else:
        log(f"⚠️ 数据新鲜度检查失败：{filename} (非今日数据 {today})", "WARN")
        log(f"  跳过处理旧数据", "WARN")
        return False


def process_news(news_type, data_file):
    """调用 news-worker 处理新闻"""
    log(f"开始处理 {news_type} 新闻...")
    
    cmd = [
        "python3", str(WORKER_SCRIPT),
        news_type,
        f"{NEWS_DATA_DIR}/{data_file}",
        f"{NEWS_HTML_DIR}/"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 输出处理日志
    print(result.stdout)
    if result.stderr:
        log(f"处理错误：{result.stderr}", "ERROR")
    
    return result.returncode == 0


def send_manager_notification(success, news_type, message=""):
    """发送通知给 Manager（通过矩阵消息或日志）"""
    timestamp = get_shanghai_time().strftime("%Y-%m-%d %H:%M")
    
    if success:
        notification = f"""
✅ 定时任务执行成功

📰 新闻类型：{news_type}
⏰ 执行时间：{timestamp}
📝 状态：处理完成并推送

"""
    else:
        notification = f"""
❌ 定时任务执行失败

📰 新闻类型：{news_type}
⏰ 执行时间：{timestamp}
📝 问题：{message}

需要人工干预。
"""
    
    log("=" * 60)
    log("Manager 通知内容:")
    log(notification)
    log("=" * 60)
    
    # 实际场景中，这里应该调用 Matrix API 发送消息
    # 目前先记录到日志
    return notification


def run_scheduled_task(news_type="all"):
    """执行定时任务"""
    log("=" * 60)
    log("🕐 定时任务触发")
    log(f"📅 执行时间：{get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"📰 新闻类型：{news_type}")
    log("=" * 60)
    
    results = {}
    
    # 确定要处理的新闻类型
    types_to_process = ["news", "ecommerce"] if news_type == "all" else [news_type]
    
    for ntype in types_to_process:
        log(f"\n--- 处理 {ntype} ---")
        
        # 步骤 1: 抓取新闻数据（news-worker 直接抓取）
        data_file = fetch_news_data(ntype)
        
        if not data_file:
            log(f"⚠️ {ntype} 抓取失败，跳过处理", "WARN")
            results[ntype] = {
                "success": False,
                "reason": "fetch_failed",
                "message": "数据抓取失败"
            }
            continue
        
        # 步骤 1.5: 检查数据新鲜度（只处理今天的数据）
        if not check_data_freshness(data_file):
            log(f"⚠️ {ntype} 数据不是今天的，跳过处理", "WARN")
            results[ntype] = {
                "success": False,
                "reason": "stale_data",
                "message": "数据不是今天生成的"
            }
            continue
        
        # 步骤 2: 处理新闻（验证→生成→部署→推送）
        # 调用 news-worker-process.py
        worker_script = Path(__file__).parent / "news-worker-process.py"
        
        cmd = [
            "python3", str(worker_script),
            ntype,
            data_file,
            f"shared/{ntype}-html/"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        
        if result.returncode == 0:
            log(f"✅ {ntype} 处理完成")
            results[ntype] = {"success": True, "message": "处理成功"}
            send_manager_notification(True, ntype)
        else:
            log(f"❌ {ntype} 处理失败", "ERROR")
            results[ntype] = {"success": False, "reason": "processing_failed", "message": result.stderr}
            send_manager_notification(False, ntype, "处理失败，请检查日志")
    
    # 总结
    log("\n" + "=" * 60)
    log("📊 执行总结:")
    for ntype, result in results.items():
        status = "✅" if result["success"] else "❌"
        log(f"  {status} {ntype}: {result.get('message', result.get('reason', 'unknown'))}")
    log("=" * 60)
    
    # 返回整体成功状态
    return all(r["success"] for r in results.values())


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="新闻处理定时任务触发脚本")
    parser.add_argument(
        "--type",
        choices=["news", "ecommerce", "all"],
        default="all",
        help="新闻类型 (默认：all)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="只检查数据，不处理"
    )
    
    args = parser.parse_args()
    
    if args.check_only:
        log("检查模式：测试抓取功能")
        for ntype in ["news", "ecommerce"] if args.type == "all" else [args.type]:
            data_file = fetch_news_data(ntype)
            if data_file:
                log(f"✅ {ntype}: 抓取成功 {data_file}")
            else:
                log(f"❌ {ntype}: 抓取失败")
        return 0
    
    # 执行定时任务
    success = run_scheduled_task(args.type)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
