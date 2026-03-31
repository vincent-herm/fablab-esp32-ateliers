# GRAFCET — Référence pour Claude Code
## Contexte de développement futur

Ce fichier sert de mémoire de travail pour Claude Code lors des futurs
développements de projets GRAFCET pour le Fablab ESP32 de Vincent.

---

## Fichiers de référence (version complète — base de développement)

| Fichier | Rôle |
|---|---|
| `grafcet_complet.py` | Moteur GRAFCET de référence — IEC 60848 |
| `ascenseur_complet.py` | Exemple pédagogique utilisant TOUTES les fonctionnalités |
| `essential.py` | Déclarations carte ENIM (boutons, LEDs, NeoPixel) |

## Fichiers historiques (ancienne version — NE PAS utiliser pour les nouveaux projets)

| Fichier | Rôle |
|---|---|
| `grafcet.py` | Première version du moteur (fronts bugués au début, corrigé ensuite) |
| `grafcet_variante.py` | Version intermédiaire avec validation auto |
| `ascenseur_enim_led.py` | Ascenseur basique (niveau, pas de front d'entrée) |
| `ascenseur_enim_led_front.py` | Ascenseur avec front montant bpA |
| `ascenseur_enim_led_variante.py` | Ascenseur avec validation auto + LED rouge mémorisée |
| `ascenseur_enim.py` | Ascenseur avec OLED |
| `ascenseur.py` | Ascenseur standalone (sans essential.py) |
| `exemple_leds.py` | 6 étapes avec divergence ET |

---

## Architecture du moteur grafcet_complet.py

### Classe Grafcet — attributs

```python
g = Grafcet(nb_etapes=3, etape_initiale=0, nb_fronts=2)

g.etapes[i]       # bool — True si étape i active
g.tempo[i]        # int  — ms depuis activation (reset auto à la désactivation)
g.compt[i]        # int  — compteur libre (reset auto à la désactivation)
g.compt_final[i]  # int  — dernière valeur de compt[i] avant reset
g.rising[i]       # bool — True pendant 1 cycle à l'activation
g.falling[i]      # bool — True pendant 1 cycle à la désactivation
g.entrees[i]      # bool — état brut de l'entrée i (à remplir par l'utilisateur)
g.fm[i]           # bool — front montant d'entrée (1 cycle)
g.fd[i]           # bool — front descendant d'entrée (1 cycle)
g._init           # list — étapes initiales (pour reinitialiser)
```

### Méthodes

```python
g.tick(dt_ms)                    # incrémente tempo des étapes actives
g.franchir(T, transitions)       # Règles 2,4,5 — validation auto + 2 passes
g.reinitialiser()                # Règle 6 — retour situation initiale
g.detecter_fronts_entrees()      # calcule fm/fd à partir de entrees/entrees_prec
```

### Cycle d'exécution (7 phases)

```
1. franchir(T, transitions)       — évolution + fronts d'étape
   [arrêt d'urgence ici si besoin — après franchir, avant tick]
2. tick(20)                       — timers
3. gerer_actions()                — actions (fronts lisibles ici)
4. affecter_sorties()             — sorties physiques
5. lire_entrees()                 — capteurs/boutons → g.entrees[i]
6. detecter_fronts_entrees()      — fm/fd
7. calculer_transitions()         — réceptivités pures (pas de g.etapes[i])
```

---

## Règles IEC 60848 implémentées

| Règle | Description | Implémentation |
|---|---|---|
| 1 | Situation initiale | `etape_initiale` int ou liste |
| 2 | Validation = sources actives + réceptivité | `franchir()` vérifie auto |
| 3 | Évolution des étapes | désactivation sources + activation cibles |
| 4 | Franchissement simultané | deux passes avec set() |
| 5 | Activation/désactivation simultanées | conflit → étape reste active |
| 6 | Réinitialisation | `reinitialiser()` |

## Modes de sortie

| Mode | Quand | Code type |
|---|---|---|
| CONTINU | 1 sortie = 1 étape | `Descendre = g.etapes[1]` |
| MÉMORISÉ | sortie traverse plusieurs étapes | `if g.rising[1]: alarme = True` |

**Règle** : ne jamais mélanger les deux modes pour une même variable.

---

## Pièges connus (à retenir pour le développement)

### 1. fm traverse les transitions
Le `fm[0]` qui déclenche une transition est encore True quand l'étape
suivante s'active. Ne pas utiliser fm pour compter dans l'étape qui
vient juste d'être activée par ce même fm.
**Solution** : compter dans une étape plus tardive.

### 2. compt est remis à 0 à la désactivation
`g.compt[i]` est reset automatiquement quand l'étape i est désactivée.
Pour lire la valeur finale, utiliser `g.compt_final[i]` sur `g.falling[i]`.
Pour compter entre les cycles (inter-étapes), utiliser une variable Python.

### 3. rising AU démarrage/reinit (conforme IEC 60848)
`__init__` et `reinitialiser()` posent `rising[s] = True` pour les
étapes initiales + `_skip_reset = True` pour que `franchir()` ne les
efface pas au premier appel. C'est conforme à la norme : l'étape
initiale "devient active" → c'est un événement d'activation (P1).
**Conséquence** : si on utilise `rising[0]` pour compter des cycles,
le démarrage compte comme un cycle. Initialiser le compteur à -1
pour ignorer ce premier rising (voir ascenseur_complet.py).

### 4. Buzzer PWM inactif après essential.py
`essential.py` appelle `buzzer.deinit()` à l'import. Pour utiliser le
buzzer, il faut `buzzer.init(freq=1000, duty=50)` (pas `buzzer.freq()`
qui crashe avec "PWM is inactive"). Pour couper : `buzzer.deinit()`.

### 5. Arrêt d'urgence hors du GRAFCET
L'AU est testé dans la boucle principale, pas dans le GRAFCET.
C'est un raccourci acceptable. Le GEMMA (cours futur) gérera ça
proprement avec un GRAFCET maître.

### 6. Divergence OU sans priorité
Si deux transitions partent de la même étape et sont toutes deux vraies,
les deux branches s'activent. Responsabilité du concepteur.

---

## Carte ENIM — brochage de référence

### Entrées
| Nom | Pin | Fonction |
|---|---|---|
| bpA | 25 | Bouton A (start) |
| bpB | 34 | Bouton B (fin de course haut) |
| bpC | 39 | Bouton C (fin de course bas) |
| bpD | 36 | Bouton D (arrêt d'urgence) |
| tp1 | 15 | TouchPad 1 |
| tp2 | 4 | TouchPad 2 |
| p1 | 35 | Potentiomètre 1 (ADC) |
| p2 | 33 | Potentiomètre 2 (ADC) |
| ldr | 32 | LDR (ADC) |

### Sorties
| Nom | Pin | Fonction |
|---|---|---|
| led_bleue | 2 | LED bleue |
| led_verte | 18 | LED verte |
| led_jaune | 19 | LED jaune |
| led_rouge | 23 | LED rouge |
| np | 26 | NeoPixel 8 LEDs |
| buzzer | 5 | Buzzer PWM (deinit par essential.py — utiliser init/deinit) |
| Pin 12 | 12 | Sortie libre (moteur descente) |
| Pin 13 | 13 | Sortie libre (moteur montée) |

---

## Projets futurs prévus

### GEMMA (Guide d'Étude des Modes de Marche et d'Arrêt)
- Cours avancé séparé
- GRAFCET maître (modes : F1 production, A1 arrêt initial, D1 arrêt d'urgence, F4 mode manuel)
- Gestion propre de l'arrêt d'urgence via GRAFCET hiérarchique
- Forçage du GRAFCET de production par le GRAFCET de sécurité

### Escape games (client Ardèche Games)
- Serrures RFID (RC522)
- Déclencheurs sonores (ESP32-A1S AudioKit)
- Détection de présence (HC-SR04)
- Synchronisation multi-salles (WiFi/MQTT)
- Tout basé sur grafcet_complet.py

### Ateliers Fablab
- Chaque atelier utilise grafcet_complet.py comme moteur
- L'utilisateur écrit ses 4 fonctions + sa table T
- Le moteur est une boîte noire documentée

---

## Pour créer un nouveau projet GRAFCET

Template minimal :
```python
from grafcet_complet import Grafcet
from essential import synchro_ms, ...

g = Grafcet(nb_etapes=N, nb_fronts=M)

T = [
    (0, (0,), (1,)),
    # ...
]

transitions = [False] * len(T)

def gerer_actions():
    # sorties continues et mémorisées
    # ex. rising[0] : buzzer.init(freq=1000, duty=50) pour bip d'entrée
    pass

def affecter_sorties():
    # application sur le matériel
    pass

def lire_entrees():
    # g.entrees[i] = capteur.value()
    pass

def calculer_transitions():
    # réceptivités pures (pas de g.etapes[i])
    transitions[0] = ...
    pass

while True:
    g.franchir(T, transitions)
    g.tick(20)
    gerer_actions()
    affecter_sorties()
    lire_entrees()
    g.detecter_fronts_entrees()
    calculer_transitions()
    synchro_ms(20)
```
