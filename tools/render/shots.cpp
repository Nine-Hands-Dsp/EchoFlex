#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_audio_utils/juce_audio_utils.h>
#include <juce_gui_basics/juce_gui_basics.h>
#define private public
#include "PluginProcessor.h"
#include "PluginEditor.h"
#undef private
using namespace juce;
static void setP (EchoflexAudioProcessor& p, const char* id, float v)
{ auto* q = p.apvts.getParameter (id); q->setValueNotifyingHost (q->convertTo0to1 (v)); }
int main (int argc, char** argv)
{
    ScopedJuceInitialiser_GUI init;
    const String dir = argv[1];
    EchoflexAudioProcessor p;
    p.setPlayConfigDetails (2, 2, 48000, 256); p.prepareToPlay (48000, 256);
    std::unique_ptr<AudioProcessorEditor> base (p.createEditor());
    auto* ed = dynamic_cast<EchoflexAudioProcessorEditor*> (base.get());
    const int H = argc > 2 ? String (argv[2]).getIntValue() : 958;
    ed->setScaledHeight (H);
    ed->stopTimer();
    ed->forceRenderScale (2.0f);
    ed->resizeSettle = 0;
    auto shot = [&] (const String& name)
    {
        ed->lastStatus = ed->buildStatusLine(); ed->lastPreset = ed->buildPresetLine();
        auto img = ed->createComponentSnapshot (ed->getLocalBounds(), true, 2.0f);
        File f (dir + "/" + name); f.deleteFile();
        FileOutputStream os (f); PNGImageFormat png; png.writeImageToStream (img, os);
        std::cout << name << " " << img.getWidth() << "x" << img.getHeight() << std::endl;
    };
    for (int i = 0; i < 20; ++i) { setP (p, "delay", (float) i * 0.5f); ed->timerCallback(); Thread::sleep (16); }
    std::cout << "blur after spin " << ed->delay.blur << " status " << ed->buildStatusLine() << std::endl;
    ed->delay.blur = 0.0f;
    auto reset = [&]
    {
        p.applyFactoryPreset (0); p.delayMsDisplay = EchoflexAudioProcessor::knobToMs (5.0f); p.ageEdit = false;
        ed->ledLevel = 1.0f; ed->footswitch.ledLevel = 1.0f; ed->ageLedLevel = 0.0f; ed->syncLedLevel = 0.0f; ed->tapFlash = 0.0f;
        ed->statusAlpha = 0.0f; ed->lastChanged = -1; ed->delay.blur = ed->sustain.blur = ed->volume.blur = 0.0f; ed->echoGlow = 0.0f; ed->ledFlicker = 1.0f;
    };
    reset(); shot ("ech_main.png");
    ed->ledLevel = 0.0f; ed->footswitch.ledLevel = 0.0f; setP (p, "active", 0.0f); shot ("ech_bypass.png");
    reset(); setP (p, "ageOn", 1.0f); ed->ageLedLevel = 1.0f; shot ("ech_age.png");
    reset(); p.ageEdit = true; setP (p, "ageOn", 1.0f); ed->ageLedLevel = 1.0f; ed->statusAlpha = 1.0f; shot ("ech_ageedit.png");
    reset(); ed->lastChanged = 0; ed->statusAlpha = 1.0f; shot ("ech_statusline.png");
    reset(); p.hostBpm = 120.0f; setP (p, "syncDiv", 4.0f); setP (p, "delay", EchoflexAudioProcessor::knobForSyncDiv (4)); setP (p, "timeSrc", 2.0f);
    p.delayMsDisplay = 375.0f; ed->syncLedLevel = 1.0f; ed->lastChanged = 7; ed->statusAlpha = 1.0f; shot ("ech_sync.png");
    reset(); setP (p, "tapMs", 420.0f); setP (p, "timeSrc", 1.0f); ed->tapFlash = 1.0f; ed->lastChanged = 8; ed->statusAlpha = 1.0f; shot ("ech_tap.png");
    reset(); setP (p, "delay", 7.0f); setP (p, "sustain", 3.0f); ed->delay.blur = 1.6f; ed->sustain.blur = 0.8f; shot ("ech_blur.png");
    for (int i = 0; i < EchoflexAudioProcessor::getNumFactoryPresets(); ++i)
    {
        reset(); p.applyFactoryPreset (i); const auto& fp = EchoflexAudioProcessor::getFactoryPreset (i);
        ed->ageLedLevel = fp.ageOn ? 1.0f : 0.0f; shot ("ech_preset" + String (i + 1) + ".png");
    }
    return 0;
}
