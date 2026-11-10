cmake_minimum_required(VERSION 3.22)

# macOS : binaire universel (Apple Silicon + Intel)
set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64" CACHE STRING "")
set(CMAKE_OSX_DEPLOYMENT_TARGET "10.13" CACHE STRING "")

project(ECHOFLEX VERSION 2.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)
FetchContent_Declare(
    JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG        8.0.15
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(JUCE)

juce_add_plugin(Echoflex
    COMPANY_NAME                "NINE HANDS | DSP"
    COMPANY_WEBSITE             ""
    PLUGIN_MANUFACTURER_CODE    Wiga
    PLUGIN_CODE                 Ecfx
    FORMATS                     VST3
    PRODUCT_NAME                "Echoflex"
    VERSION                     2.0.0
    IS_SYNTH                    FALSE
    NEEDS_MIDI_INPUT            TRUE
    NEEDS_MIDI_OUTPUT           FALSE
    IS_MIDI_EFFECT              FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE
    COPY_PLUGIN_AFTER_BUILD     FALSE
    VST3_CATEGORIES             "Fx" "Delay"
    DESCRIPTION                 "Tape echo (Dunlop EP103 Echoplex Delay model) - single pedal format"
)

# visuel integre au plugin (aucun fichier externe a l'execution)
juce_add_binary_data(EchoflexData SOURCES
    background.png knob_strip.png knob_blur1.png knob_blur2.png
    led_on_red.png led_on_amber.png led_on_green.png glow_red.png glow_amber.png glow_green.png fs_refl.png
    Poppins-Regular.ttf Poppins-Medium.ttf Poppins-Bold.ttf NineHandsLogo.svg)
set_target_properties(EchoflexData PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

target_sources(Echoflex PRIVATE
    PluginProcessor.cpp
    PluginEditor.cpp
)

if(MSVC)
  target_compile_options(Echoflex PRIVATE /utf-8)
endif()

target_compile_definitions(Echoflex PUBLIC
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0
    JUCE_DISPLAY_SPLASH_SCREEN=0
)

target_link_libraries(Echoflex
    PRIVATE
        EchoflexData
        juce::juce_audio_utils
        juce::juce_audio_processors
        juce::juce_gui_basics
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags
)
