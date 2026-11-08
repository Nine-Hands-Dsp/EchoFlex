# ECHOFLEX (NINE HANDS | DSP) - notice PDF bilingue (anglais puis francais), illustree.
# Usage : python3 tools/manual.py <fichier PDF de sortie>
#
# Images sources dans tools/manual_assets/ (reprises de la notice v1.4.1, rendu reel du plugin) :
#   pedal_cutout.png (pedale detouree, fond transparent : couverture composee ici avec reflet et halo),
#   overview.jpg (capture numerotee), intro_pedal.jpg, delay_knob_*.jpg, age_*.jpg, tap.jpg, sync_*.png,
#   fs_on/fs_bypass.png, status_line.jpg, preset_1..10.jpg, window_sizes.png ;
#   graphiques et schemas par langue : delay_chart_*, sustain_chart_*, volume_chart_*, age_charts_*,
#   bypass_chart_*, tape_machine_* (_en / _fr).
# Le menu du clic droit est decrit ici en texte (tableau) avec les libelles exacts de PluginEditor.cpp :
# a mettre a jour si le menu change.
# Pas d'historique des versions dans la notice (demande de l'utilisateur).
import os, sys
import numpy as np
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, NextPageTemplate, Frame, Paragraph, Spacer, Image as RLImage,
                                Table, TableStyle, PageBreak, CondPageBreak, KeepTogether)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AS = os.path.join(ROOT, "tools", "manual_assets")
FONTS = os.path.join(AS, "fonts")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "Echoflex_Manual_EN-FR.pdf")
TMP = tempfile.mkdtemp(prefix="echoflex_manual_")
VERSION = "1.5.2"     # = version du plugin dans CMakeLists.txt

for n, f in (("Pop", "Poppins-Regular"), ("PopL", "Poppins-Light"), ("PopM", "Poppins-Medium"), ("PopB", "Poppins-Bold"),
             ("PopI", "Poppins-Italic"), ("Mono", "DejaVuSansMono"), ("DjV", "DejaVuSans")):
    pdfmetrics.registerFont(TTFont(n, os.path.join(FONTS, f + ".ttf")))
pdfmetrics.registerFontFamily("Pop", normal="Pop", bold="PopB", italic="PopI", boldItalic="PopB")

ACC = colors.HexColor("#D8261A")          # rouge de la LED d'effet
DARK = colors.HexColor("#17181C"); GREY = colors.HexColor("#6B6B70"); LIGHT = colors.HexColor("#F3F1EF")
def A(n): return os.path.join(AS, n)

# ---------- couverture : pedale detouree, reflet au sol, halo rouge tres doux ----------
def build_cover():
    cut = Image.open(A("pedal_cutout.png")).convert("RGBA")
    cw, ch = cut.size; pad = int(cw * 0.16)
    canvas = Image.new("RGBA", (cw + 2 * pad, int(ch * 1.30) + pad), (0, 0, 0, 255))
    yy, xx = np.mgrid[0:canvas.height, 0:canvas.width].astype(np.float64)
    gcx, gcy = canvas.width / 2, pad + ch * 0.45
    glow = np.exp(-(((xx - gcx) / (cw * 0.42)) ** 2 + ((yy - gcy) / (ch * 0.34)) ** 2)) * 26
    edge = np.clip(np.minimum.reduce([xx, canvas.width - 1 - xx, yy, canvas.height - 1 - yy]) / (pad * 1.0), 0, 1)
    glow = np.maximum(glow * edge ** 3 - 1.0, 0)
    halo = np.dstack([glow * 0.95, glow * 0.22, glow * 0.16, np.full_like(glow, 255)]).astype(np.uint8)
    canvas = Image.alpha_composite(canvas, Image.fromarray(halo, "RGBA"))
    refl = cut.transpose(Image.FLIP_TOP_BOTTOM)
    ra = np.array(refl).astype(np.float64)
    fade = np.clip(1 - np.arange(refl.height) / (refl.height * 0.22), 0, 1) ** 1.6 * 0.22
    ra[..., 3] *= fade[:, None]
    canvas.alpha_composite(Image.fromarray(ra.astype(np.uint8), "RGBA"), (pad, pad + ch - int(ch * 0.035)))
    canvas.alpha_composite(cut, (pad, pad))
    canvas = canvas.crop((0, 0, canvas.width, pad + int(ch * 1.18)))
    p = os.path.join(TMP, "echoflex_cover.jpg"); canvas.convert("RGB").save(p, quality=92)
    return p
COVER = build_cover()

def img(path, width):
    im = Image.open(path); h = width * im.height / im.width
    return RLImage(path, width=width, height=h)

st = {
    "h1": ParagraphStyle("h1", fontName="PopB", fontSize=18, leading=23, textColor=DARK, spaceAfter=6, spaceBefore=8, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="PopM", fontSize=11.5, leading=15, textColor=DARK, spaceAfter=3, spaceBefore=8, keepWithNext=1),
    "h3": ParagraphStyle("h3", fontName="PopM", fontSize=9.6, leading=12.5, textColor=DARK, spaceAfter=1, spaceBefore=5, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Pop", fontSize=9, leading=13.2, textColor=DARK, spaceAfter=4),
    "b": ParagraphStyle("b", fontName="Pop", fontSize=9, leading=13.2, textColor=DARK, spaceAfter=2.5, leftIndent=11, bulletIndent=1),
    "small": ParagraphStyle("small", fontName="Pop", fontSize=7.6, leading=10.5, textColor=GREY, alignment=TA_CENTER, spaceBefore=2, spaceAfter=6),
    "note": ParagraphStyle("note", fontName="Pop", fontSize=8.4, leading=12, textColor=DARK),
    "cell": ParagraphStyle("cell", fontName="Pop", fontSize=8.2, leading=11, textColor=DARK),
    "cellb": ParagraphStyle("cellb", fontName="PopM", fontSize=8.2, leading=11, textColor=DARK),
    "cellw": ParagraphStyle("cellw", fontName="PopM", fontSize=8.2, leading=11, textColor=colors.white),
    "menu": ParagraphStyle("menu", fontName="Pop", fontSize=8.4, leading=11.2, textColor=colors.HexColor("#ECE9E9")),
    "menus": ParagraphStyle("menus", fontName="Pop", fontSize=7.4, leading=10, textColor=colors.HexColor("#A9A6A6"), leftIndent=8),
    "cover": ParagraphStyle("cover", fontName="PopL", fontSize=40, leading=48, textColor=colors.white, alignment=TA_CENTER),
    "coversub": ParagraphStyle("coversub", fontName="Pop", fontSize=11, leading=16, textColor=colors.HexColor("#BDBDBD"), alignment=TA_CENTER),
    "coverlang": ParagraphStyle("coverlang", fontName="PopM", fontSize=8, leading=11, textColor=ACC),
}
def fix(t): return t.replace("&rarr;", "<font name='DjV'>&rarr;</font>").replace("&infin;", "<font name='DjV'>&infin;</font>")
def P(t, s="p"): return Paragraph(fix(t), st[s])
def H1(num, t): return P("<font color='#D8261A'>%s</font>&nbsp;&nbsp;%s" % (num, t), "h1")
def H2(t): return P("<font name='DjV' color='#D8261A'>&#9679;</font>&nbsp;&nbsp;" + t, "h2")
def bullets(items, ch="\u2022"): return [Paragraph(fix(i), st["b"], bulletText=ch) for i in items]
CHK = ParagraphStyle("chk", parent=None, fontName="Pop", fontSize=9, leading=13.2, textColor=DARK, spaceAfter=2.5, leftIndent=11, bulletIndent=1,
                     bulletFontName="DjV", bulletColor=ACC)
def checks(items): return [Paragraph(fix(i), CHK, bulletText="\u2713") for i in items]
def table(rows, widths, header=True, dark=False):
    data = []
    for r, row in enumerate(rows):
        s = ("cellw" if dark else "cellb") if (header and r == 0) else "cell"
        data.append([Paragraph(fix(c), st[s]) for c in row])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#DCDADA")),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LEFTPADDING", (0, 0), (-1, -1), 4)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), DARK if dark else LIGHT)]
        if not dark: style += [("LINEBELOW", (0, 0), (-1, 0), 0.8, ACC)]
    t.setStyle(TableStyle(style)); return t
def note(t):
    tb = Table([[P("<font name='DjV' color='#D8261A'>&#9679;</font>&nbsp; " + t, "note")]], colWidths=[W])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return tb
def steps(items):
    rows = [[P("<font color='#D8261A'><b>%d</b></font>" % (i + 1), "p"), [P("<b>%s</b>" % h, "p"), P(x, "p")]] for i, (h, x) in enumerate(items)]
    t = Table(rows, colWidths=[8 * mm, None])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    return t
def side(a, b, wa, valign="TOP"):
    t = Table([[a, b]], colWidths=[wa, W - wa])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), valign), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 8)]))
    return t
def caption_img(path, width, cap): return [img(path, width), P(cap, "small")]
def row_imgs(items, gap=4 * mm):
    """items : (chemin, legende) ; images cote a cote sur toute la largeur."""
    n = len(items); w = (W - gap * (n - 1)) / n
    cells = [[img(p, w), P(c, "small")] for p, c in items]
    t = Table([cells], colWidths=[w + (gap if i < n - 1 else 0) for i in range(n)])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    return t
def mono(s): return "<font name='Mono' size='8.2'>" + s + "</font>"

W = A4[0] - 36 * mm

# ---------- presets (identiques a PluginProcessor.cpp) : delay, sustain, volume, age, ageOn ----------
PRESETS = [("Noon (Manual Start)", 5.0, 5.0, 5.0, 5.0, 0), ("Fifties Slapback", 2.1, 1.2, 6.5, 4.0, 1), ("Rockabilly Double", 2.8, 3.5, 5.5, 3.0, 1),
           ("Surf Echo", 3.6, 4.5, 6.5, 2.0, 0), ("Hot Lead 400", 7.3, 4.8, 5.0, 2.5, 1), ("Fresh Tape Wash", 8.6, 6.5, 6.0, 0.0, 0),
           ("Worn Cartridge", 6.2, 5.5, 6.5, 10.0, 1), ("Dark Ambience", 9.3, 7.6, 6.0, 8.0, 1), ("Dub Spiral", 7.6, 8.7, 7.0, 6.0, 1),
           ("Runaway Oscillation", 4.2, 10.0, 7.0, 5.0, 1)]
def delay_ms(d): return 65.0 * (750.0 / 65.0) ** (d / 10.0)
def num(v, lang): s = "%.1f" % v; return s.replace(".", ",") if lang == "fr" else s

DASH = "&mdash;"
T = {
"en": dict(
 lang="ENGLISH", sub="Tape echo delay &middot; VST3 &middot; Windows &amp; macOS", ver="User manual &middot; version " + VERSION,
 foot="Echoflex &middot; NINE HANDS | DSP &middot; User manual &middot; v" + VERSION,
 about_h="About this manual",
 about="Echoflex is a personal-use plug-in by NINE HANDS | DSP that recreates the Dunlop EP103 Echoplex&reg; Delay pedal, itself a compact tribute to the Maestro Echoplex EP-3 tape echo. This manual describes every control, every hidden function and the way the sound was modelled. It covers version " + VERSION + ". Echoplex is a trademark of its owner; Echoflex is an independent tribute and is not affiliated with it.",
 s01="Introduction", legend_h="The legend",
 legend=["The Maestro Echoplex EP-3 was built from 1970 to 1991 &ndash; the longest run of any Echoplex. Inside, a loop of tape in a removable cartridge runs past an erase head, a record head and a playback head; the distance between the heads and the tape speed set the delay. Its solid-state preamp, which every signal went through, became famous on its own for the way it sweetened and thickened a guitar.",
         "The EP-3 was also big, heavy and temperamental: worn tape, dirty heads and a tired pinch roller made the echo waver (wow and flutter) and darken. Many players loved precisely those flaws."],
 pedal_h="The pedal",
 pedal="The Dunlop EP103 puts that sound in a box the size of a Phase 90: a 96 kHz digital tape-echo emulation with an all-analog dry path, three knobs (DELAY, SUSTAIN, VOLUME), an AGE mode hidden under the VOLUME knob, a tap-tempo jack and a few startup options (trails, 100 % wet, stereo).",
 rec_h="What Echoflex recreates",
 rec=["The same three controls, ranges and feel: 65 &ndash; 750 ms, few repeats on the first half of SUSTAIN then an almost exponential rise up to self-oscillation, VOLUME sets the echo level only.",
      "The default \u201cfresh tape\u201d voice: clear repeats, subtle wow and flutter, the EP101 preamp colouring the echoes only.",
      "AGE mode exactly as on the pedal: click VOLUME to switch it on or off, hold it 2 seconds to adjust it, click again to lock.",
      "Tape-motor inertia: turning DELAY bends the pitch of the repeats like a real tape echo.",
      "Tap tempo up to 4 seconds (click the TAP jack), and a SYNC LED to lock the delay to the tempo of Reaper or any DAW.",
      "True bypass or trails, 100 % wet, mono or stereo &ndash; the pedal's startup settings, in the right-click menu.",
      "10 factory presets, 9 user slots, full MIDI control (MIDI Learn) and automation."],
 s02="Installation", build_h="Build with GitHub",
 build=["Put every file of the project at the root of your repository: " + mono("background.jpg") + ", " + mono("knob_strip.png") + ", " + mono("CMakeLists.txt") + ", " + mono("PluginProcessor.h/.cpp") + ", " + mono("PluginEditor.h/.cpp") + ", " + mono("README.md") + ", " + mono("Montserrat-OFL.txt") + " and the folder " + mono(".github/workflows/build.yml") + ".",
        "Push. The <b>Actions</b> tab builds the plug-in for Windows (windows-2022) and macOS (universal binary Apple Silicon + Intel).",
        "Download the artifact <b>Echoflex-VST3-Windows</b> or <b>Echoflex-VST3-macOS</b>."],
 inst_h="Install",
 inst=["<b>Windows 11</b> &ndash; copy " + mono("Echoflex.vst3") + " to " + mono("C:\\Program Files\\Common Files\\VST3\\") + ".",
       "<b>macOS</b> &ndash; unzip and copy " + mono("Echoflex.vst3") + " to " + mono("~/Library/Audio/Plug-Ins/VST3/") + ". The plug-in is signed ad hoc; if macOS blocks it, allow it in System Settings &rsaquo; Privacy &amp; Security.",
       "Rescan the plug-ins in your DAW. Echoflex appears as <b>Echoflex (NINE HANDS | DSP)</b> in the Delay category."],
 where_h="Where to put it in Reaper", chain=["Guitar", "Echoflex", "Ampire", "Impulse", "Master"],
 where="Like the other NINE HANDS | DSP plug-ins, place Echoflex <b>before</b> your amp simulator (Ampire, then Impulse). In Mono mode (default, like the pedal) the same echo goes to the left and right outputs, with no inverted signal, so nothing cancels when the amp sim sums the track to mono. To hear the echoes after the amp &ndash; like an EP-3 in an effects loop &ndash; place it after the amp sim instead.",
 s03="Overview",
 ov=[("VOLUME / PUSH FOR AGE", "echo level. Click: AGE on/off. Hold 2 s: adjust AGE."), ("SUSTAIN", "number of repeats, up to self-oscillation."),
     ("DELAY", "delay time, 65 to 750 ms."), ("AGE LED (amber)", "lit when AGE is on, blinks while you adjust it."),
     ("Effect LED (red)", "lit when the effect is on; its glow breathes with the repeats."), ("Footswitch", "click to switch the effect on or off."),
     ("TAP jack", "click it repeatedly to tap a tempo (up to 4 s)."), ("INPUT", "plug-in input (mono or stereo)."), ("OUTPUT", "plug-in output (stereo)."),
     ("Status line", "appears when a setting moves, then fades away after 2.5 s."),
     ("SYNC LED (green)", "click DELAY or the LED to lock the delay to the DAW tempo; flashes on the beat.")],
 ov_note="Right-click anywhere on the pedal to open the menu (Plugin size, presets, AGE, delay-time source, startup settings, MIDI); right-click a control for its MIDI Learn.",
 s04="DELAY",
 delay="Sets the time between your note and its echo, from <b>65 ms</b> (slapback) to <b>750 ms</b>. The knob follows a logarithmic curve, so the short delays used for slapback and doubling get as much room as the long ones: noon is about 220 ms.",
 knob_hdr=["Knob", "Time"], knob_caps=["0 &middot; 65 ms", "5 &middot; 221 ms", "10 &middot; 750 ms"],
 delay_more=["<b>Tape-motor inertia.</b> On a tape echo, changing the delay changes the tape speed, so the pitch of the repeats slides up or down until the motor settles. Echoflex does the same (about 110 ms of inertia): sweep DELAY while the repeats ring out for those classic swoops and sirens.",
             "<b>Tap and SYNC.</b> After tapping, the knob position is ignored until you turn DELAY again &ndash; exactly like the pedal. With SYNC on, DELAY chooses a note value of the DAW tempo instead of a time (see \u201cDAW tempo sync\u201d)."],
 s05="SUSTAIN",
 sus="Sets how much of the echo is fed back to the tape, so how many repeats you hear. Like the EP103, the knob is deliberately uneven:",
 sus_b=["<b>0 &rarr; 5</b>: gentle, one to four audible repeats &ndash; slapback, doubling, short ambience.",
        "<b>5 &rarr; 8</b>: the repeats multiply quickly; each one is darker and slightly more worn than the previous one.",
        "<b>8 &rarr; 10</b>: long trails, then <b>self-oscillation</b> at the maximum: the echo feeds itself and grows until the tape saturates. Turn SUSTAIN down to tame it."],
 sus_more="SUSTAIN and VOLUME interact a little, as on the pedal: the louder the echo, the more it feeds back. Near the top of SUSTAIN, a small move of VOLUME changes the behaviour noticeably &ndash; the pedal is described as \u201csensitive and twitchy\u201d there, and so is Echoflex.",
 sus_warn="Self-oscillation can get loud. The output is protected by a soft limiter, but keep your monitoring level reasonable when you push SUSTAIN to the maximum.",
 s06="VOLUME",
 vol="Sets the level of the echoes only. The dry signal always stays at unity gain and is never processed (on the pedal, the dry path is fully analog).",
 vol_hdr=["Knob", "Echo level"], vol_vals=["&minus;&infin;", "&minus;26.8 dB", "&minus;17.7 dB", "&minus;12.5 dB", "&minus;8.7 dB", "&minus;5.8 dB", "&minus;3.4 dB", "&minus;1.4 dB", "0.3 dB", "1.9 dB", "3.2 dB"],
 vol_more="Turned down, the echoes sit behind your playing; around 8 they match the dry note; above, the first repeats are louder than the note itself, as an EP-3 could do.",
 vol_note="The VOLUME knob is also a push button: see AGE mode.",
 s07="AGE mode",
 age="By default Echoflex sounds like a freshly calibrated tape echo: clear, bright repeats with very subtle wow and flutter. AGE turns it into an old, well-used machine: darker repeats, more tape saturation, deeper and more random modulation and the little level drops of a tired tape.",
 age_h="Using AGE &ndash; exactly like the pedal",
 age_steps=[("Click VOLUME", "Switches between your AGE setting and the default clear sound. The amber AGE LED is lit when AGE is on, off for the clear sound."),
            ("Hold VOLUME 2 s", "The AGE LED fills up while you hold, then blinks: you are in AGE adjust mode. The VOLUME knob now shows and sets the AGE amount (0 = pristine, 10 = worn out). The status line says \u201cpush VOLUME to lock\u201d."),
            ("Click VOLUME again", "Locks the AGE setting and gives the knob back to VOLUME. Your echo level has not changed.")],
 age_caps=["AGE off &ndash; clear tape", "AGE on &ndash; LED lit"], age_adj_cap="Adjusting AGE &ndash; LED blinks, the knob shows the AGE amount",
 age_t=[["", "Clear tape (AGE off)", "AGE at 10"], ["Repeats", "bright, clear", "dark, rounded"], ["Record / loop filters", "9.5 kHz / 7.2 kHz", "3.6 kHz / 2.5 kHz"],
        ["Wow (slow pitch drift)", "&plusmn; 0.14 ms at 0.55 Hz", "&plusmn; 2.2 ms at 0.8 Hz"], ["Flutter (fast)", "barely audible", "clearly audible"],
        ["Random drift", "very light", "strong, the modulation feels random"], ["Tape saturation", "light", "strong, slightly asymmetric"],
        ["Level drops", "none", "up to &minus;3.5 dB"], ["Hiss", "inaudible", "light, follows the echo"]],
 age_note="AGE is also available in the right-click menu (Age &rsaquo; Age on / Set Age), by MIDI (<b>Age amount</b> and <b>Age on/off</b>, assigned with MIDI Learn) and through automation (parameters Age and Age On).",
 s08="Tap tempo",
 tap="The EP103 has a TAP jack for an external MXR M199 switch. On Echoflex the jack itself is the switch: <b>click the TAP jack</b> (bottom left of the pedal) in rhythm. The nut and the TAP label light up at each tap, and the status line shows the new time.",
 tap_cap="Tapping: the TAP jack lights up and the status line shows the tapped time.",
 tap_b=["Two taps are enough; Echoflex averages the last three intervals for a steady tempo.",
        "Taps 60 ms to 4.2 s apart are accepted; the time is limited to 4 seconds, like the pedal.",
        "An interval very different from the previous one (more than 35 %) restarts the average, so you can jump from one tempo to another at once.",
        "A pause longer than 4.2 s starts a new tap sequence.", "Turning DELAY gives control back to the knob, as on the pedal.",
        "MIDI: once <b>Tap</b> is assigned with MIDI Learn, each press on that CC (value crossing 64) is a tap."],
 tap_note="To follow the tempo of your song automatically, use SYNC instead (next section).",
 s09="DAW tempo sync (SYNC)",
 sync="Echoflex can lock its delay time to the tempo of Reaper or any other DAW. A green <b>SYNC LED</b>, next to the DELAY label, shows when the delay follows the song tempo.",
 sync_steps=[("Click the word DELAY (or the SYNC LED)", "The SYNC LED lights up green: the delay now follows the DAW tempo. Click again to go back to the DELAY knob."),
             ("Turn DELAY to choose the note value", "In SYNC, the DELAY knob no longer sets milliseconds: it steps through 8 note values, from 1/16 (fully left) to 1/2 (fully right). The status line shows the note value, the tempo and the real time in ms."),
             ("Shortcuts", "Mouse wheel over the word DELAY / SYNC LED: previous or next note value. Right-click on it: menu of note values (Sync on, 1/2 &hellip; 1/16), with MIDI Learn: Sync at the top. MIDI (<b>Sync</b>, assigned with MIDI Learn): SYNC on (64-127) or off (0-63).")],
 sync_caps=["SYNC off &ndash; the knob sets the time", "SYNC on &ndash; green LED, the knob sets the note value"],
 sync_t=[["DELAY knob", "Note value", "at 120 BPM"], ["0 &ndash; 1.25", "1/16", "125 ms"], ["1.25 &ndash; 2.5", "1/8 triplet", "167 ms"], ["2.5 &ndash; 3.75", "1/8", "250 ms"],
         ["3.75 &ndash; 5", "1/4 triplet", "333 ms"], ["5 &ndash; 6.25", "1/8 dotted", "375 ms"], ["6.25 &ndash; 7.5", "1/4", "500 ms"],
         ["7.5 &ndash; 8.75", "1/4 dotted", "750 ms"], ["8.75 &ndash; 10", "1/2", "1000 ms"]],
 daw_h="In Reaper (or any DAW)",
 daw="Nothing to set up: the VST3 host sends its tempo to the plug-in. When the project plays, the SYNC LED flashes exactly on each note value of the song grid; when it is stopped, the delay still follows the project tempo and the LED flashes freely. Tempo changes and tempo automation are followed in real time (the tape motor glides to the new time). If the host sends no tempo, the LED stays dim and the DELAY knob time is used.",
 sync_cap="Status line in SYNC: real time, note value and DAW tempo.",
 sync_b=["SYNC is saved with the project and in user presets; it can be automated with the Time Source parameter.",
         "Tapping on the TAP jack leaves SYNC and uses the tapped time; click DELAY to go back to SYNC.",
         "Times are limited to 65 ms &ndash; 4 s: very slow tempos with long note values are capped at 4 s."],
 s10="LEDs, footswitch &amp; status line",
 fs_h="Footswitch and effect LED",
 fs=["Click the footswitch to switch the effect on or off. The red LED lights up and fades out smoothly; while it is lit, its glow breathes slightly with the level of the repeats.",
     "In <b>True bypass</b> (default) the echoes stop with the effect; in <b>Trails</b> they ring out naturally after you switch off (see Startup settings)."],
 fs_caps=["Effect on", "Bypass"],
 aled_h="AGE LED",
 aled="Amber. Off = clear tape, lit = AGE on, blinking = adjusting AGE, filling up = you are holding VOLUME. The green <b>SYNC LED</b> flashes on the DAW tempo when SYNC is on (see previous section).",
 st_h="Status line",
 st="Appears under the effect LED as soon as a setting moves (mouse, automation or MIDI), stays 2.5 seconds and fades away.",
 st_b=["<b>First line</b>: the real delay time in ms (knob, tap or sync), SUSTAIN and VOLUME &ndash; or the AGE value while you adjust it.",
       "<b>Second line</b>: AGE state (CLEAR TAPE or AGE x.x), TAP / SYNC, BYPASS, current preset and the last MIDI message received (it flashes red with each message or tap)."],
 s11="Right-click menu",
 rc="Right-click anywhere on the pedal. On a control (a knob, the footswitch or the TAP jack) the menu starts with the <b>MIDI Learn</b> items of that control (see 16 &middot; MIDI); a right-click on the SYNC LED opens the note-value menu, with <b>MIDI Learn: Sync</b> at the top.",
 menu=[("ONLY ON A CONTROL (here SUSTAIN, not assigned yet)", ["MIDI Learn: Sustain (" + DASH + ")", "Clear MIDI: Sustain (greyed while nothing is assigned)", "Cancel MIDI learn (while waiting for a CC)"], True),
       ("Plugin size &rsaquo;", ["60 %  (default) &middot; 75 % &middot; 100 % &middot; Default size (new windows) &rsaquo; 60 % / 75 % / 100 %"], False),
       ("Factory presets &rsaquo;", ["1. Noon (Manual Start) &hellip; 10. Runaway Oscillation"], False),
       ("Load user preset &rsaquo;", ["User 1 &hellip; User 9"], False), ("Save user preset &rsaquo;", ["User 1 &hellip; User 9"], False),
       ("Age &rsaquo;", ["Age on (click VOLUME) &middot; Set Age (hold VOLUME 2 s)"], False),
       ("Delay time &rsaquo;", ["DELAY knob (65 - 750 ms) &middot; Tap tempo (&hellip; ms) - click TAP &middot; Sync to DAW tempo (click DELAY / SYNC) &rsaquo; 1/2 &hellip; 1/16"], False),
       ("Startup settings &rsaquo;", ["True relay bypass / Trails bypass &middot; Dry + echo / 100% wet (kill dry) &middot; Mono (EP103 default) / Stereo"], False),
       ("MIDI &rsaquo;", ["Learn: Delay (" + DASH + ") &hellip; Learn: Sync (" + DASH + ") &middot; Cancel MIDI learn (while waiting) &middot; Clear all MIDI assignments &middot; Program Change 1-10  Factory presets"], False),
       ("Echoflex delay v" + VERSION + " - NINE HANDS | DSP", [], False)],
 win_h="Plugin size",
 win=["The window opens at the default size, 60 % at first, and can never be made smaller than 60 %. Choose <b>60 %</b>, <b>75 %</b> or <b>100 %</b> in Right-click &rsaquo; <b>Plugin size</b> (<b>(default)</b> is shown next to the default size), or drag the bottom-right corner to enlarge it (proportions are locked, up to 150 %).",
      "<b>Plugin size &rsaquo; Default size (new windows)</b> chooses the size at which every new Echoflex window opens: the setting is shared by all instances and saved on your computer, and the open window takes that size at once."],
 s12="Startup settings",
 su="On the EP103 these options are set by powering the pedal while holding VOLUME, then reading the AGE LED colour. On Echoflex they are simply in Right-click &rsaquo; <b>Startup settings</b>, and they are saved with your project.",
 su_t=[["Setting", "Choices", "What it does"], ["<b>Bypass</b>", "True relay bypass (default) / Trails bypass", "True bypass: the echoes stop when you switch off. Trails: the input stops feeding the tape but the echoes already recorded ring out."],
       ["<b>Mix</b>", "Dry + echo (default) / 100% wet", "100 % wet removes the dry signal, for a parallel bus or an effects send."],
       ["<b>Channels</b>", "Mono (default) / Stereo", "Mono: the input is summed and the same echo goes to both sides. Stereo: left and right each get their own tape path."]],
 su_note="As on the pedal, the dry signal is never processed in any mode.",
 s13="Inside the tape machine",
 tm="How Echoflex models the EP103 / EP-3 sound:",
 tm_b=["<b>Record head</b> &ndash; a low-pass filter (9.5 kHz, down to 3.6 kHz with AGE) and gentle tape compression before the signal is written to the tape.",
       "<b>Tape</b> &ndash; a 4-second delay memory read with Hermite interpolation, so the speed can change smoothly without clicks.",
       "<b>Transport</b> &ndash; wow at 0.55 Hz, flutter at 7.3 and 11.7 Hz, a slow random drift and occasional level drops. All of them are very light on clear tape and grow with AGE. The motor has about 110 ms of inertia when the delay time changes.",
       "<b>Feedback loop</b> &ndash; each repeat goes through a high-pass (95 to 215 Hz) and a low-pass (7.2 kHz, down to 2.5 kHz) and through tape saturation: the repeats get thinner, darker and rounder, as on a tape echo. The saturation also keeps self-oscillation under control.",
       "<b>EP101 preamp</b> &ndash; applied to the echoes only: +1.5 dB at 180 Hz, +2.5 dB presence around 3 kHz and soft saturation.",
       "<b>Output</b> &ndash; dry signal at unity + echoes &times; VOLUME, then a transparent soft limiter that only acts above &minus;0.3 dBFS."],
 s14="Factory presets",
 fp="Choose them in Right-click &rsaquo; Factory presets, in your DAW's preset menu or by MIDI Program Change 1-10. Each card shows the pedal as the preset sets it.",
 off="off",
 pdesc=["All knobs at noon, clear tape &ndash; the starting point recommended by the pedal's manual.",
        "One short, slightly worn repeat: 1950s rock'n'roll and rockabilly vocals.",
        "A tight double echo for rhythm parts and chicken picking.",
        "Clear 157 ms echo with a few repeats &ndash; spring-and-tape surf sound.",
        "The classic lead setting: a warm echo around 390 ms tucked under the solo.",
        "Long, clean wash for ambient chords and swells.",
        "AGE at 10: dark, wobbly, saturated repeats from an old cartridge.",
        "Long, very dark trails for slow, atmospheric playing.",
        "Repeats that keep coming back &ndash; play a short phrase and ride SUSTAIN and DELAY.",
        "SUSTAIN at maximum: the echo oscillates by itself. Turn DELAY for sirens; lower SUSTAIN to stop it."],
 s15="User presets",
 up="Save up to 9 presets of your own: Right-click &rsaquo; Save user preset &rsaquo; User 1 to 9, and recall them with Load user preset. A user preset stores DELAY, SUSTAIN, VOLUME, AGE amount, AGE on/off, the delay-time source, the tapped time and the sync division. All slots are shared by every project, in one file:",
 up_b=["Windows: " + mono("%APPDATA%\\NINE HANDS | DSP\\Echoflex\\UserPresets.xml"), "macOS: " + mono("~/Library/NINE HANDS | DSP/Echoflex/UserPresets.xml")],
 up_note="User presets hold the sound only. The MIDI assignments (section 16) are saved with each project, so recalling a preset never changes your pedalboard mapping.",
 s16="MIDI",
 midi="Send MIDI to the Echoflex track (in Reaper: enable MIDI input on the track, or route a MIDI track to it). Echoflex listens on every MIDI channel. <b>No CC is assigned by default</b>: each of the nine controls below is assigned to your controller with <b>MIDI Learn</b>.",
 mt=[["Control", "Type"], ["Delay", "Continuous: 0-127 &rarr; 0-10 (in SYNC: note value)"], ["Sustain", "Continuous"], ["Volume", "Continuous"],
     ["Age amount", "Continuous"], ["Age on/off", "Switch: 64-127 AGE on, 0-63 clear tape"], ["Tap", "Button: each press crossing 64 is a tap"],
     ["Footswitch", "Switch (latching): 64-127 on, 0-63 off"], ["Footswitch toggle", "Button (momentary): each press toggles on / off"],
     ["Sync", "Switch: 64-127 delay locked to the DAW tempo, 0-63 DELAY knob"],
     ["Program Change 1-10", "Factory presets 1 to 10 (fixed, no learning needed)"]],
 ml_h="MIDI Learn",
 ml_steps=[("Right-click the control.", "The menu starts with <b>MIDI Learn: Sustain (CC n)</b>, which shows the current number, or a dash (&mdash;) when nothing is assigned. VOLUME offers Volume, Age amount and Age on/off; the footswitch offers Footswitch and Footswitch toggle; the TAP jack offers Tap; the SYNC LED offers Sync."),
           ("Choose it.", "The status line reads <b>MIDI LEARN: move a control for Sustain</b>."),
           ("Move the expression pedal or press the MIDI button.", "The first CC received is assigned to the control (it does not change the sound) and the status line confirms it for 2 seconds, e.g. <b>Sustain = CC 64</b>.")],
 ml_b=["<b>Clear MIDI: Sustain</b> removes the assignment (status line: <i>Sustain = &mdash;</i>); <b>Cancel MIDI learn</b> stops waiting without changing anything.",
       "A CC drives only one control: learning a number that was already used unassigns the other control.",
       "Right-click anywhere else &rsaquo; <b>MIDI</b>: the nine controls with their current CC (<b>Learn: Delay (&mdash;)</b> &hellip; choose one to learn it), <b>Cancel MIDI learn</b> while waiting and <b>Clear all MIDI assignments</b> (status line: <i>MIDI: all assignments cleared</i>).",
       "The assignments are <b>saved with the project</b>. A project saved with an earlier version that still used the former factory CC numbers opens with no assignment; a project in which you had changed an assignment keeps its assignments. CC 0 to 119 can be learnt (120-127 are channel mode messages)."],
 ml_note="Every parameter can also be automated and assigned with your DAW's own MIDI learn: Delay, Sustain, Volume, Age, Age On, Footswitch, Bypass, Mix, Channels, Time Source, Sync Division and Tap Time.",
 s17="Sound tips &amp; troubleshooting",
 tips=[("Slapback", "DELAY 1.5 to 2.5, SUSTAIN 0 to 1.5, VOLUME 6 to 7, AGE 3 to 5. Play short, staccato notes."),
       ("Thickening a lead", "DELAY 6.5 to 7.5, SUSTAIN about 4.5, VOLUME 4 to 5: the echo sits just under the solo."),
       ("Ambient", "DELAY 8.5 to 10 (or tap a long time), SUSTAIN 6.5 to 8, AGE 6 to 9 for blurred, warm trails. Try Trails bypass."),
       ("Tape sirens", "SUSTAIN 9 to 10, VOLUME 7, then sweep DELAY slowly: the motor inertia bends the pitch."),
       ("Rhythmic echoes", "Click DELAY to switch SYNC on and turn DELAY to 1/8 dotted (between 5 and 6.25) for the classic cascading rhythm."),
       ("Expression pedal", "Learn SUSTAIN or AGE amount on your expression pedal (right-click &rsaquo; MIDI Learn) to swell the repeats or wear the tape while you play.")],
 tr_h="Troubleshooting",
 tr=[("The echoes do not change when I turn DELAY.", "That is normal if the time came from TAP or sync: the first turn of DELAY gives control back to the knob. Check the second line of the status line."),
     ("The sound keeps growing.", "SUSTAIN is near the maximum: that is self-oscillation. Lower SUSTAIN or VOLUME."),
     ("Nothing happens when I click VOLUME.", "Click without moving the mouse. A drag turns the knob; a short click toggles AGE; holding still for 2 s enters AGE adjust mode."),
     ("No echo after Ampire / an amp sim.", "Check Startup settings &rsaquo; Mix: in 100 % wet the dry signal is removed. Check also that the footswitch LED is lit."),
     ("My MIDI pedal does nothing.", "The track must receive MIDI, and no CC is assigned by default: right-click the control &rsaquo; MIDI Learn. Right-click &rsaquo; MIDI shows the CC of each control."),
     ("The window is too small.", "Right-click &rsaquo; Plugin size &rsaquo; 75 % / 100 %, or drag the corner. To open every new window bigger: Plugin size &rsaquo; Default size (new windows). It cannot be smaller than 60 %."),
     ("The SYNC LED stays dim.", "The host sends no tempo to the plug-in. In Reaper this cannot happen; in other hosts, check that the plug-in is on a normal track."),
     ("The display froze (older versions).", "Fixed by the anti-freeze v2 (v1.3): software rendering under Windows, redraw only when something changes, a watchdog that restarts the display, and no call to the host from the audio thread.")],
 s18="Specifications",
 spec=[["Format", "VST3 &middot; Windows 11 (x64) &middot; macOS 10.13+ (Apple Silicon + Intel)"], ["Inputs / outputs", "mono or stereo in &middot; stereo or mono out"],
       ["Latency", "0 samples"], ["Delay time", "65 &ndash; 750 ms (knob) &middot; up to 4 s (tap or sync)"], ["Delay memory", "4.3 s, Hermite interpolation"],
       ["Sample rates", "all rates supported by the host"], ["Presets", "10 factory &middot; 9 user"],
       ["MIDI", "9 controls with MIDI Learn (no CC assigned by default), saved with the project &middot; all channels &middot; Program Change 1-10 &middot; every parameter automatable"],
       ["Window", "Plugin size 60 % (minimum) &middot; 75 % &middot; 100 %, up to 150 % by dragging, proportions locked &middot; default size for new windows selectable"],
       ["Display", "anti-freeze v2 under Windows (software rendering, watchdog, no host call from the audio thread)"],
       ["Tail", "12 s reported to the host (trails)"], ["Version", VERSION]],
 cred_h="Credits &amp; sources",
 cred=["Plug-in, sound model and manual: NINE HANDS | DSP. Pedal visual: Echoflex by NINE HANDS | DSP.", "NINE HANDS | DSP logo typeface: Montserrat (SIL Open Font License).",
       "Sources: Dunlop EP103 Echoplex Delay manual (jimdunlop.com); product pages zZounds and Chicago Music Exchange; Premier Guitar EP103 review; Starlite Campbell, \u201cThe Maestro Echoplex EP-3\u201d.",
       "Echoplex&reg; and Dunlop&reg; are trademarks of their respective owners. Echoflex is a personal, independent tribute."]),
"fr": dict(
 lang="FRANÇAIS", sub="Écho à bande &middot; VST3 &middot; Windows &amp; macOS", ver="Notice d'utilisation &middot; version " + VERSION,
 foot="Echoflex &middot; NINE HANDS | DSP &middot; Notice d'utilisation &middot; v" + VERSION,
 about_h="À propos de cette notice",
 about="Echoflex est un plug-in à usage personnel de NINE HANDS | DSP qui reproduit la pédale Dunlop EP103 Echoplex&reg; Delay, elle-même hommage compact à l'écho à bande Maestro Echoplex EP-3. Cette notice décrit chaque réglage, chaque fonction cachée et la façon dont le son a été modélisé. Elle correspond à la version " + VERSION + ". Echoplex est une marque de son propriétaire ; Echoflex est un hommage indépendant, sans lien avec elle.",
 s01="Introduction", legend_h="La légende",
 legend=["Le Maestro Echoplex EP-3 a été fabriqué de 1970 à 1991, la plus longue carrière de tous les Echoplex. À l'intérieur, une boucle de bande dans une cartouche amovible défile devant une tête d'effacement, une tête d'enregistrement et une tête de lecture ; l'écart entre les têtes et la vitesse de la bande fixent le retard. Son préampli à transistors, traversé par tout le signal, est devenu célèbre à lui seul pour sa façon d'adoucir et d'épaissir une guitare.",
         "L'EP-3 était aussi gros, lourd et capricieux : bande usée, têtes sales et galet presseur fatigué faisaient onduler l'écho (pleurage et scintillement) et l'assombrissaient. Beaucoup de guitaristes adoraient justement ces défauts."],
 pedal_h="La pédale",
 pedal="La Dunlop EP103 met ce son dans un boîtier de la taille d'une Phase 90 : une émulation numérique d'écho à bande à 96 kHz avec un trajet direct entièrement analogique, trois potards (DELAY, SUSTAIN, VOLUME), un mode AGE caché sous le potard VOLUME, une prise tap tempo et quelques options de démarrage (trails, 100 % wet, stéréo).",
 rec_h="Ce que reproduit Echoflex",
 rec=["Les trois mêmes réglages, plages et sensations : 65 à 750 ms, peu de répétitions sur la première moitié de SUSTAIN puis une montée presque exponentielle jusqu'à l'auto-oscillation, VOLUME qui règle uniquement l'écho.",
      "La voix « bande neuve » par défaut : répétitions claires, pleurage et scintillement subtils, préampli EP101 qui colore uniquement les échos.",
      "Le mode AGE exactement comme sur la pédale : clic sur VOLUME pour l'activer ou le couper, maintien 2 secondes pour le régler, nouveau clic pour verrouiller.",
      "L'inertie du moteur de bande : tourner DELAY fait glisser la hauteur des répétitions comme sur un vrai écho à bande.",
      "Le tap tempo jusqu'à 4 secondes (clic sur la prise TAP), et une LED SYNC pour caler le delay sur le tempo de Reaper ou de n'importe quel DAW.",
      "True bypass ou trails, 100 % wet, mono ou stéréo : les réglages de démarrage de la pédale, dans le menu clic droit.",
      "10 presets d'usine, 9 emplacements utilisateur, contrôle MIDI complet (MIDI Learn) et automation."],
 s02="Installation", build_h="Compiler avec GitHub",
 build=["Déposer tous les fichiers du projet à la racine du dépôt : " + mono("background.jpg") + ", " + mono("knob_strip.png") + ", " + mono("CMakeLists.txt") + ", " + mono("PluginProcessor.h/.cpp") + ", " + mono("PluginEditor.h/.cpp") + ", " + mono("README.md") + ", " + mono("Montserrat-OFL.txt") + " et le dossier " + mono(".github/workflows/build.yml") + ".",
        "Faire un push. L'onglet <b>Actions</b> compile le plug-in pour Windows (windows-2022) et macOS (binaire universel Apple Silicon + Intel).",
        "Télécharger l'artefact <b>Echoflex-VST3-Windows</b> ou <b>Echoflex-VST3-macOS</b>."],
 inst_h="Installer",
 inst=["<b>Windows 11</b> : copier " + mono("Echoflex.vst3") + " dans " + mono("C:\\Program Files\\Common Files\\VST3\\") + ".",
       "<b>macOS</b> : dézipper puis copier " + mono("Echoflex.vst3") + " dans " + mono("~/Library/Audio/Plug-Ins/VST3/") + ". Le plug-in est signé ad hoc ; si macOS le bloque, l'autoriser dans Réglages Système &rsaquo; Confidentialité et sécurité.",
       "Relancer l'analyse des plug-ins dans le DAW. Echoflex apparaît sous le nom <b>Echoflex (NINE HANDS | DSP)</b> dans la catégorie Delay."],
 where_h="Où le placer dans Reaper", chain=["Guitare", "Echoflex", "Ampire", "Impulse", "Master"],
 where="Comme les autres plug-ins NINE HANDS | DSP, placer Echoflex <b>avant</b> le simulateur d'ampli (Ampire, puis Impulse). En mode Mono (par défaut, comme la pédale), le même écho part à gauche et à droite, sans signal inversé : rien ne s'annule quand le simulateur additionne la piste en mono. Pour entendre les échos après l'ampli, comme un EP-3 dans une boucle d'effets, le placer plutôt après le simulateur.",
 s03="Vue d'ensemble",
 ov=[("VOLUME / PUSH FOR AGE", "niveau de l'écho. Clic : AGE on/off. Maintien 2 s : réglage de l'AGE."), ("SUSTAIN", "nombre de répétitions, jusqu'à l'auto-oscillation."),
     ("DELAY", "temps de retard, de 65 à 750 ms."), ("LED AGE (ambre)", "allumée quand l'AGE est actif, clignote pendant le réglage."),
     ("LED d'effet (rouge)", "allumée quand l'effet est actif ; sa lueur respire avec les répétitions."), ("Footswitch", "clic pour activer ou couper l'effet."),
     ("Prise TAP", "cliquer plusieurs fois en rythme pour taper un tempo (jusqu'à 4 s)."), ("INPUT", "entrée du plug-in (mono ou stéréo)."), ("OUTPUT", "sortie du plug-in (stéréo)."),
     ("Ligne d'état", "apparaît quand un réglage bouge, puis s'efface au bout de 2,5 s."),
     ("LED SYNC (verte)", "clic sur DELAY ou sur la LED pour caler le delay sur le tempo du DAW ; flashe en rythme.")],
 ov_note="Un clic droit n'importe où sur la pédale ouvre le menu (Plugin size, presets, AGE, source du temps de retard, réglages de démarrage, MIDI) ; un clic droit sur une commande donne son MIDI Learn.",
 s04="DELAY",
 delay="Règle le temps entre la note et son écho, de <b>65 ms</b> (slapback) à <b>750 ms</b>. Le potard suit une courbe logarithmique : les retards courts du slapback et du doublage ont autant de place que les longs. À midi, on est vers 220 ms.",
 knob_hdr=["Potard", "Temps"], knob_caps=["0 &middot; 65 ms", "5 &middot; 221 ms", "10 &middot; 750 ms"],
 delay_more=["<b>Inertie du moteur de bande.</b> Sur un écho à bande, changer le retard change la vitesse de la bande : la hauteur des répétitions glisse vers le haut ou le bas jusqu'à ce que le moteur se stabilise. Echoflex fait pareil (environ 110 ms d'inertie) : tournez DELAY pendant que les répétitions sonnent pour les glissandos et sirènes classiques.",
             "<b>Tap et SYNC.</b> Après un tap, la position du potard est ignorée jusqu'à ce qu'on tourne à nouveau DELAY, exactement comme sur la pédale. En SYNC, DELAY choisit une valeur de note du tempo du DAW au lieu d'un temps (voir « Synchro sur le tempo du DAW »)."],
 s05="SUSTAIN",
 sus="Règle la part de l'écho renvoyée sur la bande, donc le nombre de répétitions. Comme sur l'EP103, le potard est volontairement inégal :",
 sus_b=["<b>0 &rarr; 5</b> : doux, une à quatre répétitions audibles : slapback, doublage, ambiance courte.",
        "<b>5 &rarr; 8</b> : les répétitions se multiplient vite ; chacune est un peu plus sombre et usée que la précédente.",
        "<b>8 &rarr; 10</b> : longues traînées puis <b>auto-oscillation</b> au maximum : l'écho s'alimente lui-même et grandit jusqu'à la saturation de la bande. Baisser SUSTAIN pour le calmer."],
 sus_more="SUSTAIN et VOLUME interagissent un peu, comme sur la pédale : plus l'écho est fort, plus il se réinjecte. En haut de SUSTAIN, un petit mouvement de VOLUME change nettement le comportement ; la pédale est décrite comme « sensible et nerveuse » à cet endroit, Echoflex aussi.",
 sus_warn="L'auto-oscillation peut devenir forte. La sortie est protégée par un limiteur doux, mais gardez un niveau d'écoute raisonnable quand vous poussez SUSTAIN au maximum.",
 s06="VOLUME",
 vol="Règle uniquement le niveau des échos. Le son direct reste toujours à l'unité et n'est jamais traité (sur la pédale, le trajet direct est entièrement analogique).",
 vol_hdr=["Potard", "Niveau d'écho"], vol_vals=["&minus;&infin;", "&minus;26,8 dB", "&minus;17,7 dB", "&minus;12,5 dB", "&minus;8,7 dB", "&minus;5,8 dB", "&minus;3,4 dB", "&minus;1,4 dB", "0,3 dB", "1,9 dB", "3,2 dB"],
 vol_more="Baissé, l'écho se glisse derrière le jeu ; vers 8, il égale la note directe ; au-delà, les premières répétitions sont plus fortes que la note elle-même, comme sur un EP-3.",
 vol_note="Le potard VOLUME est aussi un bouton poussoir : voir le mode AGE.",
 s07="Mode AGE",
 age="Par défaut, Echoflex sonne comme un écho à bande fraîchement réglé : répétitions claires et brillantes, pleurage et scintillement très discrets. L'AGE le transforme en vieille machine bien usée : répétitions plus sombres, plus de saturation de bande, modulation plus profonde et plus aléatoire, et les petites pertes de niveau d'une bande fatiguée.",
 age_h="Utiliser l'AGE, exactement comme sur la pédale",
 age_steps=[("Cliquer sur VOLUME", "Bascule entre votre réglage AGE et le son clair d'usine. La LED AGE ambre est allumée quand l'AGE est actif, éteinte pour le son clair."),
            ("Maintenir VOLUME 2 s", "La LED AGE se remplit pendant l'appui, puis clignote : vous êtes en mode réglage AGE. Le potard VOLUME affiche et règle maintenant la quantité d'AGE (0 = bande neuve, 10 = bande usée). La ligne d'état indique « push VOLUME to lock »."),
            ("Cliquer à nouveau sur VOLUME", "Verrouille le réglage AGE et rend le potard au VOLUME. Le niveau d'écho n'a pas changé.")],
 age_caps=["AGE coupé : bande neuve", "AGE actif : LED allumée"], age_adj_cap="Réglage de l'AGE : la LED clignote, le potard affiche la valeur",
 age_t=[["", "Bande neuve (AGE coupé)", "AGE à 10"], ["Répétitions", "brillantes, claires", "sombres, arrondies"], ["Filtres enregistrement / boucle", "9,5 kHz / 7,2 kHz", "3,6 kHz / 2,5 kHz"],
        ["Pleurage (dérive lente)", "&plusmn; 0,14 ms à 0,55 Hz", "&plusmn; 2,2 ms à 0,8 Hz"], ["Scintillement (rapide)", "à peine audible", "bien audible"],
        ["Dérive aléatoire", "très légère", "forte, la modulation paraît aléatoire"], ["Saturation de bande", "légère", "forte, un peu asymétrique"],
        ["Pertes de niveau", "aucune", "jusqu'à &minus;3,5 dB"], ["Souffle", "inaudible", "léger, suit l'écho"]],
 age_note="L'AGE est aussi disponible dans le menu clic droit (Age &rsaquo; Age on / Set Age), en MIDI (<b>Age amount</b> et <b>Age on/off</b>, assignés par MIDI Learn) et en automation (paramètres Age et Age On).",
 s08="Tap tempo",
 tap="L'EP103 a une prise TAP pour un switch externe MXR M199. Sur Echoflex, c'est la prise elle-même qui sert de switch : <b>cliquez sur la prise TAP</b> (en bas à gauche de la pédale) en rythme. L'écrou et l'inscription TAP s'éclairent à chaque appui, et la ligne d'état affiche le nouveau temps.",
 tap_cap="Tap : la prise TAP s'éclaire et la ligne d'état affiche le temps tapé.",
 tap_b=["Deux appuis suffisent ; Echoflex fait la moyenne des trois derniers intervalles pour un tempo stable.",
        "Les appuis espacés de 60 ms à 4,2 s sont acceptés ; le temps est limité à 4 secondes, comme sur la pédale.",
        "Un intervalle très différent du précédent (plus de 35 %) relance la moyenne : on passe d'un tempo à un autre immédiatement.",
        "Une pause de plus de 4,2 s démarre une nouvelle série d'appuis.", "Tourner DELAY rend la main au potard, comme sur la pédale.",
        "MIDI : une fois <b>Tap</b> assigné par MIDI Learn, chaque appui sur ce CC (valeur qui passe 64) est un tap."],
 tap_note="Pour suivre automatiquement le tempo du morceau, utilisez plutôt SYNC (section suivante).",
 s09="Synchro sur le tempo du DAW (SYNC)",
 sync="Echoflex peut caler son temps de retard sur le tempo de Reaper ou de n'importe quel autre DAW. Une <b>LED SYNC</b> verte, à côté de l'inscription DELAY, indique que le delay suit le tempo du morceau.",
 sync_steps=[("Cliquer sur le mot DELAY (ou sur la LED SYNC)", "La LED SYNC s'allume en vert : le delay suit maintenant le tempo du DAW. Un nouveau clic revient au potard DELAY."),
             ("Tourner DELAY pour choisir la valeur de note", "En SYNC, le potard DELAY ne règle plus des millisecondes : il passe par 8 valeurs de note, de la double croche 1/16 (tout à gauche) à la blanche 1/2 (tout à droite). La ligne d'état affiche la valeur de note, le tempo et le temps réel en ms."),
             ("Raccourcis", "Molette sur le mot DELAY / la LED SYNC : valeur de note précédente ou suivante. Clic droit dessus : menu des valeurs de note (Sync on, 1/2 &hellip; 1/16), avec MIDI Learn: Sync en tête. MIDI (<b>Sync</b>, assigné par MIDI Learn) : SYNC activé (64-127) ou coupé (0-63).")],
 sync_caps=["SYNC coupé : le potard règle le temps", "SYNC activé : LED verte, le potard règle la valeur de note"],
 sync_t=[["Potard DELAY", "Valeur de note", "à 120 BPM"], ["0 &ndash; 1,25", "1/16 (double croche)", "125 ms"], ["1,25 &ndash; 2,5", "1/8 triolet", "167 ms"], ["2,5 &ndash; 3,75", "1/8 (croche)", "250 ms"],
         ["3,75 &ndash; 5", "1/4 triolet", "333 ms"], ["5 &ndash; 6,25", "1/8 pointée", "375 ms"], ["6,25 &ndash; 7,5", "1/4 (noire)", "500 ms"],
         ["7,5 &ndash; 8,75", "1/4 pointée", "750 ms"], ["8,75 &ndash; 10", "1/2 (blanche)", "1000 ms"]],
 daw_h="Dans Reaper (ou un autre DAW)",
 daw="Rien à régler : l'hôte VST3 envoie son tempo au plug-in. Quand le projet joue, la LED SYNC flashe exactement sur chaque valeur de note de la grille du morceau ; à l'arrêt, le delay suit quand même le tempo du projet et la LED flashe librement. Les changements et l'automation de tempo sont suivis en temps réel (le moteur de bande glisse vers le nouveau temps). Si l'hôte n'envoie pas de tempo, la LED reste faible et c'est le temps du potard DELAY qui est utilisé.",
 sync_cap="Ligne d'état en SYNC : temps réel, valeur de note et tempo du DAW.",
 sync_b=["SYNC est enregistré avec le projet et dans les presets utilisateur ; il s'automatise avec le paramètre Time Source.",
         "Un tap sur la prise TAP quitte SYNC et utilise le temps tapé ; cliquez sur DELAY pour revenir en SYNC.",
         "Les temps sont limités à 65 ms &ndash; 4 s : aux tempos très lents, les longues valeurs de note sont plafonnées à 4 s."],
 s10="LED, footswitch et ligne d'état",
 fs_h="Footswitch et LED d'effet",
 fs=["Cliquez sur le footswitch pour activer ou couper l'effet. La LED rouge s'allume et s'éteint en fondu ; allumée, sa lueur respire légèrement avec le niveau des répétitions.",
     "En <b>True bypass</b> (par défaut), les échos s'arrêtent avec l'effet ; en <b>Trails</b>, ils s'éteignent naturellement après la coupure (voir Réglages de démarrage)."],
 fs_caps=["Effet actif", "Bypass"],
 aled_h="LED AGE",
 aled="Ambre. Éteinte = bande neuve, allumée = AGE actif, clignotante = réglage de l'AGE, qui se remplit = vous maintenez VOLUME. La <b>LED SYNC</b> verte flashe sur le tempo du DAW quand SYNC est activé (voir la section précédente).",
 st_h="Ligne d'état",
 st="Elle apparaît sous la LED d'effet dès qu'un réglage bouge (souris, automation ou MIDI), reste 2,5 secondes et s'efface en fondu.",
 st_b=["<b>Première ligne</b> : le temps de retard réel en ms (potard, tap ou synchro), SUSTAIN et VOLUME, ou la valeur d'AGE pendant le réglage.",
       "<b>Deuxième ligne</b> : état de l'AGE (CLEAR TAPE ou AGE x.x), TAP / SYNC, BYPASS, preset en cours et dernier message MIDI reçu (elle passe au rouge à chaque message ou tap)."],
 s11="Menu clic droit",
 rc="Clic droit n'importe où sur la pédale. Sur une commande (un potard, le footswitch ou la prise TAP), le menu commence par les lignes <b>MIDI Learn</b> de cette commande (voir 16 &middot; MIDI) ; un clic droit sur la LED SYNC ouvre le menu des valeurs de note, avec <b>MIDI Learn: Sync</b> en tête. Le menu est en anglais, comme sur les autres plug-ins NINE HANDS | DSP.",
 menu=[("SEULEMENT SUR UNE COMMANDE (ici SUSTAIN, pas encore assigné)", ["MIDI Learn: Sustain (" + DASH + ")", "Clear MIDI: Sustain (grisé tant que rien n'est assigné)", "Cancel MIDI learn (pendant l'attente d'un CC)"], True),
       ("Plugin size &rsaquo;", ["60 %  (default) &middot; 75 % &middot; 100 % &middot; Default size (new windows) &rsaquo; 60 % / 75 % / 100 %"], False),
       ("Factory presets &rsaquo;", ["1. Noon (Manual Start) &hellip; 10. Runaway Oscillation"], False),
       ("Load user preset &rsaquo;", ["User 1 &hellip; User 9"], False), ("Save user preset &rsaquo;", ["User 1 &hellip; User 9"], False),
       ("Age &rsaquo;", ["Age on (click VOLUME) &middot; Set Age (hold VOLUME 2 s)"], False),
       ("Delay time &rsaquo;", ["DELAY knob (65 - 750 ms) &middot; Tap tempo (&hellip; ms) - click TAP &middot; Sync to DAW tempo (click DELAY / SYNC) &rsaquo; 1/2 &hellip; 1/16"], False),
       ("Startup settings &rsaquo;", ["True relay bypass / Trails bypass &middot; Dry + echo / 100% wet (kill dry) &middot; Mono (EP103 default) / Stereo"], False),
       ("MIDI &rsaquo;", ["Learn: Delay (" + DASH + ") &hellip; Learn: Sync (" + DASH + ") &middot; Cancel MIDI learn (pendant l'attente) &middot; Clear all MIDI assignments &middot; Program Change 1-10  Factory presets"], False),
       ("Echoflex delay v" + VERSION + " - NINE HANDS | DSP", [], False)],
 win_h="Taille du plugin",
 win=["La fenêtre s'ouvre à la taille par défaut, 60 % au départ, et ne peut jamais être réduite sous 60 %. Choisissez <b>60 %</b>, <b>75 %</b> ou <b>100 %</b> dans Clic droit &rsaquo; <b>Plugin size</b> (<b>(default)</b> est indiqué à côté de la taille par défaut), ou tirez le coin inférieur droit pour l'agrandir (proportions bloquées, jusqu'à 150 %).",
      "<b>Plugin size &rsaquo; Default size (new windows)</b> choisit la taille d'ouverture de toutes les nouvelles fenêtres d'Echoflex : le réglage est commun à toutes les instances et enregistré sur l'ordinateur, et la fenêtre ouverte prend aussitôt cette taille."],
 s12="Réglages de démarrage",
 su="Sur l'EP103, ces options se règlent en allumant la pédale tout en maintenant VOLUME, puis en lisant la couleur de la LED AGE. Sur Echoflex, elles sont simplement dans Clic droit &rsaquo; <b>Startup settings</b>, et elles sont enregistrées avec le projet.",
 su_t=[["Réglage", "Choix", "Effet"], ["<b>Bypass</b>", "True relay bypass (défaut) / Trails bypass", "True bypass : les échos s'arrêtent à la coupure. Trails : l'entrée n'alimente plus la bande mais les échos déjà enregistrés continuent de s'éteindre."],
       ["<b>Mix</b>", "Dry + echo (défaut) / 100% wet", "100 % wet retire le son direct, pour un bus parallèle ou un départ d'effet."],
       ["<b>Channels</b>", "Mono (défaut) / Stereo", "Mono : l'entrée est additionnée et le même écho part des deux côtés. Stéréo : gauche et droite ont chacune leur propre bande."]],
 su_note="Comme sur la pédale, le son direct n'est jamais traité, quel que soit le mode.",
 s13="Dans la machine à bande",
 tm="Comment Echoflex modélise le son de l'EP103 / EP-3 :",
 tm_b=["<b>Tête d'enregistrement</b> : un passe-bas (9,5 kHz, jusqu'à 3,6 kHz avec l'AGE) et une légère compression de bande avant l'écriture sur la bande.",
       "<b>Bande</b> : une mémoire de 4 secondes lue avec une interpolation d'Hermite, pour que la vitesse puisse changer en douceur, sans clic.",
       "<b>Entraînement</b> : pleurage à 0,55 Hz, scintillement à 7,3 et 11,7 Hz, dérive aléatoire lente et pertes de niveau occasionnelles. Tout est très léger sur bande neuve et grandit avec l'AGE. Le moteur a environ 110 ms d'inertie quand le temps change.",
       "<b>Boucle de réinjection</b> : chaque répétition traverse un passe-haut (95 à 215 Hz), un passe-bas (7,2 kHz, jusqu'à 2,5 kHz) et la saturation de bande : les répétitions deviennent plus fines, plus sombres et plus rondes, comme sur un écho à bande. La saturation tient aussi l'auto-oscillation sous contrôle.",
       "<b>Préampli EP101</b> : appliqué aux échos seulement : +1,5 dB à 180 Hz, +2,5 dB de présence vers 3 kHz et saturation douce.",
       "<b>Sortie</b> : son direct à l'unité + échos &times; VOLUME, puis un limiteur doux transparent qui n'agit qu'au-dessus de &minus;0,3 dBFS."],
 s14="Presets d'usine",
 fp="À choisir dans Clic droit &rsaquo; Factory presets, dans le menu de presets du DAW ou en MIDI Program Change 1 à 10. Chaque fiche montre la pédale telle que le preset la règle.",
 off="coupé",
 pdesc=["Tous les potards à midi, bande neuve : le point de départ conseillé par le manuel de la pédale.",
        "Une seule répétition courte, un peu usée : rock'n'roll et voix rockabilly des années 50.",
        "Un double écho serré pour les rythmiques et le chicken picking.",
        "Écho clair de 157 ms avec quelques répétitions : son surf ressort et bande.",
        "Le réglage solo classique : un écho chaud vers 390 ms glissé sous le chorus.",
        "Longue nappe claire pour les accords et les swells ambiants.",
        "AGE à 10 : répétitions sombres, ondulantes et saturées d'une vieille cartouche.",
        "Longues traînées très sombres pour un jeu lent et atmosphérique.",
        "Des répétitions qui reviennent sans cesse : jouez une courte phrase et jouez avec SUSTAIN et DELAY.",
        "SUSTAIN au maximum : l'écho oscille tout seul. Tournez DELAY pour les sirènes ; baissez SUSTAIN pour l'arrêter."],
 s15="Presets utilisateur",
 up="Enregistrez jusqu'à 9 presets personnels : Clic droit &rsaquo; Save user preset &rsaquo; User 1 à 9, et rappelez-les avec Load user preset. Un preset utilisateur garde DELAY, SUSTAIN, VOLUME, la quantité d'AGE, AGE on/off, la source du temps de retard, le temps tapé et la division de synchro. Les emplacements sont communs à tous les projets, dans un seul fichier :",
 up_b=["Windows : " + mono("%APPDATA%\\NINE HANDS | DSP\\Echoflex\\UserPresets.xml"), "macOS : " + mono("~/Library/NINE HANDS | DSP/Echoflex/UserPresets.xml")],
 up_note="Les presets utilisateur ne gardent que le son. Les assignations MIDI (section 16) sont sauvegardées avec chaque projet : rappeler un preset ne change jamais le réglage de votre pédalier.",
 s16="MIDI",
 midi="Envoyez le MIDI sur la piste d'Echoflex (dans Reaper : activer l'entrée MIDI de la piste, ou router une piste MIDI vers elle). Echoflex écoute tous les canaux MIDI. <b>Aucun CC n'est assigné d'office</b> : chacune des neuf commandes ci-dessous s'assigne à votre contrôleur avec le <b>MIDI Learn</b>.",
 mt=[["Commande", "Type"], ["Delay", "Continu : 0-127 &rarr; 0-10 (en SYNC : valeur de note)"], ["Sustain", "Continu"], ["Volume", "Continu"],
     ["Age amount (quantité d'AGE)", "Continu"], ["Age on/off", "Bascule : 64-127 AGE actif, 0-63 bande neuve"], ["Tap", "Bouton : chaque appui qui passe 64 est un tap"],
     ["Footswitch", "Bascule (à accrochage) : 64-127 actif, 0-63 coupé"], ["Footswitch toggle", "Bouton (momentané) : chaque appui inverse actif / coupé"],
     ["Sync", "Bascule : 64-127 delay calé sur le tempo du DAW, 0-63 potard DELAY"],
     ["Program Change 1-10", "Presets d'usine 1 à 10 (fixe, sans apprentissage)"]],
 ml_h="MIDI Learn",
 ml_steps=[("Clic droit sur la commande.", "Le menu commence par <b>MIDI Learn: Sustain (CC n)</b>, qui indique le numéro actuel, ou un tiret (&mdash;) si rien n'est assigné. VOLUME propose Volume, Age amount et Age on/off ; le footswitch propose Footswitch et Footswitch toggle ; la prise TAP propose Tap ; la LED SYNC propose Sync."),
           ("Choisissez-le.", "La ligne d'état affiche <b>MIDI LEARN: move a control for Sustain</b>."),
           ("Bougez la pédale d'expression ou appuyez sur le bouton MIDI.", "Le premier CC reçu est affecté à la commande (il ne change pas le son) et la ligne d'état le confirme pendant 2 secondes, par ex. <b>Sustain = CC 64</b>.")],
 ml_b=["<b>Clear MIDI: Sustain</b> retire l'assignation (ligne d'état : <i>Sustain = &mdash;</i>) ; <b>Cancel MIDI learn</b> arrête l'attente sans rien changer.",
       "Un CC ne pilote qu'une seule commande : apprendre un numéro déjà utilisé désassigne l'autre commande.",
       "Clic droit ailleurs &rsaquo; <b>MIDI</b> : les neuf commandes avec leur CC actuel (<b>Learn: Delay (&mdash;)</b> &hellip; en choisir une lance son apprentissage), <b>Cancel MIDI learn</b> pendant l'attente et <b>Clear all MIDI assignments</b> (ligne d'état : <i>MIDI: all assignments cleared</i>).",
       "Les assignations sont <b>sauvegardées avec le projet</b>. Un projet enregistré avec une version précédente resté sur les anciens numéros de CC d'usine s'ouvre sans aucune assignation ; un projet où vous aviez changé une assignation garde ses assignations. Les CC 0 à 119 peuvent être appris (120-127 sont des messages de mode de canal)."],
 ml_note="Chaque paramètre peut aussi être automatisé et assigné avec le MIDI learn du DAW : Delay, Sustain, Volume, Age, Age On, Footswitch, Bypass, Mix, Channels, Time Source, Sync Division et Tap Time.",
 s17="Conseils de son et dépannage",
 tips=[("Slapback", "DELAY 1,5 à 2,5, SUSTAIN 0 à 1,5, VOLUME 6 à 7, AGE 3 à 5. Jouez des notes courtes et piquées."),
       ("Épaissir un solo", "DELAY 6,5 à 7,5, SUSTAIN vers 4,5, VOLUME 4 à 5 : l'écho se glisse juste sous le solo."),
       ("Ambiance", "DELAY 8,5 à 10 (ou un long temps tapé), SUSTAIN 6,5 à 8, AGE 6 à 9 pour des traînées floues et chaudes. Essayez le Trails bypass."),
       ("Sirènes de bande", "SUSTAIN 9 à 10, VOLUME 7, puis tournez DELAY lentement : l'inertie du moteur fait glisser la hauteur."),
       ("Échos rythmiques", "Cliquez sur DELAY pour activer SYNC et tournez DELAY sur 1/8 pointée (entre 5 et 6,25) pour la cascade rythmique classique."),
       ("Pédale d'expression", "Apprenez SUSTAIN ou Age amount sur votre pédale d'expression (clic droit &rsaquo; MIDI Learn) pour faire monter les répétitions ou user la bande en jouant.")],
 tr_h="Dépannage",
 tr=[("Les échos ne changent pas quand je tourne DELAY.", "C'est normal si le temps venait du TAP ou de la synchro : le premier mouvement de DELAY rend la main au potard. Regardez la deuxième ligne de la ligne d'état."),
     ("Le son n'arrête pas de grossir.", "SUSTAIN est près du maximum : c'est l'auto-oscillation. Baissez SUSTAIN ou VOLUME."),
     ("Rien ne se passe quand je clique sur VOLUME.", "Cliquez sans bouger la souris. Un glissé tourne le potard ; un clic court bascule l'AGE ; un appui immobile de 2 s ouvre le réglage AGE."),
     ("Pas d'écho après Ampire / un simulateur.", "Vérifiez Startup settings &rsaquo; Mix : en 100 % wet, le son direct est retiré. Vérifiez aussi que la LED du footswitch est allumée."),
     ("Ma pédale MIDI ne fait rien.", "La piste doit recevoir le MIDI, et aucun CC n'est assigné d'office : clic droit sur la commande &rsaquo; MIDI Learn. Clic droit &rsaquo; MIDI affiche le CC de chaque commande."),
     ("La fenêtre est trop petite.", "Clic droit &rsaquo; Plugin size &rsaquo; 75 % / 100 %, ou tirez le coin. Pour ouvrir toutes les nouvelles fenêtres plus grandes : Plugin size &rsaquo; Default size (new windows). Elle ne peut pas être plus petite que 60 %."),
     ("La LED SYNC reste faible.", "L'hôte n'envoie pas de tempo au plug-in. Dans Reaper, ça n'arrive pas ; dans d'autres hôtes, vérifiez que le plug-in est sur une piste normale."),
     ("L'affichage figeait (anciennes versions).", "Corrigé par l'anti-gel v2 (v1.3) : rendu logiciel sous Windows, redessin uniquement quand quelque chose change, chien de garde qui relance l'affichage, aucun appel à l'hôte depuis le thread audio.")],
 s18="Caractéristiques",
 spec=[["Format", "VST3 &middot; Windows 11 (x64) &middot; macOS 10.13+ (Apple Silicon + Intel)"], ["Entrées / sorties", "entrée mono ou stéréo &middot; sortie stéréo ou mono"],
       ["Latence", "0 échantillon"], ["Temps de retard", "65 à 750 ms (potard) &middot; jusqu'à 4 s (tap ou synchro)"], ["Mémoire de retard", "4,3 s, interpolation d'Hermite"],
       ["Fréquences d'échantillonnage", "toutes celles du DAW"], ["Presets", "10 d'usine &middot; 9 utilisateur"],
       ["MIDI", "9 commandes avec MIDI Learn (aucun CC assigné d'office), sauvegardé avec le projet &middot; tous les canaux &middot; Program Change 1-10 &middot; tous les paramètres automatisables"],
       ["Fenêtre", "Plugin size 60 % (minimum) &middot; 75 % &middot; 100 %, jusqu'à 150 % en tirant le coin, proportions bloquées &middot; taille d'ouverture des nouvelles fenêtres au choix"],
       ["Affichage", "anti-gel v2 sous Windows (rendu logiciel, chien de garde, aucun appel à l'hôte depuis le thread audio)"],
       ["Queue", "12 s annoncées au DAW (trails)"], ["Version", VERSION]],
 cred_h="Crédits et sources",
 cred=["Plug-in, modèle sonore et notice : NINE HANDS | DSP. Visuel de la pédale : Echoflex par NINE HANDS | DSP.", "Police du logo NINE HANDS | DSP : Montserrat (SIL Open Font License).",
       "Sources : manuel Dunlop EP103 Echoplex Delay (jimdunlop.com) ; fiches produit zZounds et Chicago Music Exchange ; test EP103 de Premier Guitar ; Starlite Campbell, « The Maestro Echoplex EP-3 ».",
       "Echoplex&reg; et Dunlop&reg; sont des marques de leurs propriétaires respectifs. Echoflex est un hommage personnel et indépendant."]),
}

CUR = {"foot": ""}
class SetFoot(Flowable):
    def __init__(self, s): Flowable.__init__(self); self.s = s
    def wrap(self, *a): return (0, 0)
    def draw(self): CUR["foot"] = self.s

def chain_box(items):
    cells = []
    for i, n in enumerate(items):
        if i: cells.append(P("<font color='#D8261A'>&rarr;</font>", "p"))
        cells.append(P(("<b>%s</b>" % n) if i == 1 else n, "cell"))
    t = Table([cells], colWidths=[24 * mm if j % 2 == 0 else 8 * mm for j in range(len(cells))])
    sty = [("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    for j in range(0, len(cells), 2):
        sty.append(("BOX", (j, 0), (j, 0), 0.8, DARK if j != 2 else ACC))
    sty.append(("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#FBE9E7")))
    t.setStyle(TableStyle(sty)); t.hAlign = "LEFT"; return t

def menu_table(t):
    rows = []
    for head, subs, ctl in t["menu"]:
        cell = [P(("<font color='#FF6B5E' size='7.4'>%s</font>" % head) if ctl else head, "menu")]
        cell += [P(s, "menus" if not ctl else "menu") for s in subs]
        rows.append([cell])
    tb = Table(rows, colWidths=[W])
    sty = [("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#262526")), ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#4A484A")),
           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]
    tb.setStyle(TableStyle(sty)); return tb

def section(lang):
    t = T[lang]; f = []
    f.append(NextPageTemplate("p"))
    f.append(Spacer(1, 4 * mm)); f.append(P(t["lang"], "coverlang")); f.append(Spacer(1, 4 * mm))
    f.append(img(COVER, W * 0.60)); f.append(Spacer(1, 4 * mm))
    f.append(P("E C H O F L E X", "cover")); f.append(Spacer(1, 2 * mm))
    f.append(P(t["sub"], "coversub")); f.append(P(t["ver"], "coversub")); f.append(Spacer(1, 7 * mm))
    f.append(img(A("logo_studio_wiga_blanc.png"), 44 * mm))
    f.append(SetFoot(t["foot"])); f.append(PageBreak())
    # 01
    f.append(H1("01", t["s01"]))
    f.append(note("<b>" + t["about_h"] + "</b><br/>" + t["about"])); f.append(Spacer(1, 2 * mm))
    left = [H2(t["legend_h"])] + [P(x) for x in t["legend"]] + [H2(t["pedal_h"]), P(t["pedal"])]
    f.append(side(left, img(A("intro_pedal.jpg"), 62 * mm), W - 64 * mm))
    f.append(H2(t["rec_h"])); f += checks(t["rec"])
    # 02
    f.append(CondPageBreak(110 * mm))
    f.append(H1("02", t["s02"])); f.append(H2(t["build_h"]))
    f += [Paragraph(fix(x), st["b"], bulletText="%d." % (i + 1)) for i, x in enumerate(t["build"])]
    f.append(H2(t["inst_h"])); f += [P(x) for x in t["inst"]]
    f.append(H2(t["where_h"])); f.append(chain_box(t["chain"])); f.append(Spacer(1, 2 * mm)); f.append(P(t["where"]))
    f.append(PageBreak())
    # 03
    f.append(H1("03", t["s03"]))
    lst = [Paragraph(fix("<b>%s</b> &ndash; %s" % (h, x)), st["b"], bulletText="%d" % (i + 1)) for i, (h, x) in enumerate(t["ov"])]
    f.append(side(img(A("overview.jpg"), 84 * mm), lst, 88 * mm))
    f.append(Spacer(1, 3 * mm)); f.append(note(t["ov_note"]))
    # 04
    f.append(CondPageBreak(150 * mm))
    f.append(H1("04", t["s04"])); f.append(P(t["delay"]))
    kt = table([t["knob_hdr"]] + [[str(k), "%d ms" % round(delay_ms(k))] for k in range(11)], [20 * mm, 26 * mm], dark=True)
    f.append(side(img(A("delay_chart_" + lang + ".png"), W - 52 * mm), kt, W - 48 * mm, "MIDDLE"))
    f.append(Spacer(1, 2 * mm))
    f.append(row_imgs([(A("delay_knob_%d.jpg" % n), c) for n, c in zip((14, 16, 18), t["knob_caps"])]))
    f += [P(x) for x in t["delay_more"]]
    # 05
    f.append(CondPageBreak(120 * mm))
    f.append(H1("05", t["s05"])); f.append(P(t["sus"])); f += bullets(t["sus_b"])
    f.append(img(A("sustain_chart_" + lang + ".png"), W * 0.72))
    f.append(P(t["sus_more"])); f.append(note(t["sus_warn"]))
    # 06
    f.append(CondPageBreak(110 * mm))
    f.append(H1("06", t["s06"])); f.append(P(t["vol"]))
    vt = table([t["vol_hdr"]] + [[str(k), v] for k, v in enumerate(t["vol_vals"])], [18 * mm, 28 * mm], dark=True)
    f.append(side(img(A("volume_chart_" + lang + ".png"), W - 52 * mm), vt, W - 48 * mm, "MIDDLE"))
    f.append(P(t["vol_more"])); f.append(note(t["vol_note"]))
    # 07
    f.append(PageBreak())
    f.append(H1("07", t["s07"])); f.append(P(t["age"])); f.append(H2(t["age_h"])); f.append(steps(t["age_steps"]))
    f.append(Spacer(1, 2 * mm))
    f.append(row_imgs([(A("age_off.jpg"), t["age_caps"][0]), (A("age_on.jpg"), t["age_caps"][1])], gap=6 * mm))
    f.append(CondPageBreak(90 * mm))
    f.append(side([img(A("age_adjust.jpg"), 70 * mm), P(t["age_adj_cap"], "small")], img(A("age_charts_" + lang + ".png"), W - 78 * mm), 76 * mm))
    f.append(Spacer(1, 2 * mm))
    f.append(table(t["age_t"], [46 * mm, (W - 46 * mm) / 2, (W - 46 * mm) / 2], dark=True))
    f.append(Spacer(1, 2 * mm)); f.append(note(t["age_note"]))
    # 08
    f.append(CondPageBreak(130 * mm))
    f.append(H1("08", t["s08"])); f.append(P(t["tap"]))
    f.append(img(A("tap.jpg"), W * 0.72)); f.append(P(t["tap_cap"], "small"))
    f += bullets(t["tap_b"]); f.append(Spacer(1, 2 * mm)); f.append(note(t["tap_note"]))
    # 09
    f.append(PageBreak())
    f.append(H1("09", t["s09"])); f.append(P(t["sync"]))
    pics = Table([[[img(A("sync_off.png"), 36 * mm), P(t["sync_caps"][0], "small")], [img(A("sync_on.png"), 36 * mm), P(t["sync_caps"][1], "small")]]],
                 colWidths=[39 * mm, 39 * mm])
    pics.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
    f.append(side(steps(t["sync_steps"]), pics, W - 80 * mm))
    f.append(Spacer(1, 3 * mm))
    f.append(side(table(t["sync_t"], [25 * mm, 34 * mm, 24 * mm], dark=True), [H2(t["daw_h"]), P(t["daw"])], 88 * mm))
    f.append(Spacer(1, 2 * mm)); f.append(img(A("sync_status.png"), W * 0.62)); f.append(P(t["sync_cap"], "small"))
    f += bullets(t["sync_b"])
    # 10
    f.append(PageBreak())
    f.append(H1("10", t["s10"])); f.append(H2(t["fs_h"]))
    fsp = Table([[[img(A("fs_on.png"), 36 * mm), P(t["fs_caps"][0], "small")], [img(A("fs_bypass.png"), 36 * mm), P(t["fs_caps"][1], "small")]]], colWidths=[39 * mm, 39 * mm])
    fsp.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
    f.append(side(fsp, [P(x) for x in t["fs"]] + [H2(t["aled_h"]), P(t["aled"])], 82 * mm))
    f.append(H2(t["st_h"])); f.append(img(A("status_line.jpg"), W * 0.8)); f.append(Spacer(1, 2 * mm)); f.append(P(t["st"])); f += bullets(t["st_b"])
    # 11
    f.append(PageBreak())
    f.append(H1("11", t["s11"])); f.append(P(t["rc"])); f.append(Spacer(1, 1 * mm)); f.append(menu_table(t))
    f.append(KeepTogether([H2(t["win_h"])] + [P(x) for x in t["win"]] + [img(A("window_sizes.png"), W * 0.45)]))
    # 12
    f.append(PageBreak())
    f.append(H1("12", t["s12"])); f.append(P(t["su"]))
    f.append(table(t["su_t"], [22 * mm, 44 * mm, W - 66 * mm], dark=True)); f.append(Spacer(1, 3 * mm))
    f.append(img(A("bypass_chart_" + lang + ".png"), W)); f.append(Spacer(1, 2 * mm)); f.append(note(t["su_note"]))
    # 13
    f.append(CondPageBreak(170 * mm))
    f.append(H1("13", t["s13"])); f.append(P(t["tm"])); f.append(img(A("tape_machine_" + lang + ".png"), W * 0.92)); f.append(Spacer(1, 2 * mm))
    f += bullets(t["tm_b"])
    # 14
    f.append(PageBreak())
    f.append(H1("14", t["s14"])); f.append(P(t["fp"]))
    for i, (n, d, s, v, a, on) in enumerate(PRESETS):
        vals = table([["DELAY", "SUSTAIN", "VOLUME", "AGE"],
                      ["<b>%s</b><br/><font color='#D8261A' size='7'>%d ms</font>" % (num(d, lang), round(delay_ms(d))), "<b>%s</b>" % num(s, lang),
                       "<b>%s</b>" % num(v, lang), "<b>%s</b>" % (num(a, lang) if on else t["off"])]], [22 * mm] * 4)
        right = [P("<font color='#D8261A'><b>%d</b></font>&nbsp;&nbsp;<b>%s</b>" % (i + 1, n), "h3"), vals, Spacer(1, 1.5 * mm), P(t["pdesc"][i])]
        f.append(KeepTogether([side(img(A("preset_%d.jpg" % (i + 1)), 60 * mm), right, 64 * mm), Spacer(1, 3 * mm)]))
    # 15
    f.append(CondPageBreak(70 * mm))
    f.append(H1("15", t["s15"])); f.append(P(t["up"])); f += bullets(t["up_b"]); f.append(Spacer(1, 2 * mm)); f.append(note(t["up_note"]))
    # 16
    f.append(PageBreak())
    f.append(H1("16", t["s16"])); f.append(P(t["midi"]))
    f.append(table(t["mt"], [46 * mm, W - 46 * mm], dark=True))
    f.append(H2(t["ml_h"])); f.append(steps(t["ml_steps"])); f.append(Spacer(1, 1 * mm)); f += bullets(t["ml_b"])
    f.append(Spacer(1, 2 * mm)); f.append(note(t["ml_note"]))
    # 17
    f.append(PageBreak())
    f.append(H1("17", t["s17"]))
    cards = [[P("<b>%s</b>" % h, "cell"), P(x, "cell")] for h, x in t["tips"]]
    grid = Table([[cards[i], cards[i + 1]] for i in range(0, len(cards), 2)], colWidths=[W / 2, W / 2])
    grid.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                              ("LINEABOVE", (0, 0), (-1, -1), 1.2, ACC), ("BOX", (0, 0), (-1, -1), 0, colors.white),
                              ("INNERGRID", (0, 0), (-1, -1), 3, colors.white), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    f.append(grid)
    f.append(H2(t["tr_h"]))
    for h, x in t["tr"]:
        f.append(KeepTogether([P("<b>%s</b>" % h, "h3"), P(x)]))
    # 18
    f.append(CondPageBreak(130 * mm))
    f.append(H1("18", t["s18"])); f.append(table(t["spec"], [40 * mm, W - 40 * mm], header=False))
    f.append(H2(t["cred_h"])); f += bullets(t["cred"])
    f.append(PageBreak())
    return f

def deco(c, doc):
    c.saveState()
    c.setFillColor(ACC); c.rect(0, A4[1] - 3 * mm, A4[0], 3 * mm, stroke=0, fill=1)
    c.setFont("Pop", 7.5); c.setFillColor(GREY)
    c.drawString(18 * mm, 10 * mm, CUR["foot"].replace("&middot;", "\u00b7"))
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    c.restoreState()

def cover_bg(c, doc):
    c.saveState(); c.setFillColor(colors.black); c.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, A4[1] - 3 * mm, A4[0], 3 * mm, stroke=0, fill=1); c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                      title="Echoflex - User manual / Notice v" + VERSION, author="NINE HANDS | DSP")
doc.addPageTemplates([PageTemplate(id="cover", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="fc")], onPage=cover_bg),
                      PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=deco)])
en = section("en"); fr = section("fr")
en[-1:] = [NextPageTemplate("cover"), PageBreak()]
doc.build(en + fr[:-1])
print(OUT)
