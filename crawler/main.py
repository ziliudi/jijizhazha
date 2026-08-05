import json
import re
import requests
import feedparser
import zhconv
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 导入 RSS 配置文件
from rss_config import RSS_LIST

articles = []


# ==========================
# 清理 HTML 标签
# ==========================
def clean_html(text):
    if not text:
        return ""
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ==========================
# 获取发布时间（统一转为北京时间 UTC+8，用于排序）
# ==========================
def get_time(entry):
    try:
        if entry.get("published_parsed"):
            utc_time = datetime(
                entry.published_parsed.tm_year,
                entry.published_parsed.tm_month,
                entry.published_parsed.tm_mday,
                entry.published_parsed.tm_hour,
                entry.published_parsed.tm_min,
                entry.published_parsed.tm_sec,
                tzinfo=timezone.utc,
            )
            beijing_time = utc_time.astimezone(timezone(timedelta(hours=8)))
            return beijing_time.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass

    return (
        datetime.now(timezone.utc)
        .astimezone(timezone(timedelta(hours=8)))
        .strftime("%Y-%m-%d %H:%M")
    )


# ==========================
# 图片 URL 处理
# ==========================
def fix_image_url(url):
    if not url:
        return ""
    url = url.strip()
    if url.startswith("//"):
        return "https:" + url
    return url


# ==========================
# HTML 中提取图片
# ==========================
def extract_img_from_html(html):
    if not html:
        return ""
    match = re.search(r'<img[^>]+src=["\']([^"\']+)', html, re.I)
    if match:
        return fix_image_url(match.group(1))
    return ""


# ==========================
# RSS 提取图片
# ==========================
def get_image(entry):
    # 1. media_thumbnail
    try:
        thumbnails = entry.get("media_thumbnail")
        if thumbnails and thumbnails[0].get("url"):
            return fix_image_url(thumbnails[0].get("url"))
    except Exception:
        pass

    # 2. media_content
    try:
        media = entry.get("media_content")
        if media and media[0].get("url"):
            return fix_image_url(media[0].get("url"))
    except Exception:
        pass

    # 3. enclosure
    try:
        enclosure = entry.get("enclosures")
        if enclosure and enclosure[0].get("href"):
            return fix_image_url(enclosure[0].get("href"))
    except Exception:
        pass

    # 4. RSS 自定义 image 字段
    try:
        image = entry.get("image")
        if isinstance(image, dict):
            url = image.get("href") or image.get("url")
            if url:
                return fix_image_url(url)
        elif isinstance(image, str):
            return fix_image_url(image)
    except Exception:
        pass

    # 5. summary
    try:
        img = extract_img_from_html(entry.get("summary", ""))
        if img:
            return img
    except Exception:
        pass

    # 6. description
    try:
        img = extract_img_from_html(entry.get("description", ""))
        if img:
            return img
    except Exception:
        pass

    # 7. content
    try:
        content = entry.get("content", [])
        if content:
            html = content[0].get("value", "")
            img = extract_img_from_html(html)
            if img:
                return img
    except Exception:
        pass

    return ""


# ==========================
# 网页获取封面图片
# ==========================
def get_web_image(url):
    if not url:
        return ""

    try:
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        # 优先 og:image
        image = soup.find("meta", property="og:image")
        if image and image.get("content"):
            return fix_image_url(image.get("content"))

        # 备用 twitter:image
        image = soup.find("meta", attrs={"name": "twitter:image"})
        if image and image.get("content"):
            return fix_image_url(image.get("content"))

    except Exception:
        pass

    return ""


# ==========================
# 抓取 RSS 并按时间排序
# ==========================
def main():
    for s in RSS_LIST:
        try:
            print(f"正在抓取 RSS: {s['name']}")
            feed = feedparser.parse(
                s["url"],
                agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )

            for x in feed.entries[:10]:
                title = clean_html(x.get("title", ""))
                summary = clean_html(x.get("summary", ""))

                if not title:
                    continue

                # 繁简转换
                title = zhconv.convert(title, 'zh-cn')
                summary = zhconv.convert(summary, 'zh-cn')

                if not summary:
                    summary = title

                summary = summary[:300]

                # 图片提取
                image = get_image(x)
                if not image and s.get("need_web_image"):
                    image = get_web_image(x.get("link", ""))

                articles.append(
                    {
                        "source": s["name"],
                        "category": s.get("category", "新闻"),
                        "title": title,
                        "summary": summary,
                        "link": x.get("link", ""),
                        "image": image,
                        "time": get_time(x),
                    }
                )

        except Exception as e:
            print(f"抓取失败 {s['name']}: {e}")

    # ==========================
    # 1. 去重
    # ==========================
    unique = {}
    for item in articles:
        key = item["link"] if item["link"] else (item["source"] + item["title"])
        if key not in unique:
            unique[key] = item

    final_articles = list(unique.values())

    # ==========================
    # 2. 【核心】全源混排：按发布时间倒序排列（最新的在最前）
    # ==========================
    final_articles.sort(key=lambda x: x["time"], reverse=True)

    # ==========================
    # 3. 双重保存到 data/ 和 website/ 目录
    # ==========================
    base_dir = Path(__file__).resolve().parent.parent

    target_paths = [
        base_dir / "data" / "articles.json",
        base_dir / "website" / "articles.json",
    ]

    for path in target_paths:
        path.parent.mkdir(exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(final_articles, f, ensure_ascii=False, indent=2)
        print(f"成功保存 {len(final_articles)} 条按时间排序后的新闻到: {path}")


if __name__ == "__main__":
    main()
