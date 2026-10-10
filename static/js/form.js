(() => {
const form = document.getElementById('book-form');
if (!form) return;
const date = document.getElementById('purchase-date'), store = document.getElementById('purchase-store');
const defaultPrice = document.getElementById('default-price'), price = document.getElementById('item-price');
const isbn = document.getElementById('isbn-input'), status = document.getElementById('lookup-status');
const list = document.getElementById('purchase-list'), save = document.getElementById('save-purchase');
let cart = [], controller, lookupVersion = 0, timer, saving = false;
try { const draft = JSON.parse(localStorage.getItem('purchase-draft-v1') || '{}'); cart = Array.isArray(draft.cart) ? draft.cart : []; date.value = draft.date || localDate(); store.value = draft.store || ''; defaultPrice.value = draft.price ?? 110; } catch { date.value = localDate(); }
price.value = defaultPrice.value;
function persist() { try { localStorage.setItem('purchase-draft-v1', JSON.stringify({cart, date: date.value, store: store.value, price: defaultPrice.value})); } catch { status.textContent = 'このブラウザでは下書きを保存できません。画面を閉じる前に登録してください。'; } }
function count() { return cart.reduce((n, item) => n + Number(item.quantity), 0); }
function render() {
 list.innerHTML = cart.length ? cart.map((item, i) => `<article class="cart-row"><div class="cart-row-top"><span class="muted">${String(i+1).padStart(2,'0')}</span><input aria-label="${i+1}番目のタイトル" data-index="${i}" data-key="title" value="${escapeHTML(item.title)}" maxlength="255" required><button type="button" class="remove-item" data-remove="${i}" aria-label="${i+1}番目を削除">×</button></div><p class="cart-meta">${escapeHTML(item.isbn || 'ISBNなし')} · ${escapeHTML(item.purchase_store || '店舗未指定')} · ${escapeHTML(item.purchase_date)}</p><div class="cart-row-bottom"><label>単価 ¥<input type="number" min="0" step="1" aria-label="単価" data-index="${i}" data-key="purchase_price" value="${item.purchase_price}"></label><label>冊数<input type="number" min="1" max="200" step="1" aria-label="冊数" data-index="${i}" data-key="quantity" value="${item.quantity}"></label><strong>¥${(item.purchase_price*item.quantity).toLocaleString()}</strong></div></article>`).join('') : '<div class="empty-state"><span class="empty-icon">▤</span><h3>仕入れた本を追加しましょう</h3><p>ISBNで検索するか、タイトルを入力して<br>左のフォームから追加できます。</p></div>';
 document.getElementById('cart-count').textContent = `${count()}冊`;
 document.getElementById('cart-total').textContent = `¥${cart.reduce((n,b) => n + b.purchase_price*b.quantity,0).toLocaleString()}`;
 save.disabled = !cart.length || saving;
 persist();
}
list.addEventListener('click', e => { const button = e.target.closest('[data-remove]'); if (button && !saving) { cart.splice(Number(button.dataset.remove),1); render(); } });
list.addEventListener('change', e => { if (!e.target.dataset.key || saving) return; const {index,key} = e.target.dataset; const value = key === 'title' ? e.target.value.trim() : Number(e.target.value); if ((key === 'title' && !value) || (key !== 'title' && (!Number.isInteger(value) || value < (key === 'quantity' ? 1 : 0))) || (key === 'quantity' && count() - Number(cart[index].quantity) + value > 200)) { toast('タイトル・金額・冊数を確認してください（最大200冊）'); render(); return; } cart[index][key] = value; render(); });
[date,store,defaultPrice].forEach(el => el.addEventListener('change', persist));
defaultPrice.addEventListener('input', () => { price.value = defaultPrice.value; });
window.fetchBookData = async value => {
 const raw = String(value ?? isbn.value).trim();
 if (!raw) return;
 controller?.abort(); controller = new AbortController(); const version = ++lookupVersion;
 const snapshot = Object.fromEntries(['title','publisher','genre','c_code'].map(key => [key,form.elements[key].value]));
 status.textContent = '書誌情報を検索中…'; document.getElementById('isbn-search').disabled = true;
 try {
  const data = await apiRequest(`/scan/isbn/${encodeURIComponent(raw)}`, {signal:controller.signal});
  if (version !== lookupVersion) return;
  isbn.value = data.isbn;
  for (const key of ['title','publisher','genre','c_code']) if (data[key] && form.elements[key].value === snapshot[key]) form.elements[key].value = data[key];
  if (data.c_code) document.getElementById('c-code-input').dispatchEvent(new Event('input'));
  status.textContent = `${data.source}から取得しました。内容を確認して追加してください。`;
 } catch(error) { if(error.name !== 'AbortError' && version === lookupVersion) status.textContent = error.message; }
 finally { if (version === lookupVersion) document.getElementById('isbn-search').disabled = false; }
};
document.getElementById('isbn-search').addEventListener('click', () => fetchBookData());
isbn.addEventListener('keydown', e => { if(e.key === 'Enter') { e.preventDefault(); fetchBookData(); } });
isbn.addEventListener('input', () => { clearTimeout(timer); controller?.abort(); ++lookupVersion; document.getElementById('isbn-search').disabled = false; const normalized = isbn.value.replace(/[\s-]/g,''); if (/^(?:\d{9}[\dXx]|97[89]\d{10})$/.test(normalized)) timer = setTimeout(() => fetchBookData(), 500); });
form.addEventListener('submit', e => {
 e.preventDefault(); if (saving) return;
 if (!date.reportValidity() || !date.value) { toast('仕入れ日を指定してください'); return; }
 const item = Object.fromEntries(new FormData(form)); item.title = item.title.trim(); item.purchase_price = Number(item.purchase_price); item.quantity = Number(item.quantity); item.purchase_date = date.value; item.purchase_store = store.value.trim();
 if (!item.title || count() + item.quantity > 200) { toast('タイトルを入力してください。リストは最大200冊です。'); return; }
 cart.push(item); controller?.abort(); ++lookupVersion; clearTimeout(timer); form.reset(); price.value = defaultPrice.value; genreManuallyEdited = formatManuallyEdited = targetManuallyEdited = false;
 document.getElementById('isbn-search').disabled = false; status.textContent = '次の本のISBNを入力できます。'; render(); isbn.focus();
});
save.addEventListener('click', async () => {
 if (saving || !cart.length) return;
 saving = true; render(); list.querySelectorAll('input,button').forEach(el => el.disabled = true); save.textContent = '登録中…';
 try { const entries = cart.flatMap(({quantity,...book}) => Array.from({length:quantity}, () => book)); const result = await apiRequest('/api/books/batch', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({books:entries})}); cart = []; toast(`${result.count}冊を登録しました`); }
 catch(error) { toast(error.message); }
 finally { saving = false; save.textContent = 'まとめて登録'; render(); }
});
render();
})();
