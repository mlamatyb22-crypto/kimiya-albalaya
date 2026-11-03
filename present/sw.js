/* يخزّن الموقع كله في المتصفح ليعمل بدون إنترنت. غيّر رقم VERSION عند أي تعديل كبير. */
const VERSION='v1';
const CACHE='present-'+VERSION;
const FILES=['./','index.html','lesson-3.html','lesson-4.html','player.html','engine.js','engine.css','decks/index.js','decks/research-tools.js','manifest.webmanifest','icon.svg','icon-192.png','icon-512.png','lib/peerjs.min.js','lib/qrcode.min.js','fonts/fonts.css']
 .concat(['arabic','latin'].flatMap(s=>[400,500,700,800].map(w=>`fonts/tajawal-${s}-${w}-normal.woff2`)));
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith('present-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
 const r=e.request;
 if(r.method!=='GET'||new URL(r.url).origin!==location.origin)return;
 e.respondWith(caches.match(r,{ignoreSearch:true}).then(hit=>{
  const net=fetch(r).then(res=>{if(res.ok)caches.open(CACHE).then(c=>c.put(r,res.clone()));return res}).catch(()=>hit);
  return hit||net;
 }));
});
