#!/usr/bin/env python3
"""多渠道推送通知脚本 - Telegram + 钉钉 + 飞书"""

import hmac
import hashlib
import base64
import urllib.parse
import time
import subprocess
import json
from datetime import datetime

def get_message():
    """获取推送消息内容"""
    UPDATE_DATE = datetime.now().strftime('%Y-%m-%d %H:%M')
    return f"""📰 每日新闻已更新！

🛒 跨境电商新闻：
http://ecommerce.shujuyunxiang.com

🌍 国际新闻：
https://news.shujuyunxiang.com

更新时间：{UPDATE_DATE}"""

def send_telegram(message):
    """发送 Telegram 通知"""
    print("[INFO] 发送 Telegram 通知...")
    token = "8393772893:AAGslcXz9ggvvgs4GaADBYfJUPPiFIBcens"
    chat_id = "-5059013183"
    
    # 限制消息长度 < 4KB
    if len(message) > 4000:
        message = message[:3900] + "\n\n... (内容过长，已截断)"
    
    msg = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    result = subprocess.run([
        'curl', '-s', '-X', 'POST', f"https://api.telegram.org/bot{token}/sendMessage",
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(msg)
    ], capture_output=True, text=True)
    
    # 空响应处理
    if not result.stdout.strip():
        print("[WARN] ⚠️ Telegram 返回空响应")
        return False
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"[WARN] ⚠️ Telegram 响应解析失败：{e}")
        return False
    
    if response.get('ok'):
        print("[INFO] ✅ Telegram 通知已发送")
        return True
    else:
        print(f"[WARN] ⚠️ Telegram 发送失败：{response}")
        return False

def send_dingtalk(message):
    """发送钉钉通知（带签名）"""
    print("[INFO] 发送钉钉通知...")
    webhook = "https://oapi.dingtalk.com/robot/send?access_token=4317cb0dded5bd67acaeefd52e5fb548e62afe60a79d91c7ba8f8097137e7a62"
    secret = "SEC932b78638f3623a2b861b4e4de50e1e5b87f84985f12231aac05cdb4940c7ed1"
    
    # 限制消息长度 < 4KB
    if len(message) > 4000:
        message = message[:3900] + "\n\n... (内容过长，已截断)"
    
    # 生成签名
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    url = f"{webhook}&timestamp={timestamp}&sign={sign}"
    
    msg = {"msgtype": "text", "text": {"content": message}}
    with open('/tmp/dingtalk_msg.json', 'w') as f:
        json.dump(msg, f)
    
    result = subprocess.run([
        'curl', '-s', '-X', 'POST', url,
        '-H', 'Content-Type: application/json',
        '-d', '@/tmp/dingtalk_msg.json'
    ], capture_output=True, text=True)
    
    # 空响应处理
    if not result.stdout.strip():
        print("[WARN] ⚠️ 钉钉返回空响应")
        return False
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"[WARN] ⚠️ 钉钉响应解析失败：{e}")
        return False
    
    if response.get('errcode') == 0:
        print("[INFO] ✅ 钉钉通知已发送")
        return True
    else:
        print(f"[WARN] ⚠️ 钉钉发送失败：{response}")
        return False

def send_feishu(message):
    """发送飞书通知（无签名）"""
    print("[INFO] 发送飞书通知...")
    webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/c5d8e91b-cec2-42b1-8b56-92a86936eca0"
    
    # 限制消息长度 < 4KB
    if len(message) > 4000:
        message = message[:3900] + "\n\n... (内容过长，已截断)"
    
    msg = {"msg_type": "text", "content": {"text": message}}
    with open('/tmp/feishu_msg.json', 'w') as f:
        json.dump(msg, f)
    
    result = subprocess.run([
        'curl', '-s', '-X', 'POST', webhook,
        '-H', 'Content-Type: application/json',
        '-d', '@/tmp/feishu_msg.json'
    ], capture_output=True, text=True)
    
    # 空响应处理
    if not result.stdout.strip():
        print("[WARN] ⚠️ 飞书返回空响应")
        return False
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"[WARN] ⚠️ 飞书响应解析失败：{e}")
        return False
    
    if response.get('code') == 0 or response.get('StatusCode') == 0:
        print("[INFO] ✅ 飞书通知已发送")
        return True
    else:
        print(f"[WARN] ⚠️ 飞书发送失败：{response}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("📱 开始发送多渠道推送通知")
    print("=" * 50)
    
    message = get_message()
    
    results = []
    results.append(("Telegram", send_telegram(message)))
    results.append(("钉钉", send_dingtalk(message)))
    results.append(("飞书", send_feishu(message)))
    
    print("\n" + "=" * 50)
    print("📊 推送结果汇总：")
    for channel, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {channel}: {status}")
    print("=" * 50)
