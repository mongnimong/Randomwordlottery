import sys
import numpy as np
import potrace
from PIL import Image, ImageDraw, ImageFilter

# 발 스케치 3종 → 좌우대칭·굵기 일정한 발 SVG
# 각 종류의 왼발을 기준으로 다듬고, 오른발은 좌우로 뒤집어 만든다.
src, outdir = sys.argv[1], sys.argv[2]
INK, SKIN = '#3A3542', '#F9C2A9'
im = np.asarray(Image.open(src).convert('RGB')).astype(int)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
H, W = r.shape
ink = (im.max(axis=2) < 120)
skin = (r > 200) & (g > 160) & (b > 130) & (r - b > 40)


def img(m):
    return Image.fromarray((m * 255).astype(np.uint8))


def blur(m, s):
    return np.asarray(img(m).filter(ImageFilter.GaussianBlur(s))).astype(float) / 255


def fill_holes(m):
    ff = img(~m).copy()
    ImageDraw.floodfill(ff, (0, 0), 128)
    return np.asarray(ff) != 128


def trace(m, ox=0, turd=30):
    if not m.any():
        return ''
    pl = potrace.Bitmap(~m).trace(turdsize=turd, alphamax=1.1, opticurve=True, opttolerance=0.4)
    f = lambda p: f'{p.x + ox:.1f} {p.y:.1f}'
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


def seg_path(segs, flip, ww, ox):
    out = []
    for a_, b_ in segs:
        fx = (lambda x: ww - 1 - x) if flip else (lambda x: x)
        out.append(f'M{fx(a_[0]) + ox:.1f} {a_[1]:.1f} L{fx(b_[0]) + ox:.1f} {b_[1]:.1f}')
    return ' '.join(out)


# 왼발 기준 영역 (스케치 속 위치)
TYPES = [('bend', '휘어진 다리', (190, 280, 480, 650)),
         ('heart', '하트 발바닥', (1010, 485, 1345, 705)),
         ('paw', '발가락 발', (45, 795, 320, 1225))]
for key, name, (x0, y0, x1, y1) in TYPES:
    pad = 30
    sl = (slice(y0 - pad, y1 + pad), slice(x0 - pad, x1 + pad))
    sk, ik = skin[sl], ink[sl]
    # 살구색 면(안쪽 선 자리까지 메운 것) = 발 모양
    # 안쪽 선이 지나가는 가는 틈을 메운다(닫기: 살짝 부풀렸다가 다시 깎기). 뽀글 윗단은 남도록 약하게.
    dil = blur(sk, 7) > 0.12
    clo = blur(dil, 7) > 0.88
    core = blur(fill_holes(clo) | sk, 2) > 0.5
    # 안쪽 선(발가락 홈, 하트 홈): 면 안에 들어온 먹선만, 굵기 고르게
    inner = ik & (blur(core, 1.5) > 0.8)
    detail0 = blur(blur(inner, 1.5) > 0.35, 1.2) > 0.5
    # 안쪽 선 덩어리마다 방향(주축)을 읽고, 같은 굵기의 깔끔한 선으로 다시 그림
    hh0, ww0 = core.shape
    dimg = Image.new('L', (ww0, hh0), 0)
    dd = ImageDraw.Draw(dimg)
    seen = np.zeros_like(detail0)
    LW = max(6, int(0.055 * ww0))
    segs = []
    for y, x in zip(*np.nonzero(detail0)):
        if seen[y, x]:
            continue
        stack, pts = [(y, x)], []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop(); pts.append((cx, cy))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < hh0 and 0 <= nx < ww0 and detail0[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; stack.append((ny, nx))
        if len(pts) < 25:
            continue
        P = np.array(pts, float); m = P.mean(axis=0)
        u = np.linalg.svd(P - m, full_matrices=False)[2][0]
        t = (P - m) @ u
        L = max(t.max() - t.min(), LW * 2.2) / 2
        a_, b_ = m - u * L, m + u * L
        dd.line([tuple(a_), tuple(b_)], fill=255, width=LW)
        segs.append(reach_edge((a_, b_), core, LW * 4))
        for q in (a_, b_):
            dd.ellipse([q[0] - LW / 2, q[1] - LW / 2, q[0] + LW / 2, q[1] + LW / 2], fill=255)
    detail = (np.asarray(dimg) > 127) & core
    print('  detail px', int(detail.sum()))
    hh, ww = core.shape
    gap = int(ww * 0.25)
    T = 0.073 * ww                                 # 지금 손·발과 같은 비율의 외곽선 굵기
    groups = ''
    for gid, flip, ox in (('leg-left', False, 0), ('leg-right', True, ww + gap)):
        c_ = np.fliplr(core) if flip else core
        d_ = np.fliplr(detail) if flip else detail
        fd = trace(c_, ox)
        groups += (f'  <g id="{gid}">\n'
                   f'    <path id="{gid}-line" fill="{INK}" fill-rule="evenodd" d="{fd}" stroke="{INK}" stroke-width="{2 * T:.1f}" stroke-linejoin="round"/>\n'
                   f'    <path id="{gid}-fill" fill="{SKIN}" fill-rule="evenodd" d="{fd}"/>\n'
                   + (f'    <path id="{gid}-detail" fill="none" fill-rule="evenodd" d="{seg_path(segs, flip, ww, ox)}" stroke="{INK}" stroke-width="{T * 0.85:.1f}" stroke-linecap="round"/>\n' if segs else '')
                   + '  </g>\n')
    tw = ww * 2 + gap
    open(f'{outdir}/feet3_{key}.svg', 'w').write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-T:.0f} {-T:.0f} {tw + 2 * T:.0f} {hh + 2 * T:.0f}" width="{tw + 2 * T:.0f}" height="{hh + 2 * T:.0f}">\n'
        f'  <!-- {name} -->\n{groups}</svg>\n')
    print(key, name, ww, hh, 'detail' if detail.any() else '-')
