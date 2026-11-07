import json
import re
import sys

# 확정 파츠 SVG → 앱용 데이터. 기본 배치는 esi_assembled_v2.svg 와 같은 자리.
D, tpl, out = sys.argv[1], sys.argv[2], sys.argv[3]
PAIR = re.compile(r'(-?\d*\.?\d+) (-?\d*\.?\d+)')


def groups(fname):
    s = open(f'{D}/{fname}').read()
    return {gid: dict(re.findall(r'<path id="[^"]*?-?(line|fill|inside|tongue|teeth)" fill="[^"]+" fill-rule="evenodd" d="([^"]+)"', body))
            for gid, body in re.findall(r'<g id="([^"]+)">\n(.*?)  </g>', s, re.S)}


def nums(paths):
    n = [float(v) for v in re.findall(r'-?\d*\.?\d+', ' '.join(paths))]
    return n[0::2], n[1::2]


def bounds(paths):
    xs, ys = nums(paths)
    return min(xs), min(ys), max(xs), max(ys)


def tf(d, tx, ty, s):
    return PAIR.sub(lambda m: f'{tx + float(m.group(1)) * s:.1f} {ty + float(m.group(2)) * s:.1f}', d)


body = groups('body_wide.svg')['body']
hands = groups('hand_skin_v2.svg')
ref = groups('hand_skin.svg')['hand-left']
legs = groups('legs_skin.svg')
mouth = groups('mouth_merong.svg')['mouth']

BW, CX, TOP = 600, 400, 90
bx0, by0, bx1, by1 = bounds(body.values())
bs = BW / (bx1 - bx0)
BH = (by1 - by0) * bs
eye = TOP + BH * 0.46


def place(g, cx, cy, width, anchor='center'):
    x0, y0, x1, y1 = bounds(g.values())
    s = width / (x1 - x0)
    ty = cy - (y0 + y1) / 2 * s if anchor == 'center' else cy - y0 * s
    return cx - (x0 + x1) / 2 * s, ty, s


T = {
    'legL': (legs['leg-left'], place(legs['leg-left'], CX - BW * 0.26, TOP + BH - 95, BW * 0.27, 'top')),
    'legR': (legs['leg-right'], place(legs['leg-right'], CX + BW * 0.26, TOP + BH - 95, BW * 0.27, 'top')),
    'body': (body, place(body, CX, TOP + BH / 2, BW)),
    'mouth': (mouth, place(mouth, CX, eye + BW * 0.115, BW * 0.2)),
}
rx0, ry0, rx1, ry1 = bounds(ref.values())
hs = BW * 0.235 / (rx1 - rx0)
top = eye - (ry1 - ry0) * hs / 2 + BW * 0.06
for key, name, sign in (('handL', 'hand-left', -1), ('handR', 'hand-right', 1)):
    g = hands[name]
    x0, y0, x1, y1 = bounds(g.values())
    ix = CX + sign * (BW * 0.085)
    T[key] = (g, (ix - (x1 if sign < 0 else x0) * hs, top - y0 * hs, hs))

# 조립 좌표 기준 외곽선 굵기: 몸통 15.2, 손·발 11.9(측정값), 입은 원본 테두리 15 단위 × 입 배율
LW = {'body': 15.2, 'legL': 11.9, 'legR': 11.9, 'handL': 11.9, 'handR': 11.9}
data = {}
for key, (g, (tx, ty, s)) in T.items():
    moved = {k: tf(d, tx, ty, s) for k, d in g.items()}
    x0, y0, x1, y1 = bounds([moved['line']])
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    data[key] = {'lw': LW.get(key, round(15 * s, 2)), 'x': round(cx, 1), 'y': round(cy, 1), 'w': round(x1 - x0, 1), 'h': round(y1 - y0, 1),
                 'p': {k: tf(d, -cx, -cy, 1) for k, d in moved.items()}}

# 입 모양들: 메롱과 같은 배율로, 입안 중심을 메롱 입안 중심에 맞춘다
mg, (mtx, mty, ms) = T['mouth']
mi = bounds([tf(mg['inside'], mtx, mty, ms)])
mcx, mcy = (mi[0] + mi[2]) / 2, (mi[1] + mi[3]) / 2
px, py = data['mouth']['x'], data['mouth']['y']
MOUTHS = [('merong', '메롱', 'mouth_merong.svg'), ('teeth', '이빨줄', 'mouth_teeth.svg'), ('wang', '와앙', 'mouth_wang.svg'),
          ('fang', '크앙', 'mouth_fang.svg'), ('o', '오', 'mouth_o.svg'), ('hehe', '헤헤', 'mouth_hehe.svg')]
data['mouths'] = {}
for key, name, fn in MOUTHS:
    g = groups(fn)['mouth']
    b = bounds([g['inside']])
    tx, ty = mcx - (b[0] + b[2]) / 2 * ms, mcy - (b[1] + b[3]) / 2 * ms
    mv = {k: tf(d, tx - px, ty - py, ms) if False else tf(tf(d, tx, ty, ms), -px, -py, 1) for k, d in g.items()}
    mv.setdefault('tongue', '')
    x0, y0, x1, y1 = bounds([mv['line'], mv['inside']] + ([mv['tongue']] if mv['tongue'] else []))
    data['mouths'][key] = {'name': name, 'w': round(max(abs(x0), abs(x1)) * 2, 1), 'h': round(max(abs(y0), abs(y1)) * 2, 1), 'p': mv}

html = open(tpl).read().replace('/*PARTS_DATA*/null', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
open(out, 'w').write(html)
print('ok', sorted(data))
