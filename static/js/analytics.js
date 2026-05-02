const summaryCards =
    document.getElementById(
        "summary-cards"
    );

async function loadSummary() {

    const response =
        await fetch(
            "/api/analytics/summary"
        );

    const data =
        await response.json();

    renderSummary(data);

}

function renderSummary(data) {

    summaryCards.innerHTML = `

        <div class="analytics-card">
            <div class="analytics-label">
                総利益
            </div>

            <div class="analytics-value">
                ¥${data.profit.toLocaleString()}
            </div>
        </div>

        <div class="analytics-card">

            <div class="analytics-label">
                利益率
            </div>

            <div class="analytics-value">
                ${data.profit_rate}%
            </div>

        </div>

        <div class="analytics-card">
            総売上<br>
            ¥${data.sales.toLocaleString()}
        </div>

        <div class="analytics-card">
            総仕入<br>
            ¥${data.purchase.toLocaleString()}
        </div>

        <div class="analytics-card">
            総送料<br>
            ¥${data.shipping.toLocaleString()}
        </div>

        <div class="analytics-card">
            経費<br>
            ¥${data.costs.toLocaleString()}
            
        </div>

        <div class="analytics-card">
            売却数<br>
            ${data.sold_count}
        </div>

        <div class="analytics-card">
            在庫数<br>
            ${data.inventory_count}
        </div>

    `;

}

async function loadMonthlyChart() {

    const response =
        await fetch(
            "/api/analytics/monthly"
        );

    const data =
        await response.json();

    renderMonthlyChart(data);

}

function renderMonthlyChart(data) {

    const ctx =
        document.getElementById(
            "monthlyChart"
        );

    new Chart(ctx, {

        type: "line",

        data: {

            labels:
                data.labels,

            datasets: [

                {
                    label: "売上",

                    data:
                        data.sales,

                    tension: 0.3
                },

                {
                    label: "利益",

                    data:
                        data.profit,

                    tension: 0.3
                },

                {
                    label: "経費",

                    data:
                        data.costs,

                    tension: 0.3
                }

            ]

        },

        options: {

            responsive: true,

            plugins: {

                legend: {
                    display: true
                }

            },

            scales: {

                y: {

                    ticks: {

                        callback:
                            function(value) {

                                return "¥"
                                    + value
                                    .toLocaleString();

                            }

                    }

                }

            }

        }

    });

}

async function loadGenreProfit() {

    const response =
        await fetch(
            "/api/analytics/genre-profit"
        );

    const data =
        await response.json();

    new Chart(

        document.getElementById(
            "genreProfitChart"
        ),

        {

            type: "doughnut",

            data: {

                labels:
                    data.labels,

                datasets: [
                    {
                        data:
                            data.values
                    }
                ]

            }

        }

    );

}

async function loadStatusChart() {

    const response =
        await fetch(
            "/api/analytics/status"
        );

    const data =
        await response.json();

    new Chart(

        document.getElementById(
            "statusChart"
        ),

        {

            type: "pie",

            data: {

                labels:
                    data.labels,

                datasets: [
                    {
                        data:
                            data.values
                    }
                ]

            }

        }

    );

}

async function loadRotationStats() {

    const response =
        await fetch(
            "/api/analytics/rotation"
        );

    const data =
        await response.json();

    renderRotationStats(data);

}

function renderRotationStats(data) {

    const container =
        document.getElementById(
            "rotation-stats"
        );

    container.innerHTML = `

        <div class="rotation-grid">

            <div class="analytics-card">

                <div class="analytics-label">
                    平均
                </div>

                <div class="analytics-value">
                    ${data.average}日
                </div>

            </div>

            <div class="analytics-card">

                <div class="analytics-label">
                    最短
                </div>

                <div class="analytics-value">
                    ${data.min}日
                </div>

            </div>

            <div class="analytics-card">

                <div class="analytics-label">
                    最長
                </div>

                <div class="analytics-value">
                    ${data.max}日
                </div>

            </div>

            <div class="analytics-card">

                <div class="analytics-label">
                    中央値
                </div>

                <div class="analytics-value">
                    ${data.median}日
                </div>

            </div>

        </div>

    `;

}

async function loadProfitRanking() {

    const response =
        await fetch(
            "/api/analytics/profit-ranking"
        );

    const data =
        await response.json();

    const container =
        document.getElementById(
            "profit-ranking"
        );

    container.innerHTML = "";

    data.forEach((item, index) => {

        container.innerHTML += `

            <div class="inventory-row">

                <div>

                    ${index + 1}.
                    ${item.title}

                </div>

                <div>

                    ${item.rate}%

                </div>

            </div>

        `;

    });

}

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadSummary();

        loadMonthlyChart();

        loadGenreProfit();

        loadStatusChart();

        loadRotationStats();

        loadProfitRanking();

    }
);