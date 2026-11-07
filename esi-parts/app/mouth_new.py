import math
import random
import sys

# 해석(설명)만 보고 새로 그린 입 6종. 레이어: 외곽(굵기 RING) / 입안 / 혀 / 혀홈 / 이빨
OUT = sys.argv[1]
RING = 15
INK, TONGUE = '#3A3542', '#E0668A'
random.seed(7)


def f(v):
    return f'{v:.1f}'


def catmull(pts, n=10):
    """닫힌 매끈한 곡선의 점들."""
    out = []
    L = len(pts)
    for i in range(L):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % L], pts[(i + 2) % L]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    return out


def path(pts):
    return 'M' + ' L'.join(f(x) + ' ' + f(y) for x, y in pts) + ' Z'


def edge(poly, x, top):
    """세로선 x가 입 윤곽과 만나는 점: 위쪽이면 가장 작은 y, 아래쪽이면 가장 큰 y."""
    ys = []
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (x1 - x) * (x2 - x) <= 0 and x1 != x2:
            ys.append(y1 + (y2 - y1) * (x - x1) / (x2 - x1))
    return (min(ys) if top else max(ys)) if ys else 0.0


def slope(poly, x, top):
    return math.atan2(edge(poly, x + 6, top) - edge(poly, x - 6, top), 12)


def tooth(poly, x, w, h, top=True, sharp=False, margin=12, jitter=True):
    """입 가장자리(위/아래)에 붙은 이빨 하나. 가장자리 기울기에 맞춰 세운다."""
    if jitter:
        w *= random.uniform(0.94, 1.06)
        h *= random.uniform(0.92, 1.08)
    s = 1 if top else -1
    ey = edge(poly, x, top) + s * margin
    if sharp:
        local = [(-w / 2, 0), (w / 2, 0), (w * 0.07, s * h), (-w * 0.07, s * h)]
        local = catmull([(-w / 2, 0), (w / 2, 0), (w * 0.22, s * h * 0.55), (0, s * h), (-w * 0.22, s * h * 0.55)], 6)
    else:
        r = w * 0.45
        local = [(-w / 2, 0), (w / 2, 0), (w / 2, s * (h - r))]
        for k in range(1, 12):
            a = math.pi * k / 12
            local.append((w / 2 * math.cos(a), s * (h - r + r * math.sin(a))))
        local += [(-w / 2, s * (h - r))]
        local = catmull(local, 3)
    ang = slope(poly, x, top) + (random.uniform(-0.05, 0.05) if jitter else 0)
    ca, sa = math.cos(ang), math.sin(ang)
    return path([(x + px * ca - py * sa, ey + px * sa + py * ca) for px, py in local])


def tongue(cx, top_y, w, bottom_y, lobe=14):
    """두 봉우리 윗선 + U자 아랫단. 가운데 홈 자리(cx)가 살짝 들어감."""
    hw = w / 2
    pts = [(cx - hw, top_y + lobe), (cx - hw * 0.5, top_y), (cx - hw * 0.08, top_y + lobe * 1.1),
           (cx + hw * 0.08, top_y + lobe * 1.1), (cx + hw * 0.5, top_y), (cx + hw, top_y + lobe),
           (cx + hw * 1.04, (top_y + bottom_y) / 2), (cx + hw * 0.72, bottom_y - (bottom_y - top_y) * 0.12),
           (cx, bottom_y), (cx - hw * 0.72, bottom_y - (bottom_y - top_y) * 0.12), (cx - hw * 1.04, (top_y + bottom_y) / 2)]
    groove = catmull([(cx - 4, top_y + lobe), (cx + 4, top_y + lobe), (cx + 3.5, top_y + (bottom_y - top_y) * 0.45),
                      (cx, top_y + (bottom_y - top_y) * 0.5), (cx - 3.5, top_y + (bottom_y - top_y) * 0.45)], 5)
    return path(catmull(pts, 8)), path(groove)


M = {}

# 1. 메롱 큰혀: 윗입술 가운데가 쏙 들어간 두 봉우리, 윗니 4(양 끝 작고 가운데 큼), 넓고 큰 혀
mouth = catmull([(-205, -18), (-150, -58), (-75, -52), (0, -24), (75, -54), (150, -60), (206, -22),
                 (205, 32), (150, 72), (60, 92), (0, 95), (-60, 92), (-150, 72), (-208, 30)])
tg, gr = tongue(0, 32, 210, 205)
M['tongue_big'] = ('메롱 큰혀', mouth, tg, gr, ' '.join([
    tooth(mouth, -152, 38, 36), tooth(mouth, -64, 62, 60), tooth(mouth, 62, 62, 58), tooth(mouth, 152, 38, 38)]))

# 2. 짓궂은 V: 입꼬리 올라간 V, 윗니 5(양 끝 뾰족), 작은 혀
mouth = catmull([(-195, -62), (-100, -46), (0, -40), (100, -48), (196, -66),
                 (178, -28), (112, 38), (42, 82), (0, 92), (-42, 82), (-112, 38), (-178, -26)])
tg, gr = tongue(0, 54, 96, 152, lobe=10)
M['tongue_v'] = ('짓궂은 V', mouth, tg, gr, ' '.join([
    tooth(mouth, -138, 34, 62, sharp=True), tooth(mouth, -60, 44, 42), tooth(mouth, 0, 44, 44),
    tooth(mouth, 60, 44, 42), tooth(mouth, 138, 34, 62, sharp=True)]))

# 3. 토끼이빨: 오른쪽으로 갈수록 올라가는 비대칭 윗선, 큰 앞니 2, 가운데 혀
mouth = catmull([(-165, -28), (-60, -40), (60, -56), (158, -84), (170, -46), (145, 8), (82, 52),
                 (0, 68), (-82, 50), (-142, 16), (-170, -6)])
tg, gr = tongue(8, 40, 112, 150, lobe=11)
M['tongue_bunny'] = ('토끼이빨', mouth, tg, gr, ' '.join([
    tooth(mouth, -30, 68, 66, jitter=False), tooth(mouth, 46, 68, 64, jitter=False)]))

# 4. 활짝 미소: 바나나 모양, 윗니 5 + 아랫니 4
mouth = catmull([(-212, -52), (-110, -16), (0, -6), (110, -16), (212, -54), (228, -22), (206, 36),
                 (120, 92), (0, 110), (-120, 92), (-206, 36), (-228, -20)])
M['grin'] = ('활짝 미소', mouth, '', '', ' '.join(
    [tooth(mouth, x, 52, 34) for x in (-150, -76, 0, 76, 150)] +
    [tooth(mouth, x, 52, 30, top=False) for x in (-114, -38, 38, 114)]))

# 5. 상어 이빨: 그릇 모양 + 윗선 가운데 살짝 들어감, 뾰족한 위 4 + 아래 4
mouth = catmull([(-172, -56), (-90, -50), (0, -36), (90, -52), (172, -58), (182, -10), (140, 60),
                 (60, 100), (0, 106), (-60, 100), (-140, 60), (-182, -10)])
M['shark'] = ('상어 이빨', mouth, '', '', ' '.join(
    [tooth(mouth, x, 50, h, sharp=True) for x, h in ((-112, 78), (-38, 86), (38, 84), (112, 76))] +
    [tooth(mouth, x, 42, h, top=False, sharp=True) for x, h in ((-96, 50), (-32, 58), (32, 56), (96, 48))]))

# 6. 이 빠진 입: 위 평평·아래 둥근 네모, 윗니 4 가지런, 아랫니 띄엄띄엄 + 오른쪽 끝 작은 이
mouth = catmull([(-160, -72), (0, -74), (160, -72), (180, -50), (178, 10), (142, 60), (60, 92),
                 (0, 96), (-60, 92), (-142, 60), (-178, 10), (-180, -50)])
M['gappy'] = ('이 빠진 입', mouth, '', '', ' '.join(
    [tooth(mouth, x, 54, 40, jitter=False) for x in (-112, -38, 38, 112)] +
    [tooth(mouth, -100, 44, 34, top=False), tooth(mouth, 8, 50, 38, top=False), tooth(mouth, 88, 46, 34, top=False),
     tooth(mouth, 148, 22, 20, top=False, margin=14)]))

for key, (name, mouth, tg, gr, teeth) in M.items():
    inside = path(mouth)
    allp = mouth[:]
    xs, ys = [p[0] for p in allp], [p[1] for p in allp]
    if tg:
        ys.append(max(float(v) for v in tg.replace('M', ' ').replace('L', ' ').replace('Z', ' ').split()[1::2]))
    pad = RING + 12
    x0, y0 = min(xs) - pad, min(ys) - pad
    w, h = max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad
    import re
    mv = lambda d: re.sub(r'(-?\d*\.?\d+) (-?\d*\.?\d+)', lambda m: f(float(m.group(1)) - x0) + ' ' + f(float(m.group(2)) - y0), d)
    inside, tg, gr, teeth = mv(inside), mv(tg), mv(gr), mv(teeth)
    line = inside + (' ' + tg if tg else '')
    out = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}">\n'
           f'  <!-- {name} (새로 그림) -->\n  <g id="mouth">\n'
           f'    <path id="mouth-line" fill="{INK}" fill-rule="nonzero" d="{line}" stroke="{INK}" stroke-width="{2 * RING}" stroke-linejoin="round"/>\n'
           f'    <path id="mouth-inside" fill="{INK}" fill-rule="evenodd" d="{inside}"/>\n'
           + (f'    <path id="mouth-tongue" fill="{TONGUE}" fill-rule="evenodd" d="{tg}"/>\n'
              f'    <path id="mouth-groove" fill="{INK}" fill-rule="evenodd" d="{gr}"/>\n' if tg else '')
           + f'    <path id="mouth-teeth" fill="#FFFFFF" fill-rule="nonzero" d="{teeth}"/>\n'
           f'  </g>\n</svg>\n')
    open(f'{OUT}/mouth4_{key}.svg', 'w').write(out)
    print(key, name, int(w), int(h))
