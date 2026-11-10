"""Apercu du visuel Echoflex v2 (ce que dessinera le plugin) : fond + LED + potards + textes vectoriels + barre de presets.
python3 tools/preview.py out.png [knobs=0.5,0.5,0.5] [led=1] [age=0] [sync=0] [status="..."]"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
L = json.load(open(os.path.join(HERE, 'layout.json')))
args = dict(a.split('=', 1) for a in sys.argv[2:])
knobs = [float(v) for v in args.get('knobs', '0.5,0.5,0.5').split(',')]
S = 2.0                                   # pixels par unite (image 1800 px)
bg = Image.open(os.path.join(ROOT, 'background.png')).convert('RGBA')
W, H = bg.size
img = Image.new('RGBA', (W, H), (14, 15, 17, 255)); img.alpha_composite(bg)

def put(path, rect, alpha=1.0):
    im = Image.open(os.path.join(ROOT, path)).convert('RGBA')
    x, y, w, h = [v * S for v in rect]
    im = im.resize((max(1, round(w)), max(1, round(h))), Image.LANCZOS)
    if alpha < 1:
        a = np.asarray(im).astype(np.float32); a[..., 3] *= alpha; im = Image.fromarray(a.astype(np.uint8))
    img.alpha_composite(im, (round(x), round(y)))

for name, on in (('red', float(args.get('led', 1))), ('amber', float(args.get('age', 0))), ('green', float(args.get('sync', 0)))):
    if on > 0:
        g = L['leds'][name]
        put(f'glow_{name}.png', g['glow'], on)
        put(f'led_on_{name}.png', g['lens'], on)

# potards (filmstrip nette, 128 positions)
strip = Image.open(os.path.join(ROOT, 'knob_strip.png')).convert('RGBA')
fs = strip.width
for key, v in zip(('sustain', 'volume', 'delay'), knobs):
    f = int(round(v * 127))
    fr = strip.crop((0, f * fs, fs, (f + 1) * fs))
    R = L['knobR'] * 1.2 * S
    fr = fr.resize((round(2 * R), round(2 * R)), Image.LANCZOS)
    cx, cy = [c * S for c in L['knobs'][key]]
    img.alpha_composite(fr, (round(cx - R), round(cy - R)))

# textes vectoriels (Poppins Bold), rendus x4 puis reduits
BOLD = os.path.join(ROOT, 'Poppins-Bold.ttf'); MED = os.path.join(ROOT, 'Poppins-Medium.ttf')
ink = tuple(L['ink'])
SS = 4
def text_layer(s, cap_units, track=0.06, font=BOLD):
    em = cap_units / 0.70 * S * SS
    f = ImageFont.truetype(font, int(round(em)))
    adv = [f.getlength(c) for c in s]
    tw = int(sum(adv) + track * em * (len(s) - 1) + em)
    lay = Image.new('L', (tw, int(em * 1.6)), 0); d = ImageDraw.Draw(lay)
    x = em * 0.3
    for c, a in zip(s, adv):
        d.text((x, em * 0.2), c, font=f, fill=255); x += a + track * em
    return lay.crop(lay.getbbox())
def place(lay, cx, cy, rot=0):
    if rot: lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    lay = lay.resize((max(1, round(lay.width / SS)), max(1, round(lay.height / SS))), Image.LANCZOS)
    col = Image.new('RGBA', lay.size, ink + (255,)); col.putalpha(lay)
    img.alpha_composite(col, (round(cx * S - lay.width / 2), round(cy * S - lay.height / 2)))
for t in L['texts']:
    place(text_layer(t['s'], t['cap'], 0.08 if t['cap'] < 12 else 0.05), t['x'], t['y'], t['rot'])

# PUSH FOR AGE en arc sous VOLUME
p = L['pushForAge']
em = p['cap'] / 0.70 * S * SS
f = ImageFont.truetype(BOLD, int(round(em)))
s = 'PUSH FOR AGE'; track = 0.10 * em
adv = [f.getlength(c) + track for c in s]
r = p['r'] * S * SS
a = math.pi / 2 + (sum(adv) - track) / r / 2
big = Image.new('L', (W * SS // 2, H * SS // 2), 0)    # demi-image (zone du potard) pour la memoire
ox, oy = p['cx'] * S * SS - big.width / 2, p['cy'] * S * SS - big.height / 4
for c, w in zip(s, adv):
    if c != ' ':
        g = Image.new('L', (int(em * 2),) * 2, 0); ImageDraw.Draw(g).text((em * 0.4, em * 0.2), c, font=f, fill=255); g = g.crop(g.getbbox())
        mid = a - (f.getlength(c) / 2) / r
        g = g.rotate(-(math.degrees(mid) - 90), expand=True, resample=Image.BICUBIC)
        px = p['cx'] * S * SS + r * math.cos(mid) - ox; py = p['cy'] * S * SS + r * math.sin(mid) - oy
        big.paste(g, (round(px - g.width / 2), round(py - g.height / 2)), g)
    a -= w / r
small = big.resize((big.width // SS, big.height // SS), Image.LANCZOS)
col = Image.new('RGBA', small.size, ink + (255,)); col.putalpha(small)
img.alpha_composite(col, (round(ox / SS), round(oy / SS)))

# logo NINE HANDS | DSP (SVG rendu en PNG blanc)
lg = Image.open('/root/src/v3/logo.png').convert('RGBA')
lw = L['logo']['w'] * S; lh = lw * lg.height / lg.width
lg = lg.resize((round(lw), round(lh)), Image.LANCZOS)
img.alpha_composite(lg, (round(L['logo']['x'] * S - lw / 2), round(L['logo']['y'] * S - lh / 2)))

# barre de presets (ou ligne d'etat) : style Screamer
x, y, w, h = L['presetRect']
cx = L['knobs']['volume'][0]
x = cx - w / 2
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
R = h / 2 * S
d.rounded_rectangle((x * S, y * S, (x + w) * S, (y + h) * S), R, fill=(6, 6, 8, 205), outline=(120, 124, 130, 120), width=2)
status = args.get('status')
fm = ImageFont.truetype(MED, int(13.0 * S))
txt = status if status else 'P1  Noon (Manual Start)'
tw = d.textlength(txt, font=fm)
d.text(((x + w / 2) * S - tw / 2, (y + h / 2) * S - 13.0 * S * 0.62), txt, font=fm, fill=(232, 232, 236, 255))
if not status:
    for sgn, ax in ((-1, x + 14), (1, x + w - 14)):
        tri = [(ax * S - sgn * 5 * S, (y + h / 2 - 6) * S), (ax * S - sgn * 5 * S, (y + h / 2 + 6) * S), (ax * S + sgn * 5 * S, (y + h / 2) * S)]
        d.polygon(tri, fill=(200, 200, 205, 255))
img.alpha_composite(ov)
img.save(sys.argv[1])
print('ok', img.size)
