# Atelier ESP-NOW — un bouton sur une carte, un écran sur l'autre

Deux cartes se parlent directement, sans box ni WiFi : l'**émetteur** (ESP32 simple + bouton) compte les appuis et envoie le total ; le **récepteur** (LilyGo T5, écran e-paper) l'affiche en gros avec la force du signal.

## Matériel

| Carte | Rôle | Branchement |
|---|---|---|
| ESP32 simple | émetteur | bouton entre GPIO5 et GND, LED intégrée sur GPIO2 |
| LilyGo T5 V2.3 | récepteur | rien (écran déjà câblé) ; pilote `../../cours-exemples/epaper/gdeh0213b73.py` à téléverser |

## Manips

| Fichier | Sur quelle carte | Rôle |
|---|---|---|
| `manip01_adresse_mac.py` | les deux | affiche l'adresse MAC de la carte |
| `manip03_recepteur_epaper.py` | T5 | affiche son adresse au démarrage, puis le nombre reçu |
| `manip02_emetteur_bouton.py` | ESP32 simple | compte les appuis et les envoie ; la LED indique si l'autre carte a répondu |

Ordre conseillé : 01 sur chaque carte, 03 sur la T5 (l'écran donne son adresse), puis recopier cette adresse dans `MAC_RECEPTEUR` de 02.

## À savoir

- MicroPython doit fournir le module `espnow` (versions récentes). Test : `import espnow` dans le REPL.
- L'émetteur envoie le **total**, pas « +1 » : un message perdu ne fausse rien.
- Le récepteur ne redessine que le dernier nombre reçu, au plus une fois toutes les 3 s (l'e-paper met ~2 s à se rafraîchir).
- Pour tester la portée, s'éloigner avec l'émetteur et regarder le signal (dBm) sur l'écran.
