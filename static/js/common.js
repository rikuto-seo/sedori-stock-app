window.escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
window.localDate = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
window.apiRequest = async (url, options = {}) => { const response = await fetch(url, options); let data; try { data = await response.json(); } catch { throw new Error('通信に失敗しました。もう一度お試しください。'); } if (!response.ok) throw new Error(data.message || '処理に失敗しました'); return data; };
window.toast = message => { const el = document.getElementById('toast'); el.textContent = message; el.classList.add('show'); clearTimeout(window.toastTimer); window.toastTimer = setTimeout(() => el.classList.remove('show'), 4500); };
document.addEventListener('keydown', e => { if (e.key === 'Escape') document.querySelectorAll('.modal').forEach(m => m.style.display = 'none'); });

window.addEventListener('unhandledrejection', e => { e.preventDefault(); toast(e.reason?.message || '通信に失敗しました'); });
