/* محرك العروض: يقرأ ملف عرض من decks/ ويعرضه. العرض الجديد = ملف جديد فقط. */
(function(){
const $=(s,r=document)=>r.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const S=(h,cls='')=>`<div class="step ${cls}">${h}</div>`;
const head=s=>`${s.kicker?`<div class="kicker">${esc(s.kicker)}</div>`:''}${s.title?`<h2>${esc(s.title)}</h2>`:''}${s.intro?`<div class="sub">${esc(s.intro)}</div>`:''}`;

/* أنواع الشرائح. أضف نوعًا جديدًا هنا ليصبح متاحًا لكل العروض. */
const T={
 title:s=>`<div class="kicker">${esc(s.kicker)}</div><h1>${esc(s.title)}</h1><div class="sub">${esc(s.sub||'')}</div><div class="meta">${esc(s.meta||'')}</div>`,
 cards:s=>head(s)+`<div class="row">${s.items.map(c=>S(`<div class="card ${c.cls||''}">${c.icon?`<div class="ic">${c.icon}</div>`:''}<h3>${esc(c.title)}</h3><p>${esc(c.text||'')}</p>${c.ex?`<div class="ex">${esc(c.ex)}</div>`:''}</div>`)).join('')}</div>`+(s.chips?`<div class="chips">${s.chips.map(c=>S(`<div class="chip">${esc(c)}</div>`)).join('')}</div>`:''),
 list:s=>head(s)+`<div class="list">${s.items.map(i=>S(`<div class="li"><b>${esc(i[0])}</b><span>${esc(i[1])}</span></div>`)).join('')}</div>`,
 steps:s=>head(s)+`<div class="steps" style="grid-template-columns:repeat(${s.items.length<=5?s.items.length:4},1fr)">${s.items.map((i,n)=>S(`<div class="stp"><div class="n">${n+1}</div><h3>${esc(i[0])}</h3><p>${esc(i[1]||'')}</p></div>`)).join('')}</div>`,
 compare:s=>head(s)+`<div class="row">${s.items.map(c=>S(`<div class="card ${c.cls||''}"><span class="tag">${esc(c.tag||'')}</span><h3>${esc(c.title)}</h3><p>${esc(c.text)}</p>${c.ex?`<div class="ex">${esc(c.ex)}</div>`:''}</div>`)).join('')}${s.note?'':''}</div>`+(s.note?S(`<div class="sub">${esc(s.note)}</div>`):''),
 q:(s,ctx)=>`<div class="qtop"><div class="kicker">${esc(s.kicker||'تحدي الفصل')} · سؤال ${ctx.qn} من ${ctx.qt}</div><div class="timer" data-timer>${s.time||12}</div></div><h2>${esc(s.q)}</h2><div class="opts">${s.options.map((o,i)=>`<div class="opt ${i===s.answer?'ans':''}"><i>${'أبجد'[i]}</i>${esc(o)}</div>`).join('')}</div>`+S(`<div class="answer">✓ الإجابة: ${esc(s.options[s.answer])}<br>${esc(s.explain||'')}</div>`),
 tf:s=>head(s)+`<div class="tf">${s.items.map(i=>S(`<div class="tfi"><span>${esc(i[0])}</span><div class="r ${i[1]?'t':'f'}">${i[1]?'صح':'خطأ'}${i[2]?`<small>${esc(i[2])}</small>`:''}</div></div>`)).join('')}</div>`,
 score:s=>`<div class="kicker">${esc(s.kicker||'تحدي الفصل')}</div><h2>${esc(s.title||'النتيجة 🏆')}</h2><div class="score"><div class="team"><b>الفريق الأول</b><span data-score="0">0</span></div><div class="team"><b>الفريق الثاني</b><span data-score="1">0</span></div></div>`,
 end:s=>`<div class="kicker"></div><h1 style="text-align:center">${esc(s.title)}</h1><div class="sub" style="text-align:center">${esc(s.sub||'')}</div>`
};

const params=new URLSearchParams(location.search);
const name=(params.get('deck')||'').replace(/[^\w-]/g,'');
const sc=document.createElement('script');
sc.src='decks/'+name+'.js';
sc.onerror=()=>document.body.innerHTML='<p style="color:#fff;padding:40px">لم أجد العرض: '+esc(name)+'</p>';
sc.onload=()=>start(window.DECK);
document.head.appendChild(sc);

function start(D){
 document.title=D.title;
 const stage=$('#stage');
 const qt=D.slides.filter(s=>s.type==='q').length;let qn=0;
 stage.innerHTML=D.slides.map((s,i)=>{
  if(s.type==='q')qn++;
  return `<section class="slide t-${s.type}" data-i="${i}">${T[s.type](s,{qn,qt})}<div class="num">${D.footer?esc(D.footer)+' · ':''}${i+1} / ${D.slides.length}</div></section>`}).join('');
 const slides=[...stage.children];
 const score=[0,0];
 let cur=0,tm=null;
 const fit=()=>{const k=Math.min(innerWidth/1920,innerHeight/1080);stage.style.transform=`translate(-50%,-50%) scale(${k})`};
 addEventListener('resize',fit);fit();

 function stopTimer(){clearInterval(tm);tm=null}
 function show(i,all){
  stopTimer();cur=Math.max(0,Math.min(slides.length-1,i));
  slides.forEach((s,k)=>s.classList.toggle('on',k===cur));
  const el=slides[cur];
  el.querySelectorAll('.step').forEach(x=>x.classList.toggle('show',!!all));
  el.querySelectorAll('.opt.ans').forEach(x=>x.classList.toggle('right',!!all));
  const t=el.querySelector('[data-timer]');
  if(t){let n=D.slides[cur].time||12;t.textContent=n;t.classList.remove('low');
   if(!all)tm=setInterval(()=>{n--;t.textContent=Math.max(n,0);t.classList.toggle('low',n<=3);if(n<=0)stopTimer()},1000)}
  $('#bar').style.width=(cur+1)/slides.length*100+'%';
  history.replaceState(null,'','#'+(cur+1));
  const nt=$('#notes textarea');nt.value=localStorage.getItem(key())??(D.slides[cur].notes||'');
  renderScore();
 }
 const key=()=>`notes:${name}:${cur}`;
 function renderScore(){document.querySelectorAll('[data-score]').forEach(e=>e.textContent=score[e.dataset.score])}
 function next(){
  const el=slides[cur],hid=el.querySelector('.step:not(.show)');
  if(hid){hid.classList.add('show');if(el.querySelector('.opt.ans')){el.querySelector('.opt.ans').classList.add('right');stopTimer()}return}
  const a=el.querySelector('.opt.ans:not(.right)');
  if(a){a.classList.add('right');stopTimer();return}
  if(cur<slides.length-1)show(cur+1,false);
 }
 function prev(){
  const sh=[...slides[cur].querySelectorAll('.step.show')];
  if(sh.length){sh.pop().classList.remove('show');return}
  if(cur>0)show(cur-1,true);
 }
 document.addEventListener('keydown',e=>{
  if(e.target.tagName==='TEXTAREA')return;
  const k=e.key;
  if([' ','ArrowLeft','PageDown','Enter'].includes(k)){e.preventDefault();next()}
  else if(['ArrowRight','PageUp','Backspace'].includes(k)){e.preventDefault();prev()}
  else if(k==='Home')show(0,false);
  else if(k==='End')show(slides.length-1,true);
  else if(k==='1'||k==='2'){score[+k-1]++;renderScore()}
  else if(k==='n'||k==='N'||k==='ن')$('#notes').classList.toggle('on');
  else if(k==='f'||k==='F'||k==='ب')fs();
  else if(k==='?'||k==='h')$('#help').classList.toggle('on');
 });
 stage.addEventListener('click',next);
 let sx=null;
 addEventListener('touchstart',e=>sx=e.touches[0].clientX,{passive:true});
 addEventListener('touchend',e=>{if(sx==null)return;const d=e.changedTouches[0].clientX-sx;sx=null;if(Math.abs(d)>60){d<0?prev():next()}});
 const fs=()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();
 $('#bfs').onclick=fs;
 $('#bnotes').onclick=()=>$('#notes').classList.toggle('on');
 $('#bhelp').onclick=()=>$('#help').classList.toggle('on');
 $('#help').onclick=()=>$('#help').classList.remove('on');
 $('#notes textarea').addEventListener('input',e=>localStorage.setItem(key(),e.target.value));
 show((parseInt(location.hash.slice(1))||1)-1,false);
}
})();
