#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
携程机票爬虫 - 简化版（测试用）
不使用 Selenium，直接测试 Telegram 通知
"""

import os
import requests
from datetime import datetime, timedelta

# Telegram 配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
QUERY_DATE = os.getenv('QUERY_DATE', '')

def send_telegram_message(message):
    """发送 Telegram 通知"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  未配置 Telegram")
        return False
    
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram 通知已发送")
            return True
        else:
            print(f"⚠️  Telegram 通知失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 发送 Telegram 失败: {e}")
        return False

def main():
    print("="*60)
    print("🚀 携程机票爬虫启动（测试版）")
    print("="*60)
    
    # 确定查询日期
    if QUERY_DATE:
        query_date = QUERY_DATE
    else:
        query_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n📅 查询日期: {query_date}")
    print(f"🛫 航线: 南通 → 长春\n")
    
    # 模拟数据（测试用）
    test_message = f"""
🧪 *测试消息 - 携程机票爬虫*

📅 查询日期: `{query_date}`
🛫 航线: 南通 → 长春

⚠️ 这是测试版本，暂时返回模拟数据
✅ Telegram 通知功能正常
🔧 下一步将集成真实爬虫

_GitHub Actions 环境测试成功！_
"""
    
    print("发送测试消息...")
    success = send_telegram_message(test_message)
    
    if success:
        print("\n✅ 测试成功！")
        print("Telegram 通知功能正常工作")
    else:
        print("\n❌ 测试失败")
        print("请检查 Telegram 配置")
    
    print("\n✅ 任务完成")

if __name__ == '__main__':
    main()
