#!/usr/bin/env python3
# Filmstrip du potard ECHOFLEX construit a partir de la PHOTO du visuel :
#  - chapeau et eclairage de la jupe : releves sur la photo (eclairage fixe, ne tourne pas)
#  - motif des dents : extrait de la photo, il tourne avec la valeur sous l'eclairage fixe
#  - aileron + trait blanc : redessines a chaque angle avec la meme lumiere (haut-gauche)
import numpy as np, math, sys, os
from PIL import Image
from scipy import ndimage as ndi

SRC, OUT = sys.argv[1], sys.argv[2]
FR = int(sys.argv[3]) if len(sys.argv) > 3 else 288
CX, CY, RP = (float(v) for v in os.environ.get('KNOB', '898.0,176.8,80.5').split(','))   # potard VOLUME du visuel (centre, rayon exterieur des dents, px)
NF, SS, HALF = 128, 2, 1.20

photo = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)

# ------------------------------------------------------------------------------
# 1. Deroulement polaire de la photo
# ------------------------------------------------------------------------------
NR, NA = 360, 2880
rr = np.linspace(0, 1.0, NR, dtype=np.float32)
aa = np.linspace(-math.pi, math.pi, NA, endpoint=False, dtype=np.float32)
RR, AA = np.meshgrid(rr, aa, indexing="ij")
px = CX + RR * RP * np.cos(AA)
py = CY + RR * RP * np.sin(AA)
polar = np.stack([ndi.map_coordinates(photo[..., c], [py - 0.5, px - 0.5], order=1) for c in range(3)], -1)

# masque d'exclusion : aileron (pointe en haut) + son ombre a droite
X = RR * np.cos(AA); Y = RR * np.sin(AA)
u = -Y                 # le long du pointeur (vers le haut)
v = X
U0, U1 = -0.80, 0.88
tt = np.clip((u - U0) / (U1 - U0), 0, 1)
w = 0.235 + (0.146 - 0.235) * tt
excl = (u > U0 - 0.06) & (u < U1 + 0.04) & (v > -w - 0.07) & (v < w + 0.20)

# ------------------------------------------------------------------------------
# 2. Ajustement : chapeau (r < 0.80) et enveloppe d'eclairage de la jupe (series de Fourier en angle)
# ------------------------------------------------------------------------------
def fourier_fit(rows, order):
    """pour chaque rayon : moindres carres sur les angles non exclus -> profil lisse."""
    out = np.zeros((len(rows), NA, 3), np.float32)
    basis = [np.ones(NA)]
    for k in range(1, order + 1):
        basis += [np.cos(k * aa), np.sin(k * aa)]
    Bm = np.stack(basis, 1)
    for j, ri in enumerate(rows):
        ok = ~excl[ri]
        for c in range(3):
            coef, *_ = np.linalg.lstsq(Bm[ok], polar[ri, ok, c], rcond=None)
            out[j, :, c] = Bm @ coef
    return out

# lissage radial avant ajustement
polar_s = ndi.gaussian_filter(polar, (2.0, 0, 0))
polar_bak = polar
polar = polar_s
# modele global du chapeau : sum_k (a + b r + c r^2) * base_k(angle), ajuste sur tous les pixels visibles
def cap_basis(rv, av):
    cols = []
    for fa in [np.ones_like(av), np.cos(av), np.sin(av), np.cos(2 * av), np.sin(2 * av), np.cos(3 * av), np.sin(3 * av)]:
        for p in range(3):
            cols.append(fa * rv ** p)
    return np.stack(cols, -1)
sel = (~excl) & (RR > 0.12) & (RR < 0.78)
Bsel = cap_basis(RR[sel], AA[sel])
cap_fit = np.zeros((NR, NA, 3), np.float32)
Ball = cap_basis(RR.ravel(), AA.ravel())
for c in range(3):
    coef, *_ = np.linalg.lstsq(Bsel, polar[..., c][sel], rcond=None)
    cap_fit[..., c] = (Ball @ coef).reshape(NR, NA)
polar = polar_bak

# dents : enveloppe = moyenne glissante sur ~3 periodes (ignore les zones exclues)
r_t0 = 0.80
prof = polar[int(0.90 * NR)].mean(1)
spec = np.abs(np.fft.rfft(prof - prof.mean()))
ntooth = int(np.argmax(spec[30:80]) + 30)
print("nombre de dents detecte :", ntooth)
period = NA / ntooth
win = int(round(period * 3))
valid = (~excl).astype(np.float32)
num = ndi.uniform_filter1d(polar * valid[..., None], win, axis=1, mode="wrap")
den = ndi.uniform_filter1d(valid, win, axis=1, mode="wrap")[..., None]
env = num / np.maximum(den, 1e-3)
# l'enveloppe la ou c'est exclu : ajustement de Fourier
env_fit = fourier_fit(np.arange(NR), 5)
env = np.where(den > 0.6, env, env_fit)
env = ndi.gaussian_filter(env, (1.5, 6, 0), mode=("nearest", "wrap", "nearest"))
pattern = polar / np.maximum(env, 4.0)
# combler le motif sous la pointe de l'aileron avec des dents voisines (decalage d'un nombre entier de dents)
shift = int(round(period * 9))
for _ in range(2):
    src = np.roll(pattern, -shift, axis=1)
    bad = excl[..., None] | (np.roll(excl, -shift, axis=1)[..., None] & False)
    pattern = np.where(excl[..., None], src, pattern)
pattern = np.clip(pattern, 0.0, 4.0)

# ------------------------------------------------------------------------------
# 3. Rendu cartesien (sur-echantillonne)
# ------------------------------------------------------------------------------
N = FR * SS
R = N / 2 / HALF
ky, kx = np.mgrid[0:N, 0:N].astype(np.float32) + 0.5
Xc = (kx - N / 2) / R
Yc = (ky - N / 2) / R
rc = np.hypot(Xc, Yc)
ac = np.arctan2(Yc, Xc)
ri = np.clip(rc, 0, 0.999) * (NR - 1)
ai = (ac + math.pi) / (2 * math.pi) * NA

def sample(arr, ri_, ai_):
    return np.stack([ndi.map_coordinates(arr[..., c], [ri_, ai_], order=1, mode="grid-wrap") for c in range(3)], -1)

cap_img = sample(cap_fit, ri, ai)
env_img = sample(env, ri, ai)
lathe = ndi.gaussian_filter1d(np.random.default_rng(9).standard_normal(8192).astype(np.float32), 1.5)
lathe_img = lathe[np.clip((rc * 6000).astype(int), 0, 8191)] * 2.2 * (0.4 + np.abs(np.cos(ac + 2.356)))
grain = ndi.gaussian_filter(np.random.default_rng(5).standard_normal((N, N)).astype(np.float32), 0.8) * 1.6

l2 = np.array([-0.7071, -0.7071], np.float32)
L3 = np.array([-0.66, -0.66, 0.36], np.float32); L3 /= np.linalg.norm(L3)
H3 = L3 + np.array([0, 0, 1.0], np.float32); H3 /= np.linalg.norm(H3)
mask = np.clip((1.0 - rc) * R + 0.5, 0, 1)
LT = np.array([-0.62, -0.62, 0.48], np.float32); LT /= np.linalg.norm(LT)
HT = LT + np.array([0, 0, 1.0], np.float32); HT /= np.linalg.norm(HT)
TOOTH_SLOPE, TOOTH_AMB, TOOTH_DIF, TOOTH_SPEC = float(os.environ.get("TS", 1.3)), 4.0, float(os.environ.get("TD", 165)), 30.0
TP = float(os.environ.get("TP", 3.4))
zone_t = np.clip((rc - r_t0) * R + 0.5, 0, 1)

def tooth_shade(theta, dph):
    tph = (((ac - theta) * ntooth / (2 * math.pi) + dph) % 1.0).astype(np.float32)
    # profil : sommet plat / flanc descendant / fond / flanc montant
    dhdt = np.where((tph > 0.30) & (tph < 0.50), -1.0, np.where((tph > 0.60) & (tph < 0.80), 1.0, 0.0)).astype(np.float32)
    hgt_t = np.where(tph <= 0.40, 1.0, np.where(tph < 0.55, 1 - (tph - 0.40) / 0.15, np.where(tph < 0.70, 0.0, np.where(tph < 0.85, (tph - 0.70) / 0.15, 1.0))))
    groove_on = np.clip((rc - (r_t0 + 0.025)) / 0.02, 0, 1)          # les rainures commencent un peu apres le bord du chapeau
    slope = TOOTH_SLOPE * dhdt * groove_on
    tx, ty = -np.sin(ac), np.cos(ac)                                  # tangente
    rx, ry = np.cos(ac), np.sin(ac)                                   # radiale
    ch_out = np.clip((rc - 0.955) / 0.045, 0, 1) * 1.1                # chanfrein exterieur
    ch_in = np.clip(1 - np.abs(rc - (r_t0 + 0.01)) / 0.015, 0, 1) * -0.6   # petit epaulement interieur
    nxv = -slope * tx + (ch_out + ch_in) * rx
    nyv = -slope * ty + (ch_out + ch_in) * ry
    nzv = np.ones_like(nxv)
    nn = np.sqrt(nxv ** 2 + nyv ** 2 + nzv ** 2)
    nxv, nyv, nzv = nxv / nn, nyv / nn, nzv / nn
    ndl_t = np.clip(nxv * LT[0] + nyv * LT[1] + nzv * LT[2], 0, 1)
    ndh_t = np.clip(nxv * HT[0] + nyv * HT[1] + nzv * HT[2], 0, 1)
    floor_dark = np.where((tph > 0.50) & (tph < 0.60) & (groove_on > 0.5), 0.35, 1.0)  # fond de rainure : occlusion
    tb = (TOOTH_AMB + TOOTH_DIF * ndl_t ** TP) * floor_dark + TOOTH_SPEC * ndh_t ** 28
    tb = tb * (0.45 + 0.55 * np.clip((1.0 - rc) / 0.012, 0, 1))      # bord exterieur sombre
    return tb

BLUR = float(os.environ.get('BLUR', 0))
TEST = os.environ.get('TEST')
ONLY = os.environ.get('ONLY')
frames = []
for i in ([int(x) for x in ONLY.split(',')] if ONLY else ([20, 64, 110] if TEST else range(NF))):
    pos = i / (NF - 1)
    a = math.pi * 1.25 + pos * math.pi * 1.5             # angle JUCE
    theta = a - 2 * math.pi                              # rotation par rapport a la photo (pointeur en haut)
    d = np.array([math.sin(a), -math.cos(a)], np.float32)
    pdir = np.array([-d[1], d[0]], np.float32)

    # dents : motif tourne, eclairage fixe
    # dents : geometrie qui tourne, eclairee par la lumiere fixe (haut-gauche)
    # flou de mouvement (comme le GIF de reference) : moyenne de l'ombrage sur une fraction de dent de part et d'autre
    if BLUR > 0:
        if os.environ.get('UNIFORM'):      # flou complet : moyenne exacte sur une dent entiere (invariant par rotation)
            offs = (np.arange(16) + 0.5) / 16 - 0.5
            w8 = np.full(16, 1 / 16)
        else:
            offs = np.linspace(-BLUR / 2, BLUR / 2, 15)
            w8 = np.exp(-0.5 * (offs / (BLUR / 4 + 1e-6)) ** 2); w8 /= w8.sum()
        tb = sum(wk * tooth_shade(theta, o) for wk, o in zip(w8, offs))
    else:
        tb = tooth_shade(theta, 0.0)
    teeth = np.stack([tb * 0.97, tb * 0.985, tb * 1.06], -1)
    img = cap_img * (1 - zone_t[..., None]) + teeth * zone_t[..., None]
    img = img + grain[..., None]
    img = img + (lathe_img * (1 - zone_t))[..., None]

    # aileron
    uu = Xc * d[0] + Yc * d[1]
    vv = Xc * pdir[0] + Yc * pdir[1]
    t_ = np.clip((uu - U0) / (U1 - U0), 0, 1)
    ww = 0.235 + (0.146 - 0.235) * t_
    fin = (uu > U0) & (uu < U1) & (np.abs(vv) < ww)
    fin &= ~((uu < U0 + ww) & (np.hypot(uu - (U0 + ww), vv) > ww))      # extremite arriere arrondie
    fin_f = ndi.gaussian_filter(fin.astype(np.float32), 0.6)

    # ombre de l'aileron sur le chapeau (opposee a la lumiere)
    sh = np.zeros_like(fin_f)
    for k in range(1, 10):
        off = k * 0.011 * R
        sh = np.maximum(sh, ndi.shift(fin_f, (-l2[1] * off, -l2[0] * off), order=1) * (1 - k / 12))
    sh = ndi.gaussian_filter(sh, R * 0.012)
    img = img * (1 - 0.70 * sh * (1 - fin_f))[..., None]

    # profil en travers de l'aileron : facettes arrondies
    vn = np.clip(vv / np.maximum(ww, 1e-3), -1, 1)
    slope = np.clip((np.abs(vn) - 0.28) / 0.30, 0, 1) ** 0.7          # 0 sur le dessus, 1 sur les flancs
    sgn = np.sign(vn)
    nx = sgn * pdir[0] * slope * 0.85
    ny = sgn * pdir[1] * slope * 0.85
    nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0.05, 1))
    ndl = np.clip(nx * L3[0] + ny * L3[1] + nz * L3[2], 0, 1)
    ndh = np.clip(nx * H3[0] + ny * H3[1] + nz * H3[2], 0, 1)
    fb = 5 + 92 * ndl + 70 * ndh ** 22
    fb = fb * (0.88 + 0.22 * (1 - t_))                                # un peu plus clair a l'arriere
    # extremite arriere biseautee
    endz = np.clip((U0 + 0.06 - uu) / 0.06, 0, 1) * 0.6
    end_b = 5 + 70 * max(0.0, float(-d @ l2))
    fb = fb * (1 - endz) + end_b * endz
    fin_rgb = np.stack([fb * 0.97, fb * 0.985, fb * 1.06], -1) + grain[..., None] * 0.6
    img = img * (1 - fin_f[..., None]) + fin_rgb * fin_f[..., None]

    # trait blanc poli (insert)
    line = (np.abs(vv) < 0.050) & (uu > 0.09) & (uu < 0.83)
    lf = ndi.gaussian_filter(line.astype(np.float32), 0.7)
    lv = 200 + 26 * np.clip(1 - np.abs(vv + 0.01) / 0.05, 0, 1) - 25 * np.clip(1 - (uu - 0.09) / 0.15, 0, 1)
    line_rgb = np.stack([lv, lv * 0.995, lv * 1.01], -1)
    img = img * (1 - lf[..., None]) + line_rgb * lf[..., None]

    img = np.clip(img / 255.0, 0, 1)
    ao = ndi.gaussian_filter(ndi.shift(mask, (0.02 * R, 0.02 * R), order=1), 0.03 * R)
    alpha = np.clip(mask + 0.35 * ao * (1 - mask), 0, 1)
    pm = np.dstack([img * mask[..., None], alpha])
    small = pm.reshape(FR, SS, FR, SS, 4).mean(axis=(1, 3))
    a_ = small[..., 3:4]
    un = np.where(a_ > 1e-5, small[..., :3] / np.maximum(a_, 1e-5), 0)
    frames.append(np.dstack([np.clip(un, 0, 1), a_]))
    if i % 32 == 0:
        print("frame", i, flush=True)

strip = np.concatenate(frames, 0)
Image.fromarray((strip * 255 + 0.5).astype(np.uint8), "RGBA").save(OUT, optimize=True)
print("ok", strip.shape)
