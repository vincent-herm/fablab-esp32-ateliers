# Régulation PID — Cours avancé

Régulation de température par PID sur ESP32 avec MicroPython.
Le système chauffe une résistance de puissance et régule sa température
à une consigne donnée (par exemple 45°C).

---

## Le principe de la régulation PID

### Le problème

On veut maintenir une température **exactement** à une consigne.
Sans régulation, on ne peut que chauffer à fond ou éteindre — la température
oscille en permanence autour de la valeur souhaitée.

### La solution : trois termes complémentaires

Le régulateur PID calcule une **commande** (0-100%) à partir de trois termes :

**P — Proportionnel** : réagit à l'erreur actuelle
- Erreur = consigne - mesure
- Plus on est loin de la consigne, plus on chauffe fort
- Seul, il laisse toujours une erreur résiduelle (erreur statique)

**I — Intégral** : corrige l'erreur accumulée dans le temps
- Additionne toutes les erreurs passées
- Élimine l'erreur statique du P
- Trop fort → oscillations lentes

**D — Dérivé** : anticipe les variations
- Réagit à la vitesse de changement de l'erreur
- Freine quand la température monte vite vers la consigne
- Réduit le dépassement (overshoot)

### La formule

```
commande = Kp × erreur + Ki × somme_erreurs + Kd × (erreur - erreur_précédente)
```

- **Kp** : gain proportionnel (plus il est grand, plus la réponse est vive)
- **Ki** : gain intégral (plus il est grand, plus l'erreur statique est corrigée vite)
- **Kd** : gain dérivé (plus il est grand, plus le freinage est fort)

---

## Matériel

| Composant | Rôle | Notes |
|---|---|---|
| ESP32 | Calculateur PID | |
| Résistance de puissance | Élément chauffant | 10Ω 5W ou similaire |
| MOSFET IRLZ44N | Interrupteur de puissance | Commandé en PWM par l'ESP32 |
| DS18B20 | Capteur de température | Collé/attaché sur la résistance |
| Résistance 4,7 kΩ | Pull-up pour le DS18B20 | Entre DATA et 3.3V |
| Alimentation 5V-12V | Alimente la résistance | Via VIN ou source externe |

---

## Câblage

```
                    +5V à +12V (alimentation résistance)
                        │
                   ┌────┤
                   │ R puissance (10Ω 5W)
                   │    │ ← DS18B20 collé dessus
                   └────┤
                        │
                     Drain
           GPIO26 ──── Gate   MOSFET IRLZ44N
                     Source
                        │
                       GND

DS18B20 (3 fils) :
   VCC  → 3.3V
   GND  → GND
   DATA → GPIO27 (+ résistance 4,7 kΩ vers 3.3V)
```

- **GPIO26** : PWM vers la gate du MOSFET (commande de chauffe)
- **GPIO27** : lecture DS18B20 (température)
- Le MOSFET IRLZ44N est "logic level" : il s'ouvre complètement avec 3,3V sur la gate

---

## Fichiers

| Fichier | Description |
|---|---|
| `pid_temperature.py` | Régulation PID complète avec affichage |
| `pid_serveur_web.py` | PID + tableau de bord web (courbe en temps réel) |
| `README.md` | Ce document |
