(() => {
const button = document.querySelector('.scan-button');
if (!button) return;
const container = document.getElementById('scanner-container');
let scanner, starting = false, processing = false, library;
function loadLibrary() {
 if (window.Html5Qrcode) return Promise.resolve();
 if (!library) library = new Promise((resolve,reject) => { const script = document.createElement('script'); script.src = 'https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js'; script.onload = resolve; script.onerror = () => { library = null; script.remove(); reject(new Error('読取機能を読み込めませんでした。ISBNを入力してください。')); }; document.head.appendChild(script); });
 return library;
}
async function stop() {
 if (starting) return;
 try { if (scanner?.isScanning) await scanner.stop(); scanner?.clear(); } catch {} finally { scanner = null; container.hidden = true; container.style.display = 'none'; button.disabled = false; processing = false; }
}
button.addEventListener('click', async () => {
 if(starting || scanner) return;
 starting = true; button.disabled = true;
 try { await loadLibrary(); container.hidden = false; container.style.display = 'block'; scanner = new Html5Qrcode('reader');
 await scanner.start({facingMode:'environment'}, {fps:10,qrbox:{width:250,height:120}}, async text => {
  if(processing || !/^97[89]\d{10}$/.test(text)) return;
  processing = true; document.getElementById('isbn-input').value = text; starting = false; await stop(); await window.fetchBookData(text);
 });
 } catch(error) { starting = false; await stop(); toast(error.message || 'カメラを起動できません。カメラの許可とHTTPS接続を確認してください。'); }
 finally { starting = false; }
});
document.getElementById('close-scanner').addEventListener('click', stop);
})();
