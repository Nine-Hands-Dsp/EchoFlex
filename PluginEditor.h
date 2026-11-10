#pragma once

#include "PluginProcessor.h"
#include <juce_gui_basics/juce_gui_basics.h>
#include "Layout.h"
#include "NineHandsMenu.h"

//==============================================================================
// POTARD Echoflex : filmstrip de 128 positions rendue d'apres la photo (lumiere fixe en haut a gauche).
// Flou de mouvement : la couronne et le centre tournent ensemble, a la meme vitesse ; quand on tourne vite,
// on passe en fondu de la bande nette a la bande floue (15 decalages de phase) puis a la bande totalement
// floue (16 decalages sur un cran) : jamais d'effet stroboscopique.
//==============================================================================
class EchoKnob : public juce::Slider
{
public:
    EchoKnob();
    void paint (juce::Graphics&) override;
    bool hitTest (int x, int y) override;

    const juce::Image* strips[3] = { nullptr, nullptr, nullptr };   // nette, floue, totalement floue (caches de l'editeur)
    float blur = 0.0f, drawnBlur = 0.0f;                             // 0 = net ... 1 = flou ... 1,6 = flou total
    float lastPos = -1.0f;
};

// VOLUME = potard poussoir (comme la pedale) : clic = AGE on/off, maintenu 2 s = reglage AGE
class PushKnob : public EchoKnob
{
public:
    std::function<void()> onShortPress, onLongPress;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseDrag (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override;
    void checkLongPress (double nowMs);
    bool isHolding() const { return holding && ! moved && ! longFired; }
    double holdStart() const { return downTime; }
private:
    bool holding = false, moved = false, longFired = false;
    double downTime = 0.0;
};

//==============================================================================
// Footswitch (photo du kit, dans le fond) : bascule a l'appui, bouton assombri tant qu'on appuie,
// reflet rouge de la LED sur l'ecrou en fondu avec elle.
//==============================================================================
class FootSwitchArea : public juce::Component
{
public:
    explicit FootSwitchArea (juce::RangedAudioParameter& p);
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override;
    bool hitTest (int x, int y) override;
    bool isOn() const { return value; }
    std::function<void()> onRightClick, onUserChange;
    juce::Image reflection;
    float ledLevel = 0.0f;
private:
    bool value = false, pressed = false;
    juce::ParameterAttachment attachment;
};

// Zone cliquable invisible (prise TAP, inscription DELAY / SYNC)
class ClickArea : public juce::Component
{
public:
    ClickArea() { setMouseCursor (juce::MouseCursor::PointingHandCursor); }
    std::function<void()> onClick, onRightClick;
    std::function<void (float)> onWheel;
    void mouseDown (const juce::MouseEvent& e) override
    {
        if (e.mods.isPopupMenu()) { if (onRightClick) onRightClick(); }
        else if (onClick) onClick();
    }
    void mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails& w) override { if (onWheel && std::abs (w.deltaY) > 0.0f) onWheel (w.deltaY); }
};

struct RightClickForwarder : public juce::MouseListener
{
    std::function<void (juce::Component*)> callback;
    void mouseDown (const juce::MouseEvent& e) override { if (e.mods.isPopupMenu() && callback) callback (e.eventComponent); }
};

class EchoflexAudioProcessorEditor;

// Serigraphie, logo et barre de presets / ligne d'etat : dessines AU-DESSUS des potards (comme sur la pedale),
// sans jamais intercepter la souris.
class PrintOverlay : public juce::Component
{
public:
    explicit PrintOverlay (EchoflexAudioProcessorEditor& e) : ed (e) { setInterceptsMouseClicks (false, false); }
    void paint (juce::Graphics&) override;
private:
    EchoflexAudioProcessorEditor& ed;
};

//==============================================================================
class EchoflexAudioProcessorEditor : public juce::AudioProcessorEditor,
                                     private juce::Timer
{
public:
    explicit EchoflexAudioProcessorEditor (EchoflexAudioProcessor&);
    ~EchoflexAudioProcessorEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;
    void parentHierarchyChanged() override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseMove (const juce::MouseEvent&) override;
    void mouseExit (const juce::MouseEvent&) override;

    // Repere du fond (pedale plein cadre, image 1246 x 1800 px / 2). Hauteurs de fenetre des pedales simples :
    // taille par defaut = taille minimale 493 px (« 60 % »), 100 % = 958 px, jusqu'a 150 %.
    static constexpr float baseW = layout::frameW;
    static constexpr float baseH = layout::frameH;
    static constexpr int defaultH = 493;
    static constexpr int refH = 958;
    static constexpr int maxH = refH * 3 / 2;
    static constexpr int numSizes = 3;          // 60 % (defaut) / 75 % / 100 %
    static int sizeHeight (int idx);
    void setScaledHeight (int h);
    void forceRenderScale (float sc) { forcedScale = sc; rebuildCaches (sc); }   // captures (outil de rendu)
    void showStatus();

    void drawOverlay (juce::Graphics&);         // appele par PrintOverlay (repere du plugin deja applique)

private:
    friend class PrintOverlay;
    void timerCallback() override;
    void useSoftwareRenderer();
    void visibilityChanged() override;
    void askRepaint (juce::Rectangle<int> r);
    void rebuildCaches (float scale = 0.0f);
    float physicalScale() const;
    float unitScale() const { return (float) getHeight() / baseH; }
    juce::Rectangle<int> scaled (juce::Rectangle<float> r) const;

    void setParamValue (const char* id, float plain);
    void attachVolumeKnob (bool toAge);
    void setAgeEdit (bool on);
    void toggleAge();
    void toggleSync();
    void stepSyncDivision (int delta);
    void stepPreset (int delta);

    void showContextMenu (juce::Array<int> learnItems = {});
    void showSyncMenu();
    void showPresetMenu();
    void addLearnItems (juce::PopupMenu&, const juce::Array<int>& learnItems);
    bool handleLearnResult (int r);

    juce::String buildStatusLine() const;
    juce::String buildPresetLine() const;
    void buildPrint();
    void drawLeds (juce::Graphics&);
    void drawTapFlash (juce::Graphics&);
    void drawPresetBar (juce::Graphics&);

    EchoflexAudioProcessor& proc;
    RightClickForwarder rightClickFwd;
    NineHandsMenu::MenuLnf menuLnf;        // menus clic droit au design d'Octopus

    // images d'origine et caches a la taille de l'ecran (reconstruits par le timer seulement)
    juce::Image background, bgScaled;
    juce::Image strip[3], stripS[3];
    juce::Image glow[3], glowS[3], lens[3];
    int cacheW = 0, cacheH = 0;
    float cacheScale = 0.0f, forcedScale = 0.0f;
    int resizeSettle = 0;

    // anti-gel v2 : suivi de la fenetre hote, de l'echelle et des redessins
    void* lastPeer = nullptr;
    double lastPaintMs = 0.0, repaintAskedMs = 0.0, lastScaleCheckMs = 0.0, lastRendererCheckMs = 0.0, lastTime = 0.0;

    juce::Typeface::Ptr regFace, medFace, boldFace;
    juce::Path printPath;                  // inscriptions + PUSH FOR AGE, en unites du plugin
    std::unique_ptr<juce::Drawable> logo;

    EchoKnob sustain, delay;
    PushKnob volume;
    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> aSustain, aDelay, aVolume;
    bool volumeOnAge = false;
    FootSwitchArea footswitch;
    ClickArea tapArea, syncArea;
    PrintOverlay overlay { *this };

    // LED : rouge (effet actif), ambre (AGE), verte (SYNC)
    float ledLevel = 0.0f, ledFlicker = 1.0f, echoGlow = 0.0f, ageLedLevel = 0.0f, syncLedLevel = 0.0f;
    float drawnLed = -1.0f, drawnAge = -1.0f, drawnSync = -1.0f;
    double blinkPhase = 0.0, freePhase = 0.0;
    float tapFlash = 0.0f, drawnTap = -1.0f;
    int lastTapCount = 0;
    juce::Random rng;

    // barre de presets et ligne d'etat : meme pilule ; la ligne d'etat remplace les presets le temps d'un reglage
    float statusAlpha = 0.0f, drawnStatus = -1.0f;
    double statusUntil = 0.0;
    juce::String lastStatus, lastPreset;
    int lastChanged = -1;
    float lastValues[9];
    int lastMidiCount = 0, midiFlash = 0;
    int hoverZone = 0, drawnHover = -1;
    juce::String learnMsg;
    double learnMsgUntil = 0.0;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (EchoflexAudioProcessorEditor)
};
