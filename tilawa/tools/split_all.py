#!/usr/bin/env python3
"""يقطّع مجلد سور كاملة (001_Al_Fatiha.mp3 ... 114_An_Nas.mp3) إلى آيات باستخدام split_ayahs.py.

    python3 split_all.py ~/Movies/ruqayah_audio --out ~/tilawa-clips/ruqayah
    python3 split_all.py ~/Movies/ruqayah_audio --only 112 113 114     # جرّب على سور قصيرة أولًا
    python3 split_all.py ~/Movies/ruqayah_audio --check-only           # تقرير دون قص

لكل سورة يجرّب وجود 0 أو 1 أو 2 مقطع تمهيدي (استعاذة/بسملة) ويختار الأعلى ثقة.
السور التي ثقتها منخفضة لا تُقص، وتظهر في report.csv لتراجعها يدويًا.
"""
import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPLIT = HERE / 'split_ayahs.py'
MIN_MARGIN = 1.25


def trial(src, surah, lead, out, check, noise, min_silence):
    cmd = [sys.executable, '-I', str(SPLIT), str(src), '--surah', str(surah), '--lead', str(lead),
           '--out', str(out), '--noise', str(noise), '--min-silence', str(min_silence)]
    if check:
        cmd.append('--check-only')
    r = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r'هامش الثقة: ([\d.]+)', r.stdout)
    return (float(m.group(1)) if m else 0.0), r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--out', default='clips')
    ap.add_argument('--only', type=int, nargs='*', help='أرقام سور محددة')
    ap.add_argument('--check-only', action='store_true')
    ap.add_argument('--noise', type=float, default=-35)
    ap.add_argument('--min-silence', type=float, default=0.25)
    a = ap.parse_args()

    folder = Path(a.folder).expanduser()
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in ('.mp3', '.m4a', '.wav', '.ogg') and re.match(r'\d{1,3}', p.name))
    if not files:
        sys.exit('لم أجد ملفات صوتية مرقّمة في المجلد')
    out = Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in files:
        surah = int(re.match(r'(\d{1,3})', p.name).group(1))
        if not 1 <= surah <= 114 or (a.only and surah not in a.only):
            continue
        # نفضّل أقل عدد مقاطع تمهيدية يعطي ثقة مقبولة؛ فعند تساوي عدد الوقفات مع المطلوب
        # تظهر ثقة عالية دائمًا، ولا تدل على صحة الفرضية.
        best = None
        for lead in (0, 1, 2):
            margin, _ = trial(p, surah, lead, out, True, a.noise, a.min_silence)
            if margin >= MIN_MARGIN:
                best = (margin, lead)
                break
            if best is None or margin > best[0]:
                best = (margin, lead)
        margin, lead = best
        status = 'متخطّى (ثقة منخفضة)'
        if margin >= MIN_MARGIN:
            if a.check_only:
                status = 'جيد (فحص فقط)'
            else:
                _, r = trial(p, surah, lead, out, False, a.noise, a.min_silence)
                status = 'تم القص' if r.returncode == 0 else 'فشل القص'
        print(f'{surah:03d} {p.name}: lead={lead} margin={margin:.2f} -> {status}')
        rows.append([surah, p.name, lead, f'{margin:.2f}', status])
    with open(out / 'report.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['surah', 'file', 'lead_clips', 'margin', 'status'])
        w.writerows(rows)
    bad = [r for r in rows if r[4] not in ('تم القص', 'جيد (فحص فقط)')]
    print(f'\nالمجموع {len(rows)} سورة · تحتاج مراجعة يدوية: {len(bad)} · التقرير: {out / "report.csv"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
