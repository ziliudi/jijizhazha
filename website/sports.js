document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("news");
    if (!container) return;

    let sportsData = { latest_30: [], hot_20: [] };
    let currentTab = "latest";

    const fetchSports = async () => {
        try {
            let res = await fetch("sports.json?v=" + Date.now());

            if (!res.ok) {
                res = await fetch("data/sports.json?v=" + Date.now());
            }

            if (!res.ok) {
                throw new Error("404");
            }

            const rawData = await res.json();

            if (Array.isArray(rawData)) {
                sportsData.latest_30 = rawData;
                sportsData.hot_20 = rawData.slice(0, 20);
            } else {
                sportsData.latest_30 = rawData.latest_30 || rawData.data || [];
                sportsData.hot_20 = rawData.hot_20 || [];
            }

            renderPage();
        } catch (err) {
            console.error(err);
            renderPage();
        }
    };

    const renderPage = () => {
        const items =
            currentTab === "latest"
                ? sportsData.latest_30
                : sportsData.hot_20;

        let listHtml = "";
        if (!items || items.length === 0) {
            listHtml = `<li style="text-align:center; padding:30px; color:#888; list-style:none;">
                            暂无${currentTab === 'latest' ? '最新资讯' : '热榜'}数据
                        </li>`;
        } else {
            items.forEach((item, index) => {
                // 🔥 核心修改：在这里读取 heat 和 comment
                const heatHtml = item.heat ? `<span style="color:#e74c3c;font-weight:bold;">🔥 ${item.heat}</span>` : '';
                const commentHtml = item.comment ? `<span style="color:#999;font-size:12px;margin-left:8px;">${item.comment}</span>` : '';

                // 构建 HTML 列表
                listHtml += `
                    <div class="hot-item" style="padding:12px 0;border-bottom:1px solid #f0f0f0;display:flex;align-items:flex-start;gap:12px;">
                        <span class="rank-num" style="font-weight:bold;width:24px;color:#888;flex-shrink:0;margin-top:2px;">${index + 1}</span>
                        <div style="flex:1;display:flex;flex-direction:column;gap:4px;">
                            <a href="${item.url}" target="_blank" style="text-decoration:none;color:#1a73e8;font-weight:500;font-size:15px;line-height:1.4;">${item.title}</a>
                            <div style="font-size:13px;display:flex;align-items:center;flex-wrap:wrap;gap:4px;">
                                ${heatHtml}
                                ${commentHtml}
                            </div>
                        </div>
                    </div>
                `;
            });
        }

        const html = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;padding:0 4px;">
                <span style="font-size:13px;color:#666;">
                    ${currentTab === 'latest' ? '最新体育资讯' : '24小时热榜'}
                </span>
                <div style="font-size:14px;">
                    <span id="btn-latest"
                          style="cursor:pointer;
                          ${currentTab === 'latest' ? 'font-weight:bold;color:#1890ff;' : 'color:#666;'}
                          margin-right:12px;">
                        🕒 最新
                    </span>
                    <span id="btn-hot"
                          style="cursor:pointer;
                          ${currentTab === 'hot' ? 'font-weight:bold;color:#ff4d4f;' : 'color:#666;'}">
                        🔥 最热
                    </span>
                </div>
            </div>
            <div class="card hot-card"
                 style="background:#fff;border-radius:8px;padding:16px;">
                <h2 class="card-title"
                    style="font-size:18px;margin-bottom:12px;">
                    ${currentTab === 'latest' ? '最新体育资讯' : '24小时热榜'}
                </h2>
                <div style="padding:0;margin:0;">
                    ${listHtml}
                </div>
            </div>
        `;

        container.innerHTML = html;

        document.getElementById("btn-latest")
            ?.addEventListener("click", () => {
                if (currentTab !== "latest") {
                    currentTab = "latest";
                    renderPage();
                }
            });

        document.getElementById("btn-hot")
            ?.addEventListener("click", () => {
                if (currentTab !== "hot") {
                    currentTab = "hot";
                    renderPage();
                }
            });
    };

    fetchSports();
});
