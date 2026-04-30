const scanButton = document.querySelector(".scan-button");

const scannerContainer = document.getElementById(
    "scanner-container"
);

const closeScannerButton = document.getElementById(
    "close-scanner"
);

const isbnInput = document.querySelector(
    'input[name="isbn"]'
);

let html5QrCode = null;


// スキャン開始
async function startScanner() {

    scannerContainer.style.display = "block";

    html5QrCode = new Html5Qrcode("reader");

    try {

        await html5QrCode.start(
            {
                facingMode: "environment"
            },
            {
                fps: 10,
                qrbox: {
                    width: 250,
                    height: 120
                }
            },

            // 成功時
            async (decodedText) => {

                console.log("読み取り:", decodedText);

                isbnInput.value = decodedText;

                stopScanner();

                // ISBN自動取得
                fetchBookData(decodedText);

            }
        );

    } catch (error) {

        console.error(error);

        alert("カメラを起動できません");

    }

}


// スキャン停止
async function stopScanner() {

    if (html5QrCode) {

        await html5QrCode.stop();

        await html5QrCode.clear();

        html5QrCode = null;

    }

    scannerContainer.style.display = "none";

}


// Google Books API取得
async function fetchBookData(isbn) {

    try {

        const response = await fetch(
            `/scan/isbn/${isbn}`
        );

        const data = await response.json();

        console.log(data);

        if (data.title) {

            document.querySelector(
                'input[name="title"]'
            ).value = data.title || "";

            document.querySelector(
                'input[name="publisher"]'
            ).value = data.publisher || "";

            document.querySelector(
                'input[name="genre"]'
            ).value = data.genre || "";

        }

    } catch (error) {

        console.error(error);

    }

}


// ボタンイベント
if (scanButton) {

    scanButton.addEventListener(
        "click",
        startScanner
    );

}


if (closeScannerButton) {

    closeScannerButton.addEventListener(
        "click",
        stopScanner
    );

}