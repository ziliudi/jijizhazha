import requests
from bs4 import BeautifulSoup
import json
import os

# 热榜来源
url = "https://top.open2hub.com/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

try:
    response = requests.get(url, headers=headers, timeout=20)
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    hot_data = []

    target_platforms = ["抖音", "微博", "网易新闻", "知乎"]

    cards = soup.select(".card-rebang")

    for card in cards:
        title = card.select_one(".platform-title")
        if not title: continue
        platform = title.text.strip()
        if platform not in target_platforms: continue

        items = []
        links = card.select("a.list-item-link")

        for link in links[:20]:
            number = link.select_one(".list-number")
            text = link.select_one(".list-text")
            if text:
                items.append({
                    "rank": number.text.strip() if number else "",
                    "title": text.text.strip(),
                    "url": link.get("href", "")
                })

        hot_data.append({"platform": platform, "items": items})

    os.makedirs("data", exist_ok=True)
    with open("data/hot.json", "w", encoding="utf-8") as f:
        json.dump(hot_data, f, ensure_ascii=False, indent=2)

    print("hot.json 更新完成")
    for item in hot_data:
        print(item["platform"], len(item["items"]))

except Exception as e:
    print(f"[WARN] top.open2hub.com 访问失败或服务挂掉: {e}")
    print("[INFO] hot.py 已跳过，等待服务恢复...")
