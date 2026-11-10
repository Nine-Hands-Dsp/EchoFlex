// genere par tools/design/make_layout.py - ne pas modifier a la main (repere 623.0 x 900.0 = fond 1246 x 1800 px / 2)
#pragma once
#include <juce_graphics/juce_graphics.h>
namespace layout
{
    constexpr float frameW = 623.00f, frameH = 900.00f;   // pedale plein cadre (jacks aux bords gauche / droit)
    const juce::Rectangle<float> boxRect { 19.50f, 0.00f, 583.84f, 900.00f };
    // potards : volume (poussoir AGE), sustain, delay ; rayon exterieur de la couronne
    const juce::Point<float> knobVolume { 310.30f, 125.87f }, knobSustain { 128.66f, 258.00f }, knobDelay { 492.24f, 259.04f };
    const float knobR = 60.02f, knobHalf = 1.20f;   // filmstrip = 2 x 1,20 x rayon
    // LED : lentille allumee (photo), calque de lumiere sur la facade, centre et rayon de la lentille
    const juce::Rectangle<float> redLens { 296.00f, 502.50f, 31.00f, 31.00f }, redGlow { 208.00f, 414.50f, 207.00f, 207.00f }; const juce::Point<float> redPos { 311.27f, 518.15f }; const float redR = 13.79f;
    const juce::Rectangle<float> amberLens { 300.50f, 259.50f, 21.00f, 21.00f }, amberGlow { 257.50f, 216.50f, 107.50f, 107.50f }; const juce::Point<float> amberPos { 311.20f, 270.07f }; const float amberR = 8.95f;
    const juce::Rectangle<float> greenLens { 540.50f, 175.00f, 21.00f, 21.00f }, greenGlow { 497.00f, 131.50f, 107.50f, 107.50f }; const juce::Point<float> greenPos { 550.93f, 185.37f }; const float greenR = 8.95f;
    const juce::Point<float> fsPos { 312.17f, 679.53f }; const float footR = 43.25f, fsS = 198.50f;   // bouton / sprite
    const float jackOutY = 444.41f, jackInY = 444.03f, jackTapY = 762.05f;
    const juce::Point<float> tapJack { 10.0f, 762.05f };   // ecrou de la prise TAP (bord gauche)
    const juce::Rectangle<float> tapRect { 0.0f, 728.05f, 64.0f, 68.0f };   // prise TAP + inscription
    const juce::Rectangle<float> syncRect { 450.04f, 156.89f, 116.88f, 42.00f };   // inscription DELAY + SYNC + LED verte
    const juce::Rectangle<float> presetRect { 160.30f, 578.10f, 300.00f, 30.00f };   // barre de presets = ligne d'etat (meme place)
    // serigraphie vectorielle (Poppins Bold) : texte, hauteur de capitale, espacement (em), centre, rotation (degres)
    struct Txt { const char* s; float cap, track, x, y, rot; };
    const Txt texts[] = {
        { "SUSTAIN", 12.68f, 0.05f, 129.11f, 180.07f, 0.00f },
        { "DELAY", 12.68f, 0.05f, 484.04f, 180.07f, 0.00f },
        { "VOLUME", 13.42f, 0.05f, 311.42f, 230.41f, 0.00f },
        { "SYNC", 7.46f, 0.08f, 550.93f, 168.89f, 0.00f },
        { "OUT", 10.44f, 0.08f, 52.68f, 444.41f, -90.00f },
        { "IN", 10.44f, 0.08f, 569.79f, 444.03f, 90.00f },
        { "TAP", 10.44f, 0.08f, 52.68f, 762.05f, -90.00f },
        { "DELAY", 24.61f, 0.05f, 311.42f, 787.65f, 0.00f }
    };
    const juce::Point<float> pushCentre { 310.30f, 125.87f }; const float pushR = 72.33f, pushCap = 7.83f;   // PUSH FOR AGE en arc
    const juce::Point<float> logoPos { 311.42f, 833.13f }; const float logoW = 152.86f;
    const juce::Colour ink { (juce::uint8) 228, (juce::uint8) 228, (juce::uint8) 230 };
}
