(() => {
const yen = n => `¥${Number(n || 0).toLocaleString('ja-JP')}`;
let period = '6m', controller, version = 0;
const status = document.getElementById('analytics-status');
function metric(label, value, note, featured = false) { return `<div class="analytics-card ${featured?'featured':''}"><div class="analytics-label">${label}</div><div class="analytics-value">${value}</div><p>${note}</p></div>`; }
function render(data) {
 const s = data.summary;
 document.getElementById('summary-cards').innerHTML = metric('実現利益',yen(s.profit),`売上に対する利益率 ${s.profit_rate}%`,true) + metric('総売上',yen(s.sales),`${s.sold_count}冊を売却`) + metric('在庫の仕入れ総額',yen(s.inventory_value),`${s.inventory_count}冊を保有`) + metric('資金収支',yen(s.cash_flow),'全仕入れ・経費を差し引いた収支') + metric('総仕入れ',yen(s.purchase),'売却分・在庫分を含む') + metric('手数料・送料',yen(s.fees+s.shipping),`手数料 ${yen(s.fees)} / 送料 ${yen(s.shipping)}`) + metric('経費',yen(s.costs),'クーポンによる値引きを反映') + metric('平均販売単価',yen(s.average_sale),'セット販売は1取引として集計');
 document.getElementById('summary-cards').setAttribute('aria-busy','false');
 document.getElementById('inventory-insights').innerHTML = `<div class="inventory-stat"><div><span class="muted">売却率</span><strong>${s.sell_through}%</strong></div><span>${s.sold_count}冊売却 / ${s.sold_count+s.inventory_count}冊仕入れ</span></div><div class="progress-track"><div style="width:${s.sell_through}%"></div></div><div class="aging-notice"><strong>90日を超えた在庫 ${s.aging_count}冊</strong><a href="/inventory?aging=90">在庫を確認 →</a></div>`;
 const r = data.rotation;
 document.getElementById('rotation-stats').innerHTML = r.count ? ['平均','中央値','最短','最長'].map((label,i) => `<div><span class="muted">${label === "中央値" ? "回転日数の中央値" : label+"回転日数"}</span><strong>${[r.average,r.median,r.min,r.max][i]}<small>日</small></strong></div>`).join('') : '<p class="muted">売却データが増えると回転日数を表示します。</p>';
 document.getElementById('profit-ranking').innerHTML = data.ranking.length ? data.ranking.map((item,i) => `<div class="ranking-row"><span class="rank-number">${i+1}</span><div><strong>${escapeHTML(item.title)}</strong><span class="muted">仕入れ値に対する利益率 ${item.rate === null ? '—' : item.rate+'%'}</span></div><b class="${item.profit < 0 ? 'profit-minus':'profit-plus'}">${yen(item.profit)}</b></div>`).join('') : '<div class="empty-state compact">販売を登録するとランキングが表示されます。</div>';
 for(const [id,rows] of [['genre-breakdown',data.genres],['store-breakdown',data.stores]]) document.getElementById(id).innerHTML = rows.length ? rows.map(item => `<div class="breakdown-row"><div><strong>${escapeHTML(item.label)}</strong><span class="muted">${item.count}冊売却</span></div><b class="${item.profit < 0 ? 'profit-minus':'profit-plus'}">${yen(item.profit)}</b></div>`).join('') : '<div class="empty-state compact">販売データがまだありません。</div>';
 renderMonthly(data.monthly);
}
function renderMonthly(data) {
 const series = [data.sales,data.profit,data.purchase], colors = ['#195d50','#dc9351','#90a7a0'];
 const values = series.flat(), max = Math.max(1,...values), min = Math.min(0,...values);
 const width = Math.max(620, data.labels.length*48), height = 250, left = 72, right = width-24, top = 18, bottom = 205;
 const x = i => left + i*(right-left)/Math.max(1,data.labels.length-1), y = value => bottom - (value-min)/(max-min)*(bottom-top);
 let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="月別の売上、実現利益、仕入れ額。下の月別明細で数値を確認できます。">`;
 for(let i=0;i<=4;i++) { const v = min+(max-min)*i/4; svg += `<line x1="${left}" x2="${right}" y1="${y(v)}" y2="${y(v)}" stroke="#e5ebe7"/><text x="${left-12}" y="${y(v)+4}" text-anchor="end" fill="#7a8780" font-size="11">${Math.round(v).toLocaleString()}</text>`; }
 svg += `<line x1="${left}" x2="${right}" y1="${y(0)}" y2="${y(0)}" stroke="#b8c6be"/>`;
 series.forEach((values,j) => { svg += `<polyline points="${values.map((v,i) => `${x(i)},${y(v)}`).join(' ')}" fill="none" stroke="${colors[j]}" stroke-width="3" stroke-linejoin="round"/>`; values.forEach((v,i) => { svg += `<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="${colors[j]}"><title>${data.labels[i]} ${['売上','実現利益','仕入れ'][j]} ${yen(v)}</title></circle>`; }); });
 data.labels.forEach((label,i) => { if(i%Math.max(1,Math.ceil(data.labels.length/12))===0 || i===data.labels.length-1) svg += `<text x="${x(i)}" y="232" text-anchor="middle" fill="#7a8780" font-size="11">${label}</text>`; });
 document.getElementById('monthly-chart').innerHTML = svg+'</svg>';
 document.getElementById('monthly-table').innerHTML = `<table><thead><tr><th>月</th><th>売上</th><th>実現利益</th><th>仕入れ</th><th>経費</th><th>資金収支</th></tr></thead><tbody>${data.labels.map((label,i) => `<tr><td>${label}</td>${['sales','profit','purchase','costs','cash_flow'].map(k => `<td>${yen(data[k][i])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}
async function load() {
 controller?.abort(); controller = new AbortController(); const requestVersion = ++version; status.textContent = '集計しています…';
 try { const data = await apiRequest(`/api/analytics/dashboard?period=${period}`, {signal:controller.signal}); if(requestVersion !== version) return; render(data); status.textContent = `更新 ${new Date().toLocaleTimeString('ja-JP')} · 上の指標は全期間、グラフは選択期間`; }
 catch(error) { if(error.name !== 'AbortError') { status.textContent = `${error.message} 「更新」で再試行できます。`; document.getElementById('summary-cards').setAttribute('aria-busy','false'); } }
}
document.querySelectorAll('.period-btn').forEach(button => button.addEventListener('click', () => { period = button.dataset.period; document.querySelectorAll('.period-btn').forEach(b => b.classList.toggle('active', b === button)); load(); }));
document.getElementById('refresh-analytics').addEventListener('click', load);
load();
})();
