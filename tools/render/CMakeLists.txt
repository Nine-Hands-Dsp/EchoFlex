cmake_minimum_required(VERSION 3.22)
project(EchoTest2 VERSION 2.0.0 LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(JUCE_DIR "" CACHE PATH "Copie locale de JUCE 8.0.15")
add_subdirectory(${JUCE_DIR} ${CMAKE_BINARY_DIR}/juce)
get_filename_component(R ${CMAKE_CURRENT_SOURCE_DIR}/../.. ABSOLUTE)
juce_add_binary_data(EchoflexData SOURCES ${R}/background.png ${R}/knob_strip.png ${R}/knob_blur1.png ${R}/knob_blur2.png
    ${R}/led_on_red.png ${R}/led_on_amber.png ${R}/led_on_green.png ${R}/glow_red.png ${R}/glow_amber.png ${R}/glow_green.png ${R}/fs_refl.png
    ${R}/Poppins-Regular.ttf ${R}/Poppins-Medium.ttf ${R}/Poppins-Bold.ttf ${R}/NineHandsLogo.svg)
set_target_properties(EchoflexData PROPERTIES POSITION_INDEPENDENT_CODE TRUE)
juce_add_console_app(EchoShots PRODUCT_NAME "EchoShots")
target_sources(EchoShots PRIVATE shots.cpp ${R}/PluginProcessor.cpp ${R}/PluginEditor.cpp)
target_include_directories(EchoShots PRIVATE ${R})
target_compile_definitions(EchoShots PRIVATE JucePlugin_Name="Echoflex" JucePlugin_VersionString="2.0.0" JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0
  JUCE_USE_XRANDR=0 JUCE_USE_XINERAMA=0 JUCE_USE_XCURSOR=0 JUCE_USE_XRENDER=0 JUCE_USE_XSHM=0 JUCE_ALSA=0 JUCE_JACK=0)
target_link_libraries(EchoShots PRIVATE EchoflexData juce::juce_audio_utils juce::juce_audio_processors juce::juce_gui_basics
  juce::juce_recommended_config_flags juce::juce_recommended_warning_flags)
