import numpy as np
from PIL import Image, ImageDraw


def carve(mask, segs, depth, hw, out=30):
    """홈 선이 외곽에 닿는 쪽 끝에 V자 홈을 판다 → 외곽선이 안으로 접혀 들어가 홈 선과 한 줄로 이어짐."""
    H, W = mask.shape
    im = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(im)
    for a, b in segs:
        a, b = np.array(a, float), np.array(b, float)
        for p, q in ((a, b), (b, a)):
            v = p - q
            n = np.hypot(*v)
            if n == 0:
                continue
            v /= n
            x, y = p + v * 6
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < W and 0 <= yi < H and mask[yi, xi]:
                continue  # 이 끝은 안쪽 → 홈 안 팜
            nrm = np.array([-v[1], v[0]])
            apex = p - v * depth
            base = p + v * out
            poly = [tuple(apex), tuple(p + nrm * hw * .55 - v * depth * .35), tuple(base + nrm * hw * 1.2),
                    tuple(base - nrm * hw * 1.2), tuple(p - nrm * hw * .55 - v * depth * .35)]
            dr.polygon(poly, fill=255)
    return mask & ~(np.asarray(im) > 127)


def toe_bumps(mask, segs, T):
    """발가락 선이 닿는 외곽 사이사이를 동그랗게 부풀려 발가락 끝을 뭉툭·동글하게."""
    H, W = mask.shape
    ends = []
    for a, b in segs:
        a, b = np.array(a, float), np.array(b, float)
        for p, q in ((a, b), (b, a)):
            v = p - q
            n = np.hypot(*v)
            if n == 0:
                continue
            v /= n
            x, y = p + v * 6
            xi, yi = int(round(x)), int(round(y))
            if not (0 <= xi < W and 0 <= yi < H and mask[yi, xi]):
                ends.append((p, v))
    if len(ends) < 1:
        return mask
    pts = np.array([e for e, _ in ends])
    out = np.mean([v for _, v in ends], axis=0)
    out /= np.hypot(*out)
    tan = np.array([out[1], -out[0]])
    order = np.argsort(pts @ tan)
    pts = pts[order]
    sp = np.mean(np.hypot(*np.diff(pts, axis=0).T)) if len(pts) > 1 else T * 2.2
    cen = [pts[0] - tan * sp / 2] + [(pts[i] + pts[i + 1]) / 2 for i in range(len(pts) - 1)] + [pts[-1] + tan * sp / 2]
    r = sp * 0.40
    im = Image.fromarray((mask * 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    for c in cen:
        c = c - out * r * 0.62
        dr.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)
    return np.asarray(im) > 127
