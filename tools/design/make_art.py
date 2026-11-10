"""
Echoflex (NINE HANDS | DSP) v2 - visuel du plugin d'apres le design realiste fourni par l'utilisateur (nov. 2026).

Source : design/source/echoflex_realiste.png (1800 x 1235, pedale detouree au centre).
  - textes d'origine (SUSTAIN, DELAY, VOLUME, PUSH FOR AGE, SYNC, OUTPUT, INPUT, TAP, DELAY, logo Studio Wiga) effaces :
    teinte basse frequence par inpainting + grain du panneau repris d'une zone propre ; ils sont redessines en vectoriel
    par le plugin (Poppins) d'apres Layout.h ;
  - potards effaces (dessines par le plugin : knob_strip.png + flou de mouvement), jacks dores retires et remplaces
    par les embases photo du kit (OUT a gauche, TAP a gauche en bas, IN a droite) ;
  - plaque alu, vis, titre ECHOFLEX et ondes, bagues des LED, footswitch : photo d'origine.
Pedale simple : image de 1800 px de haut, pedale plein cadre, largeur aux proportions de la pedale,
fond transparent seulement autour des jacks et dans les coins arrondis. Repere du plugin = image / 2.
Sorties (racine du depot) : background.png, led_on_red.png / led_on_amber.png / led_on_green.png,
glow_red.png / glow_amber.png / glow_green.png, Layout.h, tools/layout.json
"""
import os, sys, json, math
import numpy as np, cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import photo_controls as PC

SRC = os.path.join(ROOT, 'design', 'source', 'echoflex_realiste.png')
src = np.asarray(Image.open(SRC).convert('RGBA')).astype(np.float32)
rgb0, a0 = src[..., :3].copy(), src[..., 3] / 255.0

# ------------------------------------------------------------------ geometrie de la source (px)
BOX_X0, BOX_X1, BOX_Y0, BOX_Y1 = 508, 1291, 8, 1215          # boitier (plaque alu comprise)
PANEL = (537, 38, 1261, 1180)                                 # panneau noir interieur
KNOBS = {'volume': (898.0, 176.8), 'sustain': (654.4, 354.0), 'delay': (1142.0, 355.4)}
KNOB_RP = 80.5                                                # rayon exterieur de la couronne
LEDS = {'red': (899.3, 702.9, 18.5), 'amber': (899.2, 370.2, 12.0), 'green': (1220.7, 256.6, 12.0)}  # centre, rayon de la LED photo (= bague d'origine)
BEZEL_R = {'red': 21.0, 'amber': 15.5, 'green': 15.5}       # bagues d'origine effacees (LED remplacees par la photo fournie)
FOOT = (900.5, 892.5)
FOOT_DY = 40.0                                                 # footswitch abaisse de 20 px dans l'image 1800 px (demande de l'utilisateur)
JACK_Y = {'out': 604.0, 'in': 603.5, 'tap': 1030.0}

# fenetres des textes d'origine (seuil de clarte) : x0, y0, x1, y1
TEXT_WINS = [(585, 228, 725, 270), (1085, 226, 1205, 268), (1194, 220, 1250, 248), (828, 296, 972, 338),
             (812, 226, 990, 290), (553, 545, 580, 655), (1220, 562, 1247, 647), (553, 999, 579, 1056),
             (800, 1010, 1000, 1066), (770, 1076, 1032, 1120)]
CLEAN = (588, 768, 800, 990)                                  # zone de panneau sans inscription (grain de reference)

# ------------------------------------------------------------------ 1. masque d'effacement
H0, W0 = a0.shape
lum = rgb0.mean(2)
mask = np.zeros((H0, W0), np.uint8)
for x0, y0, x1, y1 in TEXT_WINS:
    m = (lum[y0:y1, x0:x1] > 95).astype(np.uint8)
    mask[y0:y1, x0:x1] |= m
mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=3)
yy, xx = np.mgrid[0:H0, 0:W0].astype(np.float32)
for (cx, cy) in KNOBS.values():
    mask[np.hypot(xx - cx, yy - cy) <= KNOB_RP + 4] = 1
# footswitch de la photo efface : remplace par le footswitch photo du kit (assets/kit/footswitch_photo.png)
mask[np.hypot(xx - FOOT[0], yy - FOOT[1]) <= 98] = 1
# bagues des LED protegees (jamais effacees par les fenetres de texte voisines)
for name, (lx, ly, lr) in LEDS.items():
    mask[np.hypot(xx - lx, yy - ly) <= BEZEL_R[name] + 2] = 1
# rien en dehors du panneau noir
pm = np.zeros_like(mask); pm[PANEL[1] + 2:PANEL[3] - 2, PANEL[0] + 2:PANEL[2] - 2] = 1
mask &= pm

# ------------------------------------------------------------------ 2. remplissage : basse frequence + grain
SIG = 5.0
mask_big = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=2)
inp = cv2.inpaint(np.clip(rgb0, 0, 255).astype(np.uint8), mask_big, 9, cv2.INPAINT_TELEA).astype(np.float32)
low_in = cv2.GaussianBlur(inp, (0, 0), SIG)          # teinte basse frequence sans le texte
mask = mask_big
cx0, cy0, cx1, cy1 = CLEAN
patch = rgb0[cy0:cy1, cx0:cx1]
hp = patch - cv2.GaussianBlur(patch, (0, 0), SIG)
ph, pw = hp.shape[:2]
# pavage miroir du grain (sans couture), decale de facon aleatoire par zone
rng = np.random.default_rng(11)
tile = np.concatenate([hp, hp[:, ::-1]], 1); tile = np.concatenate([tile, tile[::-1]], 0)
TH, TW = tile.shape[:2]
reps = np.tile(tile, (H0 // TH + 2, W0 // TW + 2, 1))
oy, ox = rng.integers(0, TH), rng.integers(0, TW)
grain = reps[oy:oy + H0, ox:ox + W0]
mf = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.2)
filled = low_in + grain
rgb = rgb0 * (1 - mf[..., None]) + filled * mf[..., None]

# vis du bas = copies exactes des vis du haut (vis du bas du visuel moins nettes) : centres recales par correlation
def _refine(c, tpl, r=6):
    x, y = c; h = tpl.shape[0] // 2
    zone = rgb[int(y) - h - r:int(y) + h + r + 1, int(x) - h - r:int(x) + h + r + 1].mean(2).astype(np.float32)
    res = cv2.matchTemplate(zone, tpl, cv2.TM_CCOEFF_NORMED)
    _, _, _, mx = cv2.minMaxLoc(res)
    return (int(x) - r + mx[0] + 0.0, int(y) - r + mx[1] + 0.0)
SR = 22
for top, bot in (((569.5, 68.5), (571.5, 1149.5)), ((1229.5, 65.5), (1228.5, 1149.5))):
    tx, ty = int(round(top[0])), int(round(top[1]))
    tpl = rgb[ty - SR:ty + SR + 1, tx - SR:tx + SR + 1].mean(2).astype(np.float32)
    bx, by = _refine(bot, tpl)
    Ms = np.float32([[1, 0, bx - tx], [0, 1, by - ty]])
    cp = cv2.warpAffine(rgb, Ms, (W0, H0), flags=cv2.INTER_CUBIC)
    ds = np.hypot(xx - bx, yy - by)
    ws = np.clip((SR - 1.5 - ds) / 2.5, 0, 1)[..., None]
    rgb = rgb * (1 - ws) + cp * ws

# ------------------------------------------------------------------ 3. recadrage + mise a l'echelle (1800 px de haut)
OUT_H = 1800
K = OUT_H / (BOX_Y1 - BOX_Y0)
JACK_LEN = 104.0 / 958.0 * OUT_H                               # longueur d'une embase le long de la tranche (px)
_j = PC.jack_sprite(JACK_LEN, 1, 1)
JP = int(round(_j[1])) - 2                                     # saillie hors du boitier (px)
BOXW = (BOX_X1 - BOX_X0) * K
OUT_W = int(round(BOXW + 2 * JP))
M = np.float32([[K, 0, JP - BOX_X0 * K], [0, K, -BOX_Y0 * K]])
def warp(a, interp=cv2.INTER_LANCZOS4):
    return cv2.warpAffine(a, M, (OUT_W, OUT_H), flags=interp, borderValue=0)
box_a = a0.copy(); box_a[:, :BOX_X0] = 0; box_a[:, BOX_X1:] = 0           # jacks dores retires
pre = np.dstack([rgb * box_a[..., None], box_a])
o = warp(pre)
oa = np.clip(o[..., 3], 0, 1)
orgb = np.where(oa[..., None] > 1e-3, o[..., :3] / np.maximum(oa, 1e-3)[..., None], 0)
# leger rehaussement apres l'agrandissement (x1,49)
blur = cv2.GaussianBlur(orgb, (0, 0), 1.1)
orgb = np.clip(orgb + 0.45 * (orgb - blur), 0, 255)
def X(x): return (x - BOX_X0) * K + JP
def Y(y): return (y - BOX_Y0) * K

# ------------------------------------------------------------------ 4. embases jack du kit
def over(dst_rgb, dst_a, spr, x0, y0):
    h, w = spr.shape[:2]
    x0, y0 = int(round(x0)), int(round(y0))
    sa = spr[..., 3:4] / 255.0
    sl = (slice(max(0, y0), min(OUT_H, y0 + h)), slice(max(0, x0), min(OUT_W, x0 + w)))
    ss = (slice(sl[0].start - y0, sl[0].stop - y0), slice(sl[1].start - x0, sl[1].stop - x0))
    dst_rgb[sl] = dst_rgb[sl] * (1 - sa[ss]) + spr[ss][..., :3] * sa[ss]
    dst_a[sl] = np.maximum(dst_a[sl], sa[ss][..., 0])
jacks = {}
for key, side in (('out', -1), ('tap', -1), ('in', 1)):
    spr, w_, h_ = PC.jack_sprite(JACK_LEN, 1, side)
    jw, jh = spr.shape[1], spr.shape[0]
    yc = Y(JACK_Y[key])
    x0 = (JP + 2 - jw) if side < 0 else (OUT_W - JP - 2)
    over(orgb, oa, spr, x0, yc - jh / 2)
    jacks[key] = yc
FS_FLATS = 140.0 * K                                            # distance entre plats de l'ecrou (px)
fs_spr, fs_refl, FS_S, FS_BTN = PC.footswitch_sprite(FS_FLATS, 1, refl_colour=(255.0, 60.0, 40.0))
over(orgb, oa.copy(), fs_spr, X(FOOT[0]) - fs_spr.shape[1] / 2, Y(FOOT[1]) + FOOT_DY - fs_spr.shape[0] / 2)
Image.fromarray(fs_refl, 'RGBA').save(os.path.join(ROOT, 'fs_refl.png'))

# ------------------------------------------------------------------ 5. LED allumees (d'apres la lentille photo) + lumiere sur la facade
COLS = {'red': (np.array([255, 52, 34.]), np.array([255, 236, 225.])),
        'amber': (np.array([255, 150, 30.]), np.array([255, 244, 214.])),
        'green': (np.array([60, 235, 90.]), np.array([228, 255, 230.]))}
glows = {}
for name, (lx, ly, lr) in LEDS.items():
    cx, cy, R = X(lx), Y(ly), lr * K
    n = int(math.ceil(R * 2 + 6)); n += n % 2
    x0, y0 = int(round(cx - n / 2)), int(round(cy - n / 2))
    reg = orgb[y0:y0 + n, x0:x0 + n]
    yy2, xx2 = np.mgrid[0:n, 0:n].astype(np.float32) + 0.5
    d = np.hypot(xx2 + x0 - cx, yy2 + y0 - cy) / R
    body, core = COLS[name]
    # photo de LED allumee fournie (150 px, lentille centree en 74,6 / 74,7, rayon 47 px) : calee exactement sur la lentille
    phs = np.asarray(Image.open(os.path.join(ROOT, 'assets', 'kit', 'led_on_photo.png')).convert('RGBA')).astype(np.float32)
    pm_ = phs.copy(); pm_[..., :3] *= pm_[..., 3:4] / 255.0
    kk = R / 47.0
    Mz = np.float32([[kk, 0, (cx - x0) - 74.64 * kk], [0, kk, (cy - y0) - 74.67 * kk]])
    ph = cv2.warpAffine(pm_, Mz, (n, n), flags=cv2.INTER_AREA if kk < 1 else cv2.INTER_CUBIC, borderValue=0)
    ph[..., 3] = np.clip(ph[..., 3], 0, 255)
    ph[..., :3] = np.where(ph[..., 3:4] > 1, ph[..., :3] / np.maximum(ph[..., 3:4], 1) * 255.0, 0)
    Rr, Gg, Bb = ph[..., 0], ph[..., 1], ph[..., 2]
    if name == 'red':
        col = ph[..., :3]
    elif name == 'amber':
        col = np.dstack([np.clip(Rr * 1.02 + 0.2 * Gg, 0, 255), np.clip(0.55 * Rr + 0.45 * Gg, 0, 255), 0.10 * Rr + 0.7 * Bb])
    else:
        col = np.dstack([0.20 * Rr + 0.6 * Gg, np.clip(Rr * 0.95 + 0.2 * Gg, 0, 255), 0.25 * Rr + 0.5 * Bb])
    a = ph[..., 3] / 255.0
    Image.fromarray(np.dstack([np.clip(col, 0, 255), a * 255]).astype(np.uint8), 'RGBA').save(os.path.join(ROOT, f'led_on_{name}.png'))
    # LED eteinte (meme photo, lentille sombre teintee : on garde les alveoles et le relief), posee dans le fond
    lumv = ph[..., :3].mean(2) / 255.0
    det = lumv - cv2.GaussianBlur(lumv, (0, 0), max(1.0, R * 0.12))
    dark = {'red': np.array([58, 12, 10.]), 'amber': np.array([60, 38, 10.]), 'green': np.array([14, 44, 20.])}[name]
    offc = dark[None, None, :] * (0.55 + 0.9 * lumv)[..., None] + (det * 120)[..., None]
    hl = np.exp(-(((xx2 + x0 - cx + 0.38 * R) / (0.26 * R)) ** 2 + ((yy2 + y0 - cy + 0.40 * R) / (0.18 * R)) ** 2))
    offc = offc + (hl * 150)[..., None] * np.array([0.95, 0.93, 0.92])
    offc = offc * np.clip(0.7 + 0.3 * (1 - d), 0, 1)[..., None]
    # ombre de contact + ombre portee (lumiere en haut a gauche)
    ga_ = np.zeros((OUT_H, OUT_W), np.float32)
    yyF, xxF = np.mgrid[y0 - 8:y0 + n + 8, x0 - 8:x0 + n + 8].astype(np.float32)
    dsh = np.hypot(xxF - cx - R * 0.10, yyF - cy - R * 0.14) / R
    shd = np.clip((1.12 - dsh) / 0.18, 0, 1) * 0.65
    sl2 = (slice(y0 - 8, y0 + n + 8), slice(x0 - 8, x0 + n + 8))
    orgb[sl2] *= (1 - shd)[..., None]
    reg2 = orgb[y0:y0 + n, x0:x0 + n]
    orgb[y0:y0 + n, x0:x0 + n] = reg2 * (1 - a[..., None]) + np.clip(offc, 0, 255) * a[..., None]
    # lumiere recue par la facade (calque alpha : seule la lumiere ajoutee)
    GR = R * (7.5 if name == 'red' else 6.0)
    s = int(round(2 * GR))
    gx0, gy0 = int(round(cx - GR)), int(round(cy - GR))
    sl = (slice(max(0, gy0), gy0 + s), slice(max(0, gx0), gx0 + s))
    reg = orgb[sl].astype(np.float64)
    yy3, xx3 = np.mgrid[sl[0], sl[1]].astype(np.float64)
    dd = np.hypot(xx3 + 0.5 - cx, yy3 + 0.5 - cy)
    h1, h2 = R * 0.9, R * 3.2
    E = 1.0 * h1 ** 3 / (dd ** 2 + h1 ** 2) ** 1.5 + 0.20 * h2 ** 3 / (dd ** 2 + h2 ** 2) ** 1.5
    E *= np.clip((GR - dd) / (GR * 0.3), 0, 1) * (1.0 if name == "red" else 0.55)
    E[dd < R * 1.02] = 0
    lum2 = reg.mean(2, keepdims=True)
    c = body / 255.0
    lit = reg + (reg * 2.2 + 14.0 * np.clip(lum2 / 40.0, 0.3, 1.6)) * E[..., None] * c
    add = lit - reg
    ga = np.clip(np.abs(add).max(-1) / 12.0, 0, 1)
    grgb = np.where(ga[..., None] > 1e-3, reg + add / np.maximum(ga, 1e-3)[..., None], reg)
    Image.fromarray(np.dstack([np.clip(grgb, 0, 255), ga * 255]).astype(np.uint8), 'RGBA').save(os.path.join(ROOT, f'glow_{name}.png'))
    glows[name] = dict(lens=[x0 / 2, y0 / 2, n / 2, n / 2], glow=[sl[1].start / 2, sl[0].start / 2, (sl[1].stop - sl[1].start) / 2, (sl[0].stop - sl[0].start) / 2], c=[cx / 2, cy / 2], r=R / 2)

out = np.dstack([orgb, oa * 255]).astype(np.uint8)
Image.fromarray(out, 'RGBA').save(os.path.join(ROOT, 'background.png'), optimize=True)

# ------------------------------------------------------------------ 6. disposition (repere du plugin = image / 2)
U = lambda v: v / 2.0
lay = dict(
    frameW=OUT_W / 2, frameH=OUT_H / 2,
    box=[U(JP), 0, U(BOXW), OUT_H / 2],
    knobs={k: [U(X(x)), U(Y(y))] for k, (x, y) in KNOBS.items()}, knobR=U(KNOB_RP * K),
    leds=glows, foot=[U(X(FOOT[0])), U(Y(FOOT[1]) + FOOT_DY)], footR=U(58 * K),
    jacks={k: U(v) for k, v in jacks.items()},
    # inscriptions (centre, taille de capitale en unites, rotation)
    texts=[
        dict(s='SUSTAIN', x=U(X(655.0)), y=U(Y(249.5)), cap=U(17 * K), rot=0),
        dict(s='DELAY', x=U(X(1131.0)), y=U(Y(249.5)), cap=U(17 * K), rot=0, click='sync'),
        dict(s='VOLUME', x=U(X(899.5)), y=U(Y(317.0)), cap=U(18 * K), rot=0),
        dict(s='SYNC', x=U(X(1220.7)), y=U(Y(234.5)), cap=U(10 * K), rot=0),
        dict(s='OUT', x=U(X(552.5)), y=U(Y(604.0)), cap=U(14 * K), rot=-90),
        dict(s='IN', x=U(X(1246.0)), y=U(Y(603.5)), cap=U(14 * K), rot=90),
        dict(s='TAP', x=U(X(552.5)), y=U(Y(1030.0)), cap=U(14 * K), rot=-90),
        dict(s='DELAY', x=U(X(899.5)), y=U(Y(1037.5) + 40.0), cap=U(33 * K), rot=0),
    ],
    pushForAge=dict(cx=U(X(898.0)), cy=U(Y(176.8)), r=U(97.0 * K), cap=U(10.5 * K)),
    logo=dict(x=U(X(899.5)), y=U(Y(1098.5) + 40.0), w=U(205 * K)),
    presetRect=[U(X(900)) - 150.0, U(Y(790.0) + 20.0) - 15.0, 300.0, 30.0],
    ink=[228, 228, 230],
)
json.dump(lay, open(os.path.join(HERE, 'layout.json'), 'w'), indent=1)
print('ok', OUT_W, OUT_H, 'jack', JP, 'K', round(K, 4))
