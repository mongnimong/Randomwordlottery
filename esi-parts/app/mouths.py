import math
import sys

# 메롱 입과 같은 그림체·같은 단위(가로 약 400)로 새 입 모양을 만든다.
# 레이어: mouth-line(외곽, 굵기 15) / mouth-inside(입안) / mouth-tongue(혀) / mouth-teeth(이빨)
OUT = sys.argv[1]
INK = '#3A3542'
LINE = 15


def f(v):
    return f'{v:.1f}'


def poly(pts):
    return 'M' + ' L'.join(f(x) + ' ' + f(y) for x, y in pts) + ' Z'


def shape(a, p, ht, hb, c=lambda x: 0, q=1.0, n=120):
    """입 모양: 가로 반폭 a, 끝 둥글기 p, 위/아래 반높이 ht/hb, 중심선 c(x)."""
    def env(x):
        return max(0.0, 1 - (abs(x) / a) ** p) ** (1 / (p * q))
    top = lambda x: c(x) - ht * env(x)
    bot = lambda x: c(x) + hb * env(x)
    xs = [-a + 2 * a * i / n for i in range(n + 1)]
    # 양 끝을 촘촘히 (둥근 끝이 각지지 않게)
    xs = [-a * math.cos(math.pi * i / n) for i in range(n + 1)]
    pts = [(x, top(x)) for x in xs] + [(x, bot(x)) for x in reversed(xs)]
    return pts, top, bot


def teeth_band(top, x0, x1, n, depth, from_bottom=False, inset=2.0):
    """윗니(또는 아랫니) 띠: 입 가장자리를 따라가고, 안쪽 끝은 둥근 이빨 n개."""
    m = 24 * n
    xs = [x0 + (x1 - x0) * i / m for i in range(m + 1)]
    sgn = -1 if from_bottom else 1
    edge = [(x, top(x) + sgn * inset) for x in xs]
    tips = []
    for x in reversed(xs):
        u = (x - x0) / (x1 - x0) * n
        bump = math.sin(math.pi * (u - math.floor(u))) ** 0.6     # 이빨 하나 = 둥근 볼록
        d = depth * (0.45 + 0.55 * bump)
        tips.append((x, top(x) + sgn * d))
    return poly(edge + tips)


def tongue(bot, cx, w, h, lift=4, notch=True):
    """입 바닥에서 솟은 혀. 가운데 작은 홈."""
    m = 60
    xs = [cx - w / 2 + w * i / m for i in range(m + 1)]
    base = [(x, bot(x) - lift) for x in xs]
    topc = []
    for x in reversed(xs):
        u = (x - cx) / (w / 2)
        y = bot(x) - lift - h * max(0.0, 1 - u * u) ** 0.55
        if notch and abs(u) < 0.07:
            y += h * 0.35 * (1 - abs(u) / 0.07)
        topc.append((x, y))
    return poly(base + topc)


def fangs(edge, specs, from_bottom=False):
    d = []
    sgn = -1 if from_bottom else 1
    for x, w, L in specs:
        y0 = edge(x)
        d.append(poly([(x - w / 2, edge(x - w / 2) + sgn * 1.5), (x, y0 + sgn * L), (x + w / 2, edge(x + w / 2) + sgn * 1.5)]))
    return ' '.join(d)


M = {}

# 이빨줄: 넓고 납작, 위아래 이빨
pts, top, bot = shape(185, 5, 44, 44, c=lambda x: -16 * (x / 185) ** 2)
M['teeth'] = ('이빨줄', poly(pts), '', teeth_band(top, -150, 150, 5, 30) + ' ' + teeth_band(bot, -120, 120, 4, 24, from_bottom=True))

# 와앙: 세로로 크게, 위 이빨 4 + 아래 3, 작은 혀
pts, top, bot = shape(115, 2, 125, 125)
M['wang'] = ('와앙', poly(pts), '', teeth_band(top, -78, 78, 4, 38) + ' ' + teeth_band(bot, -55, 55, 3, 28, from_bottom=True))

# 크앙: 송곳니 위 2·아래 2, 혀는 옆으로
pts, top, bot = shape(200, 3, 58, 85, c=lambda x: -22 * (x / 200) ** 2)
M['fang'] = ('크앙', poly(pts), tongue(bot, 45, 150, 62), fangs(top, [(-112, 46, 62), (112, 46, 62), (-40, 30, 30), (40, 30, 30)]) + ' ' + fangs(bot, [(-75, 36, 40), (75, 36, 40)], from_bottom=True))

# 오: 작고 동그랗게, 앞니 2 + 혀
pts, top, bot = shape(78, 2, 88, 96)
M['o'] = ('오', poly(pts), tongue(bot, 0, 92, 52), teeth_band(top, -42, 42, 2, 34))

# 헤헤: D자, 큰 윗니 4 + 큰 혀
pts, top, bot = shape(195, 3, 14, 175, c=lambda x: -50 + 6 * (x / 195) ** 2, q=0.8)
M['hehe'] = ('헤헤', poly(pts), tongue(bot, 0, 210, 82), teeth_band(top, -150, 150, 4, 44))

for key, (name, inside, tg, teeth) in M.items():
    xs = [float(v) for v in inside.replace('M', ' ').replace('L', ' ').replace('Z', ' ').split()[0::2]]
    ys = [float(v) for v in inside.replace('M', ' ').replace('L', ' ').replace('Z', ' ').split()[1::2]]
    pad = LINE + 10
    ox, oy = -min(xs) + pad, -min(ys) + pad
    w, h = max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad
    import re
    mv = lambda d: re.sub(r'(-?\d*\.?\d+) (-?\d*\.?\d+)', lambda m: f(float(m.group(1)) + ox) + ' ' + f(float(m.group(2)) + oy), d)
    inside, tg, teeth = mv(inside), mv(tg), mv(teeth)
    body = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}">\n'
            f'  <g id="mouth">\n'
            f'    <path id="mouth-line" fill="{INK}" fill-rule="evenodd" d="{inside}" stroke="{INK}" stroke-width="{2 * LINE}" stroke-linejoin="round"/>\n'
            f'    <path id="mouth-inside" fill="{INK}" fill-rule="evenodd" d="{inside}"/>\n'
            + (f'    <path id="mouth-tongue" fill="#F35C8A" fill-rule="evenodd" d="{tg}"/>\n' if tg else '')
            + f'    <path id="mouth-teeth" fill="#FFFFFF" fill-rule="evenodd" d="{teeth}"/>\n'
            f'  </g>\n</svg>\n')
    open(f'{OUT}/mouth_{key}.svg', 'w').write(body)
    print(key, name, int(w), int(h))
