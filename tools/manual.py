# ECHOFLEX (NINE HANDS | DSP) - notice PDF en francais, illustree avec le rendu reel du plugin.
# Usage : python3 tools/manual.py <dossier des captures> <fichier PDF de sortie>
#   captures (2 x 958 px de haut) produites par le banc de rendu du plugin : ech_main.png, ech_bypass.png, ech_age.png,
#   ech_ageedit.png, ech_statusline.png, ech_sync.png, ech_tap.png, ech_blur.png
import os, sys, json, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, PageTemplate, NextPageTemplate, Frame, Paragraph, Spacer, Image as RLImage,
                                Table, TableStyle, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS, OUT = sys.argv[1], sys.argv[2]
VERSION = "2.0.0"
import tempfile
TMP = tempfile.mkdtemp(prefix="echoflex_notice_")      # images intermediaires (hors du depot)
FONTS = os.path.join(ROOT, "tools", "fonts")
CHARTS = os.path.join(ROOT, "tools", "manual_assets")

for n, f in (("Pop", "Poppins-Regular"), ("PopL", "Poppins-Light"), ("PopM", "Poppins-Medium"), ("PopB", "Poppins-Bold"),
             ("Title", "BarlowCondensed-ExtraBold"), ("DjV", "DejaVuSans")):
    pdfmetrics.registerFont(TTFont(n, os.path.join(FONTS, f + ".ttf")))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("Pop", normal="Pop", bold="PopB", italic="PopL", boldItalic="PopB")    # <b> = Poppins Bold

ACC = colors.HexColor("#D8261A"); ACC_L = colors.HexColor("#FF7A62")      # rouge de la LED d'Echoflex
DARK = colors.HexColor("#1B1C1F"); GREY = colors.HexColor("#63666C"); LIGHT = colors.HexColor("#F3F1F0")
LAY = json.load(open(os.path.join(ROOT, "tools", "design", "layout.json")))
LOGO_PNG = os.path.join(TMP, "nine_hands_logo_blanc.png")
if shutil.which("rsvg-convert"):
    subprocess.run(["rsvg-convert", "-w", "1200", os.path.join(ROOT, "NineHandsLogo.svg"), "-o", LOGO_PNG], check=True)
else:   # sans librsvg : rendu du SVG par Chromium (Playwright)
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "svg2png.py"), os.path.join(ROOT, "NineHandsLogo.svg"), LOGO_PNG, "1200"], check=True)

# ------------------------------------------------------------------ illustrations (rendu reel du plugin)
def shot(name): return Image.open(os.path.join(SHOTS, name)).convert("RGB")
src = shot("ech_main.png")
k = src.height / 900.0                              # repere du plugin : 623 x 900 unites (fond 1246 x 1800 / 2)
def crop_u(im, box): return im.crop(tuple(int(v * k) for v in box))
GAP = 18
def strip(parts, path, vertical=False):
    if vertical:
        s = Image.new("RGB", (max(p.width for p in parts), sum(p.height for p in parts) + GAP * (len(parts) - 1)), (255, 255, 255)); y = 0
        for p in parts: s.paste(p, (0, y)); y += p.height + GAP
    else:
        s = Image.new("RGB", (sum(p.width for p in parts) + GAP * (len(parts) - 1), max(p.height for p in parts)), (255, 255, 255)); x = 0
        for p in parts: s.paste(p, (x, 0)); x += p.width + GAP
    p = os.path.join(TMP, path); s.save(p); return p

KN = LAY["knobs"]; LE = LAY["leds"]; FOOT = LAY["foot"]; J = LAY["jacks"]
marks = [  # numero, x, y (unites du plugin)
    (1, KN["volume"][0] + 82, KN["volume"][1] - 58), (2, KN["sustain"][0] - 70, KN["sustain"][1] + 60), (3, KN["delay"][0] + 70, KN["delay"][1] + 60),
    (4, LE["amber"]["c"][0] + 36, LE["amber"]["c"][1]), (5, LE["green"]["c"][0] + 30, LE["green"]["c"][1] - 24),
    (6, LE["red"]["c"][0] + 40, LE["red"]["c"][1] - 6), (7, 148, 593), (8, FOOT[0] + 72, FOOT[1]),
    (9, 46, J["tap"] - 52), (10, 46, J["out"] - 52), (11, 580, J["in"] - 52)]
ann = src.copy(); dr = ImageDraw.Draw(ann)
fnt = ImageFont.truetype(os.path.join(FONTS, "Poppins-Bold.ttf"), 34)
for n, x, y in marks:
    cx, cy, r = x * k, y * k, 27
    dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255), outline=(216, 38, 26), width=5)
    dr.text((cx, cy + 1), str(n), font=fnt, fill=(27, 28, 31), anchor="mm")
annotated = os.path.join(TMP, "ech_annotated.png"); ann.save(annotated)

on_img = strip([crop_u(src, (205, 470, 420, 735)), crop_u(shot("ech_bypass.png"), (205, 470, 420, 735))], "ech_onoff.png")
age_box = (225, 48, 398, 300)
age_img = strip([crop_u(src, age_box), crop_u(shot("ech_age.png"), age_box)], "ech_age_strip.png")
sync_box = (412, 150, 600, 340)
sync_img = strip([crop_u(src, sync_box), crop_u(shot("ech_sync.png"), sync_box)], "ech_sync_strip.png")
tap_img = strip([crop_u(shot("ech_tap.png"), (0, 560, 470, 800))], "ech_tap_crop.png")
pr = (LAY["knobs"]["volume"][0] - 150 - 8, LAY["presetRect"][1] - 8, LAY["knobs"]["volume"][0] + 150 + 8, LAY["presetRect"][1] + 38)
bar_img = strip([crop_u(shot(n), pr) for n in ("ech_main.png", "ech_statusline.png", "ech_sync.png", "ech_ageedit.png")], "ech_bar.png", vertical=True)
def kbox(c, r=68): return (c[0] - r, c[1] - r, c[0] + r, c[1] + r)
blur_img = strip([crop_u(src, kbox(KN["delay"])), crop_u(shot("ech_blur.png"), kbox(KN["sustain"])), crop_u(shot("ech_blur.png"), kbox(KN["delay"]))], "ech_blur_strip.png")

# couverture : pedale detouree avec le canal alpha du fond (boitier + jacks), reflet au sol, halo rouge tres doux
bg_a = Image.open(os.path.join(ROOT, "background.png")).split()[3].resize(src.size, Image.LANCZOS)
cut = Image.new("RGBA", src.size, (0, 0, 0, 0)); cut.paste(src, (0, 0), bg_a)
cut = cut.crop(cut.getbbox())
cw, ch = cut.size
pad = int(cw * 0.16)
canvas = Image.new("RGBA", (cw + 2 * pad, int(ch * 1.30) + pad), (0, 0, 0, 255))
yy, xx = np.mgrid[0:canvas.height, 0:canvas.width].astype(np.float64)
gcx, gcy = canvas.width / 2, pad + ch * 0.45
glow = np.exp(-(((xx - gcx) / (cw * 0.62)) ** 2 + ((yy - gcy) / (ch * 0.48)) ** 2)) * 30
edge = np.clip(np.minimum.reduce([xx, canvas.width - 1 - xx, yy, canvas.height - 1 - yy]) / (pad * 0.9), 0, 1)
glow *= edge ** 2
halo = np.dstack([glow * 0.95, glow * 0.22, glow * 0.16, np.full_like(glow, 255)]).astype(np.uint8)
canvas = Image.alpha_composite(canvas, Image.fromarray(halo, "RGBA"))
refl = cut.transpose(Image.FLIP_TOP_BOTTOM)
ra = np.array(refl).astype(np.float64)
fade = np.clip(1 - np.arange(refl.height) / (refl.height * 0.22), 0, 1) ** 1.6 * 0.22
ra[..., 3] *= fade[:, None]
canvas.alpha_composite(Image.fromarray(ra.astype(np.uint8), "RGBA"), (pad, pad + ch + 6))
canvas.alpha_composite(cut, (pad, pad))
canvas = canvas.crop((0, 0, canvas.width, pad + int(ch * 1.20)))
cover = os.path.join(TMP, "ech_cover_cutout.png"); canvas.convert("RGB").save(cover)

def img(path, width):
    im = Image.open(path); return RLImage(path, width=width, height=width * im.height / im.width)

# ------------------------------------------------------------------ styles
st = {
    "h1": ParagraphStyle("h1", fontName="PopB", fontSize=20, leading=24, textColor=ACC, spaceAfter=8, spaceBefore=4, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="PopM", fontSize=13, leading=17, textColor=DARK, spaceAfter=4, spaceBefore=10, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Pop", fontSize=9.6, leading=14, textColor=DARK, spaceAfter=5),
    "tip": ParagraphStyle("tip", fontName="Pop", fontSize=9.0, leading=12.4, textColor=DARK, spaceAfter=3),
    "small": ParagraphStyle("small", fontName="Pop", fontSize=8.2, leading=11.5, textColor=GREY, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="Pop", fontSize=8.4, leading=11, textColor=DARK),
    "cellb": ParagraphStyle("cellb", fontName="PopM", fontSize=8.4, leading=11, textColor=DARK),
    "cells": ParagraphStyle("cells", fontName="Pop", fontSize=7.6, leading=9.6, textColor=DARK),
    "cellbs": ParagraphStyle("cellbs", fontName="PopM", fontSize=7.6, leading=9.6, textColor=DARK),
}
def P(t, s="p"): return Paragraph(t, st[s])
def bullets(items, s="p"): return [P("&bull;&nbsp;&nbsp;" + i, s) for i in items]
def table(rows, widths, header=True, small=False):
    data = [[P(c, ("cellbs" if small else "cellb") if (header and r == 0) else ("cells" if small else "cell")) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#E0DCDA")),
             ("TOPPADDING", (0, 0), (-1, -1), 2 if small else 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 2 if small else 3)]
    if header: style += [("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACC)]
    t.setStyle(TableStyle(style)); return t
def steps(items):
    rows = [[P("<font color='#D8261A'><b>%d</b></font>" % (i + 1)), [P("<b>%s</b>" % h), P(x)]] for i, (h, x) in enumerate(items)]
    t = Table(rows, colWidths=[8 * mm, None])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    return t
W = A4[0] - 36 * mm
def side(a, b, wa):
    t = Table([[a, b]], colWidths=[wa, W - wa])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 8)]))
    return t
def mono(s): return "<font name='PopM'>" + s + "</font>"
AR = "<font name='DjV'>&#9664;</font> <font name='DjV'>&#9654;</font>"
def num(v): return ("%.1f" % v).replace(".", ",")

# ------------------------------------------------------------------ contenu
FACTORY = [("Noon (Manual Start)", 5.0, 5.0, 5.0, 5.0, 0), ("Fifties Slapback", 2.1, 1.2, 6.5, 4.0, 1), ("Rockabilly Double", 2.8, 3.5, 5.5, 3.0, 1),
           ("Surf Echo", 3.6, 4.5, 6.5, 2.0, 0), ("Hot Lead 400", 7.3, 4.8, 5.0, 2.5, 1), ("Fresh Tape Wash", 8.6, 6.5, 6.0, 0.0, 0),
           ("Worn Cartridge", 6.2, 5.5, 6.5, 10.0, 1), ("Dark Ambience", 9.3, 7.6, 6.0, 8.0, 1), ("Dub Spiral", 7.6, 8.7, 7.0, 6.0, 1),
           ("Runaway Oscillation", 4.2, 10.0, 7.0, 5.0, 1)]
PDESC = ["Tous les potards à midi, bande neuve : le point de départ conseillé par le manuel de la pédale.",
         "Une seule répétition courte, un peu usée : rock'n'roll et voix rockabilly des années 50.",
         "Un double écho serré pour les rythmiques et le chicken picking.",
         "Écho clair d'environ 157 ms avec quelques répétitions : son surf, ressort et bande.",
         "Le réglage solo classique : un écho chaud vers 390 ms glissé sous le chorus.",
         "Longue nappe claire pour les accords et les swells ambiants.",
         "AGE à 10 : répétitions sombres, ondulantes et saturées d'une vieille cartouche.",
         "Longues traînées très sombres pour un jeu lent et atmosphérique.",
         "Des répétitions qui reviennent sans cesse : jouez une courte phrase et jouez avec SUSTAIN et DELAY.",
         "SUSTAIN au maximum : l'écho oscille tout seul. Tournez DELAY pour les sirènes ; baissez SUSTAIN pour l'arrêter."]
def delay_ms(d): return 65.0 * (750.0 / 65.0) ** (d / 10.0)

f = [NextPageTemplate("p"), Spacer(1, 1), PageBreak()]
# 1. Presentation
f.append(P("1. Présentation", "h1"))
f.append(P("Echoflex est un plug-in VST3 à usage personnel de NINE HANDS | DSP qui reproduit la pédale <b>Dunlop EP103 Echoplex&reg; Delay</b>, elle-même hommage compact à l'écho à bande <b>Maestro Echoplex EP-3</b>. Echoplex est une marque de son propriétaire ; Echoflex est un hommage indépendant, sans lien avec elle."))
f.append(P("La légende", "h2"))
f.append(P("Le Maestro Echoplex EP-3 a été fabriqué de 1970 à 1991. À l'intérieur, une boucle de bande dans une cartouche amovible défile devant une tête d'effacement, une tête d'enregistrement et une tête de lecture ; l'écart entre les têtes et la vitesse de la bande fixent le retard. Son préampli à transistors est devenu célèbre à lui seul pour sa façon d'adoucir et d'épaissir une guitare. L'EP-3 était aussi gros, lourd et capricieux : bande usée, têtes sales et galet presseur fatigué faisaient onduler l'écho et l'assombrissaient, et beaucoup de guitaristes adoraient justement ces défauts."))
f.append(P("La pédale et son caractère sonore", "h2"))
f.append(P("La Dunlop EP103 met ce son dans un petit boîtier : un écho à bande numérique avec un trajet direct entièrement analogique, trois potards (DELAY, SUSTAIN, VOLUME), un mode AGE caché sous le potard VOLUME, une prise tap tempo et quelques options de démarrage. Par défaut, elle sonne comme une bande neuve fraîchement réglée : répétitions claires et chaudes, pleurage et scintillement discrets, préampli EP101 qui colore uniquement les échos. L'AGE la transforme en vieille machine bien usée."))
f.append(P("Ce que reproduit Echoflex", "h2"))
f += bullets(["Les trois mêmes réglages, plages et sensations : 65 à 750 ms, peu de répétitions sur la première moitié de SUSTAIN puis une montée presque exponentielle jusqu'à l'auto-oscillation, VOLUME qui règle uniquement l'écho.",
              "Le mode AGE exactement comme sur la pédale : clic sur VOLUME pour l'activer ou le couper, maintien 2 secondes pour le régler, nouveau clic pour verrouiller.",
              "L'inertie du moteur de bande : tourner DELAY fait glisser la hauteur des répétitions comme sur un vrai écho à bande.",
              "Le tap tempo jusqu'à 4 secondes (clic sur la prise TAP) et la synchro sur le tempo de Reaper ou de n'importe quel DAW (LED SYNC).",
              "Les réglages de démarrage (trails, 100 % wet, mono ou stéréo), 10 presets d'usine, 9 presets utilisateur, MIDI Learn et automation."])
# 2. Installation
f.append(P("2. Installation", "h1"))
f.append(P("Sur la page GitHub d'Echoflex (github.com/Nine-Hands-Dsp/EchoFlex), cliquez sur le bouton <b>Windows</b> ou <b>macOS</b> : vous obtenez " + mono("Echoflex-VST3-Windows.zip") + " ou " + mono("Echoflex-VST3-macOS.zip") + ", toujours la dernière version."))
f += bullets(["<b>Windows 11</b> : dézipper puis copier " + mono("Echoflex.vst3") + " dans " + mono("C:\\Program Files\\Common Files\\VST3\\") + ".",
              "<b>macOS</b> : dézipper puis copier " + mono("Echoflex.vst3") + " dans " + mono("~/Library/Audio/Plug-Ins/VST3/") + ". Le plug-in est signé ad hoc ; si macOS le bloque, l'autoriser dans Réglages Système &rsaquo; Confidentialité et sécurité.",
              "<b>Reaper</b> : Options &rsaquo; Preferences &rsaquo; Plug-ins &rsaquo; VST &rsaquo; <b>Re-scan</b>. Echoflex apparaît sous le nom <b>Echoflex (NINE HANDS | DSP)</b> dans la catégorie Delay. Une nouvelle version remplace simplement l'ancienne : vos projets et presets se rechargent à l'identique."])
f.append(PageBreak())
# 3. Vue d'ensemble
f.append(P("3. Vue d'ensemble", "h1"))
ov_rows = [["N°", "Élément", "Rôle"],
           ["1", "VOLUME / PUSH FOR AGE", "Niveau de l'écho. Clic : AGE on/off. Maintien 2 s : réglage de l'AGE."],
           ["2", "SUSTAIN", "Nombre de répétitions, jusqu'à l'auto-oscillation."],
           ["3", "DELAY", "Temps de retard, de 65 à 750 ms (valeur de note en SYNC)."],
           ["4", "LED AGE (ambre)", "Allumée quand l'AGE est actif, clignote pendant le réglage."],
           ["5", "DELAY / SYNC (LED verte)", "Clic : delay calé sur le tempo du DAW ; molette ou clic droit : valeur de note."],
           ["6", "LED d'effet (rouge)", "Effet actif ; sa lueur respire avec les répétitions."],
           ["7", "Barre de presets / ligne d'état", AR + " preset précédent / suivant, clic sur le nom : menu des presets. Pendant un réglage : sa valeur."],
           ["8", "Footswitch", "Active ou coupe l'effet."],
           ["9", "Prise TAP", "Cliquer en rythme pour taper un tempo (jusqu'à 4 s)."],
           ["10", "OUT", "Sortie du plug-in."], ["11", "IN", "Entrée du plug-in (mono ou stéréo)."]]
ov = Table([[img(annotated, 88 * mm), table(ov_rows, [8 * mm, 30 * mm, W - 92 * mm - 38 * mm])]], colWidths=[92 * mm, W - 92 * mm])
ov.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
f.append(ov)
f.append(Spacer(1, 3 * mm))
f.append(P("Un clic droit n'importe où sur la pédale ouvre le menu, à l'endroit du clic ; un clic droit sur une commande met son MIDI Learn en tête du menu (voir 5.6 et 6)."))
f.append(PageBreak())
# 4. Commandes
f.append(P("4. Les commandes", "h1"))
f.append(P("DELAY", "h2"))
f.append(side([P("Règle le temps entre la note et son écho, de <b>65 ms</b> (slapback) à <b>750 ms</b>. Le potard suit une courbe logarithmique : les retards courts du slapback et du doublage ont autant de place que les longs. À midi, on est vers 220 ms."),
               P("<b>Inertie du moteur de bande.</b> Changer le retard change la vitesse de la bande : la hauteur des répétitions glisse jusqu'à ce que le moteur se stabilise (environ 110 ms). Tournez DELAY pendant que les répétitions sonnent pour les glissandos et sirènes classiques."),
               P("<b>Tap et SYNC.</b> Après un tap, la position du potard est ignorée jusqu'à ce qu'on tourne à nouveau DELAY, comme sur la pédale. En SYNC, DELAY choisit une valeur de note (voir 5.4).")],
              img(os.path.join(CHARTS, "delay_chart_fr.png"), 66 * mm), W - 70 * mm))
f.append(P("SUSTAIN", "h2"))
f.append(P("Règle la part de l'écho renvoyée sur la bande, donc le nombre de répétitions. Comme sur l'EP103, le potard est volontairement inégal :"))
f += bullets(["<b>0 &rarr; 5</b> : doux, une à quatre répétitions audibles : slapback, doublage, ambiance courte.",
              "<b>5 &rarr; 8</b> : les répétitions se multiplient vite ; chacune est un peu plus sombre et usée que la précédente.",
              "<b>8 &rarr; 10</b> : longues traînées puis <b>auto-oscillation</b> au maximum : l'écho s'alimente lui-même jusqu'à la saturation de la bande. Baissez SUSTAIN pour le calmer."])
f.append(KeepTogether([img(os.path.join(CHARTS, "sustain_chart_fr.png"), W * 0.62),
                       P("SUSTAIN et VOLUME interagissent un peu, comme sur la pédale : plus l'écho est fort, plus il se réinjecte. L'auto-oscillation peut devenir forte : la sortie est protégée par un limiteur doux, mais gardez un niveau d'écoute raisonnable.", "small")]))
f.append(P("VOLUME", "h2"))
f.append(side([P("Règle uniquement le niveau des échos. Le son direct reste toujours à l'unité et n'est jamais traité (sur la pédale, le trajet direct est entièrement analogique)."),
               P("Baissé, l'écho se glisse derrière le jeu ; vers 8, il égale la note directe ; au-delà, les premières répétitions sont plus fortes que la note elle-même, comme sur un EP-3. Midi ≈ −6 dB, maximum ≈ +3 dB."),
               P("Le potard VOLUME est aussi un bouton poussoir (PUSH FOR AGE) : voir ci-dessous.")],
              img(os.path.join(CHARTS, "volume_chart_fr.png"), 66 * mm), W - 70 * mm))
f.append(P("Mode AGE (PUSH FOR AGE)", "h2"))
f.append(P("Par défaut, Echoflex sonne comme une bande neuve. L'AGE en fait une vieille machine usée : répétitions plus sombres, plus de saturation de bande, modulation plus profonde et plus aléatoire, petites pertes de niveau d'une bande fatiguée."))
f.append(steps([("Cliquer sur VOLUME", "Bascule entre votre réglage AGE et le son clair d'usine. La LED AGE ambre est allumée quand l'AGE est actif, éteinte pour le son clair."),
                ("Maintenir VOLUME 2 s", "La LED AGE se remplit pendant l'appui, puis clignote : le potard VOLUME règle maintenant la quantité d'AGE (0 = bande neuve, 10 = bande usée). La barre affiche <i>AGE 5.0 - push VOLUME to lock</i> sur un contour ambre."),
                ("Cliquer à nouveau sur VOLUME", "Verrouille le réglage AGE et rend le potard au VOLUME. Le niveau d'écho n'a pas changé.")]))
f.append(KeepTogether([Spacer(1, 2 * mm), side([img(age_img, 72 * mm), P("AGE coupé (LED éteinte) puis AGE actif (LED ambre allumée).", "small")],
                                              [table([["", "Bande neuve", "AGE à 10"], ["Répétitions", "brillantes, claires", "sombres, arrondies"],
                                                      ["Filtres enr. / boucle", "9,5 / 7,2 kHz", "3,6 / 2,5 kHz"], ["Pleurage", "± 0,14 ms à 0,55 Hz", "± 2,2 ms à 0,8 Hz"],
                                                      ["Dérive aléatoire", "très légère", "forte"], ["Saturation", "légère", "forte, asymétrique"],
                                                      ["Pertes de niveau", "aucune", "jusqu'à −3,5 dB"], ["Souffle", "inaudible", "léger, suit l'écho"]],
                                                     [27 * mm, 26 * mm, W - 76 * mm - 53 * mm], small=True)], 76 * mm)]))
f.append(KeepTogether([P("Le flou de mouvement des potards", "h2"),
                       P("Les potards sont rendus d'après la photo de la pédale, sous une lumière fixe en haut à gauche. Quand vous les tournez vite (souris, automation ou MIDI), la couronne crantée et le centre tournent ensemble, à la même vitesse, et passent en fondu du net au flou puis au flou total : jamais d'effet stroboscopique. Le flou retombe dès que le potard ralentit."),
                       img(blur_img, W * 0.62), P("Potard immobile, rotation rapide, rotation très rapide.", "small")]))
# 5. Footswitch, LED, tap, sync, demarrage, MIDI
f.append(P("5. Footswitch, LED, tap, synchro et MIDI", "h1"))
f.append(P("5.1 Footswitch et LED d'effet", "h2"))
f.append(side([P("Cliquez sur le footswitch pour activer ou couper l'effet ; le bouton s'enfonce tant que vous appuyez. La LED rouge s'allume et s'éteint en fondu et éclaire la façade autour d'elle ; allumée, sa lueur respire légèrement avec le niveau des répétitions et se reflète sur l'écrou du footswitch."),
               P("En <b>True bypass</b> (par défaut), les échos s'arrêtent avec l'effet ; en <b>Trails</b>, ils s'éteignent naturellement après la coupure (voir 5.5).")],
              [img(on_img, 62 * mm), P("Effet actif, puis bypass.", "small")], W - 66 * mm))
f.append(P("5.2 LED AGE et LED SYNC", "h2"))
f.append(P("<b>LED AGE (ambre)</b> : éteinte = bande neuve, allumée = AGE actif, clignotante = réglage de l'AGE, qui se remplit = vous maintenez VOLUME. <b>LED SYNC (verte)</b> : éteinte hors synchro ; en SYNC, elle flashe sur chaque valeur de note de la grille du morceau. Les deux LED éclairent aussi la façade."))
f.append(P("5.3 Tap tempo", "h2"))
f.append(side([P("L'EP103 a une prise TAP pour un switch externe. Sur Echoflex, c'est la prise elle-même qui sert de switch : <b>cliquez sur la prise TAP</b> (en bas à gauche) en rythme. L'écrou s'éclaire à chaque appui et la barre affiche le temps tapé."),
               ] + bullets(["Deux appuis suffisent ; Echoflex fait la moyenne des trois derniers intervalles.",
                             "Appuis espacés de 60 ms à 4,2 s ; le temps est limité à 4 secondes, comme sur la pédale.",
                             "Un intervalle très différent du précédent (plus de 35 %) relance la moyenne ; une pause de plus de 4,2 s démarre une nouvelle série.",
                             "Tourner DELAY rend la main au potard."], "tip"),
              [img(tap_img, 66 * mm), P("Tap : la prise TAP s'éclaire, la barre affiche le temps.", "small")], W - 70 * mm))
f.append(P("5.4 Synchro sur le tempo du DAW (SYNC)", "h2"))
f.append(steps([("Cliquer sur le mot DELAY (ou sur la LED SYNC)", "La LED SYNC s'allume en vert : le delay suit le tempo du DAW. Un nouveau clic revient au potard DELAY."),
                ("Tourner DELAY pour choisir la valeur de note", "En SYNC, le potard passe par 8 valeurs de note, de la double croche 1/16 (à gauche) à la blanche 1/2 (à droite). La barre affiche la valeur et le tempo, par ex. <i>SYNC 1/8 dotted - 120.0 BPM</i>."),
                ("Raccourcis", "Molette sur DELAY / SYNC : valeur précédente ou suivante. Clic droit dessus : menu des valeurs de note, avec <b>MIDI Learn: Sync</b> en tête.")]))
f.append(KeepTogether([Spacer(1, 2 * mm), side([img(sync_img, 72 * mm), P("SYNC coupé, puis SYNC activé (LED verte).", "small")],
                       table([["Potard DELAY", "Valeur de note", "à 120 BPM"], ["0 – 1,25", "1/16", "125 ms"], ["1,25 – 2,5", "1/8 triolet", "167 ms"], ["2,5 – 3,75", "1/8", "250 ms"],
                              ["3,75 – 5", "1/4 triolet", "333 ms"], ["5 – 6,25", "1/8 pointée", "375 ms"], ["6,25 – 7,5", "1/4", "500 ms"],
                              ["7,5 – 8,75", "1/4 pointée", "750 ms"], ["8,75 – 10", "1/2", "1000 ms"]], [24 * mm, 24 * mm, W - 76 * mm - 48 * mm], small=True), 76 * mm)]))
f.append(P("Rien à régler dans Reaper : l'hôte envoie son tempo au plug-in. Quand le projet joue, la LED flashe exactement sur la grille ; à l'arrêt, le delay suit quand même le tempo du projet. Les changements de tempo sont suivis en temps réel. Si l'hôte n'envoie pas de tempo, la LED reste faible et la barre indique <i>no host tempo</i>. Un tap quitte SYNC ; les temps sont limités à 65 ms – 4 s."))
f.append(P("5.5 Réglages de démarrage", "h2"))
f.append(P("Sur l'EP103, ces options se règlent à la mise sous tension. Sur Echoflex, elles sont dans Clic droit &rsaquo; <b>Startup settings</b> et sont enregistrées avec le projet. Le son direct n'est jamais traité, quel que soit le mode."))
f.append(table([["Réglage", "Choix", "Effet"], ["<b>Bypass</b>", "True relay bypass (défaut) / Trails bypass", "True bypass : les échos s'arrêtent à la coupure. Trails : l'entrée n'alimente plus la bande mais les échos déjà enregistrés s'éteignent naturellement."],
                ["<b>Mix</b>", "Dry + echo (défaut) / 100% wet (kill dry)", "100 % wet retire le son direct, pour un bus parallèle ou un départ d'effet."],
                ["<b>Channels</b>", "Mono (EP103 default) / Stereo", "Mono : le même écho part des deux côtés, sans opposition de phase. Stéréo : chaque côté a sa propre bande."]],
               [22 * mm, 52 * mm, W - 74 * mm]))
f.append(KeepTogether([Spacer(1, 2 * mm), img(os.path.join(CHARTS, "bypass_chart_fr.png"), W * 0.78)]))
f.append(P("5.6 MIDI", "h2"))
f.append(P("Envoyez le MIDI sur la piste d'Echoflex (dans Reaper : activez l'entrée MIDI de la piste ou routez une piste MIDI vers elle). Echoflex écoute tous les canaux. <b>Aucun CC n'est assigné d'office</b> : chaque commande s'assigne avec le <b>MIDI Learn</b>."))
f.append(table([["Commande", "Type"], ["Delay", "Continu : 0-127 &rarr; 0-10 (en SYNC : valeur de note)"], ["Sustain / Volume", "Continu"], ["Age amount", "Continu (quantité d'AGE)"],
                ["Age on/off", "Bascule : 64-127 AGE actif, 0-63 bande neuve"], ["Tap", "Bouton : chaque appui qui passe 64 est un tap"],
                ["Footswitch", "Bascule : 64-127 actif, 0-63 coupé"], ["Footswitch toggle", "Bouton : chaque appui inverse actif / coupé"],
                ["Sync", "Bascule : 64-127 delay calé sur le tempo du DAW, 0-63 potard DELAY"], ["Program Change 1-10", "Presets d'usine 1 à 10 (fixe)"]],
               [36 * mm, W - 36 * mm], small=True))
f.append(Spacer(1, 2 * mm))
f += bullets(["<b>MIDI Learn</b> : clic droit sur la commande (VOLUME propose Volume, Age amount et Age on/off ; le footswitch, Footswitch et Footswitch toggle ; la prise TAP, Tap ; DELAY / SYNC, Sync), choisissez <b>MIDI Learn: &lt;nom&gt; (CC n)</b> (un tiret si rien n'est assigné), puis bougez la pédale d'expression ou appuyez sur le bouton MIDI. La barre affiche <i>MIDI learn: move a control for Sustain</i>, puis confirme 2 secondes, par ex. <i>Sustain = CC 64</i>.",
              "<b>Clear MIDI</b> retire une assignation ; <b>Cancel MIDI learn</b> arrête l'attente ; clic droit &rsaquo; <b>MIDI</b> liste toutes les commandes avec leur CC et propose <b>Clear all MIDI assignments</b>. Un CC ne pilote qu'une commande. Les assignations sont sauvegardées avec le projet.",
              "Tous les paramètres sont aussi automatisables dans le DAW : Delay, Sustain, Volume, Age, Age On, Footswitch, Bypass, Mix, Channels, Time Source, Sync Division et Tap Time."], "tip")
# 6. Fenetre, barre de presets, menus
f.append(P("6. Fenêtre, barre de presets et menus", "h1"))
f.append(P("Taille de la fenêtre", "h2"))
f.append(P("Echoflex utilise le format pédale simple NINE HANDS | DSP : la fenêtre s'ouvre à la taille par défaut (60 % au départ, 493 pixels de haut) et ne peut jamais être réduite en dessous. Clic droit &rsaquo; <b>Plugin size</b> : <b>60 %</b>, <b>75 %</b> ou <b>100 %</b> pour cette fenêtre, « (default) » indiquant la taille par défaut ; <b>Default size (new windows)</b> choisit la taille d'ouverture de toutes les nouvelles fenêtres d'Echoflex (réglage commun à toutes les instances, enregistré sur l'ordinateur) et redimensionne aussitôt la fenêtre. Vous pouvez aussi tirer le coin en bas à droite jusqu'à 150 % (proportions conservées)."))
f.append(P("Barre de presets et ligne d'état", "h2"))
f.append(side([P("La <b>barre de presets</b> et la <b>ligne d'état</b> partagent la même pastille, entre la LED et le footswitch. Au repos, elle affiche le preset en cours (<i>P1 Noon (Manual Start)</i>, <i>User 3</i> ou <i>Edited</i> dès qu'un réglage a bougé) : " + AR + " passe au preset précédent ou suivant, un clic sur le nom ouvre le menu des presets."),
               P("Dès qu'un réglage bouge (souris, molette, automation, MIDI, tap), la ligne d'état prend sa place et affiche la valeur en direct : temps réel en ms, SUSTAIN, VOLUME, AGE, SYNC et tempo, temps tapé, effet on / bypass, messages du MIDI Learn. Elle reste 2,5 s après le dernier mouvement, puis la barre de presets revient en fondu. Pendant le réglage de l'AGE, le contour passe à l'ambre."),
               P("La barre clignote en rouge pâle à chaque message MIDI reçu.", "small")],
              [img(bar_img, 66 * mm), P("Au repos (presets), puis pendant un réglage : DELAY, SYNC, réglage de l'AGE.", "small")], W - 70 * mm))
f.append(P("Menu clic droit", "h2"))
f.append(P("Clic droit n'importe où sur la pédale : le menu s'ouvre à l'endroit du clic. Il est en anglais, comme sur les autres plug-ins NINE HANDS | DSP."))
f.append(table([["Menu", "Contenu"], ["<i>(sur une commande)</i>", "MIDI Learn: &lt;commande&gt; (CC n) · Clear MIDI · Cancel MIDI learn"],
                ["Plugin size", "60 % · 75 % · 100 % · Default size (new windows)"], ["Factory presets", "1. Noon (Manual Start) … 10. Runaway Oscillation"],
                ["Load / Save user preset", "User 1 … User 9"], ["Age", "Age on (click VOLUME) · Set Age (hold VOLUME 2 s) / Lock Age setting"],
                ["Delay time", "DELAY knob (65 - 750 ms) · Tap tempo (… ms) - click TAP · Sync to DAW tempo &rsaquo; 1/2 … 1/16"],
                ["Startup settings", "True relay bypass / Trails bypass · Dry + echo / 100% wet (kill dry) · Mono (EP103 default) / Stereo"],
                ["MIDI", "Learn: Delay … Learn: Sync · Cancel MIDI learn · Clear all MIDI assignments · Program Change 1-10"]],
               [36 * mm, W - 36 * mm], small=True))
# 7. Presets
f.append(P("7. Presets", "h1"))
f.append(P("Utilisez les flèches de la barre de presets, cliquez sur son nom, passez par Clic droit &rsaquo; Factory presets, par le menu de presets du DAW ou par MIDI Program Change 1 à 10."))
rows = [["PC", "Preset", "Delay / Sustain / Volume", "AGE", "Description"]]
for i, (n, d, s, v, a, ao) in enumerate(FACTORY):
    rows.append([str(i + 1), "<b>" + n + "</b>", f"{num(d)} ({round(delay_ms(d))} ms) / {num(s)} / {num(v)}", num(a) if ao else "coupé", PDESC[i]])
f.append(table(rows, [8 * mm, 30 * mm, 30 * mm, 14 * mm, W - 82 * mm], small=True))
f.append(P("Presets utilisateur", "h2"))
f.append(P("Clic droit &rsaquo; <b>Save user preset</b> &rsaquo; User 1 à 9 enregistre le réglage ; <b>Load user preset</b> le rappelle. Un preset utilisateur garde DELAY, SUSTAIN, VOLUME, la quantité d'AGE, AGE on/off, la source du temps de retard, le temps tapé et la division de synchro (pas les assignations MIDI, sauvegardées avec le projet). Les emplacements sont communs à tous les projets : " + mono("%APPDATA%\\NINE HANDS | DSP\\Echoflex\\UserPresets.xml") + " (Windows), " + mono("~/Library/NINE HANDS | DSP/Echoflex/UserPresets.xml") + " (macOS)."))
# 8. Conseils
f.append(P("8. Conseils d'utilisation", "h1"))
f += bullets(["<b>Dans Reaper</b>, placez Echoflex <b>avant</b> le simulateur d'ampli (Ampire, puis Impulse pour le baffle), comme la pédale devant un ampli. En mode Mono, rien ne s'annule quand le simulateur additionne la piste en mono. Pour des échos après l'ampli, comme un EP-3 dans une boucle d'effets, placez-le après le simulateur.",
              "<b>7 cordes et accordages graves</b> : gardez SUSTAIN sous 5 et un AGE modéré (3 à 6) : les répétitions sombres restent derrière les riffs au lieu d'empâter le grave. Pour les palm mutes, un slapback court (DELAY 1,5 à 2,5, SUSTAIN 0 à 1,5) épaissit sans brouiller.",
              "<b>Épaissir un solo</b> : DELAY 6,5 à 7,5, SUSTAIN vers 4,5, VOLUME 4 à 5 : l'écho se glisse juste sous la note.",
              "<b>Ambiance</b> : DELAY 8,5 à 10 (ou un long temps tapé), SUSTAIN 6,5 à 8, AGE 6 à 9, avec le Trails bypass.",
              "<b>Sirènes de bande</b> : SUSTAIN 9 à 10, VOLUME 7, puis tournez DELAY lentement : l'inertie du moteur fait glisser la hauteur.",
              "<b>Échos rythmiques</b> : cliquez sur DELAY pour activer SYNC et réglez 1/8 pointée (entre 5 et 6,25).",
              "<b>Pédale d'expression</b> : apprenez SUSTAIN ou Age amount (clic droit &rsaquo; MIDI Learn) pour faire monter les répétitions ou user la bande en jouant."], "tip")
f.append(P("Dépannage", "h2"))
f += bullets(["<b>Les échos ne changent pas quand je tourne DELAY</b> : le temps venait du TAP ; le premier mouvement de DELAY rend la main au potard.",
              "<b>Le son n'arrête pas de grossir</b> : SUSTAIN est près du maximum (auto-oscillation). Baissez SUSTAIN ou VOLUME.",
              "<b>Rien ne se passe quand je clique sur VOLUME</b> : cliquez sans bouger la souris ; un glissé tourne le potard, un appui immobile de 2 s ouvre le réglage AGE.",
              "<b>Pas de son direct</b> : Startup settings &rsaquo; Mix est sur 100 % wet. <b>Pas d'écho</b> : vérifiez que la LED rouge est allumée.",
              "<b>Ma pédale MIDI ne fait rien</b> : la piste doit recevoir le MIDI, et aucun CC n'est assigné d'office (clic droit &rsaquo; MIDI Learn)."], "tip")
# 9. Caracteristiques
f.append(KeepTogether([P("9. Caractéristiques techniques", "h1"),
    table([["Format", "VST3 · Windows 11 (x64) · macOS 10.13+ (Apple Silicon + Intel)"], ["Entrées / sorties", "entrée mono ou stéréo · sortie stéréo"],
           ["Latence", "0 échantillon"], ["Temps de retard", "65 à 750 ms (potard) · jusqu'à 4 s (tap ou synchro)"], ["Mémoire de retard", "4,3 s, interpolation d'Hermite"],
           ["Modèle", "têtes d'enregistrement et de lecture filtrées, compression et saturation de bande, pleurage 0,55 Hz, scintillement 7,3 / 11,7 Hz, dérive aléatoire, inertie du moteur ~110 ms, préampli EP101 sur les échos, limiteur doux à −0,3 dBFS"],
           ["Fréquences d'échantillonnage", "toutes celles du DAW"], ["Presets", "10 d'usine · 9 utilisateur"],
           ["MIDI", "MIDI Learn sur 9 commandes (aucun CC assigné d'office), sauvegardé avec le projet · tous les canaux · Program Change 1-10"],
           ["Fenêtre", "Plugin size 60 % (minimum) / 75 % / 100 %, jusqu'à 150 %, taille des nouvelles fenêtres au choix · anti-gel v2 sous Windows"],
           ["Queue", "12 s annoncées au DAW (trails)"],
           ["Sources", "manuel Dunlop EP103 Echoplex Delay (jimdunlop.com) ; zZounds ; Chicago Music Exchange ; Premier Guitar ; Starlite Campbell, « The Maestro Echoplex EP-3 »"]], [36 * mm, W - 36 * mm], header=False, small=True)]))

# ------------------------------------------------------------------ pages
def deco(c, doc):
    c.saveState()
    c.setFillColor(DARK); c.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, A4[1] - 6.8 * mm, A4[0], 0.8 * mm, stroke=0, fill=1)
    c.setFont("Pop", 7.5); c.setFillColor(GREY)
    c.drawString(18 * mm, 10 * mm, "Echoflex (NINE HANDS | DSP) · v" + VERSION)
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                      title="ECHOFLEX - Notice v" + VERSION, author="NINE HANDS | DSP")
# ---- Couverture « minimale » (modele 6) : gabarit fixe commun a toutes les notices (mm depuis le HAUT, logo depuis le bas)
PEDAL_H, PEDAL_MAXW, PEDAL_TOP = 82 * mm, 115 * mm, 84 * mm
LANG_TOP = 18 * mm
NAME_TOP, NAME_PT = 194 * mm, 30
SUB_TOP, SUB_PT = 208 * mm, 10
LOGO_W, LOGO_BOTTOM = 38 * mm, 22 * mm
BAND_H = 3 * mm
def cover_bg(c, doc):
    c.saveState(); c.setFillColor(colors.black); c.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, 0, A4[0], BAND_H, stroke=0, fill=1)
    def line(text, top, font, size, cs, col):
        w = pdfmetrics.stringWidth(text, font, size) + cs * (len(text) - 1)
        t = c.beginText((A4[0] - w) / 2, A4[1] - top - size * 0.8); t.setFont(font, size); t.setCharSpace(cs)
        t.setFillColor(col); t.textOut(text); c.drawText(t)
    line("FRANÇAIS", LANG_TOP, "PopM", 8.5, 0, ACC_L)
    ci = Image.open(cover); iw, ih = ci.size
    cw_, ch_ = cw, ch
    kk = min(PEDAL_H / ch_, PEDAL_MAXW / cw_)
    dw, dh = iw * kk, ih * kk
    y0 = A4[1] - (PEDAL_TOP + (PEDAL_H - ch_ * kk) / 2) + pad * kk
    c.drawImage(cover, (A4[0] - dw) / 2, y0 - dh, dw, dh)
    line("ECHOFLEX", NAME_TOP - NAME_PT * 0.02, "Title", NAME_PT, NAME_PT * 0.5, colors.white)
    line("Écho à bande", SUB_TOP, "Pop", SUB_PT, 1.5, colors.HexColor("#BDC4B8"))
    lw, lh = Image.open(LOGO_PNG).size
    c.drawImage(LOGO_PNG, (A4[0] - LOGO_W) / 2, LOGO_BOTTOM, LOGO_W, LOGO_W * lh / lw, mask="auto")
    c.restoreState()
doc.addPageTemplates([PageTemplate(id="cover", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="fc")], onPage=cover_bg),
                      PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=deco)])
doc.build(f)
print(OUT)
