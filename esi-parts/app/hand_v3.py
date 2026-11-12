import sys
import numpy as np
import potrace
from PIL import Image, ImageFilter, ImageDraw

# 손그림 손 → 손가락 홈을 '선(중심선)'으로 분리한 손 SVG (앱에서 홈 굵기도 고정)
src, out = sys.argv[1], sys.argv[2]
im = np.asarray(Image.open(src).convert('RGB')).astype(int)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
H, W = r.shape
mid = W // 2


def img(m):
    return Image.fromarray((m * 255).astype(np.uint8))


def blur(m, s):
    return np.asarray(img(m).filter(ImageFilter.GaussianBlur(s))).astype(float) / 255


fill = (im.min(axis=2) > 120) & ((r - b) > 30)
fill = blur(fill, 3) > 0.5
# 손가락 사이 가는 홈을 메운 손 모양 (닫기)
closed = blur(blur(fill, 9) > 0.1, 9) > 0.9
closed = blur(closed | fill, 2) > 0.5
notch = closed & ~fill & (blur(closed, 4) > 0.95)

ys, xs = np.where(closed)
pad = 40
x0, y0, x1, y1 = xs.min() - pad, ys.min() - pad, xs.max() + pad, ys.max() + pad


def trace(mask):
    pl = potrace.Bitmap(~mask).trace(turdsize=60, alphamax=1.0, opticurve=True, opttolerance=0.3)
    f = lambda p: f"{p.x - x0:.1f} {p.y - y0:.1f}"
    d = []
    for c in pl:
        d.append('M' + f(c.start_point))
        for s in c.segments:
            d.append(('L' + f(s.c) + ' L' + f(s.end_point)) if s.is_corner else ('C' + f(s.c1) + ' ' + f(s.c2) + ' ' + f(s.end_point)))
        d.append('Z')
    return ' '.join(d)


def reach_edge(seg, mask, maxd):
    """선분 양 끝 중 외곽에 가까운 쪽을 면이 끝나는 지점(외곽선이 시작되는 곳)까지 늘린다."""
    import numpy as _np
    a_, b_ = _np.array(seg[0], float), _np.array(seg[1], float)
    hh_, ww_ = mask.shape
    out = [a_, b_]
    for i, (p_, q_) in enumerate(((a_, b_), (b_, a_))):
        v = p_ - q_
        n = _np.hypot(*v)
        if n == 0:
            continue
        v /= n
        for step in range(0, int(maxd)):
            x, y = p_ + v * step
            xi, yi = int(round(x)), int(round(y))
            if not (0 <= xi < ww_ and 0 <= yi < hh_) or not mask[yi, xi]:
                out[i] = p_ + v * step
                break
    return out[0], out[1]


def segments(mask):
    """홈 덩어리마다 주축 방향 선분 하나."""
    seen = np.zeros_like(mask)
    segs = []
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        stack, pts = [(y, x)], []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop(); pts.append((cx, cy))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; stack.append((ny, nx))
        if len(pts) < 60:
            continue
        P = np.array(pts, float); m = P.mean(axis=0)
        u = np.linalg.svd(P - m, full_matrices=False)[2][0]
        t = (P - m) @ u
        a_, b_ = m + u * t.min(), m + u * t.max()
        if a_[1] > b_[1]:
            a_, b_ = b_, a_
        segs.append(reach_edge((a_, b_), closed, 120))
    return segs


body = ''
for gid, left in (('hand-left', True), ('hand-right', False)):
    c_ = closed.copy(); n_ = notch.copy()
    if left:
        c_[:, mid:] = False; n_[:, mid:] = False
    else:
        c_[:, :mid] = False; n_[:, :mid] = False
    fd = trace(c_)
    det = ' '.join(f'M{a[0] - x0:.1f} {a[1] - y0:.1f} L{b_[0] - x0:.1f} {b_[1] - y0:.1f}' for a, b_ in segments(n_))
    body += (f'  <g id="{gid}">\n'
             f'    <path id="{gid}-line" fill="#353241" fill-rule="evenodd" d="{fd}" stroke="#353241" stroke-width="100" stroke-linejoin="round"/>\n'
             f'    <path id="{gid}-fill" fill="#F3CBB3" fill-rule="evenodd" d="{fd}"/>\n'
             + (f'    <path id="{gid}-detail" fill="none" fill-rule="evenodd" d="{det}" stroke="#353241" stroke-width="40" stroke-linecap="round"/>\n' if det else '')
             + '  </g>\n')
w, h = x1 - x0, y1 - y0
open(out, 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n{body}</svg>\n')
print('ok', w, h, body.count('-detail'))
