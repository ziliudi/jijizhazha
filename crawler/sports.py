import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import os
import re
from openai import OpenAI
from datetime import datetime, timezone, timedelta

# ======================= 配置区 =======================
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if not API_KEY:
    print("⚠️ 警告：未检测到 DEEPSEEK_API_KEY 环境变量，将不使用 AI 生成。")
    USE_AI = False
else:
    USE_AI = True
    client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com/v1")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Referer": "https://bbs.hupu.com/",
}

# ======================= 核心过滤词库 =======================
ESPORTS_WORDS = [
    "电竞", "英雄联盟", "lpl", "lol", "tes", "blg", "ig", "edg", "lgd", "rng", "fpx", "jdg", "wbg", "nip",
    "王者荣耀", "tarzan", "mvp", "dota", "csgo", "瓦洛兰特", "lck", "kanavi", "cuzz", "bdd", "tsw", "cfo",
    "s16", "世界赛", "总决赛", "一图流", "jr热议", "皇子", "gank", "一血", "反蹲", "单杀", "游走", "蓝buff",
    "击杀", "团战", "韩国队", "全华班", "韩援"
]

NON_SPORTS = [
    "步行街", "恋爱", "职场", "股票", "数码", "汽车", "影视", "音乐", 
    "搞笑", "历史", "情感", "装修", "美食", "宠物", "房产", "游戏"
]

SPORTS_WORDS = [
    "nba", "cba", "篮球", "湖人", "勇士", "詹姆斯", "库里", "杜兰特", "哈登",
    "足球", "英超", "欧冠", "皇马", "巴萨", "梅西", "曼联", "曼城",
    "利物浦", "切尔西", "阿森纳", "拜仁", "姆巴佩", "哈兰德",
    "体育", "奥运", "网球", "f1", "c罗", "ufc","网球",
"乒乓球",
"羽毛球",
"排球",
"赛车",
"f1",
"游泳",
"田径",
"体操",
"斯诺克",
"拳击",
"ufc",
"奥运",
"亚运",
"全运会",
"自行车",
"滑雪",
"冰球"
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

# ======================= 保留原样：最新资讯抓取 =======================
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

# ======================= AI 逻辑：热榜生成 =======================
def fetch_hupu_for_ai():
    posts = []
    seen = set()

    hupu_boards = [
        "https://bbs.hupu.com/cba",
        "https://bbs.hupu.com/na",
        "https://bbs.hupu.com/vote",
        "https://bbs.hupu.com/3502",
        "https://bbs.hupu.com/482",
        "https://bbs.hupu.com/topic",
        "https://bbs.hupu.com/china-soccer",
        "https://bbs.hupu.com/sports"
    ]

    try:
        session = requests.Session()
        session.headers.update(HEADERS)

        for board in hupu_boards:
            r = session.get(board, timeout=20)
            r.encoding = r.apparent_encoding

            soup = BeautifulSoup(r.text, "html.parser")

            for a in soup.find_all("a"):
                title = a.get_text(" ", strip=True)
                href = a.get("href", "")

                if not title or not href:
                    continue

                if ".html" not in href:
                    continue

                url = urljoin("https://bbs.hupu.com/", href)

                if url in seen:
                    continue

                title_clean = clean_title(title)
                if not title_clean:
                    continue

                t = title_clean.lower()

                if any(w in t for w in ESPORTS_WORDS):
                    continue

                if any(w in t for w in NON_SPORTS):
                    continue

                if not any(w in t for w in SPORTS_WORDS):
                    continue

                seen.add(url)

                posts.append({
                    "title": title_clean,
                    "url": url
                })

                if len(posts) >= 50:
                    return posts

        return posts

    except Exception as e:
        print("❌ 抓取虎扑板块数据失败:", e)
        return []


def generate_ai_hot():
    raw_posts = fetch_hupu_for_ai()
    if not raw_posts or len(raw_posts) == 0:
        return []
        
    if not USE_AI:
        return raw_posts[:20]
    
    prompt = f"""
请根据以下虎扑体育帖子数据，生成【今日体育精华热门榜】。

要求：

1. 优先选择讨论度高、影响力大的体育事件。
2. 如果数据中存在篮球、足球之外的综合体育内容，请优先保留；如果不足，不要编造。
3. 输出15-20条。
4. 不要输出标题、说明、Markdown、表格。
5. 每条必须严格一行：

排名.标题|热度整数|点评短评|链接地址

6. 点评短评要求：
- 虎扑球迷风格
- 简短犀利
- 不超过18个字

帖子数据：

{json.dumps(raw_posts,ensure_ascii=False)}
"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[{"role": "system", "content": "绝对严格遵循用户要求的竖线分隔格式输出。"}, {"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=4096
        )
        
        items = []
        content = response.choices[0].message.content.strip()
        for line in content.split('\n'):
            line = line.strip()
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    rank_title = parts[0]
                    rank = "0"
                    title = rank_title
                    if '.' in rank_title:
                        try:
                            rank = rank_title.split('.')[0].strip()
                            title = rank_title.split('.', 1)[1].strip()
                        except: pass
                    
                    # ⭐【核心修复】提取热度和点评
                    heat = parts[1] if len(parts) > 1 else "0"
                    comment = parts[2] if len(parts) > 2 else ""
                    url = parts[3] if len(parts) > 3 else ""

                    if title and rank.isdigit() and url != "":
                        # 🚀 将热度和点评完整写入 JSON
                        items.append({
                            "title": title, 
                            "url": url, 
                            "heat": heat, 
                            "comment": comment
                        })
        return items[:20]
    except Exception as e:
        print("❌ 调用 DeepSeek AI 失败:", e)
        return []

# ======================= 主程序 ========================
if __name__ == "__main__":
    print("📰 开始抓取最新资讯...")
    latest = []
    try:
        html = fetch_news("https://www.hupu.com/")
        latest = parse_latest(html)[:30]
    except Exception as e:
        print("最新资讯抓取失败:", e)
    print(f"✅ 抓取到 {len(latest)} 条最新资讯")

    print("🔥 开始抓取热榜并调用 AI 生成...")
    hot = generate_ai_hot()
    print(f"✅ AI 生成了 {len(hot)} 条热榜")

    data = {"latest_30": latest, "hot_20": hot}
    Path("data").mkdir(exist_ok=True)
    with open("data/sports.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("🎉 data/sports.json 生成完毕！")
