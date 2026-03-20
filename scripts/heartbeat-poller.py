#!/usr/bin/env python3
"""
HEARTBEAT 轮询脚本 - 每 5 分钟检查定时任务状态

功能：
1. 定期检查 MinIO 中的 HEARTBEAT 触发文件
2. 自动响应 Cron 任务触发
3. 确保 news-worker 及时执行定时任务
"""

import os
import sys
import time
import subprocess
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 配置
MINIO_ALIAS = "hiclaw"
MINIO_BUCKET = "hiclaw-storage"
POLL_INTERVAL = 300  # 5 分钟
HEARTBEAT_DIR = "shared/heartbeat"
TASKS_DIR = "shared/tasks"

# 定时任务配置
SCHEDULED_TASKS = {
    "morning-digest": {"time": "09:30", "type": "news"},
    "noon-update": {"time": "12:00", "type": "all"},
    "evening-digest": {"time": "18:30", "type": "all"},
    "night-update": {"time": "22:00", "type": "all"},
}


def get_shanghai_time():
    """获取当前上海时间"""
    shanghai_tz = timezone(timedelta(hours=8))
    return datetime.now(shanghai_tz)


def log(message, level="INFO"):
    """记录日志"""
    timestamp = get_shanghai_time().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def check_heartbeat_files():
    """检查 MinIO 中的 HEARTBEAT 触发文件"""
    log("检查 HEARTBEAT 触发文件...")
    
    # 列出 MinIO 中的 heartbeat 文件
    cmd = ["mc", "ls", f"{MINIO_ALIAS}/{MINIO_BUCKET}/{HEARTBEAT_DIR}/"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        log(f"MinIO 访问失败：{result.stderr}", "WARN")
        return []
    
    # 解析文件列表
    heartbeat_files = []
    for line in result.stdout.strip().split('\n'):
        if line and 'HEARTBEAT' in line:
            parts = line.split()
            if parts:
                filename = parts[-1]
                heartbeat_files.append(filename)
    
    log(f"发现 {len(heartbeat_files)} 个 HEARTBEAT 文件")
    return heartbeat_files


def check_task_freshness(filename):
    """检查任务文件是否已处理"""
    # 从文件名提取时间戳
    # 格式：HEARTBEAT-YYYYMMDD-HHMMSS.md
    try:
        parts = filename.replace('HEARTBEAT-', '').replace('.md', '').split('-')
        if len(parts) >= 2:
            date_str = parts[0]
            time_str = parts[1]
            task_time = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
            
            # 检查是否是今天 2 小时内的任务
            now = get_shanghai_time()
            age = now - task_time.replace(tzinfo=timezone(timedelta(hours=8)))
            
            if age.total_seconds() < 7200:  # 2 小时内
                return True, age.total_seconds() / 60  # 返回分钟数
    except Exception as e:
        log(f"解析文件名失败：{e}", "WARN")
    
    return False, 0


def trigger_task(task_type="all"):
    """触发新闻处理任务"""
    log(f"触发 {task_type} 新闻处理任务...")
    
    # 调用 scheduled-task-trigger.py
    trigger_script = Path(__file__).parent.parent / "scheduled-task-trigger.py"
    
    if not trigger_script.exists():
        log(f"触发脚本不存在：{trigger_script}", "ERROR")
        return False
    
    cmd = ["python3", str(trigger_script), "--type", task_type]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        log(f"任务执行错误：{result.stderr}", "ERROR")
    
    return result.returncode == 0


def send_status_report(success, task_name, message=""):
    """发送状态报告到 MinIO"""
    timestamp = get_shanghai_time().strftime("%Y-%m-%d %H:%M:%S")
    
    report = {
        "task": task_name,
        "timestamp": timestamp,
        "success": success,
        "message": message,
        "worker": "news-worker"
    }
    
    # 保存到本地
    report_file = Path(f"/tmp/heartbeat-report-{task_name}.json")
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    
    # 上传到 MinIO
    remote_path = f"{MINIO_ALIAS}/{MINIO_BUCKET}/shared/heartbeat/reports/"
    cmd = ["mc", "cp", str(report_file), f"{remote_path}report-{task_name}-{get_shanghai_time().strftime('%Y%m%d-%H%M%S')}.json"]
    subprocess.run(cmd, capture_output=True)
    
    log(f"状态报告已保存：{report_file}")


def run_poller():
    """运行轮询主循环"""
    log("=" * 60)
    log("🫀 HEARTBEAT 轮询启动")
    log(f"🕐 轮询间隔：{POLL_INTERVAL}秒 ({POLL_INTERVAL/60}分钟)")
    log(f"📍 工作目录：{Path(__file__).parent.parent}")
    log("=" * 60)
    
    processed_files = set()  # 已处理的文件
    
    while True:
        try:
            # 检查 HEARTBEAT 文件
            heartbeat_files = check_heartbeat_files()
            
            for filename in heartbeat_files:
                if filename in processed_files:
                    continue
                
                # 检查任务新鲜度
                is_fresh, age_minutes = check_task_freshness(filename)
                
                if is_fresh:
                    log(f"发现新任务：{filename} ({age_minutes:.1f}分钟前)")
                    
                    # 触发任务
                    success = trigger_task("all")
                    
                    if success:
                        log(f"✅ 任务执行成功：{filename}")
                        send_status_report(True, filename, "执行成功")
                    else:
                        log(f"❌ 任务执行失败：{filename}", "ERROR")
                        send_status_report(False, filename, "执行失败")
                    
                    processed_files.add(filename)
                else:
                    log(f"跳过旧任务：{filename}")
                    processed_files.add(filename)
            
            # 等待下次轮询
            log(f"等待 {POLL_INTERVAL}秒后下次检查...")
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            log("轮询被用户中断", "WARN")
            break
        except Exception as e:
            log(f"轮询错误：{e}", "ERROR")
            time.sleep(60)  # 错误后等待 1 分钟


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="HEARTBEAT 轮询脚本")
    parser.add_argument("--once", action="store_true", help="只执行一次检查")
    parser.add_argument("--interval", type=int, default=300, help="轮询间隔（秒）")
    
    args = parser.parse_args()
    
    if args.once:
        # 只执行一次
        log("单次检查模式")
        heartbeat_files = check_heartbeat_files()
        for filename in heartbeat_files:
            is_fresh, age_minutes = check_task_freshness(filename)
            if is_fresh:
                log(f"发现新任务：{filename} ({age_minutes:.1f}分钟前)")
                trigger_task("all")
        return 0
    
    # 更新轮询间隔
    global POLL_INTERVAL
    POLL_INTERVAL = args.interval
    
    # 运行轮询
    run_poller()


if __name__ == "__main__":
    main()
