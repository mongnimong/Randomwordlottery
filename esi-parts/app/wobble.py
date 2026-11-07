import re
import sys
import numpy as np
import potrace
from PIL import Image, ImageFilter

# 매끈한 파츠 → 손그림처럼 울퉁불퉁한 파츠
# 면 가장자리를 살짝 흔들고, 외곽선 굵기를 자리마다 다르게(마커로 그린 느낌)
src_svg, ras, scale, line, fillcol, groups_spec, out, seed = sys.argv[1:9]
scale, line, seed = float(scale), float(line), int(seed)
T = line * scale                                    # 래스터 기준 외곽선 굵기(px)
INK = '#3A3542'
im = np.asarray(Image.open(ras).convert('RGB')).astype(int)
H, W = im.shape[:2]
c = np.array([int(fillcol[i:i + 2], 16) for i in (1, 3, 5)])
fill = np.abs(im - c).sum(axis=2) < 70
rng = np.random.default_rng(seed)


def img(m):
    return Image.fromarray((m * 255).astype(np.uint8))


def noise(cell):
    """부드러운 무작위 장: cell(px) 간격의 격자를 매끈하게 키운다 (-1~1)."""
    gw, gh = max(2, int(W / cell) + 2), max(2, int(H / cell) + 2)
    g = (rng.random((gh, gw)) * 255).astype(np.uint8)
    up = np.asarray(Image.fromarray(g).resize((W, H), Image.BICUBIC)).astype(float)
    return (up / 127.5 - 1).clip(-1, 1)


def warp(mask, amp, cell):
    dx, dy = noise(cell) * amp, noise(cell) * amp
    yy, xx = np.mgrid[0:H, 0:W]
    sx = np.clip(np.rint(xx + dx), 0, W - 1).astype(int)
    sy = np.clip(np.rint(yy + dy), 0, H - 1).astype(int)
    return mask[sy, sx]


def blur_thr(mask, sigma, thr):
    return np.asarray(img(mask).filter(ImageFilter.GaussianBlur(sigma))) > thr


def smooth(m, s):
    return blur_thr(m, s, 127)


fill_w = smooth(warp(fill, 0.16 * T, 2.6 * T), 0.08 * T)            # 면 가장자리 살짝 흔들기
outer = blur_thr(fill_w, T / 2, 6) | fill_w                          # 기본 굵기 T로 두르기
outer = smooth(warp(outer, 0.42 * T, 1.9 * T), 0.1 * T) | fill_w    # 바깥선만 더 흔들어 굵기 변화


def trace(mask):
    pl = potrace.Bitmap(~mask).trace(turdsize=40, alphamax=1.0, opticurve=True, opttolerance=0.3)
    f = lambda p: f'{p.x / scale:.1f} {p.y / scale:.1f}'
    d = []
    for cv in pl:
        d.append('M' + f(cv.start_point))
        for s in cv.segments:
            d.append(('L' + f(s.c) + ' L' + f(s.end_point)) if s.is_corner else ('C' + f(s.c1) + ' ' + f(s.c2) + ' ' + f(s.end_point)))
        d.append('Z')
    return ' '.join(d)


vb = re.search(r'viewBox="([^"]+)"', open(src_svg).read()).group(1)
body = ''
# groups_spec: "id" 하나 또는 "left-id,right-id" (가로 절반으로 나눔)
ids = groups_spec.split(',')
for i, gid in enumerate(ids):
    o, f_ = outer.copy(), fill_w.copy()
    if len(ids) == 2:
        mid = W // 2
        if i == 0:
            o[:, mid:] = False; f_[:, mid:] = False
        else:
            o[:, :mid] = False; f_[:, :mid] = False
    body += (f'  <g id="{gid}">\n'
             f'    <path id="{gid}-line" fill="{INK}" fill-rule="evenodd" d="{trace(o)}"/>\n'
             f'    <path id="{gid}-fill" fill="{fillcol}" fill-rule="evenodd" d="{trace(f_)}"/>\n'
             f'  </g>\n')
w, h = vb.split()[2:]
open(out, 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{w}" height="{h}">\n{body}</svg>\n')
print('ok', out)
