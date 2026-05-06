let monthlyChartInstance = null;
let genreChartInstance = null;
let statusChartInstance = null;

/* =========================
   DOM取得（←これが必要）
========================= */

const summaryCards = document.getElementById("summary-cards");

/* =========================
   Summary
========================= */

async function loadSummary() {

    const res = await fetch("/api/analytics/summary");
    const data = await res.json();

    renderSummary(data);
}

function safeNumber(val) {
    return Number(val || 0);
}

function renderSummary(data) {

    if (!summaryCards) return; // 念のため防御

    summaryCards.innerHTML = `

        <div class="analytics-card">
            <div class="analytics-label">総利益</div>
            <div class="analytics-value">
                ¥${safeNumber(data.profit).toLocaleString()}
            </div>
        </div>

        <div class="analytics-card">
            <div class="analytics-label">利益率</div>
            <div class="analytics-value">
                ${safeNumber(data.profit_rate)}%
            </div>
        </div>

        <div class="analytics-card">
            総売上<br>
            ¥${safeNumber(data.sales).toLocaleString()}
        </div>

        <div class="analytics-card">
            総仕入<br>
            ¥${safeNumber(data.purchase).toLocaleString()}
        </div>

        <div class="analytics-card">
            総送料<br>
            ¥${safeNumber(data.shipping).toLocaleString()}
        </div>

        <div class="analytics-card">
            経費<br>
            ¥${safeNumber(data.costs).toLocaleString()}
        </div>

        <div class="analytics-card">
            売却数<br>
            ${safeNumber(data.sold_count)}
        </div>

        <div class="analytics-card">
            在庫数<br>
            ${safeNumber(data.inventory_count)}
        </div>

    `;
}

/* =========================
   Monthly Chart
========================= */

async function loadMonthlyChart() {

    const res = await fetch("/api/analytics/monthly");
    const data = await res.json();

    renderMonthlyChart(data);
}

function renderMonthlyChart(data) {

    const ctx = document.getElementById("monthlyChart");

    if (monthlyChartInstance) {
        monthlyChartInstance.destroy();
    }

    monthlyChartInstance = new Chart(ctx, {

        type: "line",

        data: {
            labels: data.labels || [],
            datasets: [
                {
                    label: "売上",
                    data: data.sales || [],
                    tension: 0.3
                },
                {
                    label: "利益",
                    data: data.profit || [],
                    tension: 0.3
                },
                {
                    label: "経費",
                    data: data.costs || [],
                    tension: 0.3
                }
            ]
        },

        options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            },
            scales: {
                y: {
                    ticks: {
                        callback: (v) => "¥" + v.toLocaleString()
                    }
                }
            }
        }

    });
}

/* =========================
   Genre Profit
========================= */

async function loadGenreProfit() {

    const res = await fetch("/api/analytics/genre-profit");
    const data = await res.json();

    const ctx = document.getElementById("genreProfitChart");

    if (genreChartInstance) {
        genreChartInstance.destroy();
    }

    genreChartInstance = new Chart(ctx, {

        type: "doughnut",

        data: {
            labels: data.labels || [],
            datasets: [
                {
                    data: data.values || []
                }
            ]
        }

    });
}

/* =========================
   Status
========================= */

async function loadStatusChart() {

    const res = await fetch("/api/analytics/status");
    const data = await res.json();

    const ctx = document.getElementById("statusChart");

    if (statusChartInstance) {
        statusChartInstance.destroy();
    }

    statusChartInstance = new Chart(ctx, {

        type: "pie",

        data: {
            labels: data.labels || [],
            datasets: [
                {
                    data: data.values || []
                }
            ]
        }

    });
}

/* =========================
   Rotation
========================= */

async function loadRotationStats() {

    const res = await fetch("/api/analytics/rotation");
    const data = await res.json();

    renderRotationStats(data);
}

function renderRotationStats(data) {

    const container =
        document.getElementById("rotation-stats");

    container.innerHTML = `

        <div class="rotation-grid">

            <div class="analytics-card">
                <div class="analytics-label">平均</div>
                <div class="analytics-value">
                    ${safeNumber(data.average)}日
                </div>
            </div>

            <div class="analytics-card">
                <div class="analytics-label">最短</div>
                <div class="analytics-value">
                    ${safeNumber(data.min)}日
                </div>
            </div>

            <div class="analytics-card">
                <div class="analytics-label">最長</div>
                <div class="analytics-value">
                    ${safeNumber(data.max)}日
                </div>
            </div>

            <div class="analytics-card">
                <div class="analytics-label">中央値</div>
                <div class="analytics-value">
                    ${safeNumber(data.median)}日
                </div>
            </div>

        </div>

    `;
}

/* =========================
   Profit Ranking
========================= */

async function loadProfitRanking() {

    const res = await fetch("/api/analytics/profit-ranking");
    const data = await res.json();

    const container =
        document.getElementById("profit-ranking");

    container.innerHTML = "";

    (data || []).forEach((item, index) => {

        container.innerHTML += `
            <div class="inventory-row">
                <div>${index + 1}. ${item.title}</div>
                <div>${safeNumber(item.rate)}%</div>
            </div>
        `;
    });
}

/* =========================
   Init
========================= */

document.addEventListener("DOMContentLoaded", () => {

    loadSummary();
    loadMonthlyChart();
    loadGenreProfit();
    loadStatusChart();
    loadRotationStats();
    loadProfitRanking();

});