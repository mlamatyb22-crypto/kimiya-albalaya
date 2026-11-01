// Shared helpers for the site (index.html) and the admin page (admin.html).
const KB = (() => {
  const ORD = ['الأولى', 'الثانية', 'الثالثة', 'الرابعة', 'الخامسة', 'السادسة', 'السابعة', 'الثامنة', 'التاسعة', 'العاشرة',
    'الحادية عشرة', 'الثانية عشرة', 'الثالثة عشرة', 'الرابعة عشرة', 'الخامسة عشرة', 'السادسة عشرة', 'السابعة عشرة',
    'الثامنة عشرة', 'التاسعة عشرة', 'العشرون'];
  const digits = n => String(n).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
  const ordinal = i => ORD[i] || ('رقم ' + digits(i + 1));
  const VIDEO_EXT = { 'video/mp4': 'mp4', 'video/webm': 'webm', 'video/quicktime': 'mov' };
  const videoExt = t => VIDEO_EXT[t] || 'mp4';

  // Rules are numbered by stage order: all of stage 1, then all of stage 2.
  function numberRules(rules) {
    const sorted = [...rules.filter(r => String(r.stage) === '1'), ...rules.filter(r => String(r.stage) !== '1')];
    return sorted.map((r, i) => Object.assign({}, r, { num: digits(i + 1), ord: ordinal(i), next: sorted[i + 1] && sorted[i + 1].id }));
  }

  // ---------- card image (1080 × 1350), same design as the original cards ----------
  const W = 1080, H = 1350;
  const C = { deep: '#2E1B10', mid: '#5A3318', warm: '#8A4B1F', gold: '#F0C978', gold2: '#EDBE6A', cream: '#FFF0D2', quote: '#FFF6E4', crocus: '#9B7BC8' };

  async function fontsReady() {
    await Promise.all([
      '700 62px "Aref Ruqaa"', '400 38px "Aref Ruqaa"', '400 44px "Amiri"', '700 44px "Amiri"', '400 24px "Reem Kufi"', '600 24px "Reem Kufi"'
    ].map(f => document.fonts.load(f, 'كيمياء')));
  }

  function squares(ctx, cx, cy, size) {
    for (const rot of [0, Math.PI / 4]) {
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot); ctx.rect(-size / 2, -size / 2, size, size); ctx.restore();
    }
  }

  function wrap(ctx, text, maxW) {
    const words = String(text).split(/\s+/).filter(Boolean), lines = [];
    let line = '';
    for (const w of words) {
      const t = line ? line + ' ' + w : w;
      if (ctx.measureText(t).width > maxW && line) { lines.push(line); line = w; } else line = t;
    }
    if (line) lines.push(line);
    return lines;
  }

  async function drawCard(rule) {
    await fontsReady();
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    const x = cv.getContext('2d');
    x.direction = 'rtl'; x.textAlign = 'center'; x.textBaseline = 'alphabetic';

    // background
    const g = x.createRadialGradient(W / 2, H * 0.42, 40, W / 2, H * 0.42, H * 0.8);
    g.addColorStop(0, C.warm); g.addColorStop(0.5, C.mid); g.addColorStop(1, C.deep);
    x.fillStyle = g; x.fillRect(0, 0, W, H);
    // pattern
    x.save(); x.globalAlpha = 0.10; x.strokeStyle = C.gold2; x.lineWidth = 1.4;
    for (let py = 0; py < H; py += 90) for (let px = 0; px < W; px += 90) {
      x.beginPath(); squares(x, px + 45, py + 45, 46); x.stroke();
      x.beginPath(); x.arc(px + 45, py + 45, 8, 0, 7); x.stroke();
    }
    x.restore();
    // frame
    x.strokeStyle = 'rgba(240,201,120,.8)'; x.lineWidth = 2.5; x.strokeRect(40, 40, W - 80, H - 80);
    x.strokeStyle = 'rgba(240,201,120,.45)'; x.lineWidth = 1; x.strokeRect(53, 53, W - 106, H - 106);
    x.strokeStyle = C.gold; x.lineWidth = 1.6;
    for (const [cx, cy] of [[80, 80], [W - 80, 80], [80, H - 80], [W - 80, H - 80]]) {
      x.beginPath(); x.moveTo(cx, cy - 22); x.lineTo(cx + 22, cy); x.lineTo(cx, cy + 22); x.lineTo(cx - 22, cy); x.closePath(); x.stroke();
      x.beginPath(); x.moveTo(cx, cy - 11); x.lineTo(cx + 11, cy); x.lineTo(cx, cy + 11); x.lineTo(cx - 11, cy); x.closePath(); x.stroke();
    }

    let y = 150;
    x.fillStyle = C.gold; x.font = '400 38px "Aref Ruqaa"'; x.fillText('كيمياء البلايا والمحن', W / 2, y);
    y += 44;
    x.fillStyle = 'rgba(240,201,120,.85)'; x.font = '400 24px "Reem Kufi"';
    x.fillText(rule.stageLabel || '', W / 2, y);

    // number badge: solid gold star with a large dark numeral
    const by = y + 92;
    x.beginPath(); squares(x, W / 2, by, 96); x.fillStyle = '#E0A848'; x.fill();
    x.strokeStyle = '#9A6418'; x.lineWidth = 2.5; x.stroke();
    x.beginPath(); squares(x, W / 2, by, 76); x.fillStyle = '#F3C772'; x.fill();
    x.fillStyle = C.deep; x.font = '700 58px "Amiri"'; x.textBaseline = 'middle';
    x.fillText(rule.num, W / 2, by + 4); x.textBaseline = 'alphabetic';
    y = by + 96;

    // title
    x.fillStyle = C.cream; x.font = '700 60px "Aref Ruqaa"';
    for (const l of wrap(x, rule.name, 820)) { y += 78; x.fillText(l, W / 2, y); }
    x.fillStyle = C.gold; x.font = '700 50px "Amiri"';
    for (const l of wrap(x, '«' + rule.motto + '»', 820)) { y += 72; x.fillText(l, W / 2, y); }
    // ornament
    y += 46;
    x.strokeStyle = C.gold; x.lineWidth = 2; x.globalAlpha = .75;
    x.beginPath(); x.moveTo(W / 2 - 180, y); x.lineTo(W / 2 - 18, y); x.moveTo(W / 2 + 18, y); x.lineTo(W / 2 + 180, y); x.stroke();
    x.globalAlpha = 1; x.fillStyle = C.crocus;
    x.beginPath(); x.moveTo(W / 2, y - 9); x.lineTo(W / 2 + 9, y); x.lineTo(W / 2, y + 9); x.lineTo(W / 2 - 9, y); x.closePath(); x.fill();

    // body, shrunk until it fits above the source pill
    const top = y + 40, bottom = rule.src ? H - 175 : H - 110, maxW = 840;
    const [o, c] = rule.quran ? ['﴿', '﴾'] : ['«', '»'];
    let size = 58, layout;
    for (; size >= 24; size -= 1) {
      const ctxSize = Math.min(30, Math.round(size * .7));
      x.font = `400 ${ctxSize}px "Amiri"`; const ctxLines = rule.ctx ? wrap(x, rule.ctx, maxW) : [];
      x.font = `400 ${size}px "Amiri"`; const qLines = wrap(x, o + rule.text + c, maxW);
      const h = 46 + ctxLines.length * ctxSize * 1.85 + (ctxLines.length ? 14 : 0) + qLines.length * size * 1.9;
      layout = { ctxSize, ctxLines, qLines, h };
      if (top + h <= bottom) break;
    }
    let by2 = top + Math.max(0, (bottom - top - layout.h) / 2);
    x.fillStyle = C.gold2; x.font = '400 28px "Reem Kufi"'; by2 += 30; x.fillText(rule.narr || '', W / 2, by2); by2 += 16;
    x.fillStyle = 'rgba(255,240,210,.82)'; x.font = `400 ${layout.ctxSize}px "Amiri"`;
    for (const l of layout.ctxLines) { by2 += layout.ctxSize * 1.85; x.fillText(l, W / 2, by2); }
    if (layout.ctxLines.length) by2 += 14;
    x.fillStyle = C.quote; x.font = `400 ${size}px "Amiri"`;
    for (const l of layout.qLines) { by2 += size * 1.9; x.fillText(l, W / 2, by2 - size * .45); }

    // source pill
    if (rule.src) {
      x.font = '400 25px "Reem Kufi"';
      const tw = x.measureText(rule.src).width + 64, ph = 50, py = H - 140;
      x.strokeStyle = 'rgba(240,201,120,.6)'; x.lineWidth = 1.5;
      x.beginPath(); x.roundRect(W / 2 - tw / 2, py - ph / 2, tw, ph, 25); x.stroke();
      x.fillStyle = C.gold2; x.textBaseline = 'middle'; x.fillText(rule.src, W / 2, py + 2); x.textBaseline = 'alphabetic';
    }
    return new Promise(res => cv.toBlob(res, 'image/jpeg', 0.9));
  }

  return { digits, ordinal, numberRules, videoExt, drawCard };
})();
