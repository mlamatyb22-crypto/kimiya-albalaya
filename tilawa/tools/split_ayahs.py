#!/usr/bin/env python3
"""يقطّع تسجيل سورة كاملة إلى ملف لكل آية، عند أطول فترات الصمت.

الفكرة: بين الآيات في التلاوة المرتلة يكون الوقف أطول من الوقفات داخل الآية.
إذا كان عدد الآيات N، نأخذ أطول (N-1) فترة صمت ونقطع في منتصفها، فلا يُقطع صوت كلمة.
ثم نحسب هامش ثقة: الفرق بين أقصر وقفة اخترناها وأطول وقفة تركناها. هامش صغير يعني أن
القطع قد يكون خاطئًا، فيُطلب منك الاستماع لتلك المقاطع قبل اعتمادها.

الاستخدام (يحتاج ffmpeg على جهازك):
    python3 split_ayahs.py 067.mp3 --surah 67 --out ~/tilawa-clips/minshawi
    python3 split_ayahs.py 002.mp3 --surah 2 --lead 1      # تبدأ الملف بالبسملة منفصلة (تُحفظ 000.mp3)
    python3 split_ayahs.py f.mp3 --ayahs 29 --check-only   # فحص دون قص

هذا التقطيع آلي ولا يعرف الكلمات؛ لا تعتمد النتيجة إلا بعد فحص تقرير الثقة وسماع عينات.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# عدد آيات كل سورة (مجموعها ٦٢٣٦). تُراجَع النتيجة دائمًا بعدد المقاطع المكتشفة.
AYAHS = [7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111, 110, 98, 135, 112, 78,
         118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38,
         29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20,
         56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
         11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6]
assert len(AYAHS) == 114 and sum(AYAHS) == 6236


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def duration(path):
    r = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)])
    return float(r.stdout.strip())


def silences(path, noise_db, min_len):
    r = run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-af',
             f'silencedetect=noise={noise_db}dB:d={min_len}', '-f', 'null', '-'])
    starts = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', r.stderr)]
    ends = [(float(a), float(b)) for a, b in re.findall(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)', r.stderr)]
    out = []
    for s, (e, d) in zip(starts, ends):
        out.append((max(0.0, s), e, d))
    return out


def choose(sil, total, need):
    """نختار أطول `need` وقفة داخلية (نتجاهل الصمت في أول الملف وآخره)."""
    inner = [x for x in sil if x[0] > 0.3 and x[1] < total - 0.3]
    ranked = sorted(inner, key=lambda x: x[2], reverse=True)
    if len(ranked) < need:
        return None, 0.0, ranked
    picked = sorted(ranked[:need], key=lambda x: x[0])
    margin = (ranked[need - 1][2] / ranked[need][2]) if len(ranked) > need else 99.0
    return picked, margin, ranked


def main():
    ap = argparse.ArgumentParser(description='تقطيع سورة إلى آيات عند أطول الوقفات')
    ap.add_argument('input')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--surah', type=int, help='رقم السورة (١–١١٤)')
    g.add_argument('--ayahs', type=int, help='عدد الآيات يدويًا')
    ap.add_argument('--lead', type=int, default=0, help='عدد المقاطع التمهيدية قبل الآية الأولى (استعاذة/بسملة) تُحفظ باسم 000a,000b')
    ap.add_argument('--out', default='clips')
    ap.add_argument('--noise', type=float, default=-35, help='عتبة الصمت بالديسيبل')
    ap.add_argument('--min-silence', type=float, default=0.25)
    ap.add_argument('--min-margin', type=float, default=1.25, help='أقل هامش ثقة مقبول')
    ap.add_argument('--check-only', action='store_true')
    ap.add_argument('--force', action='store_true', help='اقطع حتى مع ثقة منخفضة')
    a = ap.parse_args()

    if a.surah:
        if not 1 <= a.surah <= 114:
            sys.exit('رقم السورة بين ١ و١١٤')
        n, surah = AYAHS[a.surah - 1], a.surah
    else:
        n, surah = a.ayahs, 0
    src = Path(a.input).expanduser()
    if not src.exists() or not run(['ffmpeg', '-version']).returncode == 0:
        sys.exit('الملف غير موجود أو ffmpeg غير مثبت (brew install ffmpeg)')

    total = duration(src)
    need = n + a.lead - 1
    sil = silences(src, a.noise, a.min_silence)
    picked, margin, ranked = choose(sil, total, need)
    print(f'الملف: {src.name} · المدة {total:.1f}ث · الآيات {n}' + (f' + {a.lead} تمهيدي' if a.lead else ''))
    print(f'وقفات مكتشفة: {len(sil)} · المطلوب للقطع: {need}')
    if picked is None:
        print(f'عدد الوقفات ({len(ranked)}) أقل من المطلوب. جرّب --noise -30 أو --min-silence 0.15', file=sys.stderr)
        return 1

    cuts = [(s + e) / 2 for s, e, _ in picked]
    bounds = [0.0] + cuts + [total]
    segs = list(zip(bounds[:-1], bounds[1:]))
    durs = [b - a_ for a_, b in segs]
    med = sorted(durs)[len(durs) // 2]
    odd = [i for i, d in enumerate(durs) if d < med * 0.25 or d > med * 4]
    ok = margin >= a.min_margin
    print(f'هامش الثقة: {margin:.2f} ({"جيد" if ok else "منخفض: قد تكون بعض القصّات خاطئة"})')
    if odd:
        print('مقاطع بطول غير معتاد (راجعها بالسماع): ' + ', '.join(str(i + 1) for i in odd))
    if a.check_only:
        return 0 if ok else 2
    if not ok and not a.force:
        print('توقفت دون قص. راجع الإعدادات أو استخدم --force وافحص الناتج يدويًا.', file=sys.stderr)
        return 2

    out = Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    names = [f'000{chr(97 + i)}' for i in range(a.lead)] + [f'{surah:03d}{i + 1:03d}' if surah else f'{i + 1:03d}' for i in range(n)]
    manifest = []
    for name, (s, e) in zip(names, segs):
        dest = out / f'{name}.mp3'
        r = run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(src), '-ss', f'{s:.3f}', '-to', f'{e:.3f}',
                 '-vn', '-c:a', 'libmp3lame', '-q:a', '4', str(dest)])
        if r.returncode:
            print(f'فشل قص {name}: {r.stderr.strip()}', file=sys.stderr)
            return 1
        manifest.append({'file': dest.name, 'start': round(s, 3), 'end': round(e, 3), 'seconds': round(e - s, 2)})
    (out / 'manifest.json').write_text(json.dumps(
        {'source': src.name, 'surah': surah, 'ayahs': n, 'margin': round(margin, 2), 'clips': manifest},
        ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'تم: {len(manifest)} مقطعًا في {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
