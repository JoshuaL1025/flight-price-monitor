#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
携程机票爬虫 - GitHub Actions 版本
南通 → 长春
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Telegram 配置（从环境变量读取）
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

class FlightCrawler:
    def __init__(self):
        self.from_city = 'NTG'  # 南通
        self.to_city = 'CGQ'    # 长春
        self.driver = None
        
    def init_driver(self):
        """初始化 Chrome 浏览器"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        print("✅ 浏览器初始化成功")
        
    def get_flights(self, date_str):
        """获取航班信息"""
        try:
            # 构造携程搜索 URL
            url = f'https://flights.ctrip.com/booking/{self.from_city.lower()}-{self.to_city.lower()}-day-1.html?ddate1={date_str}'
            
            print(f"🔍 正在访问: {url}")
            self.driver.get(url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 等待航班列表加载
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'flight-item')))
            
            print("✅ 页面加载完成，开始解析数据...")
            
            # 解析航班信息
            flights = []
            flight_items = self.driver.find_elements(By.CLASS_NAME, 'flight-item')
            
            for item in flight_items[:5]:  # 只取前 5 个航班
                try:
                    # 提取航班号
                    flight_no = item.find_element(By.CLASS_NAME, 'flight-No').text
                    
                    # 提取时间
                    times = item.find_elements(By.CLASS_NAME, 'time')
                    departure_time = times[0].text if len(times) > 0 else ''
                    arrival_time = times[1].text if len(times) > 1 else ''
                    
                    # 提取价格
                    price_elem = item.find_element(By.CLASS_NAME, 'price')
                    price_text = price_elem.text.replace('¥', '').replace(',', '')
                    price = int(price_text) if price_text.isdigit() else 0
                    
                    # 提取航空公司
                    airline = item.find_element(By.CLASS_NAME, 'airline-name').text
                    
                    flight_info = {
                        'date': date_str,
                        'flight_no': flight_no,
                        'airline': airline,
                        'departure_time': departure_time,
                        'arrival_time': arrival_time,
                        'price': price,
                        'platform': '携程',
                        'url': url
                    }
                    
                    flights.append(flight_info)
                    print(f"  ✈️  {flight_no} - ¥{price}")
                    
                except Exception as e:
                    print(f"  ⚠️  解析单个航班失败: {e}")
                    continue
            
            return flights
            
        except Exception as e:
            print(f"❌ 获取航班失败: {e}")
            # 保存截图用于调试
            self.driver.save_screenshot('error.png')
            return []
    
    def get_lowest_price(self, date_str):
        """获取最低价"""
        flights = self.get_flights(date_str)
        
        if not flights:
            return None
        
        # 过滤有效价格
        valid_flights = [f for f in flights if f['price'] > 0]
        
        if not valid_flights:
            return None
        
        # 找最低价
        lowest = min(valid_flights, key=lambda x: x['price'])
        return lowest
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("✅ 浏览器已关闭")


def send_telegram_message(message):
    """发送 Telegram 通知"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  未配置 Telegram，跳过通知")
        return
    
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
        else:
            print(f"⚠️  Telegram 通知失败: {response.text}")
    except Exception as e:
        print(f"❌ 发送 Telegram 失败: {e}")


def save_to_file(data, filename='flight_prices.json'):
    """保存数据"""
    try:
        # 读取历史数据
        history = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        # 添加新记录
        record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'flight': data
        }
        history.append(record)
        
        # 只保留最近 30 天
        history = history[-30:]
        
        # 保存
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 数据已保存到 {filename}")
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")


def main():
    print("="*60)
    print("🚀 携程机票爬虫启动")
    print("="*60)
    
    crawler = FlightCrawler()
    
    try:
        # 初始化浏览器
        crawler.init_driver()
        
        # 查询明天的航班
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"\n📅 查询日期: {tomorrow}")
        print(f"🛫 航线: 南通 → 长春\n")
        
        # 获取最低价
        lowest = crawler.get_lowest_price(tomorrow)
        
        if lowest:
            # 格式化消息
            message = f"""
🎫 *携程机票最低价*

📅 日期: `{lowest['date']}`
✈️ 航班: `{lowest['flight_no']}`
🏢 航司: {lowest['airline']}
🛫 起飞: {lowest['departure_time']}
🛬 到达: {lowest['arrival_time']}
💰 价格: *¥{lowest['price']}*

🔗 [点击查看]({lowest['url']})
"""
            
            print("\n" + "="*60)
            print("✅ 找到最低价航班：")
            print("="*60)
            print(f"📅 日期: {lowest['date']}")
            print(f"✈️  航班号: {lowest['flight_no']}")
            print(f"🏢 航空公司: {lowest['airline']}")
            print(f"🛫 起飞: {lowest['departure_time']}")
            print(f"🛬 到达: {lowest['arrival_time']}")
            print(f"💰 价格: ¥{lowest['price']}")
            print("="*60)
            
            # 保存数据
            save_to_file(lowest)
            
            # 发送 Telegram 通知
            send_telegram_message(message)
            
        else:
            error_msg = "❌ 未找到航班数据，可能需要调整爬虫策略"
            print(error_msg)
            send_telegram_message(error_msg)
        
    except Exception as e:
        error_msg = f"❌ 程序运行出错: {e}"
        print(error_msg)
        send_telegram_message(error_msg)
        
    finally:
        # 关闭浏览器
        crawler.close()
    
    print("\n✅ 任务完成")


if __name__ == '__main__':
    main()
