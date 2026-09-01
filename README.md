# 叽叽喳喳 (jijizhazha) 📢

一个基于 **GitHub Actions + Python 爬虫** 实现的全自动化新闻、热搜与体育资讯聚合平台。

---

## 🌟 功能特点

- **全自动化更新**：利用 GitHub Actions 定时任务，无需服务器即可实现数据的自动抓取与推送。
- **多维度资讯聚合**：
  - **新闻资讯**：包含全球/国内核心新闻聚合。
  - **全网热搜**：聚合微博、抖音、知乎、网易新闻等热门榜单。
  - **体育热榜**：精准抓取虎扑体育资讯。
- **轻量前端展示**：极简响应式页面，支持移动端与桌面端自适应浏览。

---

## 📂 项目结构

```text
.
├── .github/workflows/   # GitHub Actions 自动化工作流配置
│   └── update.yml      # 定时触发爬虫并同步数据的脚本
├── crawler/             # Python 爬虫核心代码
│   ├── main.py         # 新闻类爬虫
│   ├── hot.py          # 全网热搜爬虫 (抖音/微博/知乎等)
│   └── sports.py       # 体育资讯爬虫 (虎扑体育)
├── data/                # 爬虫抓取生成的 JSON 数据缓存
│   ├── articles.json
│   ├── hot.json
│   └── sports.json
└── website/             # 前端静态页面与站点展示
    ├── articles.json
    ├── hot.json
    └── sports.json

🛠️ 工作原理
 * 定时触发：根据 .github/workflows/update.yml 中的 Cron 定时配置，触发自动化部署。
 * 数据爬取：运行 crawler/ 目录下的 Python 脚本解析网页内容并提取最新热榜。
 * 数据同步：脚本生成 JSON 数据并自动提交更新回仓库及 website/ 目录。
 * 前端渲染：静态托管平台（如 Cloudflare Pages / GitHub Pages）通过 Fetch 请求最新的 JSON 数据完成页面展示。
⚙️ 本地开发与测试
如果你想在本地运行爬虫：
 * 克隆仓库
   git clone [https://github.com/ziliudi/jijizhazha.git](https://github.com/ziliudi/jijizhazha.git)
cd jijizhazha

 * 安装依赖
   pip install -r crawler/requirements.txt

 * 手动运行爬虫
   python crawler/main.py
python crawler/hot.py
python crawler/sports.py

📄 License
MIT License

