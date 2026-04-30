const form = document.getElementById("book-form");

if (form) {
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const formData = new FormData(form);

        const data = Object.fromEntries(formData.entries());

        data.purchase_price = Number(data.purchase_price);

        const response = await fetch("/api/books", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            alert("登録しました");
            form.reset();
        } else {
            alert("登録に失敗しました");
        }
    });
}