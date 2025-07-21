import requests as req
from bs4 import BeautifulSoup as bs
from pprint import pprint
import json
from datetime import date
import os
import re

CACHE_FILE = "care_center.json"

def get_carecenter_data():
    # 如果有快取資料 & 今天日期， 就直接讀取
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
            if cache['data'] == str(date.today()):
                return cache['data']
            
# 否則執行爬蟲
    url = 'https://1966.gov.tw/LTC/cp-6443-69944-207.html'
    headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'}
    res = req.get(url, headers=headers)
    res.encoding='utf-8'
    soup = bs(res.text, "html.parser")
    data = []
    # 找出所以li元素 (排除不是連絡資訊的ul)
    all_ul = soup.find_all('ul') 
    for ul in all_ul:
        li_list = ul.find_all('li')
        for li in li_list:
            a_tags = li.find_all('a')
            if len(a_tags) == 2:
                center_a = a_tags[0]
                apply_a = a_tags[1]
    # 取出 管照中心的名稱和連結
                center_name = center_a.text.strip()
                center_url = center_a['href']
    # 取出 線上申請的名稱和連結
                apply_name = apply_a.text.strip()
                apply_url = apply_a['href']
    # 取出電話號碼： li 文字中間會有(02-xxxx)
                full_text = li.get_text()
                phone_math = re.search(r'（(.+?)）', full_text)  # 用re.search(r'（(.+?)）'的方式 取得含用全型()內
                phone = phone_math.group(1) if phone_math else ""           

                data.append({
                    'center': center_name,
                    'center_urls':center_url,
                    'TEL' : phone,
                    'apply': apply_name,
                    'apply_urls': apply_url
                })

    # 寫入快取
    with open (CACHE_FILE, 'w' , encoding='utf-8')as f:
        json.dump({
            "date":str(date.today()),
            "data":data
        },f, ensure_ascii=False, indent=2)  
    
    return data