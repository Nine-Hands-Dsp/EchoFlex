# Echoflex (NINE HANDS | DSP) — VST3

Reproduction en plugin VST3 (Windows 11 et macOS) de la pédale **Dunlop EP103 Echoplex Delay**, la version « boîtier » de l'écho à bande Maestro **Echoplex EP-3** (1970-1991).
Usage personnel. Visuel réaliste au format pédale simple NINE HANDS | DSP (image 1246 × 1800, pédale plein cadre), sérigraphie vectorielle en Poppins, logo NINE HANDS | DSP.

<p align="center">
  <a href="https://github.com/Nine-Hands-Dsp/EchoFlex/releases/latest/download/Echoflex-VST3-Windows.zip"><img alt="Télécharger pour Windows" src="https://img.shields.io/badge/%E2%AC%87%20T%C3%A9l%C3%A9charger-Windows-0078D6?style=for-the-badge"></a>
  <a href="https://github.com/Nine-Hands-Dsp/EchoFlex/releases/latest/download/Echoflex-VST3-macOS.zip"><img alt="Télécharger pour macOS" src="https://img.shields.io/badge/%E2%AC%87%20T%C3%A9l%C3%A9charger-macOS-111111?style=for-the-badge&logo=apple&logoColor=white"></a>
  <br>
  <a href="https://github.com/Nine-Hands-Dsp/EchoFlex/releases/latest/download/Echoflex-Notice.pdf"><img alt="Télécharger la notice (PDF)" src="https://img.shields.io/badge/%F0%9F%93%96%20Notice-PDF-919496?style=for-the-badge"></a>
  <br>
  <a href="https://github.com/Nine-Hands-Dsp/EchoFlex/releases/latest"><img alt="Dernière version" src="https://img.shields.io/github/v/release/Nine-Hands-Dsp/EchoFlex?label=derni%C3%A8re%20version&color=919496"></a>
</p>

## Installation

1. Télécharger le zip de son système avec les boutons ci-dessus.
   - **Windows** : copier `Echoflex.vst3` dans `C:\Program Files\Common Files\VST3\`
   - **macOS** : dézipper puis copier `Echoflex.vst3` dans `~/Library/Audio/Plug-Ins/VST3/`
2. Relancer l'analyse des plugins dans le DAW. Le plugin apparaît comme **Echoflex (NINE HANDS | DSP)**.

Chaque push sur `main` recompile Windows (`windows-2022`) et macOS (binaire universel) et publie la Release `v<version>` avec des fichiers à nom fixe.

## Ce que fait la vraie EP103 (documentation)

| Élément | Pédale d'origine | Dans le plugin |
|---|---|---|
| DELAY | Temps de retard 65 → 750 ms | Identique (courbe logarithmique : midi ≈ 221 ms) |
| SUSTAIN | Nombre de répétitions ; 1re moitié douce (1 à 2 répétitions), 2e moitié qui monte « presque exponentiellement », auto-oscillation au maximum | Identique ; l'auto-oscillation est bornée par la saturation de la bande |
| VOLUME | Niveau de l'écho (le son direct reste à l'unité). Peut glisser l'écho derrière le jeu ou rendre les premières répétitions plus fortes | Midi ≈ −6 dB, maximum ≈ +3 dB. Légère interaction avec SUSTAIN, comme sur la pédale |
| AGE (VOLUME poussé) | Clic sur VOLUME : bascule entre le réglage AGE et le son clair d'usine (LED AGE éteinte = son clair). Maintenir VOLUME 2 s : la LED AGE clignote, VOLUME règle alors l'usure ; nouvel appui = verrouillage | Identique : **clic** sur le potard VOLUME = AGE on/off ; **appui maintenu 2 s** = réglage AGE (LED qui clignote, le potard affiche la valeur AGE) ; **clic** = verrouillage |
| Son clair | Bande neuve fraîchement réglée : écho clair, pleurage/scintillement subtils | Wow 0,55 Hz et flutter 7,3/11,7 Hz très légers |
| AGE au maximum | Plus sombre, plus de saturation de bande, plus de modulation (qui paraît aléatoire), « fatigue » de la bande | Filtres fermés jusqu'à ~2,5 kHz, saturation, wow ×15, dérive aléatoire, pertes de niveau, léger souffle qui suit l'écho |
| Préampli | L'écho reçoit la coloration du préampli Echoplex EP101 ; le son direct est intact | Grave +1,5 dB / présence +2,5 dB / saturation douce sur l'écho uniquement |
| Moteur de bande | Tourner DELAY fait glisser la hauteur des répétitions | Inertie du moteur reproduite (~110 ms) |
| TAP | Prise pour MXR M199, jusqu'à 4 s | Clic sur la prise **TAP** (à gauche, en bas) ou CC assigné par MIDI Learn ; moyenne des 3 derniers intervalles ; tourner DELAY reprend la main |
| Footswitch / LED | True bypass relais, LED rouge | Clic sur le footswitch, LED rouge animée |
| Mode de démarrage | Trails bypass, 100 % wet, mono/stéréo (switch interne) | Clic droit > **Startup settings** |

Sources : manuel Dunlop EP103 (jimdunlop.com), fiches zZounds et Chicago Music Exchange, test Premier Guitar, article Starlite Campbell sur l'EP-3.

## Interface

- Fenêtre ouverte par défaut à **493 px de haut** (« 60 % »), impossible de la réduire en dessous, proportions bloquées, jusqu'à 150 %. Clic droit > *Plugin size* (60 / 75 / 100 %) et *Default size (new windows)*.
- **Potards** d'après la photo (128 positions, lumière fixe en haut à gauche). **Flou de mouvement** : quand on tourne vite, la couronne crantée et le centre tournent ensemble, à la même vitesse, et passent en fondu du net au flou puis au flou total (aucun effet stroboscopique) ; le flou retombe dès que le potard ralentit.
- **LED** (photo de LED à lentille facettée) : rouge = effet actif (fondu, lueur qui respire avec les répétitions, reflet sur l'écrou du footswitch), ambre = AGE (clignote pendant le réglage, se remplit pendant l'appui long), verte = SYNC (flashe sur la grille du morceau). Chaque LED éclaire la façade autour d'elle.
- **Barre de presets** entre la LED et le footswitch : ◀ ▶ = preset précédent / suivant, clic sur le nom = menu des presets (usine et utilisateur). Pendant un réglage, la **ligne d'état** prend sa place (valeur du réglage qui bouge, MIDI Learn…), reste 2,5 s puis la barre de presets revient en fondu.
- **SYNC** : clic sur l'inscription DELAY / SYNC = delay calé sur le tempo du DAW ; molette ou clic droit = valeur de note. **TAP** : clic sur la prise TAP (à gauche, en bas).
- **Clic droit** : menus au design Octopus, ouverts à l'endroit du clic (taille, presets, AGE, temps de retard, réglages de démarrage, MIDI). Clic droit sur une commande = son MIDI Learn en tête du menu.

## MIDI

| Message | Fonction |
|---|---|
| CC (MIDI Learn) | Aucun CC assigné par défaut : clic droit > MIDI > Learn (Delay, Sustain, Volume, quantité d'AGE, AGE 64+ ON, TAP à chaque appui, Footswitch ≥ 64 ON, Footswitch bascule, SYNC 64+ = tempo du DAW) |
| Program Change 1-10 | Presets d'usine |

Aucun CC assigné par défaut : clic droit > MIDI > Learn (ou clic droit sur une commande). « Clear all MIDI assignments » efface toutes les assignations. Tous les paramètres sont aussi automatisables dans le DAW.

## Presets d'usine

1. Noon (Manual Start) — tout à midi, le réglage de départ du manuel · 2. Fifties Slapback · 3. Rockabilly Double · 4. Surf Echo · 5. Hot Lead 400 · 6. Fresh Tape Wash · 7. Worn Cartridge · 8. Dark Ambience · 9. Dub Spiral · 10. Runaway Oscillation

## Placement dans Reaper

Comme les autres plugins NINE HANDS | DSP : **avant** Ampire / Impulse. Le mode Mono (par défaut, comme la pédale) envoie le même écho à gauche et à droite, sans opposition de phase : aucune annulation quand un simulateur d'ampli additionne la piste en mono.

## Nouveautés v2.0

- v2.0.0 : pédale refaite au format NINE HANDS | DSP : visuel réaliste plein cadre, sérigraphie vectorielle Poppins, logo NINE HANDS | DSP, LED photo (rouge, ambre, verte) avec lumière sur la façade, jacks et footswitch du kit photo, flou de mouvement des potards, barre de presets partagée avec la ligne d'état, menus au design Octopus. Son et presets inchangés (les projets et presets existants se rechargent à l'identique).
- Sources du visuel : `tools/design/` (`make_art.py`, `make_knob.py`, `make_layout.py` → `Layout.h`).

## Nouveautés v1.4

- v1.4.0 : MIDI Learn sur toutes les commandes (clic droit sur une commande ou menu MIDI), assignations sauvegardées avec le projet

## Nouveautés v1.3

- v1.3.0 : anti-gel v2 (JUCE 8.0.15, caches refaits par le timer, chien de garde, aucun appel à l'hôte depuis le thread audio)

## Nouveautés v1.2

- Nom du plug-in : **Echoflex** (fichier `Echoflex.vst3`, « Echoflex (NINE HANDS | DSP) » dans le DAW).
- **SYNC** : clic sur l'inscription DELAY ou sur la LED SYNC verte = delay calé sur le tempo de Reaper / du DAW. En SYNC, le potard DELAY choisit la valeur de note (1/16 → 1/2) ; molette ou clic droit sur DELAY/SYNC = valeur de note ; CC 28. La LED flashe sur la grille du morceau.
- Crans des potards redessinés : ils tournent sous la lumière fixe (haut-gauche), plus sombres pour le volume.
- « PUSH FOR AGE » plus lisible ; inscription SYNC au-dessus de sa LED.
- Affichage fluide : fond et potards pré-dimensionnés à l'écran, seules les LED et la ligne d'état sont redessinées ; geste d'automation de VOLUME toujours refermé après l'appui long AGE.
- Notice : `docs/Echoflex_Manual_EN-FR_v1.4.1.pdf` (anglais puis français, à jour pour la v1.4.1).

- v1.4.1 : menu de taille de fenêtre : « 60 % (default) », 75 %, 100 % (plus de taille en pixels)
- v1.5.0 : clic droit > *Plugin size* > *Default size (new windows)* : taille par défaut des nouvelles fenêtres au choix (60 / 75 / 100 %), comme dans Octopus
- v1.5.1 : plus aucun CC MIDI assigné par défaut (tout passe par le MIDI Learn)
