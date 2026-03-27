# Threading — Dual Core ESP32

L'ESP32 possède **2 cœurs** de processeur (Tensilica LX6 à 240 MHz chacun). Le module `_thread` de MicroPython permet de lancer une tâche sur le second cœur, pendant que le programme principal tourne sur le premier.

---

## Principe

```python
import _thread

def ma_tache():
    while True:
        # ... code qui tourne en boucle sur le cœur 1
        pass

# Lancer la tâche sur le 2e cœur
_thread.start_new_thread(ma_tache, ())

# Le programme principal continue sur le cœur 0
while True:
    # ... autre code en parallèle
    pass
```

---

## Règles importantes

1. **La fonction du thread ne doit JAMAIS se terminer** — toujours une boucle `while True`
2. **Pas de `print()` dans le thread** si le programme principal en fait aussi (risque de collision sur le port série) — préférer écrire dans une variable partagée
3. **Variables partagées** : utiliser un dictionnaire simple pour échanger des données entre les deux cœurs
4. **Un seul thread supplémentaire** — MicroPython sur ESP32 ne supporte qu'un thread en plus du principal
5. **`Ctrl+C` n'arrête pas le thread** — il faut faire un reset (Ctrl+D ou bouton RST)

---

## Exemples

| Fichier | Ce qu'il fait |
|---|---|
| `exemple1_deux_leds.py` | LED clignote (cœur 1) + comptage bouton (cœur 0) |
| `exemple2_temperature_et_led.py` | LED respire en PWM (cœur 1) + affichage température (cœur 0) |
| `exemple3_serveur_web_et_capteur.py` | Serveur web (cœur 0) + mesure température en continu (cœur 1) |

---

## Quand utiliser le threading ?

- **Serveur web + capteurs** : le serveur attend les connexions pendant que les capteurs mesurent
- **Animation + interaction** : une LED/écran s'anime pendant qu'on lit des boutons
- **Acquisition + traitement** : un cœur enregistre les données, l'autre les traite

## Quand NE PAS utiliser le threading ?

- Si une seule boucle `while True` suffit (la plupart des cas simples)
- Si les deux tâches ont besoin du même matériel (même bus SPI, même pin)
- Pour des tâches très courtes (utiliser des timers à la place)
