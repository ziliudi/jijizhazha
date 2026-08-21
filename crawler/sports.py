import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import os
import re
import time

# ======================= 配置区 =======================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ 警告：未检测到 GEMINI_API_KEY 环境变量，将使用原始微博体育榜数据。")
    USE_AI = False
else:
    USE_AI = True

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Referer": "https://bbs.hupu.com/",
}

ESPORTS_WORDS = [
    "电竞", "英雄联盟", "lpl", "lol", "tes", "blg", "ig", "edg", "lgd", "rng", "fpx", "jdg", "wbg", "nip",
    "王者荣耀", "tarzan", "mvp", "dota", "csgo", "瓦洛兰特", "lck", "kanavi", "cuzz", "bdd", "tsw", "cfo",
    "s16", "世界赛", "总决赛", "一图流", "jr热议", "皇子", "gank", "一血", "反蹲", "单杀", "游走", "蓝buff",
    "击杀", "团战", "韩国队", "全华班", "韩援"
]

REMOVE_SUFFIX = [
    "-NBA新闻-虎扑社区", "-CBA专区-虎扑社区", "-篮球资讯-虎扑社区",
    "-足球话题区-虎扑社区", "-国际足球资讯-虎扑社区",
    "-英雄联盟-虎扑社区", "-虎扑社区"
]

def clean_title(title):
    title = title.strip()
    title = re.sub(r'^\d+\.?\s*', '', title)
    if len(title) < 4 or "来源：虎扑" in title:
        return ""
    for s in REMOVE_SUFFIX:
        title = title.replace(s, "")
    return title.strip()

def fetch_news(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.encoding = r.apparent_encoding
    return r.text

def parse_latest(html):
    soup = BeautifulSoup(html, "html.parser")
    result = []
    seen = set()
    for a in soup.find_all("a"):
        href = a.get("href", "")
        title = a.get_text(" ", strip=True)
        if not href or not title: continue
        if "bbs.hupu.com/" not in href: continue
        if not href.endswith(".html"): continue
        url = urljoin("https://www.hupu.com/", href)
        if url in seen: continue
        t = title.lower()
        if any(w in t for w in ESPORTS_WORDS): continue
        seen.add(url)
        clean_t = clean_title(title)
        if not clean_t: continue
        result.append({"title": clean_t, "url": url})
    return result

def fetch_weibo_sports():
    """
    从 top.open2hub.com 抓取体育分类下的微博体育榜
    精准定位：data-filter="体育" 的卡片中，platform-title 为 "微博"
    """
    url = "https://top.open2hub.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 查找所有卡片容器（col-* 是卡片的外层容器）
        cards = soup.select(".col-12.col-md-6.col-xl-4")
        
        for card in cards:
            # 检查 data-filter 是否为 "体育"
            data_filter = card.get("data-filter", "")
            if data_filter != "体育":
                continue
            
            # 在该卡片内查找平台标题
            platform_title = card.select_one(".platform-title")
            if not platform_title:
                continue
            platform = platform_title.text.strip()
            
            # 只取平台名为 "微博" 的卡片
            if platform != "微博":
                continue
            
            # 采集该卡片下的列表项
            items = []
            links = card.select("a.list-item-link")
            for link in links[:20]:
                number = link.select_one(".list-number")
                text = link.select_one(".list-text")
                if text:
                    items.append({
                        "title": text.text.strip(),
                        "url": link.get("href", ""),
                        "rank": number.text.strip() if number else "",
                        "heat": str((20 - len(items)) * 100 + 500) if len(items) < 20 else "500"
                    })
            return items
        
        print("⚠️ 未找到体育分类下的微博卡片")
        return []
    except Exception as e:
        print(f"❌ 抓取微博体育榜失败: {e}")
        return []

def generate_ai_hot(raw_posts):
    """
    调用 Gemini API 生成热榜，如果失败则返回原始数据
    """
    if not raw_posts:
        print("❌ 未抓取到微博体育榜数据")
        return []

    if not USE_AI:
        print("⚠️ AI 未启用（无密钥），使用原始微博体育榜数据")
        return raw_posts[:20]

    clean_inputs = [
        {"rank": p.get("rank", ""), "title": p.get("title", ""), "url": p.get("url", "")}
        for p in raw_posts
    ]

    prompt_text = (
        "你是一个资深的体育编辑与虎扑资深JR。\n"
        "请根据传入的微博体育榜话题数据，遴选出15-20条最受关注的体育事件，生成 JSON 格式数据。\n"
        "生成要求：\n"
        "1. 优先选择高热度、高讨论度的体育事件（篮球、足球、综合体育等）。\n"
        "2. 输出格式必须为严格的 JSON 数组，数组每个元素包含四个字段：\n"
        "   - 'title': 话题标题（精简明确）\n"
        "   - 'url': 对应原话题的链接地址（原样保留）\n"
        "   - 'heat': 根据排名/热度评估的一个整数数值字符串（如 '1850'）\n"
        "   - 'comment': 虎扑球迷风格的短评（简短犀利，不超过18个字）\n"
        "3. 绝对不要添加任何 Markdown 标识（如 ```json），只返回纯 JSON 字符串。\n\n"
        f"微博体育榜话题数据如下：\n{json.dumps(clean_inputs, ensure_ascii=False)}"
    )

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048,
            "response_mime_type": "application/json"
        }
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.post(api_url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                items = json.loads(content)
                if isinstance(items, list) and len(items) >= 3:
                    return items[:20]
                else:
                    print("⚠️ Gemini 返回数据结构不符合要求，使用原始数据")
                    return raw_posts[:20]
            elif resp.status_code == 429:
                wait_time = (attempt + 1) * 5
                print(f"⚠️ 触发 Gemini API 限流 (429)，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                if attempt == max_retries - 1:
                    print("⚠️ 429 限流重试耗尽，使用原始微博体育榜数据")
                    return raw_posts[:20]
            else:
                print(f"❌ Gemini API 请求失败: HTTP {resp.status_code}，使用原始数据")
                return raw_posts[:20]
        except Exception as e:
            print(f"❌ 调用 Gemini 发生异常: {e}，使用原始数据")
            return raw_posts[:20]

    print("⚠️ 多次重试失败，使用原始微博体育榜数据")
    return raw_posts[:20]

if __name__ == "__main__":
    print("📰 开始抓取最新资讯（虎扑）...")
    latest = []
    try:
        html = fetch_news("https://www.hupu.com/")
        latest = parse_latest(html)[:30]
    except Exception as e:
        print("最新资讯抓取失败:", e)
    print(f"✅ 抓取到 {len(latest)} 条最新资讯")

    print("🔥 开始生成热榜（数据源：微博体育榜）...")
    
    # 先抓取原始数据
    raw_sports = fetch_weibo_sports()
    print(f"📊 抓取到 {len(raw_sports)} 条微博体育榜原始数据")
    
    # 生成热榜（优先 AI，失败则降级为原始数据）
    hot = generate_ai_hot(raw_sports)
    print(f"✅ 共生成 {len(hot)} 条热榜")
    
    if hot and "comment" not in hot[0]:
        # 如果是原始数据（无 comment 字段），补全格式
        hot = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "heat": item.get("heat", "500"),
                "comment": "微博体育热榜"
            }
            for item in hot
        ]

    data = {"latest_30": latest, "hot_20": hot}
    Path("data").mkdir(exist_ok=True)
    with open("data/sports.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("🎉 data/sports.json 生成完毕！")