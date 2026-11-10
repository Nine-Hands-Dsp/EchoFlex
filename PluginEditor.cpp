#include "PluginEditor.h"
#include "BinaryData.h"
#include "WigaWindowSize.h"

using namespace juce;

namespace
{
    const float rotStart = MathConstants<float>::pi * 1.25f;   // meme course que la filmstrip (make_knob.py)
    const float rotEnd   = MathConstants<float>::pi * 2.75f;
    constexpr int   knobFrames = 128;
    constexpr float knobTeeth  = 47.0f;                        // dents de la couronne

    const Colour amber  (0xffffa02a);
    const Colour pillBg (0xcd060608);                           // pilule : noir 80 %
    const Colour pillLine (0xff787c82);

    constexpr double longPressMs = 2000.0;   // comme la pedale : maintenir VOLUME 2 s

    // reglages suivis pour la ligne d'etat (dans cet ordre)
    const char* const valueIds[] = { "delay", "sustain", "volume", "age", "ageOn", "active", "timeSrc", "syncDiv", "tapMs" };
    constexpr int numValueIds = 9;

    const Rectangle<float> lensRect[3] = { layout::redLens, layout::amberLens, layout::greenLens };
    const Rectangle<float> glowRect[3] = { layout::redGlow, layout::amberGlow, layout::greenGlow };
}

//==============================================================================
// POTARD (filmstrip + flou de mouvement)
//==============================================================================
EchoKnob::EchoKnob()
{
    setSliderStyle (Slider::RotaryHorizontalVerticalDrag);
    setTextBoxStyle (Slider::NoTextBox, false, 0, 0);
    setRotaryParameters (rotStart, rotEnd, true);
    setMouseDragSensitivity (220);
    setMouseCursor (MouseCursor::PointingHandCursor);
    setBufferedToImage (false);
}

bool EchoKnob::hitTest (int x, int y)
{
    const auto c = getLocalBounds().toFloat().getCentre();
    return c.getDistanceFrom ({ (float) x, (float) y }) <= (float) getWidth() * 0.5f / layout::knobHalf;
}

void EchoKnob::paint (Graphics& g)
{
    drawnBlur = blur;
    const float pos = (float) valueToProportionOfLength (getValue());
    const int frame = jlimit (0, knobFrames - 1, roundToInt (pos * (float) (knobFrames - 1)));
    const auto b = getLocalBounds().toFloat();

    auto drawFrame = [&] (const Image* img, float alpha)
    {
        if (img == nullptr || ! img->isValid() || alpha <= 0.003f) return;
        const int fs = img->getWidth();
        g.setOpacity (jmin (1.0f, alpha));
        g.drawImage (*img, roundToInt (b.getX()), roundToInt (b.getY()), getWidth(), getHeight(), 0, frame * fs, fs, fs);
    };

    g.setImageResamplingQuality (Graphics::mediumResamplingQuality);
    // net -> flou (fondu) -> totalement flou ; la bande nette reste dessous tant que le flou n'est pas complet
    if (blur < 1.0f) drawFrame (strips[0], 1.0f);
    drawFrame (strips[1], jmin (1.0f, blur));
    if (blur > 1.0f) drawFrame (strips[2], (blur - 1.0f) / 0.6f);
    g.setOpacity (1.0f);
}

//==============================================================================
// POTARD POUSSOIR (VOLUME / AGE)
//==============================================================================
void PushKnob::mouseDown (const MouseEvent& e)
{
    if (e.mods.isPopupMenu())
        return;
    holding = true; moved = false; longFired = false;
    downTime = Time::getMillisecondCounterHiRes();
    Slider::mouseDown (e);
}

void PushKnob::mouseDrag (const MouseEvent& e)
{
    if (e.mods.isPopupMenu() || longFired)
        return;
    if (e.getDistanceFromDragStart() > 3)
        moved = true;
    Slider::mouseDrag (e);
}

void PushKnob::mouseUp (const MouseEvent& e)
{
    if (e.mods.isPopupMenu())
        return;
    const bool wasClick = holding && ! moved && ! longFired
                          && Time::getMillisecondCounterHiRes() - downTime < 600.0;
    holding = false;
    Slider::mouseUp (e);
    if (wasClick && onShortPress)
        onShortPress();
}

void PushKnob::checkLongPress (double nowMs)
{
    if (isHolding() && nowMs - downTime >= longPressMs)
    {
        longFired = true;
        if (onLongPress)
            onLongPress();
    }
}

//==============================================================================
// FOOTSWITCH
//==============================================================================
FootSwitchArea::FootSwitchArea (RangedAudioParameter& p)
    : attachment (p, [this] (float v) { value = v > 0.5f; repaint(); })
{
    attachment.sendInitialUpdate();
    setMouseCursor (MouseCursor::PointingHandCursor);
}

bool FootSwitchArea::hitTest (int x, int y)
{
    const auto c = getLocalBounds().toFloat().getCentre();
    return c.getDistanceFrom ({ (float) x, (float) y }) <= (float) getWidth() * (layout::footR * 1.30f / layout::fsS);
}

void FootSwitchArea::paint (Graphics& g)
{
    const auto b = getLocalBounds().toFloat();
    if (ledLevel > 0.003f && reflection.isValid())
    {
        g.setOpacity (ledLevel);
        g.drawImage (reflection, b);
        g.setOpacity (1.0f);
    }
    if (pressed)
    {
        const float r = b.getWidth() * (layout::footR / layout::fsS) * 0.98f;
        const auto c = b.getCentre();
        g.setColour (Colours::black.withAlpha (0.25f));
        g.fillEllipse (c.x - r, c.y - r, r * 2.0f, r * 2.0f);
    }
}

void FootSwitchArea::mouseDown (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) { if (onRightClick) onRightClick(); return; }
    pressed = true;
    repaint();
    attachment.setValueAsCompleteGesture (value ? 0.0f : 1.0f);    // bascule des l'appui
    if (onUserChange) onUserChange();
}

void FootSwitchArea::mouseUp (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) return;
    pressed = false;
    repaint();
}

void PrintOverlay::paint (Graphics& g)
{
    g.addTransform (AffineTransform::scale (ed.unitScale()));
    ed.drawOverlay (g);
}

//==============================================================================
// EDITEUR
//==============================================================================
EchoflexAudioProcessorEditor::EchoflexAudioProcessorEditor (EchoflexAudioProcessor& p)
    : AudioProcessorEditor (&p), proc (p),
      footswitch (*p.apvts.getParameter ("active"))
{
    background = ImageCache::getFromMemory (BinaryData::background_png, BinaryData::background_pngSize);
    strip[0] = ImageCache::getFromMemory (BinaryData::knob_strip_png, BinaryData::knob_strip_pngSize);
    strip[1] = ImageCache::getFromMemory (BinaryData::knob_blur1_png, BinaryData::knob_blur1_pngSize);
    strip[2] = ImageCache::getFromMemory (BinaryData::knob_blur2_png, BinaryData::knob_blur2_pngSize);
    glow[0]  = ImageCache::getFromMemory (BinaryData::glow_red_png,   BinaryData::glow_red_pngSize);
    glow[1]  = ImageCache::getFromMemory (BinaryData::glow_amber_png, BinaryData::glow_amber_pngSize);
    glow[2]  = ImageCache::getFromMemory (BinaryData::glow_green_png, BinaryData::glow_green_pngSize);
    lens[0]  = ImageCache::getFromMemory (BinaryData::led_on_red_png,   BinaryData::led_on_red_pngSize);
    lens[1]  = ImageCache::getFromMemory (BinaryData::led_on_amber_png, BinaryData::led_on_amber_pngSize);
    lens[2]  = ImageCache::getFromMemory (BinaryData::led_on_green_png, BinaryData::led_on_green_pngSize);
    footswitch.reflection = ImageCache::getFromMemory (BinaryData::fs_refl_png, BinaryData::fs_refl_pngSize);
    regFace  = Typeface::createSystemTypefaceFor (BinaryData::PoppinsRegular_ttf, BinaryData::PoppinsRegular_ttfSize);
    medFace  = Typeface::createSystemTypefaceFor (BinaryData::PoppinsMedium_ttf,  BinaryData::PoppinsMedium_ttfSize);
    boldFace = Typeface::createSystemTypefaceFor (BinaryData::PoppinsBold_ttf,    BinaryData::PoppinsBold_ttfSize);
    if (auto xml = XmlDocument::parse (String::fromUTF8 (BinaryData::NineHandsLogo_svg, BinaryData::NineHandsLogo_svgSize)))
        logo = Drawable::createFromSVG (*xml);
    buildPrint();
    menuLnf.f = { regFace, medFace, boldFace };
    setLookAndFeel (&menuLnf);             // menus (et sous-menus) au design d'Octopus

    // clic droit sur une commande : MIDI Learn de cette commande en tete du menu
    rightClickFwd.callback = [this] (Component* c)
    {
        using P = EchoflexAudioProcessor;
        Array<int> items;
        if      (c == &delay)   items = { P::lDelay };
        else if (c == &sustain) items = { P::lSustain };
        else if (c == &volume)  items = { P::lVolume, P::lAge, P::lAgeOn };   // VOLUME + poussoir AGE
        showContextMenu (items);
    };

    for (auto* s : { (EchoKnob*) &sustain, (EchoKnob*) &delay, (EchoKnob*) &volume })
    {
        s->addMouseListener (&rightClickFwd, false);
        addAndMakeVisible (*s);
    }
    aSustain = std::make_unique<AudioProcessorValueTreeState::SliderAttachment> (proc.apvts, "sustain", sustain);
    aDelay   = std::make_unique<AudioProcessorValueTreeState::SliderAttachment> (proc.apvts, "delay",   delay);
    attachVolumeKnob (proc.ageEdit.load());

    // Tourner DELAY reprend la main sur le TAP (comme la pedale) ;
    // en SYNC, le potard DELAY choisit la division de tempo (1/16 ... 1/2)
    delay.onDragStart = [this]
    {
        if (roundToInt (proc.apvts.getRawParameterValue ("timeSrc")->load()) == 1)
            setParamValue ("timeSrc", 0.0f);
        proc.currentPreset = -1;
    };
    delay.onValueChange = [this]
    {
        if (roundToInt (proc.apvts.getRawParameterValue ("timeSrc")->load()) != 2 || ! delay.isMouseButtonDown())
            return;
        const int d = EchoflexAudioProcessor::syncDivFromKnob ((float) delay.getValue());
        if (d != roundToInt (proc.apvts.getRawParameterValue ("syncDiv")->load()))
            setParamValue ("syncDiv", (float) d);
    };
    sustain.onDragStart = [this] { proc.currentPreset = -1; };
    volume.onDragStart  = [this] { proc.currentPreset = -1; };
    volume.onShortPress = [this]
    {
        if (proc.ageEdit.load()) setAgeEdit (false);      // verrouille le reglage AGE
        else                     toggleAge();             // reglage AGE <-> son clair d'usine
    };
    volume.onLongPress = [this] { setAgeEdit (! proc.ageEdit.load()); };

    footswitch.onRightClick = [this] { showContextMenu ({ EchoflexAudioProcessor::lFoot, EchoflexAudioProcessor::lFootToggle }); };
    footswitch.onUserChange = [this] { lastChanged = 5; showStatus(); };
    addAndMakeVisible (footswitch);

    tapArea.onClick      = [this] { proc.tap(); };
    tapArea.onRightClick = [this] { showContextMenu ({ EchoflexAudioProcessor::lTap }); };
    addAndMakeVisible (tapArea);

    // SYNC : clic = suit le tempo du DAW (on/off), clic droit = division, molette = division
    syncArea.onClick      = [this] { toggleSync(); };
    syncArea.onRightClick = [this] { showSyncMenu(); };
    syncArea.onWheel      = [this] (float dy) { stepSyncDivision (dy > 0 ? -1 : 1); };
    addAndMakeVisible (syncArea);

    addAndMakeVisible (overlay);           // serigraphie + barre de presets par-dessus tout

    for (int i = 0; i < numValueIds; ++i) lastValues[i] = proc.apvts.getRawParameterValue (valueIds[i])->load();
    lastMidiCount = proc.midiCounter.load();
    lastTapCount  = proc.tapCounter.load();
    ledLevel = proc.apvts.getRawParameterValue ("active")->load() > 0.5f ? 1.0f : 0.0f;

    // Taille par defaut = taille minimale (impossible de reduire en dessous), proportions bloquees
    const int defaultW = roundToInt ((float) defaultH * baseW / baseH);
    setResizable (true, true);
    setResizeLimits (defaultW, defaultH, roundToInt ((float) maxH * baseW / baseH), maxH);
    if (auto* cons = getConstrainer())
        cons->setFixedAspectRatio ((double) baseW / (double) baseH);
    setOpaque (true);                      // anti-gel : l'hote ne redessine jamais ce qui est derriere la fenetre
    setSize (defaultW, defaultH);
    // taille des nouvelles fenetres : celle choisie dans le menu « Default size (new windows) »
    setScaledHeight (sizeHeight (WigaWindowSize::defaultIndex (JucePlugin_Name, numSizes)));
    rebuildCaches();

    lastTime = Time::getMillisecondCounterHiRes();
    startTimerHz (30);
}

EchoflexAudioProcessorEditor::~EchoflexAudioProcessorEditor()
{
    stopTimer();
    proc.ageEdit = false;
    for (auto* s : { (Slider*) &sustain, (Slider*) &delay, (Slider*) &volume })
        s->removeMouseListener (&rightClickFwd);
    setLookAndFeel (nullptr);
}

void EchoflexAudioProcessorEditor::setParamValue (const char* id, float plain)
{
    if (auto* prm = proc.apvts.getParameter (id))
    {
        prm->beginChangeGesture();
        prm->setValueNotifyingHost (prm->convertTo0to1 (plain));
        prm->endChangeGesture();
    }
}

void EchoflexAudioProcessorEditor::attachVolumeKnob (bool toAge)
{
    aVolume.reset();
    aVolume = std::make_unique<AudioProcessorValueTreeState::SliderAttachment> (proc.apvts, toAge ? "age" : "volume", volume);
    volumeOnAge = toAge;
}

void EchoflexAudioProcessorEditor::setAgeEdit (bool on)
{
    proc.ageEdit = on;
    if (on)
        setParamValue ("ageOn", 1.0f);          // on entend le reglage pendant qu'on le fait
    // l'attachement du potard ne change qu'une fois le bouton de la souris relache
    // (sinon le geste d'automation du DAW reste ouvert : affichage fige dans Reaper)
    if (! volume.isMouseButtonDown())
        attachVolumeKnob (on);
    lastChanged = 3;
    showStatus();
}

void EchoflexAudioProcessorEditor::toggleAge()
{
    const bool on = proc.apvts.getRawParameterValue ("ageOn")->load() > 0.5f;
    setParamValue ("ageOn", on ? 0.0f : 1.0f);
    lastChanged = 4;
    showStatus();
}

void EchoflexAudioProcessorEditor::toggleSync()
{
    const bool on = roundToInt (proc.apvts.getRawParameterValue ("timeSrc")->load()) == 2;
    if (! on)   // la division suit la position actuelle du potard DELAY
        setParamValue ("syncDiv", (float) EchoflexAudioProcessor::syncDivFromKnob (proc.apvts.getRawParameterValue ("delay")->load()));
    setParamValue ("timeSrc", on ? 0.0f : 2.0f);
    proc.currentPreset = -1;
    lastChanged = 6;
    showStatus();
}

void EchoflexAudioProcessorEditor::stepSyncDivision (int delta)
{
    const int n = EchoflexAudioProcessor::syncNames().size();
    const int d = jlimit (0, n - 1, roundToInt (proc.apvts.getRawParameterValue ("syncDiv")->load()) + delta);
    setParamValue ("syncDiv", (float) d);
    setParamValue ("delay", EchoflexAudioProcessor::knobForSyncDiv (d));
    if (roundToInt (proc.apvts.getRawParameterValue ("timeSrc")->load()) != 2)
        setParamValue ("timeSrc", 2.0f);
    lastChanged = 7;
    showStatus();
}

void EchoflexAudioProcessorEditor::stepPreset (int delta)
{
    const int n = EchoflexAudioProcessor::getNumFactoryPresets();
    int cp = proc.currentPreset.load();
    if (cp < 0 || cp >= n) cp = delta > 0 ? -1 : 0;
    proc.applyFactoryPreset ((cp + delta + n) % n);
}

void EchoflexAudioProcessorEditor::showStatus()
{
    statusUntil = Time::getMillisecondCounterHiRes() + 2500.0;
}

int EchoflexAudioProcessorEditor::sizeHeight (int idx)
{
    const int h[numSizes] = { (int) defaultH, roundToInt (refH * 0.75f), (int) refH };
    return h[jlimit (0, numSizes - 1, idx)];
}

void EchoflexAudioProcessorEditor::setScaledHeight (int h)
{
    h = jlimit ((int) defaultH, (int) maxH, h);
    setSize (roundToInt ((float) h * baseW / baseH), h);
}

Rectangle<int> EchoflexAudioProcessorEditor::scaled (Rectangle<float> r) const
{
    return r.transformedBy (AffineTransform::scale (unitScale())).getSmallestIntegerContainer();
}

float EchoflexAudioProcessorEditor::physicalScale() const
{
    if (forcedScale > 0.0f) return forcedScale;
    return jlimit (1.0f, 4.0f, (float) Component::getApproximateScaleFactorForComponent (this));
}

//==============================================================================
// Caches d'affichage : fond, potards et calques de lumiere deja a la bonne taille
// (reconstruits par le timer seulement, jamais dans paint)
//==============================================================================
void EchoflexAudioProcessorEditor::rebuildCaches (float sc)
{
    if (sc <= 0.0f) sc = cacheScale > 0.0f ? cacheScale : physicalScale();
    const int w = getWidth(), h = getHeight();
    if (w <= 0 || h <= 0) return;
    if (w == cacheW && h == cacheH && std::abs (sc - cacheScale) < 0.01f && bgScaled.isValid()) return;
    cacheW = w; cacheH = h; cacheScale = sc;

    const int pw = roundToInt ((float) w * sc), ph = roundToInt ((float) h * sc);
    bgScaled = (pw >= background.getWidth()) ? background : background.rescaled (pw, ph, Graphics::highResamplingQuality);

    const float s = unitScale();
    const int kpx = roundToInt (layout::knobR * layout::knobHalf * 2.0f * s * sc);
    for (int i = 0; i < 3; ++i)
    {
        stripS[i] = (! strip[i].isValid() || kpx >= strip[i].getWidth()) ? Image()
                                                                          : strip[i].rescaled (kpx, kpx * knobFrames, Graphics::highResamplingQuality);
        const int gpx = roundToInt (glowRect[i].getWidth() * s * sc);
        glowS[i] = (! glow[i].isValid() || gpx >= glow[i].getWidth()) ? Image()
                                                                      : glow[i].rescaled (gpx, gpx, Graphics::highResamplingQuality);
    }
    for (auto* k : { (EchoKnob*) &sustain, (EchoKnob*) &delay, (EchoKnob*) &volume })
        for (int i = 0; i < 3; ++i)
            k->strips[i] = stripS[i].isValid() ? &stripS[i] : &strip[i];
    repaint();
}

void EchoflexAudioProcessorEditor::resized()
{
    const float half = layout::knobR * layout::knobHalf;
    auto place = [&] (Slider& sl, Point<float> c) { sl.setBounds (scaled ({ c.x - half, c.y - half, half * 2.0f, half * 2.0f })); };
    place (volume,  layout::knobVolume);
    place (sustain, layout::knobSustain);
    place (delay,   layout::knobDelay);

    const float fr = layout::fsS * 0.5f;
    footswitch.setBounds (scaled ({ layout::fsPos.x - fr, layout::fsPos.y - fr, fr * 2.0f, fr * 2.0f }));
    tapArea.setBounds (scaled (layout::tapRect));
    syncArea.setBounds (scaled (layout::syncRect));
    overlay.setBounds (getLocalBounds());

    // anti-gel : jamais de setSize ici (les limites du constrainer suffisent) ;
    // pendant un redimensionnement a la souris, on attend que la taille se stabilise
    resizeSettle = 4;
}

//==============================================================================
// Ligne d'etat (le reglage qui bouge) et barre de presets
//==============================================================================
String EchoflexAudioProcessorEditor::buildStatusLine() const
{
    auto raw = [this] (const char* id) { return proc.apvts.getRawParameterValue (id)->load(); };
    const int lt = proc.learnTarget.load();
    if (lt >= 0)
        return "MIDI learn: move a control for " + String (EchoflexAudioProcessor::learnInfo (lt).name);
    if (Time::getMillisecondCounterHiRes() < learnMsgUntil)
        return learnMsg;
    if (proc.ageEdit.load())
        return "AGE " + String (raw ("age"), 1) + "  -  push VOLUME to lock";

    const int src = roundToInt (raw ("timeSrc"));
    auto syncText = [&]
    {
        String s = "SYNC " + EchoflexAudioProcessor::syncNames()[roundToInt (raw ("syncDiv"))];
        const float bpm = proc.hostBpm.load();
        s << (bpm > 1.0f ? "  -  " + String (bpm, 1) + " BPM" : String ("  -  no host tempo"));
        return s;
    };
    switch (lastChanged)
    {
        case 0:  return src == 2 ? syncText() : "DELAY " + String (roundToInt (proc.delayMsDisplay.load())) + " ms";
        case 1:  return "SUSTAIN " + String (raw ("sustain"), 1);
        case 2:  return "VOLUME " + String (raw ("volume"), 1);
        case 3:  return "AGE " + String (raw ("age"), 1);
        case 4:  return raw ("ageOn") > 0.5f ? "AGE on  -  " + String (raw ("age"), 1) : String ("AGE off  -  clear tape");
        case 5:  return raw ("active") > 0.5f ? String ("Echo on") : String ("Bypass");
        case 6:
        case 7:
        case 8:  return src == 2 ? syncText()
                      : src == 1 ? "TAP " + String (roundToInt (raw ("tapMs"))) + " ms"
                                 : "DELAY knob  -  " + String (roundToInt (proc.delayMsDisplay.load())) + " ms";
        default: return {};
    }
}

String EchoflexAudioProcessorEditor::buildPresetLine() const
{
    const int cp = proc.currentPreset.load();
    String s;
    if (cp >= 0 && cp < EchoflexAudioProcessor::getNumFactoryPresets())
        s << "P" << (cp + 1) << "  " << EchoflexAudioProcessor::getFactoryPreset (cp).name;
    else if (cp > 100) s << "User " << (cp - 100);
    else               s << "Edited";
    return s;
}

//==============================================================================
// Anti-gel v2 (NINE HANDS | DSP) :
//  1. moteur de rendu logiciel force sur Windows, applique a chaque nouvelle fenetre hote (peer)
//     et reverifie toutes les secondes, jamais en boucle ;
//  2. aucun calcul lourd dans paint() : caches reconstruits par le timer seulement ;
//  3. chien de garde : redessin demande non servi en 1,5 s -> moteur de rendu reapplique, tout redessine ;
//  4. cote audio : aucun appel a l'hote depuis le thread audio (voir PluginProcessor).
//==============================================================================
void EchoflexAudioProcessorEditor::useSoftwareRenderer()
{
    auto* peer = getPeer();
    if (peer != lastPeer) { lastPeer = peer; repaint(); }
   #if JUCE_WINDOWS
    if (peer != nullptr)
    {
        int sw = peer->getAvailableRenderingEngines().indexOf ("Software Renderer");
        if (sw < 0) sw = 0;
        if (peer->getCurrentRenderingEngine() != sw) peer->setCurrentRenderingEngine (sw);
    }
   #endif
}

void EchoflexAudioProcessorEditor::parentHierarchyChanged() { useSoftwareRenderer(); }
void EchoflexAudioProcessorEditor::visibilityChanged()      { useSoftwareRenderer(); if (isShowing()) repaint(); }

void EchoflexAudioProcessorEditor::askRepaint (Rectangle<int> r)
{
    if (repaintAskedMs <= 0.0) repaintAskedMs = Time::getMillisecondCounterHiRes();
    repaint (r);
}

//==============================================================================
void EchoflexAudioProcessorEditor::timerCallback()
{
    const double now = Time::getMillisecondCounterHiRes();
    const double dt = jlimit (0.001, 0.1, (now - lastTime) * 0.001);
    lastTime = now;

    if (getPeer() != lastPeer || now - lastRendererCheckMs > 1000.0) { lastRendererCheckMs = now; useSoftwareRenderer(); }

    if (resizeSettle > 0 && --resizeSettle == 0) rebuildCaches();
    else if (resizeSettle == 0 && now - lastScaleCheckMs > 250.0)
    {
        lastScaleCheckMs = now;
        const float sc = physicalScale();
        if (std::abs (sc - cacheScale) > 0.01f) rebuildCaches (sc);
    }

    if (repaintAskedMs > 0.0 && isShowing() && now - repaintAskedMs > 1500.0 && lastPaintMs < repaintAskedMs)
    {
        repaintAskedMs = 0.0; lastPeer = nullptr;
        useSoftwareRenderer(); repaint();
    }

    volume.checkLongPress (now);
    if (volumeOnAge != proc.ageEdit.load() && ! volume.isMouseButtonDown())
        attachVolumeKnob (proc.ageEdit.load());

    // --- Flou de mouvement des potards : niveau = vitesse de rotation (en crans par image a 60 i/s) ;
    //     monte immediatement, redescend en douceur (x 0,6 par image)
    for (auto* k : { (EchoKnob*) &sustain, (EchoKnob*) &delay, (EchoKnob*) &volume })
    {
        const float pos = (float) k->valueToProportionOfLength (k->getValue());
        if (k->lastPos < 0.0f) k->lastPos = pos;
        const float degPerSec = std::abs (pos - k->lastPos) * 270.0f / (float) dt;
        k->lastPos = pos;
        const float teethPerFrame = degPerSec / 60.0f / (360.0f / knobTeeth);
        const float target = jlimit (0.0f, 1.6f, (teethPerFrame - 0.15f) / 0.6f);
        k->blur = target >= k->blur ? target : k->blur * (float) std::pow (0.6, dt * 60.0);
        if (k->blur < 0.01f) k->blur = 0.0f;
        if (std::abs (k->blur - k->drawnBlur) > 0.01f)
            k->repaint();
    }

    // --- Ligne d'etat : le dernier reglage qui bouge (un seul a la fois ; un preset ne l'affiche pas)
    {
        int changed = -1, numChanged = 0;
        for (int i = 0; i < numValueIds; ++i)
        {
            const float v = proc.apvts.getRawParameterValue (valueIds[i])->load();
            if (std::abs (v - lastValues[i]) > 1.0e-4f) { lastValues[i] = v; changed = i; ++numChanged; }
        }
        if (numChanged == 1 || (numChanged == 2 && changed == 7)) { lastChanged = changed; showStatus(); }   // SYNC : division + potard
        if (sustain.isMouseButtonDown()) { lastChanged = 1; showStatus(); }
        if (delay.isMouseButtonDown())   { lastChanged = 0; showStatus(); }
        if (volume.isMouseButtonDown() && ! volume.isHolding()) { lastChanged = volumeOnAge ? 3 : 2; showStatus(); }
        if (proc.ageEdit.load()) showStatus();
    }

    // MIDI Learn : la ligne d'etat reste affichee pendant l'attente ; message 2 s apres l'affectation
    const int learned = proc.lastLearned.exchange (-1);
    if (learned >= 0)
    {
        learnMsg = String (EchoflexAudioProcessor::learnInfo (learned).name) + " = CC " + String (proc.ccNum[learned].load());
        learnMsgUntil = now + 2000.0;
        statusUntil = jmax (statusUntil, learnMsgUntil);
    }
    if (proc.learnTarget.load() >= 0)
        showStatus();
    const int mc = proc.midiCounter.load();
    if (mc != lastMidiCount) { lastMidiCount = mc; midiFlash = 8; }
    if (midiFlash > 0) --midiFlash;

    const int tc = proc.tapCounter.load();
    if (tc != lastTapCount) { lastTapCount = tc; tapFlash = 1.0f; lastChanged = 8; showStatus(); }
    tapFlash = jmax (0.0f, tapFlash - (float) dt * 5.0f);

    const float target = now < statusUntil ? 1.0f : 0.0f;
    statusAlpha += (target - statusAlpha) * (target > statusAlpha ? 0.45f : 0.12f);
    if (statusAlpha < 0.005f) statusAlpha = 0.0f;
    if (statusAlpha > 0.995f) statusAlpha = 1.0f;

    // --- LED AGE (ambre) : allumee si AGE actif, clignote pendant le reglage, se remplit pendant l'appui long
    blinkPhase += dt;
    const bool ageOn = proc.apvts.getRawParameterValue ("ageOn")->load() > 0.5f;
    float ageTarget = ageOn ? 1.0f : 0.0f;
    if (proc.ageEdit.load())
        ageTarget = std::fmod (blinkPhase, 0.4) < 0.2 ? 1.0f : 0.08f;
    else if (volume.isHolding() && now - volume.holdStart() > 350.0)
        ageTarget = (float) jlimit (0.0, 1.0, (now - volume.holdStart()) / longPressMs) * (std::fmod (blinkPhase, 0.2) < 0.1 ? 1.0f : 0.5f);
    ageLedLevel += (ageTarget - ageLedLevel) * 0.6f;
    if (std::abs (ageTarget - ageLedLevel) < 0.002f) ageLedLevel = ageTarget;

    // --- LED SYNC (verte) : eteinte hors synchro ; en synchro, flash a chaque division du tempo
    {
        const bool syncOn = roundToInt (proc.apvts.getRawParameterValue ("timeSrc")->load()) == 2;
        float tg = 0.0f;
        if (syncOn)
        {
            const double bpm = proc.hostBpm.load();
            const double beats = EchoflexAudioProcessor::syncBeats (roundToInt (proc.apvts.getRawParameterValue ("syncDiv")->load()));
            double ph;
            if (bpm > 1.0 && proc.hostPlaying.load())
            {
                const double ppq = proc.hostPpq.load() + (now - proc.hostPpqTime.load()) / 60000.0 * bpm;
                ph = std::fmod (ppq / beats, 1.0);
                if (ph < 0.0) ph += 1.0;
            }
            else
            {
                const double periodMs = jmax (65.0, (double) proc.delayMsDisplay.load());
                freePhase = std::fmod (freePhase + dt * 1000.0 / periodMs, 1.0);
                ph = freePhase;
            }
            tg = bpm > 1.0 ? 0.30f + 0.70f * (float) std::exp (-ph * 9.0) : 0.22f;
        }
        syncLedLevel += (tg - syncLedLevel) * (tg > syncLedLevel ? 0.85f : 0.5f);
        if (std::abs (tg - syncLedLevel) < 0.002f) syncLedLevel = tg;
    }

    // --- LED rouge : fondu 0,45 a l'allumage / 0,28 a l'extinction, lueur qui respire avec les repetitions
    const bool on = footswitch.isOn();
    ledLevel += ((on ? 1.0f : 0.0f) - ledLevel) * (on ? 0.45f : 0.28f);
    if (ledLevel < 0.003f) ledLevel = 0.0f;
    if (ledLevel > 0.997f) ledLevel = 1.0f;
    const float echoNow = jlimit (0.0f, 1.0f, proc.echoLevel.load() * 2.5f);
    echoGlow += (echoNow - echoGlow) * (echoNow > echoGlow ? 0.5f : 0.12f);
    ledFlicker = ledLevel > 0.0f ? 0.975f + 0.025f * rng.nextFloat() : 1.0f;

    // --- On ne redessine que ce qui a change (zones separees)
    const float ledNow = ledLevel * ledFlicker * (0.88f + 0.12f * echoGlow);
    if (std::abs (ledNow - drawnLed) > 0.003f)
    {
        drawnLed = ledNow;
        footswitch.ledLevel = ledLevel;
        askRepaint (scaled (layout::redGlow));
        footswitch.repaint();
    }
    if (std::abs (ageLedLevel - drawnAge) > 0.003f)   { drawnAge = ageLedLevel;   askRepaint (scaled (layout::amberGlow)); }
    if (std::abs (syncLedLevel - drawnSync) > 0.003f) { drawnSync = syncLedLevel; askRepaint (scaled (layout::greenGlow)); }
    const float tapNow = jmax (tapFlash, tapArea.isMouseOver() ? 0.25f : 0.0f);
    if (std::abs (tapNow - drawnTap) > 0.003f)
    {
        drawnTap = tapNow;
        askRepaint (scaled (layout::tapRect.expanded (12.0f)));
    }

    const auto st = buildStatusLine(), pl = buildPresetLine();
    const bool textChanged = st != lastStatus || pl != lastPreset;
    lastStatus = st; lastPreset = pl;
    if (std::abs (statusAlpha - drawnStatus) > 0.003f || textChanged || hoverZone != drawnHover || midiFlash > 0)
    {
        drawnStatus = statusAlpha; drawnHover = hoverZone;
        askRepaint (scaled (layout::presetRect.expanded (3.0f)));
    }
}

//==============================================================================
void EchoflexAudioProcessorEditor::drawLeds (Graphics& g)
{
    const float level[3] = { ledLevel, ageLedLevel, syncLedLevel };
    const float glowMul[3] = { ledFlicker * (0.88f + 0.12f * echoGlow), 1.0f, 1.0f };
    for (int i = 0; i < 3; ++i)
    {
        if (level[i] <= 0.003f) continue;
        // la facade recoit la lumiere de la LED (calque precalcule) puis la lentille allumee (photo)
        const Image& gl = glowS[i].isValid() ? glowS[i] : glow[i];
        if (gl.isValid()) { g.setOpacity (jmin (1.0f, level[i] * glowMul[i])); g.drawImage (gl, glowRect[i]); }
        if (lens[i].isValid()) { g.setOpacity (level[i]); g.drawImage (lens[i], lensRect[i]); }
    }
    g.setOpacity (1.0f);
}

void EchoflexAudioProcessorEditor::drawTapFlash (Graphics& g)
{
    const float a = jmax (tapFlash, tapArea.isMouseOver() ? 0.25f : 0.0f);
    if (a <= 0.0f) return;
    const auto c = layout::tapJack;
    const float r = 30.0f;
    ColourGradient gl (Colours::white.withAlpha (0.45f * a), c.x, c.y, Colours::white.withAlpha (0.0f), c.x + r, c.y, true);
    g.setGradientFill (gl);
    g.fillEllipse (c.x - r, c.y - r, r * 2.0f, r * 2.0f);
}

void EchoflexAudioProcessorEditor::drawPresetBar (Graphics& g)
{
    const auto r = layout::presetRect;
    const float rad = r.getHeight() * 0.5f;
    const float sa = statusAlpha, pa = 1.0f - statusAlpha;     // fondu enchaine presets <-> ligne d'etat
    const bool ageEdit = proc.ageEdit.load();

    g.setColour (pillBg);
    g.fillRoundedRectangle (r, rad);
    const Colour line = (ageEdit && sa > 0.0f) ? amber.withAlpha (0.75f) : pillLine.withAlpha (hoverZone != 0 ? 0.80f : 0.47f);
    g.setColour (line);
    g.drawRoundedRectangle (r.reduced (0.5f), rad, 1.0f);

    const Font f (FontOptions (medFace).withPointHeight (13.0f));
    g.setFont (f);
    const float aw = 30.0f;
    if (pa > 0.003f)
    {
        auto arrow = [&] (float ax, bool left, bool hot)
        {
            Path p; const float cy = r.getCentreY();
            if (left) p.addTriangle (ax + 5.0f, cy - 6.0f, ax + 5.0f, cy + 6.0f, ax - 5.0f, cy);
            else      p.addTriangle (ax - 5.0f, cy - 6.0f, ax - 5.0f, cy + 6.0f, ax + 5.0f, cy);
            g.setColour (Colour (200, 200, 205).withAlpha ((hot ? 1.0f : 0.78f) * pa));
            g.fillPath (p);
        };
        arrow (r.getX() + 14.0f, true, hoverZone == 1);
        arrow (r.getRight() - 14.0f, false, hoverZone == 3);
        g.setColour ((midiFlash > 0 ? Colour (0xffff8a70) : Colour (232, 232, 236)).withAlpha ((hoverZone == 2 ? 1.0f : 0.92f) * pa));
        g.drawFittedText (lastPreset, r.reduced (aw, 0.0f).toNearestInt(), Justification::centred, 1, 0.75f);
    }
    if (sa > 0.003f)
    {
        g.setColour ((ageEdit ? Colour (0xffffd9a0) : Colour (232, 232, 236)).withAlpha (sa));
        g.drawFittedText (lastStatus, r.reduced (14.0f, 0.0f).toNearestInt(), Justification::centred, 1, 0.7f);
    }
}

//==============================================================================
// Serigraphie vectorielle : construite une fois en chemins (unites du plugin), remplie a l'echelle de la fenetre
//==============================================================================
void EchoflexAudioProcessorEditor::buildPrint()
{
    printPath.clear();
    auto glyphPath = [this] (const Font& font, const String& s, float track)
    {
        GlyphArrangement ga;
        float x = 0.0f;
        for (int i = 0; i < s.length(); ++i)
        {
            const String ch = String::charToString (s[i]);
            ga.addLineOfText (font, ch, x, 0.0f);
            x += GlyphArrangement::getStringWidth (font, ch) + track;
        }
        Path p; ga.createPath (p);
        const auto c = p.getBounds().getCentre();           // centre = boite des lettres (comme l'apercu)
        p.applyTransform (AffineTransform::translation (-c.x, -c.y));
        return p;
    };

    for (const auto& t : layout::texts)
    {
        const float em = t.cap / 0.70f;                      // Poppins : capitale = 0,70 em
        const Font font (FontOptions (boldFace).withPointHeight (em));
        Path p = glyphPath (font, t.s, t.track * em);
        p.applyTransform (AffineTransform::rotation (-t.rot * MathConstants<float>::pi / 180.0f).translated (t.x, t.y));
        printPath.addPath (p);
    }

    // PUSH FOR AGE en arc sous le potard VOLUME (lettres droites vers le centre)
    {
        const float em = layout::pushCap / 0.70f, track = 0.10f * em, r = layout::pushR;
        const Font font (FontOptions (boldFace).withPointHeight (em));
        const String s ("PUSH FOR AGE");
        float total = -track;
        for (int i = 0; i < s.length(); ++i) total += GlyphArrangement::getStringWidth (font, String::charToString (s[i])) + track;
        float a = MathConstants<float>::halfPi + total / r * 0.5f;
        for (int i = 0; i < s.length(); ++i)
        {
            const String ch = String::charToString (s[i]);
            const float w = GlyphArrangement::getStringWidth (font, ch);
            if (ch != " ")
            {
                const float mid = a - (w * 0.5f) / r;
                Path p = glyphPath (font, ch, 0.0f);
                p.applyTransform (AffineTransform::rotation (mid - MathConstants<float>::halfPi)
                                      .translated (layout::pushCentre.x + r * std::cos (mid), layout::pushCentre.y + r * std::sin (mid)));
                printPath.addPath (p);
            }
            a -= (w + track) / r;
        }
    }
}

void EchoflexAudioProcessorEditor::drawOverlay (Graphics& g)
{
    g.setColour (layout::ink);
    g.fillPath (printPath);
    if (logo != nullptr)
    {
        const auto vb = logo->getDrawableBounds();
        const float w = layout::logoW, h = w * vb.getHeight() / jmax (1.0f, vb.getWidth());
        logo->drawWithin (g, { layout::logoPos.x - w * 0.5f, layout::logoPos.y - h * 0.5f, w, h }, RectanglePlacement::centred, 1.0f);
    }
    drawPresetBar (g);
}

void EchoflexAudioProcessorEditor::paint (Graphics& g)
{
    lastPaintMs = Time::getMillisecondCounterHiRes();
    repaintAskedMs = 0.0;
    g.fillAll (Colour (0xff111112));          // autour des jacks : le fond de l'image est transparent
    // anti-gel : aucun rescale ici, on dessine le cache existant (ou l'original en attendant le timer)
    const Image& bg = bgScaled.isValid() ? bgScaled : background;
    g.setImageResamplingQuality (&bg == &background ? Graphics::highResamplingQuality : Graphics::lowResamplingQuality);
    if (bg.isValid()) g.drawImage (bg, getLocalBounds().toFloat());

    g.addTransform (AffineTransform::scale (unitScale()));
    g.setImageResamplingQuality (Graphics::mediumResamplingQuality);
    drawLeds (g);
    drawTapFlash (g);
}

//==============================================================================
// Souris : barre de presets (fleches = precedent / suivant, nom = menu deroulant), clic droit = menu
//==============================================================================
static int presetZoneAt (Point<float> p)
{
    const auto r = layout::presetRect;
    if (! r.contains (p)) return 0;
    if (p.x < r.getX() + 30.0f) return 1;
    if (p.x > r.getRight() - 30.0f) return 3;
    return 2;
}

void EchoflexAudioProcessorEditor::mouseMove (const MouseEvent& e)
{
    hoverZone = presetZoneAt (e.position / unitScale());
    setMouseCursor (hoverZone != 0 ? MouseCursor::PointingHandCursor : MouseCursor::NormalCursor);
}

void EchoflexAudioProcessorEditor::mouseExit (const MouseEvent&) { hoverZone = 0; }

void EchoflexAudioProcessorEditor::mouseDown (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) { showContextMenu(); return; }
    switch (presetZoneAt (e.position / unitScale()))
    {
        case 1: stepPreset (-1); break;
        case 2: showPresetMenu(); break;
        case 3: stepPreset (1); break;
        default: break;
    }
}

//==============================================================================
// MENUS (design Octopus, NineHandsMenu.h)
//==============================================================================
void EchoflexAudioProcessorEditor::showPresetMenu()
{
    PopupMenu m;
    m.addSectionHeader ("Factory presets");
    for (int i = 0; i < EchoflexAudioProcessor::getNumFactoryPresets(); ++i)
        m.addItem (100 + i, String (i + 1) + ". " + EchoflexAudioProcessor::getFactoryPreset (i).name, true, proc.currentPreset.load() == i);
    m.addSeparator();
    PopupMenu load, save;
    for (int slot = 1; slot <= 9; ++slot)
    {
        const bool exists = proc.hasUserPreset (slot);
        load.addItem (200 + slot, "User " + String (slot) + (exists ? "" : "  (empty)"), exists, proc.currentPreset.load() == 100 + slot);
        save.addItem (300 + slot, "User " + String (slot) + (exists ? "  (overwrite)" : ""));
    }
    m.addSubMenu ("Load user preset", load);
    m.addSubMenu ("Save user preset", save);

    m.setLookAndFeel (&menuLnf);
    m.showMenuAsync (PopupMenu::Options().withTargetScreenArea (localAreaToGlobal (scaled (layout::presetRect))),
        [safe = Component::SafePointer<EchoflexAudioProcessorEditor> (this)] (int r)
        {
            if (safe == nullptr || r == 0) return;
            auto& pr = safe->proc;
            if      (r >= 100 && r < 200) pr.applyFactoryPreset (r - 100);
            else if (r > 200 && r < 300)  pr.loadUserPreset (r - 200);
            else if (r > 300 && r < 400)  pr.saveUserPreset (r - 300);
        });
}

void EchoflexAudioProcessorEditor::showSyncMenu()
{
    auto raw = [this] (const char* id) { return proc.apvts.getRawParameterValue (id)->load(); };
    const int src = roundToInt (raw ("timeSrc"));
    PopupMenu m;
    NineHandsMenu::addHeader (m, menuLnf.f, NineHandsMenu::icoSettings, Colour (0xff36e05a), "Sync", "Delay locked to the DAW tempo");
    addLearnItems (m, { EchoflexAudioProcessor::lSync });
    m.addSectionHeader ("Sync delay to DAW tempo");
    m.addItem (1, "Sync on", true, src == 2);
    m.addSeparator();
    const auto names = EchoflexAudioProcessor::syncNames();
    for (int i = 0; i < names.size(); ++i)
        m.addItem (10 + i, names[i], true, src == 2 && roundToInt (raw ("syncDiv")) == i);

    m.setLookAndFeel (&menuLnf);
    m.showMenuAsync (PopupMenu::Options().withMousePosition(),
        [safe = Component::SafePointer<EchoflexAudioProcessorEditor> (this)] (int r)
        {
            if (safe == nullptr || r == 0 || r == 9001) return;
            if (safe->handleLearnResult (r)) return;
            if (r == 1) safe->toggleSync();
            else
            {
                safe->setParamValue ("syncDiv", (float) (r - 10));
                safe->setParamValue ("delay", EchoflexAudioProcessor::knobForSyncDiv (r - 10));
                safe->setParamValue ("timeSrc", 2.0f);
                safe->lastChanged = 7;
                safe->showStatus();
            }
        });
}

// MIDI Learn (menus) : 1000 + n = learn, 1100 = annuler, 1101 = tout effacer, 1200 + n = effacer
static String ccLabel (int cc)
{
    return cc >= 0 ? "CC " + String (cc) : String (CharPointer_UTF8 ("\xe2\x80\x94"));
}

void EchoflexAudioProcessorEditor::addLearnItems (PopupMenu& m, const Array<int>& learnItems)
{
    if (learnItems.isEmpty()) return;
    for (int i : learnItems)
    {
        const String name = EchoflexAudioProcessor::learnInfo (i).name;
        const int cc = proc.ccNum[i].load();
        m.addItem (1000 + i, "MIDI Learn: " + name + " (" + ccLabel (cc) + ")", true, proc.learnTarget.load() == i);
        m.addItem (1200 + i, "Clear MIDI: " + name, cc >= 0);
    }
    if (proc.learnTarget.load() >= 0)
        m.addItem (1100, "Cancel MIDI learn");
    m.addSeparator();
}

bool EchoflexAudioProcessorEditor::handleLearnResult (int r)
{
    using P = EchoflexAudioProcessor;
    if (r >= 1000 && r < 1000 + P::numLearn)      proc.learnTarget.store (r - 1000);
    else if (r == 1100)                           proc.learnTarget.store (-1);
    else if (r == 1101)
    {
        proc.learnTarget.store (-1);
        proc.clearMidiMap();
        learnMsg = "MIDI: all assignments cleared";
        learnMsgUntil = Time::getMillisecondCounterHiRes() + 2000.0;
    }
    else if (r >= 1200 && r < 1200 + P::numLearn)
    {
        proc.ccNum[r - 1200].store (-1);
        learnMsg = String (P::learnInfo (r - 1200).name) + " = " + ccLabel (-1);
        learnMsgUntil = Time::getMillisecondCounterHiRes() + 2000.0;
    }
    else
        return false;
    showStatus();
    return true;
}

void EchoflexAudioProcessorEditor::showContextMenu (Array<int> learnItems)
{
    auto raw = [this] (const char* id) { return proc.apvts.getRawParameterValue (id)->load(); };
    PopupMenu menu;
    if (learnItems.isEmpty())
        NineHandsMenu::addHeader (menu, menuLnf.f, NineHandsMenu::icoPedal, Colour (0xffff4a36), "Echoflex", "Tape echo  v" + String (JucePlugin_VersionString));
    else
        NineHandsMenu::addHeader (menu, menuLnf.f, learnItems[0] == EchoflexAudioProcessor::lFoot ? NineHandsMenu::icoSwitch
                                                    : learnItems[0] == EchoflexAudioProcessor::lTap ? NineHandsMenu::icoMidi : NineHandsMenu::icoKnob,
                                  Colour (0xffff4a36), EchoflexAudioProcessor::learnInfo (learnItems[0]).name, "MIDI Learn");
    addLearnItems (menu, learnItems);

    {
        // Plugin size : taille de cette fenetre + taille par defaut des nouvelles fenetres
        const char* names[numSizes] = { "60 %", "75 %", "100 %" };
        const int def = WigaWindowSize::defaultIndex (JucePlugin_Name, numSizes);
        PopupMenu sizes, defSizes;
        for (int i = 0; i < numSizes; ++i)
        {
            sizes.addItem (1 + i, String (names[i]) + (i == def ? "  (default)" : ""), true, std::abs (getHeight() - sizeHeight (i)) <= 2);
            defSizes.addItem (20 + i, names[i], true, i == def);
        }
        sizes.addSeparator();
        sizes.addSubMenu ("Default size (new windows)", defSizes);
        menu.addSubMenu ("Plugin size", sizes);
    }
    menu.addSeparator();

    PopupMenu factory;
    for (int i = 0; i < EchoflexAudioProcessor::getNumFactoryPresets(); ++i)
        factory.addItem (100 + i, String (i + 1) + ". " + EchoflexAudioProcessor::getFactoryPreset (i).name,
                         true, proc.currentPreset.load() == i);
    menu.addSubMenu ("Factory presets", factory);
    PopupMenu load, save;
    for (int slot = 1; slot <= 9; ++slot)
    {
        const bool exists = proc.hasUserPreset (slot);
        load.addItem (200 + slot, "User " + String (slot) + (exists ? "" : "  (empty)"), exists,
                      proc.currentPreset.load() == 100 + slot);
        save.addItem (300 + slot, "User " + String (slot) + (exists ? "  (overwrite)" : ""));
    }
    menu.addSubMenu ("Load user preset", load);
    menu.addSubMenu ("Save user preset", save);
    menu.addSeparator();

    PopupMenu age;
    age.addItem (50, "Age on (click VOLUME)", true, raw ("ageOn") > 0.5f);
    age.addItem (51, proc.ageEdit.load() ? "Lock Age setting" : "Set Age (hold VOLUME 2 s)");
    menu.addSubMenu ("Age", age);

    const int src = roundToInt (raw ("timeSrc"));
    PopupMenu timeMenu;
    timeMenu.addItem (60, "DELAY knob (65 - 750 ms)", true, src == 0);
    timeMenu.addItem (61, "Tap tempo (" + String (roundToInt (raw ("tapMs"))) + " ms) - click TAP", true, src == 1);
    PopupMenu sync;
    const auto names = EchoflexAudioProcessor::syncNames();
    for (int i = 0; i < names.size(); ++i)
        sync.addItem (70 + i, names[i], true, src == 2 && roundToInt (raw ("syncDiv")) == i);
    timeMenu.addSubMenu ("Sync to DAW tempo (click DELAY / SYNC)", sync, true, nullptr, src == 2);
    menu.addSubMenu ("Delay time", timeMenu);

    PopupMenu settings;
    settings.addItem (40, "True relay bypass",       true, raw ("bypassMode") < 0.5f);
    settings.addItem (41, "Trails bypass",           true, raw ("bypassMode") > 0.5f);
    settings.addSeparator();
    settings.addItem (42, "Dry + echo",              true, raw ("mix") < 0.5f);
    settings.addItem (43, "100% wet (kill dry)",     true, raw ("mix") > 0.5f);
    settings.addSeparator();
    settings.addItem (44, "Mono (EP103 default)",    true, raw ("channels") < 0.5f);
    settings.addItem (45, "Stereo",                  true, raw ("channels") > 0.5f);
    menu.addSubMenu ("Startup settings", settings);
    menu.addSeparator();

    PopupMenu midi;
    for (int i = 0; i < EchoflexAudioProcessor::numLearn; ++i)
        midi.addItem (1000 + i, "Learn: " + String (EchoflexAudioProcessor::learnInfo (i).name)
                                  + " (" + ccLabel (proc.ccNum[i].load()) + ")", true, proc.learnTarget.load() == i);
    midi.addSeparator();
    if (proc.learnTarget.load() >= 0)
        midi.addItem (1100, "Cancel MIDI learn");
    midi.addItem (1101, "Clear all MIDI assignments");
    midi.addSeparator();
    midi.addItem (908, "Program Change 1-" + String (EchoflexAudioProcessor::getNumFactoryPresets()) + "  Factory presets", false);
    menu.addSubMenu ("MIDI", midi);

    menu.addSeparator();
    menu.addItem (999, "Echoflex delay v" + String (JucePlugin_VersionString) + " - NINE HANDS | DSP", false);

    menu.setLookAndFeel (&menuLnf);
    menu.showMenuAsync (PopupMenu::Options().withMousePosition(),       // menu clic droit : toujours la ou l'on clique
        [safe = Component::SafePointer<EchoflexAudioProcessorEditor> (this)] (int r)
        {
            if (safe == nullptr || r == 0 || r == 9001) return;
            auto& ed = *safe;
            if (ed.handleLearnResult (r)) return;
            if      (r >= 1 && r < 1 + numSizes) ed.setScaledHeight (ed.sizeHeight (r - 1));
            else if (r >= 20 && r < 20 + numSizes)
            {
                WigaWindowSize::setDefaultIndex (JucePlugin_Name, r - 20);   // toutes les nouvelles fenetres de ce plugin
                ed.setScaledHeight (ed.sizeHeight (r - 20));                // et cette fenetre tout de suite
            }
            else if (r == 40 || r == 41) ed.setParamValue ("bypassMode", r == 41 ? 1.0f : 0.0f);
            else if (r == 42 || r == 43) ed.setParamValue ("mix",        r == 43 ? 1.0f : 0.0f);
            else if (r == 44 || r == 45) ed.setParamValue ("channels",   r == 45 ? 1.0f : 0.0f);
            else if (r == 50) ed.toggleAge();
            else if (r == 51) ed.setAgeEdit (! ed.proc.ageEdit.load());
            else if (r == 60) ed.setParamValue ("timeSrc", 0.0f);
            else if (r == 61) ed.setParamValue ("timeSrc", 1.0f);
            else if (r >= 70 && r < 80)
            {
                ed.setParamValue ("syncDiv", (float) (r - 70));
                ed.setParamValue ("delay", EchoflexAudioProcessor::knobForSyncDiv (r - 70));
                ed.setParamValue ("timeSrc", 2.0f);
            }
            else if (r >= 100 && r < 200) ed.proc.applyFactoryPreset (r - 100);
            else if (r > 200 && r < 300)  ed.proc.loadUserPreset (r - 200);
            else if (r > 300 && r < 400)  ed.proc.saveUserPreset (r - 300);
        });
}
