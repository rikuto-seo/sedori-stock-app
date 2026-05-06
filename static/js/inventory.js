const inventoryTable = document.getElementById(
    "inventory-table"
);

const searchInput = document.getElementById(
    "search-input"
);

const statusFilter = document.getElementById(
    "status-filter"
);

const bookCount = document.getElementById(
    "book-count"
);

const salePriceInput = document.getElementById(
    "sale-price"
);

const saleFeeInput = document.getElementById(
    "sale-fee"
);

const saleDateInput = document.getElementById(
    "sale-date"
);

const saleStatusInput = document.getElementById(
    "sale-status"
);

const shippingMethodInput = document.getElementById(
    "shipping-method"
);

const shippingInput = document.getElementById(
    "sale-shipping"
);

let books = [];

let feeManuallyEdited = false;
let shippingManuallyEdited = false;
let selectedBooks = [];

/* =========================
   初期化
========================= */

async function initInventory() {

    try {

        const response = await fetch(
            "/api/books"
        );

        books = await response.json();

        renderBooks(books);

    }

    catch (error) {

        console.error(error);

    }

}

function toggleBookSelection(bookId) {

    if (selectedBooks.includes(bookId)) {

        selectedBooks =
            selectedBooks.filter(
                id => id !== bookId
            );

    } else {

        selectedBooks.push(bookId);

    }

    renderBooks();

}

function openGroupSaleModal() {

    if (selectedBooks.length === 0) {

        alert("本を選択してください");

        return;

    }

    document.getElementById(
        "group-sale-modal"
    ).style.display = "flex";

    document.getElementById(
        "selected-books"
    ).innerHTML = `

        <div class="inventory-count">

            ${selectedBooks.length}冊選択中

        </div>

    `;

}


function closeGroupSaleModal() {

    document.getElementById(
        "group-sale-modal"
    ).style.display = "none";

}

async function submitGroupSale(e) {

    e.preventDefault();

    const payload = {

        book_ids: selectedBooks,

        sale_price:
            document.getElementById(
                "group-sale-price"
            ).value,

        fee:
            document.getElementById(
                "group-sale-fee"
            ).value,

        shipping_cost:
            document.getElementById(
                "group-sale-shipping"
            ).value,

        shipping_method:
            document.getElementById(
                "group-shipping-method"
            ).value,

        sale_date:
            document.getElementById(
                "group-sale-date"
            ).value

    };

    const response = await fetch(

        "/api/sales/group",

        {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify(
                payload
            )

        }

    );

    if (!response.ok) {

        alert("セット販売失敗");

        return;

    }

    alert("セット販売完了");

    selectedBooks = [];

    closeGroupSaleModal();

    initInventory();

}

/* =========================
   描画
========================= */

function renderBooks(bookList = books) {

    inventoryTable.innerHTML = "";
    bookCount.textContent = bookList.length;

    if (bookList.length === 0) {
        inventoryTable.innerHTML = `
            <div class="inventory-row">
                データがありません
            </div>
        `;
        return;
    }

    bookList.forEach((book) => {

        let profitHTML = "";

        const sale = book.sale || {};

        const salePrice = Number(sale.sale_price || 0);
        const fee = Number(sale.fee || 0);
        const shipping = Number(sale.shipping_cost || 0);
        const purchasePrice = Number(book.purchase_price || 0);

        if (salePrice > 0) {

            const profit =
                salePrice - fee - shipping - purchasePrice;

            const profitClass =
                profit >= 0 ? "profit-plus" : "profit-minus";

            const sign = profit >= 0 ? "+" : "-";

            profitHTML = `
                <div class="inventory-profit ${profitClass}">
                    ${sign}¥${Math.abs(profit).toLocaleString()}
                </div>
            `;
        }

        const checked =
            selectedBooks.includes(book.id)
                ? "checked"
                : "";

        const row = document.createElement("div");

        row.className = "inventory-row";

        row.innerHTML = `

            <div class="inventory-main">

                <input
                    type="checkbox"
                    class="group-checkbox"
                    ${checked}
                    onchange="toggleBookSelection(${book.id})"
                >

                <div class="status-badge status-${book.status}">
                    ${book.status}
                </div>

                <div class="inventory-title-area">

                    <div class="inventory-title">
                        ${book.title || ""}
                    </div>

                    ${profitHTML}

                </div>

            </div>

            <div class="inventory-actions">

                <button
                    class="detail-button"
                    onclick='openDetailModal(${JSON.stringify(book)})'
                >
                    詳細
                </button>

                <button
                    class="sale-button"
                    onclick='openSaleModal(${JSON.stringify(book)})'
                >
                    販売
                </button>

                <button
                    class="delete-button"
                    onclick="deleteBook(${book.id})"
                >
                    削除
                </button>

            </div>

        `;

        inventoryTable.appendChild(row);

    });
}

/* =========================
   Cコード自動分類
========================= */

const TARGET_MAP = {

    "0": "一般",
    "1": "教養",
    "2": "実用",
    "3": "専門",
    "4": "検定",
    "5": "婦人",
    "6": "学参I(小中)",
    "7": "学参II(高校)",
    "8": "児童",
    "9": "雑誌扱い"

};


const FORMAT_MAP = {

    "0": "単行本",
    "1": "文庫",
    "2": "新書",
    "3": "全集・双書",
    "4": "ムック・その他",
    "5": "事・辞典",
    "6": "図鑑",
    "7": "絵本",
    "8": "磁性媒体など",
    "9": "コミック"

};


const GENRE_MAP = {

    "00": "総記",
    "01": "百科事典",
    "02": "年鑑・雑誌",
    "04": "情報科学",
    "10": "哲学",

    "11": "心理学",
    "12": "倫理学",
    "14": "宗教",
    "15": "仏学",
    "16": "キリスト教",

    "20": "歴史総記",
    "21": "日本歴史",
    "22": "外国歴史",
    "23": "伝記",
    "25": "地理",
    "26": "旅行",

    "30": "社会科学総記",
    "31": "政治含む国防軍事",
    "32": "法律",
    "33": "経済・財政・統計",
    "34": "経営",
    "36": "社会",
    "37": "教育",
    "39": "民族・風習",

    "40": "自然科学総記",
    "41": "数学",
    "42": "物理",
    "43": "化学",
    "44": "天文・地学",
    "45": "生物学",
    "47": "医学・歯学・薬学",

    "50": "工学・工学総記",
    "51": "土木",
    "52": "建築",
    "53": "機械",
    "54": "電気",
    "55": "電子通信",
    "56": "海事",
    "57": "採鉱・冶金",
    "58": "その他の工業",

    "60": "産業総記",
    "61": "農林業",
    "62": "水産業",
    "63": "産業",
    "65": "交通・通信",

    "70": "芸術総記",
    "71": "絵画・彫刻",
    "72": "写真・工芸",
    "73": "音楽・舞踊",
    "74": "演劇・映画",
    "75": "体育",
    "76": "諸芸・娯楽",
    "77": "家事",
    "79": "コミックス・劇画",

    "80": "語学総記",
    "81": "日本語",
    "82": "英米語",
    "84": "ドイツ語",
    "85": "フランス語",
    "87": "各国語",

    "90": "文学総記",
    "91": "日本文学総記",
    "92": "日本文学詩歌",
    "93": "日本文学、小説・物語",
    "95": "文学、評論、随筆、その他",
    "97": "外国文学小説",
    "98": "外国文学、その他"

};


/* =========================
   要素取得
========================= */

const cCodeInput = document.getElementById(
    "c-code-input"
);

const genreInput = document.getElementById(
    "genre-input"
);

const formatInput = document.getElementById(
    "format-input"
);

const targetInput = document.getElementById(
    "target-input"
);


/* =========================
   手動編集フラグ
========================= */

let genreManuallyEdited = false;

let formatManuallyEdited = false;

let targetManuallyEdited = false;


/* =========================
   手動入力監視
========================= */

if (genreInput) {

    genreInput.addEventListener(
        "input",
        () => {

            genreManuallyEdited = true;

        }
    );

}


if (formatInput) {

    formatInput.addEventListener(
        "input",
        () => {

            formatManuallyEdited = true;

        }
    );

}


if (targetInput) {

    targetInput.addEventListener(
        "input",
        () => {

            targetManuallyEdited = true;

        }
    );

}


/* =========================
   Cコード解析
========================= */

function parseCCode(cCode) {

    if (!cCode) {

        return null;

    }

    const normalized =
        cCode
            .toUpperCase()
            .replace("C", "");

    if (normalized.length < 4) {

        return null;

    }

    const targetCode =
        normalized[0];

    const formatCode =
        normalized[1];

    const genreCode =
        normalized.slice(2, 4);

    return {

        target:
            TARGET_MAP[targetCode]
            || "",

        book_format:
            FORMAT_MAP[formatCode]
            || "",

        genre:
            GENRE_MAP[genreCode]
            || ""

    };

}


/* =========================
   自動入力
========================= */

if (cCodeInput) {

    cCodeInput.addEventListener(
        "input",
        () => {

            const parsed =
                parseCCode(
                    cCodeInput.value
                );

            if (!parsed) {

                return;

            }

            if (
                !genreManuallyEdited
                && parsed.genre
            ) {

                genreInput.value =
                    parsed.genre;

            }

            if (
                !formatManuallyEdited
                && parsed.book_format
            ) {

                formatInput.value =
                    parsed.book_format;

            }

            if (
                !targetManuallyEdited
                && parsed.target
            ) {

                targetInput.value =
                    parsed.target;

            }

        }
    );

}


/* =========================
   フィルター
========================= */

function filterBooks() {

    const search =
        searchInput.value.toLowerCase();

    const status =
        statusFilter.value;

    const filtered = books.filter(
        (book) => {

            const matchesSearch =

                (book.title || "")
                    .toLowerCase()
                    .includes(search)

                ||

                (book.isbn || "")
                    .includes(search);

            const matchesStatus =

                !status

                ||

                book.status === status;

            return (
                matchesSearch
                && matchesStatus
            );

        }
    );

    renderBooks(filtered);

}


/* =========================
   詳細モーダル
========================= */

function openDetailModal(book) {

    document.getElementById(
        "detail-modal"
    ).style.display = "flex";

    document.getElementById(
        "detail-id"
    ).value = book.id;

    document.getElementById(
        "detail-title"
    ).value = book.title || "";

    document.getElementById(
        "detail-isbn"
    ).value = book.isbn || "";

    document.getElementById(
        "detail-publisher"
    ).value = book.publisher || "";

    document.getElementById(
        "detail-genre"
    ).value = book.genre || "";

    document.getElementById(
        "detail-purchase-price"
    ).value =
        book.purchase_price || "";

    document.getElementById(
        "detail-purchase-store"
    ).value =
        book.purchase_store || "";

    document.getElementById(
        "detail-c-code"
    ).value = book.c_code || "";

    document.getElementById(
        "detail-memo"
    ).value = book.memo || "";

}


function closeDetailModal() {

    document.getElementById(
        "detail-modal"
    ).style.display = "none";

}


/* =========================
   販売モーダル
========================= */

function openSaleModal(book) {

    feeManuallyEdited = false;
    shippingManuallyEdited = false;

    const sale = book.sale || {};

    document.getElementById("sale-modal").style.display = "flex";

    document.getElementById("sale-id").value = book.id;

    salePriceInput.value = sale.sale_price || "";
    saleFeeInput.value = sale.fee || "";
    shippingInput.value = sale.shipping_cost || "";

    saleDateInput.value =
        sale.sale_date
            ? sale.sale_date.slice(0, 10)
            : "";

    shippingMethodInput.value =
        sale.shipping_method || "";

    saleStatusInput.value =
        book.status || "出品中";
}


/* =========================
   販売モーダル閉じる
========================= */

function closeSaleModal() {

    document.getElementById(
        "sale-modal"
    ).style.display = "none";

}


/* =========================
   手数料手動変更
========================= */

if (saleFeeInput) {

    saleFeeInput.addEventListener(
        "input",
        () => {

            feeManuallyEdited = true;

        }
    );

}


/* =========================
   送料手動変更
========================= */

if (shippingInput) {

    shippingInput.addEventListener(
        "input",
        () => {

            shippingManuallyEdited = true;

        }
    );

}


/* =========================
   配送方法変更
========================= */

if (shippingMethodInput) {

    shippingMethodInput.addEventListener(
        "change",
        () => {

            if (shippingManuallyEdited) {

                return;

            }

            const method =
                shippingMethodInput.value;

            if (
                method ===
                "らくらくメルカリ便"
            ) {

                shippingInput.value = 210;

            }

            else if (
                method ===
                "ゆうゆうパケットポストミニ"
            ) {

                shippingInput.value = 160;

            }

        }
    );

}


/* =========================
   販売価格入力
========================= */

if (salePriceInput) {

    salePriceInput.addEventListener(
        "input",
        () => {

            const salePrice =
                Number(
                    salePriceInput.value || 0
                );

            /* =========================
               手数料自動計算
            ========================= */

            if (!feeManuallyEdited) {

                const fee =
                    Math.floor(
                        salePrice * 0.1
                    );

                saleFeeInput.value = fee;

            }

            /* =========================
               ステータス自動変更
            ========================= */

            if (salePrice > 0) {

                saleStatusInput.value =
                    "売却済";

                if (!saleDateInput.value) {

                    saleDateInput.valueAsDate =
                        new Date();

                }

            }

            else {

                saleStatusInput.value =
                    "出品中";

            }

        }
    );

}


/* =========================
   詳細保存
========================= */

const detailForm =
    document.getElementById(
        "detail-form"
    );

if (detailForm) {

    detailForm.addEventListener(
        "submit",
        async (e) => {

            e.preventDefault();

            const id =
                document.getElementById(
                    "detail-id"
                ).value;

            const data = {

                title:
                    document.getElementById(
                        "detail-title"
                    ).value,

                isbn:
                    document.getElementById(
                        "detail-isbn"
                    ).value,

                publisher:
                    document.getElementById(
                        "detail-publisher"
                    ).value,

                genre:
                    document.getElementById(
                        "detail-genre"
                    ).value,

                purchase_price:
                    document.getElementById(
                        "detail-purchase-price"
                    ).value,

                purchase_store:
                    document.getElementById(
                        "detail-purchase-store"
                    ).value,

                c_code:
                    document.getElementById(
                        "detail-c-code"
                    ).value,

                memo:
                    document.getElementById(
                        "detail-memo"
                    ).value

            };

            await fetch(
                `/api/books/${id}`,
                {

                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify(data)

                }
            );

            closeDetailModal();

            initInventory();

        }
    );

}


/* =========================
   販売保存
========================= */

const saleForm =
    document.getElementById(
        "sale-form"
    );

if (saleForm) {

    saleForm.addEventListener(
        "submit",
        async (e) => {

            e.preventDefault();

            const id =
                document.getElementById(
                    "sale-id"
                ).value;

            const data = {

                sale_price:
                    salePriceInput.value,

                fee:
                    saleFeeInput.value,

                shipping_cost:
                    shippingInput.value,

                sale_date:
                    saleDateInput.value,

                shipping_method:
                    shippingMethodInput.value,

                status:
                    saleStatusInput.value

            };

            await fetch(
                `/api/books/${id}/sale`,
                {

                    method: "PATCH",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify(data)

                }
            );

            closeSaleModal();

            initInventory();

        }
    );

}


/* =========================
   削除
========================= */

async function deleteBook(id) {

    const confirmed = confirm(
        "本当に削除しますか？"
    );

    if (!confirmed) return;

    await fetch(
        `/api/books/${id}`,
        {
            method: "DELETE"
        }
    );

    initInventory();

}


/* =========================
   イベント
========================= */

if (searchInput) {

    searchInput.addEventListener(
        "input",
        filterBooks
    );

}


if (statusFilter) {

    statusFilter.addEventListener(
        "change",
        filterBooks
    );

}


/* =========================
   起動
========================= */

initInventory();