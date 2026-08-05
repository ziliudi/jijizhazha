document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("hot");
    if (!container) return;

    let hotData = [];
    let currentPlatform = "全部";

    const fetchHot = async () => {
        try {
            let res = await fetch("hot.json?v=" + Date.now());
            if (!res.ok) throw new Error("404");
            const data = await res.json();
            hotData = data;
            renderPage();
        } catch (err) {
            console.error(err);
            container.innerHTML = `<p style="text-align:center; color:#888; padding:30px;">热搜加载失败</p>`;
        }
    };

    const getColor = (platform) => {
        switch(platform) {
            case "抖音": return "#000";
            case "微博": return "#e6162d";
            case "知乎": return "#0084ff";
            case "网易新闻": return "#d71920";
            default: return "#333";
        }
    };

    const renderPage = () => {
        let platforms = [...new Set(hotData.map(p => p.platform))];
        let displayData = currentPlatform === "全部" ? hotData : hotData.filter(p => p.platform === currentPlatform);

        // 🎯 增加横向滑动样式 overflow-x: auto; 和 防止换行 white-space: nowrap;
        let buttonsHtml = `
            <div style="display:flex; gap:10px; overflow-x:auto; padding-bottom:12px; margin-bottom:15px; border-bottom:1px solid #eee; flex-wrap:nowrap; white-space:nowrap; -webkit-overflow-scrolling:touch;">
                <button class="tab-btn" data-platform="全部" style="cursor:pointer;border:none;background:transparent;padding:4px 12px;border-radius:20px;font-size:13px;flex-shrink:0;${currentPlatform === '全部' ? 'background:#1890ff;color:#fff;font-weight:bold;' : 'color:#666;'}">全部</button>`;
        
        platforms.forEach(p => {
            let isActive = currentPlatform === p;
            let color = getColor(p);
            buttonsHtml += `
                <button class="tab-btn" data-platform="${p}" style="cursor:pointer;border:none;background:transparent;padding:4px 12px;border-radius:20px;font-size:13px;flex-shrink:0;${isActive ? `background:${color};color:#fff;font-weight:bold;` : 'color:#666;'}">${p}</button>`;
        });
        buttonsHtml += `</div>`;

        let listHtml = "";
        displayData.forEach(platform => {
            if (!platform.items || platform.items.length === 0) return;
            let color = getColor(platform.platform);
            listHtml += `
                <div class="hot-card" style="background:#fff;border-radius:8px;padding:12px 16px;margin-bottom:16px;box-shadow:0 2px 6px rgba(0,0,0,0.04);">
                    <h2 style="font-size:16px;color:${color};margin-bottom:10px;">${platform.platform}</h2>
                    <ul style="list-style:none;padding:0;margin:0;">
                        ${platform.items.map(item => `
                            <li style="padding:8px 0;border-bottom:1px solid #f5f5f5;display:flex;align-items:center;">
                                <span style="font-weight:bold;color:#999;width:24px;font-size:14px;flex-shrink:0;">${item.rank}</span>
                                <a href="${item.url}" target="_blank" style="text-decoration:none;color:#333;flex:1;font-size:14px;line-height:1.5;word-break:break-all;">${item.title}</a>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        });

        if (listHtml === "") listHtml = `<p style="text-align:center; padding:20px; color:#888;">暂无数据</p>`;
        container.innerHTML = buttonsHtml + listHtml;

        container.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                currentPlatform = this.dataset.platform;
                renderPage();
            });
        });
    };
    fetchHot();
});
