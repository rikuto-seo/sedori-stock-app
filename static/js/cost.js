const costForm =
    document.getElementById(
        "cost-form"
    );

const costList =
    document.getElementById(
        "cost-list"
    );


/* =========================
   一覧取得
========================= */

async function loadCosts() {

    const response =
        await fetch("/api/costs");

    const costs =
        await response.json();

    renderCosts(costs);

}


/* =========================
   描画
========================= */

function renderCosts(costs) {

    costList.innerHTML = "";

    if (costs.length === 0) {

        costList.innerHTML = `
            <div class="inventory-row">
                データがありません
            </div>
        `;

        return;

    }

    costs.forEach((cost) => {

        const div =
            document.createElement("div");

        div.className =
            "inventory-row";

        const quantityText =
            cost.quantity
            ? ` × ${cost.quantity}`
            : "";

        const typeText =
            cost.cost_type === "coupon"
            ? "クーポン"
            : "梱包材";

        div.innerHTML = `

            <div>

                <strong>
                    ${cost.name}
                </strong>

                <div>
                    ${typeText}
                </div>

                <div>
                    ¥${Number(cost.amount)
                        .toLocaleString()}
                    ${quantityText}
                </div>

            </div>

            <div>
                ${cost.cost_date}
            </div>

        `;

        costList.appendChild(div);

    });

}


/* =========================
   登録
========================= */

if (costForm) {

    costForm.addEventListener(
        "submit",
        async (e) => {

            e.preventDefault();

            const costType =
                costForm.cost_type.value;

            const unitPrice =
                Number(
                    costForm.unit_price.value || 0
                );

            const quantity =
                Number(
                    costForm.quantity.value || 1
                );

            // 合計金額
            const totalAmount =
                unitPrice * quantity;

            const data = {

                cost_type:
                    costType,

                name:
                    costForm.name.value,

                amount:
                    totalAmount,

                quantity:
                    quantity,

                memo:
                    costForm.memo.value,

                cost_date:
                    costForm.cost_date.value

            };

            await fetch(
                "/api/costs",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(data)

                }
            );

            costForm.reset();

            // 日付再設定
            const dateInput =
                document.querySelector(
                    'input[name="cost_date"]'
                );

            if (dateInput) {

                dateInput.valueAsDate =
                    new Date();

            }

            loadCosts();

        }
    );

}


/* =========================
   初期化
========================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const dateInput =
            document.querySelector(
                'input[name="cost_date"]'
            );

        if (dateInput) {

            dateInput.valueAsDate =
                new Date();

        }

        loadCosts();

    }
);