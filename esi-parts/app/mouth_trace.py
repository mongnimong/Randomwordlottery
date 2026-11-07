import sys
import numpy as np
import potrace
from PIL import Image, ImageDraw, ImageFilter

# 손그림 입 6종 → 레이어 SVG (외곽 / 입안 / 혀 / 혀홈 / 이빨). 이빨 모양은 그대로, 테두리만 매끈하게.
src, outdir = sys.argv[1], sys.argv[2]
RING = float(sys.argv[3]) if len(sys.argv) > 3 else 22.0       # 바깥 먹색 테두리 굵기(px)
INK = '#3A3542'
im = np.asarray(Image.open(src).convert('RGB')).astype(int)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
H, W = r.shape

ink = np.abs(im - np.array([58, 53, 66])).sum(axis=2) < 120
pink = (r > 170) & (g < 150) & (b > 100) & (r - g > 60)
white = im.min(axis=2) > 225


def img(m):
    return Image.fromarray((m * 255).astype(np.uint8))


def smooth(m, s=3):
    return np.asarray(img(m).filter(ImageFilter.GaussianBlur(s))) > 127


def fill_holes(m):
    ff = img(~m).copy()
    ImageDraw.floodfill(ff, (0, 0), 128)
    return np.asarray(ff) != 128


def erode(m, rad):
    # 가우시안으로 둥글게 깎기: 경계에서 rad 만큼 안쪽만 남김 (σ=rad/2, 문턱 97.7%)
    return np.asarray(img(m).filter(ImageFilter.GaussianBlur(rad / 2))) > 249


region = fill_holes(ink | pink)
# 입 하나하나 나누기: 가로 3칸 × 세로 2줄
cols = np.where(region.any(axis=0))[0]
rows = np.where(region.any(axis=1))[0]


def split(idx, n):
    gaps = np.where(np.diff(idx) > 40)[0]
    edges = [idx[0]] + [v for gp in gaps for v in (idx[gp], idx[gp + 1])] + [idx[-1]]
    return [(edges[2 * i], edges[2 * i + 1]) for i in range(len(edges) // 2)]


rspans = split(rows, 2)
names = [('tongue_big', '메롱 큰혀'), ('tongue_v', '짓궂은 V'), ('tongue_bunny', '토끼이빨'),
         ('grin', '활짝 미소'), ('shark', '상어 이빨'), ('gappy', '이 빠진 입')]
k = 0
for (y0, y1) in rspans:
    band = region[y0:y1 + 1]
    cspans = split(np.where(band.any(axis=0))[0], 3)
    for (x0, x1) in cspans:
        pad = 30
        sl = (slice(max(0, y0 - pad), min(H, y1 + pad + 1)), slice(max(0, x0 - pad), min(W, x1 + pad + 1)))
        reg = smooth(region[sl], 3)
        tg_raw = pink[sl] & region[sl]
        tg = smooth(tg_raw, 2)
        tg_full = smooth(fill_holes(smooth(tg_raw, 6) | tg_raw), 2)      # 홈까지 메운 혀
        groove = tg_full & ~tg
        th = smooth(white[sl] & region[sl], 2)
        inside = erode(reg, RING)
        hh, ww = reg.shape

        def trace(m):
            if not m.any():
                return ''
            pl = potrace.Bitmap(~m).trace(turdsize=30, alphamax=1.0, opticurve=True, opttolerance=0.3)
            f = lambda p: f'{p.x:.1f} {p.y:.1f}'
            d = []
            for c in pl:
                d.append('M' + f(c.start_point))
                for s in c.segments:
                    d.append(('L' + f(s.c) + ' L' + f(s.end_point)) if s.is_corner else ('C' + f(s.c1) + ' ' + f(s.c2) + ' ' + f(s.end_point)))
                d.append('Z')
            return ' '.join(d)

        key, name = names[k]
        layers = [('mouth-line', INK, trace(reg)), ('mouth-inside', INK, trace(inside)),
                  ('mouth-tongue', '#E0668A', trace(tg_full)), ('mouth-groove', INK, trace(groove)),
                  ('mouth-teeth', '#FFFFFF', trace(th))]
        body = ''.join(f'    <path id="{i}" fill="{c}" fill-rule="evenodd" d="{d}"/>\n' for i, c, d in layers if d)
        open(f'{outdir}/mouth2_{key}.svg', 'w').write(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ww} {hh}" width="{ww}" height="{hh}">\n'
            f'  <!-- {name} -->\n  <g id="mouth">\n{body}  </g>\n</svg>\n')
        print(key, name, ww, hh, 'tongue' if tg.any() else 'no-tongue')
        k += 1
