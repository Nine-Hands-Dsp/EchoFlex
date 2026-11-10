# Banc de rendu (captures de la notice)

Compile l'éditeur hors DAW et enregistre les captures utilisées par `tools/manual.py` (2 x 958 px de haut) :

    cmake -S tools/render -B build-render -DJUCE_DIR=/chemin/vers/JUCE-8.0.15 -DCMAKE_BUILD_TYPE=Release
    cmake --build build-render -j
    ./build-render/EchoShots_artefacts/Release/EchoShots captures 958
    python3 tools/manual.py captures docs/Echoflex_Notice_FR_v<version>.pdf
