import requests as req
from bs4 import BeautifulSoup as bs
from pprint import pprint
import sqlite3
import os
from datetime import date
import json

CACHE_FILE = 'crawler_news.json'

def get_crawler_news():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
            if cache['date'] == str(date.today()):
                return cache['data']

    news_list = []
    count = 0
    url = 'https://www.twreporter.org/tag/58e5b2660f56b40d001ae6ea'
    res = req.get(url)
    soup = bs(res.text, 'lxml')
    profix = 'https://www.twreporter.org'
    for div in soup.select('div.list-item__Container-sc-1dx5lew-0'):
        title_tag = div.select_one('div.list-item__Title-sc-1dx5lew-5')
        context = div.select_one('div.list-item__Desc-sc-1dx5lew-6')
        img = div.select_one('img')
        link = div.select_one('a')
        
        # 先抓下來再判斷是否有值, 直接抓值會抱錯
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            title = '無標題'

        if context:
            context = context.get_text(strip=True)        
        else:
            context = '無內容'

        if img:
            img = img['src']
        else: img = '無圖片'
        
        if link:
            href = link['href']
            full_link = profix + href
        else: 
            full_link = '無連結'

        news_list.append({
            'title': title,
            'context': context,
            'img': img,
            'link': full_link,
        })
        count+=1
        if count>=10: break
    
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "date": str(date.today()),
            "data": news_list,
            
        }, f, ensure_ascii=False, indent=2)

    
    return news_list



# # 儲存至資料庫
# def save_news_to_db(news_list):
#     conn = sqlite3.connect('news.db')
#     c = conn.cursor()
#     for news in news_list:
#         c.execute('''
#         INSERT INTO news (title, context, img, link)
#         VALUES (?,?,?,?)
#     ''',(news['title'], news['context'], news['img'], news['link']))
#     conn.commit()
#     conn.close()  


if __name__ == "__main__":
    news_list = get_crawler_news()
    # save_news_to_db(news_list)
    pprint(news_list)
    # print("已儲存到資料庫")
