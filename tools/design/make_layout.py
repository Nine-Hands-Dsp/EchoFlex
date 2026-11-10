"""Genere Layout.h (racine du depot) depuis tools/design/layout.json (ecrit par make_art.py).
python3 tools/design/make_layout.py"""
import os, json
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
L = json.load(open(os.path.join(HERE, 'layout.json')))
fsS = Image.open(os.path.join(REPO, 'fs_refl.png')).width / 2.0      # sprite du footswitch (unites)

f = lambda v: f'{v:.2f}f'
pt = lambda p: '{ ' + f(p[0]) + ', ' + f(p[1]) + ' }'
rc = lambda r: '{ ' + ', '.join(f(v) for v in r) + ' }'
K = L['knobs']; LE = L['leds']; P = L['pushForAge']
pr = L['presetRect']; pr = [K['volume'][0] - pr[2] / 2, pr[1], pr[2], pr[3]]

o = []
o.append(f"// genere par tools/design/make_layout.py - ne pas modifier a la main (repere {L['frameW']:.1f} x {L['frameH']:.1f} = fond 1246 x 1800 px / 2)")
o.append('#pragma once\n#include <juce_graphics/juce_graphics.h>\nnamespace layout\n{')
o.append(f"    constexpr float frameW = {f(L['frameW'])}, frameH = {f(L['frameH'])};   // pedale plein cadre (jacks aux bords gauche / droit)")
o.append(f"    const juce::Rectangle<float> boxRect {rc(L['box'])};")
o.append('    // potards : volume (poussoir AGE), sustain, delay ; rayon exterieur de la couronne')
o.append(f"    const juce::Point<float> knobVolume {pt(K['volume'])}, knobSustain {pt(K['sustain'])}, knobDelay {pt(K['delay'])};")
o.append(f"    const float knobR = {f(L['knobR'])}, knobHalf = 1.20f;   // filmstrip = 2 x 1,20 x rayon")
o.append('    // LED : lentille allumee (photo), calque de lumiere sur la facade, centre et rayon de la lentille')
for n in ('red', 'amber', 'green'):
    d = LE[n]
    o.append(f"    const juce::Rectangle<float> {n}Lens {rc(d['lens'])}, {n}Glow {rc(d['glow'])}; const juce::Point<float> {n}Pos {pt(d['c'])}; const float {n}R = {f(d['r'])};")
o.append(f"    const juce::Point<float> fsPos {pt(L['foot'])}; const float footR = {f(L['footR'])}, fsS = {f(fsS)};   // bouton / sprite")
J = L['jacks']
o.append(f"    const float jackOutY = {f(J['out'])}, jackInY = {f(J['in'])}, jackTapY = {f(J['tap'])};")
o.append(f"    const juce::Point<float> tapJack {{ 10.0f, {f(J['tap'])} }};   // ecrou de la prise TAP (bord gauche)")
o.append(f"    const juce::Rectangle<float> tapRect {{ 0.0f, {f(J['tap'] - 34)}, 64.0f, 68.0f }};   // prise TAP + inscription")
t = {x['s'] + ('2' if x['s'] == 'DELAY' and x['cap'] > 20 else ''): x for x in L['texts']}
d, s = t['DELAY'], t['SYNC']
x0 = d['x'] - 34; x1 = s['x'] + 16
o.append(f"    const juce::Rectangle<float> syncRect {rc([x0, s['y'] - 12, x1 - x0, 42])};   // inscription DELAY + SYNC + LED verte")
o.append(f"    const juce::Rectangle<float> presetRect {rc(pr)};   // barre de presets = ligne d'etat (meme place)")
o.append('    // serigraphie vectorielle (Poppins Bold) : texte, hauteur de capitale, espacement (em), centre, rotation (degres)')
o.append('    struct Txt { const char* s; float cap, track, x, y, rot; };')
o.append('    const Txt texts[] = {')
o.append(',\n'.join(f"        {{ \"{x['s']}\", {f(x['cap'])}, {f(0.08 if x['cap'] < 12 else 0.05)}, {f(x['x'])}, {f(x['y'])}, {f(x['rot'])} }}" for x in L['texts']))
o.append('    };')
o.append(f"    const juce::Point<float> pushCentre {pt([P['cx'], P['cy']])}; const float pushR = {f(P['r'])}, pushCap = {f(P['cap'])};   // PUSH FOR AGE en arc")
o.append(f"    const juce::Point<float> logoPos {pt([L['logo']['x'], L['logo']['y']])}; const float logoW = {f(L['logo']['w'])};")
o.append(f"    const juce::Colour ink {{ (juce::uint8) {L['ink'][0]}, (juce::uint8) {L['ink'][1]}, (juce::uint8) {L['ink'][2]} }};")
o.append('}\n')
open(os.path.join(REPO, 'Layout.h'), 'w').write('\n'.join(o))
print('Layout.h ok')
