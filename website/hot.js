document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("hot");
    if (!container) return;

    let hotData = [];
    let currentPlatform = "全部";

    // 🎯 平台显示名称映射（网易新闻 → 网易）
    const PLATFORM_DISPLAY = {
        "网易新闻": "网易",
        "抖音": "抖音",
        "微博": "微博",
        "知乎": "知乎",
        "必应": "必应"
    };

    // 🎯 平台排序顺序（全部 Tab 下的展示顺序）
    const PLATFORM_ORDER = ["抖音", "必应", "微博", "知乎", "网易"];

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
            case "必应": return "#0078d4";
            default: return "#333";
        }
    };

    const getDisplayName = (platform) => {
        return PLATFORM_DISPLAY[platform] || platform;
    };

    const renderPage = () => {
        let platforms = [...new Set(hotData.map(p => p.platform))];
        
        // 🎯 按 PLATFORM_ORDER 排序平台列表（用于 Tab 显示）
        platforms.sort((a, b) => {
            const displayA = getDisplayName(a);
            const displayB = getDisplayName(b);
            const indexA = PLATFORM_ORDER.indexOf(displayA);
            const indexB = PLATFORM_ORDER.indexOf(displayB);
            if (indexA === -1) return 1;
            if (indexB === -1) return -1;
            return indexA - indexB;
        });

        let displayData = currentPlatform === "全部" 
            ? [...hotData] 
            : hotData.filter(p => getDisplayName(p.platform) === currentPlatform);

        // 🎯 全部 Tab 下按 PLATFORM_ORDER 排序
        if (currentPlatform === "全部") {
            displayData.sort((a, b) => {
                const displayA = getDisplayName(a.platform);
                const displayB = getDisplayName(b.platform);
                const indexA = PLATFORM_ORDER.indexOf(displayA);
                const indexB = PLATFORM_ORDER.indexOf(displayB);
                if (indexA === -1) return 1;
                if (indexB === -1) return -1;
                return indexA - indexB;
            });
        }

        // 🎯 增加横向滑动样式 overflow-x: auto; 和 防止换行 white-space: nowrap;
        let buttonsHtml = `
            <div style="display:flex; gap:10px; overflow-x:auto; padding-bottom:12px; margin-bottom:15px; border-bottom:1px solid #eee; flex-wrap:nowrap; white-space:nowrap; -webkit-overflow-scrolling:touch;">
                <button class="tab-btn" data-platform="全部" style="cursor:pointer;border:none;background:transparent;padding:4px 12px;border-radius:20px;font-size:13px;flex-shrink:0;${currentPlatform === '全部' ? 'background:#1890ff;color:#fff;font-weight:bold;' : 'color:#666;'}">全部</button>`;
        
        platforms.forEach(p => {
            const displayName = getDisplayName(p);
            let isActive = currentPlatform === displayName;
            let color = getColor(p);
            buttonsHtml += `
                <button class="tab-btn" data-platform="${displayName}" style="cursor:pointer;border:none;background:transparent;padding:4px 12px;border-radius:20px;font-size:13px;flex-shrink:0;${isActive ? `background:${color};color:#fff;font-weight:bold;` : 'color:#666;'}">${displayName}</button>`;
        });
        buttonsHtml += `</div>`;

        let listHtml = "";
        displayData.forEach(platform => {
            if (!platform.items || platform.items.length === 0) return;
            let color = getColor(platform.platform);
            const displayName = getDisplayName(platform.platform);
            listHtml += `
                <div class="hot-card" style="background:#fff;border-radius:8px;padding:12px 16px;margin-bottom:16px;box-shadow:0 2px 6px rgba(0,0,0,0.04);">
                    <h2 style="font-size:16px;color:${color};margin-bottom:10px;">${displayName}</h2>
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