import sys
import numpy as np
import potrace
from PIL import Image, ImageDraw, ImageFilter

# 손그림 입 6종을 바탕으로 '그래픽' 버전을 다시 그린다.
# 구성(이빨 개수·자리·혀)은 그림 그대로, 모양은 좌우대칭·같은 크기·매끈한 선으로 정돈.
src, outdir = sys.argv[1], sys.argv[2]
RING = 22.0
INK = '#3A3542'
im = np.asarray(Image.open(src).convert('RGB')).astype(int)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
H, W = r.shape
ink = np.abs(im - np.array([58, 53, 66])).sum(axis=2) < 120
pink = (r > 170) & (g < 150) & (b > 100) & (r - g > 60)
white = im.min(axis=2) > 225


def img(m):
    return Image.fromarray((m * 255).astype(np.uint8))


def blur(m, s):
    return np.asarray(img(m).filter(ImageFilter.GaussianBlur(s))).astype(float) / 255


def smooth(m, s):
    return blur(m, s) > 0.5


def fill_holes(m):
    ff = img(~m).copy()
    ImageDraw.floodfill(ff, (0, 0), 128)
    return np.asarray(ff) != 128


def erode(m, rad):
    return blur(m, rad / 2) > 0.977


def mirror(m, cx):
    h, w = m.shape
    xs = np.clip(np.rint(2 * cx - np.arange(w)).astype(int), 0, w - 1)
    return m[:, xs]


def symmetric(m, cx, s):
    return (blur(m, s) + blur(mirror(m, cx), s)) / 2 > 0.5


def components(m):
    """흰 이빨 덩어리들 (간단한 4-연결 라벨링)."""
    lab = np.zeros(m.shape, int)
    out, n = [], 0
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if lab[y, x]:
            continue
        n += 1
        stack, pts = [(y, x)], []
        lab[y, x] = n
        while stack:
            cy, cx = stack.pop()
            pts.append((cy, cx))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] and m[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = n
                    stack.append((ny, nx))
        if len(pts) > 150:
            p = np.array(pts)
            out.append(p)
    return out


region_all = fill_holes(ink | pink)
rows = np.where(region_all.any(axis=1))[0]


def split(idx):
    gaps = np.where(np.diff(idx) > 40)[0]
    e = [idx[0]] + [v for gp in gaps for v in (idx[gp], idx[gp + 1])] + [idx[-1]]
    return [(e[2 * i], e[2 * i + 1]) for i in range(len(e) // 2)]


names = [('tongue_big', '메롱 큰혀', True), ('tongue_v', '짓궂은 V', True), ('tongue_bunny', '토끼이빨', False),
         ('grin', '활짝 미소', True), ('shark', '상어 이빨', True), ('gappy', '이 빠진 입', True)]
k = 0
for (y0, y1) in split(rows):
    band = region_all[y0:y1 + 1]
    for (x0, x1) in split(np.where(band.any(axis=0))[0]):
        key, name, sym = names[k]
        pad = 40
        sl = (slice(max(0, y0 - pad), min(H, y1 + pad + 1)), slice(max(0, x0 - pad), min(W, x1 + pad + 1)))
        reg0 = fill_holes(ink[sl] | pink[sl])
        hh, ww = reg0.shape
        xs_ = np.where(reg0.any(axis=0))[0]
        cx = (xs_[0] + xs_[-1]) / 2
        reg = symmetric(reg0, cx, 9) if sym else smooth(reg0, 9)
        inside = erode(reg, RING)

        # 혀: 대칭 U자 + 가운데 곧은 홈
        tg0 = fill_holes(smooth(pink[sl] & reg0, 6) | (pink[sl] & reg0))
        tongue = np.zeros_like(reg)
        groove = np.zeros_like(reg)
        if tg0.sum() > 500:
            txs = np.where(tg0.any(axis=0))[0]
            tcx = cx if sym else (txs[0] + txs[-1]) / 2
            tongue = symmetric(tg0, tcx, 7) & erode(reg, RING * 0.9)
            tongue = smooth(tongue, 2)
            tys = np.where(tongue[:, int(tcx)])[0]
            if len(tys):
                gimg = Image.new('L', (ww, hh), 0)
                d = ImageDraw.Draw(gimg)
                gw = RING * 0.42
                gy0, gy1 = tys[0] - 4, tys[0] + (tys[-1] - tys[0]) * 0.42
                d.line([(tcx, gy0), (tcx, gy1)], fill=255, width=int(gw))
                d.ellipse([tcx - gw / 2, gy1 - gw / 2, tcx + gw / 2, gy1 + gw / 2], fill=255)
                groove = (np.asarray(gimg) > 127) & tongue

        # 이빨: 덩어리마다 위/아래, 둥근/뾰족을 읽고 줄마다 같은 크기로 다시 그림
        teeth_src = white[sl] & reg0
        comps = components(teeth_src)
        iys = np.where(inside.any(axis=1))[0]
        midy = (iys[0] + iys[-1]) / 2
        info = []
        for p in comps:
            ty0, tx0 = p.min(axis=0)
            ty1, tx1 = p.max(axis=0)
            w_, h_ = tx1 - tx0 + 1, ty1 - ty0 + 1
            ratio = len(p) / (w_ * h_)
            info.append(dict(cx=(tx0 + tx1) / 2, top=p[:, 0].mean() < midy, sharp=ratio < 0.6, w=w_, h=h_))
        timg = Image.new('L', (ww * 2, hh * 2), 0)
        d = ImageDraw.Draw(timg)
        for row in (True, False):
            ts = sorted([t for t in info if t['top'] == row], key=lambda t: t['cx'])
            if not ts:
                continue
            # 이빨 모양: 입마다 해석대로 (상어=뾰족, V=양 끝만 뾰족, 나머지=둥근)
            for i, t in enumerate(ts):
                if key == 'shark':
                    t['sharp'] = True
                elif key == 'tongue_v':
                    t['sharp'] = i in (0, len(ts) - 1)
                else:
                    t['sharp'] = False
            for sharp in (True, False):
                grp = [t for t in ts if t['sharp'] == sharp]
                if grp:
                    mw = float(np.median([t['w'] for t in grp])) * 0.95
                    mh = float(np.median([t['h'] for t in grp]))
                    for t in grp:
                        t['W'], t['H'] = mw, mh
            if sym and key != 'gappy':
                pos = [t['cx'] for t in ts]
                for i, t in enumerate(ts):
                    t['cx'] = (pos[i] + (2 * cx - pos[len(ts) - 1 - i])) / 2
            for t in ts:
                x = int(round(t['cx']))
                col = np.where(inside[:, min(max(x, 0), ww - 1)])[0]
                if not len(col):
                    continue
                edge = col[0] if row else col[-1]
                s = 1 if row else -1
                w2, L = t['W'] / 2, t['H']
                X = lambda v: v * 2
                if t['sharp']:
                    pts = [(t['cx'] - w2, edge - s * RING), (t['cx'] + w2, edge - s * RING), (t['cx'] + w2 * 0.15, edge + s * L), (t['cx'] - w2 * 0.15, edge + s * L)]
                    d.polygon([(X(a), X(bb)) for a, bb in pts], fill=255)
                else:
                    tip = edge + s * L
                    yA, yB = sorted([edge - s * RING, tip - s * w2])
                    d.rectangle([X(t['cx'] - w2), X(yA), X(t['cx'] + w2), X(yB)], fill=255)
                    d.ellipse([X(t['cx'] - w2), X(tip - w2 * (1 if row else -1) - w2), X(t['cx'] + w2), X(tip - w2 * (1 if row else -1) + w2)], fill=255)
        teeth = np.asarray(timg.resize((ww, hh), Image.LANCZOS)) > 127
        teeth = smooth(teeth, 1.5) & inside

        def trace(m):
            if not m.any():
                return ''
            pl = potrace.Bitmap(~m).trace(turdsize=30, alphamax=1.1, opticurve=True, opttolerance=0.4)
            f = lambda p: f'{p.x:.1f} {p.y:.1f}'
            dd = []
            for c in pl:
                dd.append('M' + f(c.start_point))
                for sg in c.segments:
                    dd.append(('L' + f(sg.c) + ' L' + f(sg.end_point)) if sg.is_corner else ('C' + f(sg.c1) + ' ' + f(sg.c2) + ' ' + f(sg.end_point)))
                dd.append('Z')
            return ' '.join(dd)

        layers = [('mouth-line', INK, trace(reg)), ('mouth-inside', INK, trace(inside)),
                  ('mouth-tongue', '#E0668A', trace(tongue)), ('mouth-groove', INK, trace(groove)),
                  ('mouth-teeth', '#FFFFFF', trace(teeth))]
        body = ''.join(f'    <path id="{i}" fill="{c}" fill-rule="evenodd" d="{dd}"/>\n' for i, c, dd in layers if dd)
        open(f'{outdir}/mouth3_{key}.svg', 'w').write(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ww} {hh}" width="{ww}" height="{hh}">\n'
            f'  <!-- {name} (그래픽) -->\n  <g id="mouth">\n{body}  </g>\n</svg>\n')
        print(key, len(info), 'teeth')
        k += 1
