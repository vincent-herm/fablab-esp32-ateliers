# Manipulation 01 — Le REPL et la LED intégrée
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# Tout se fait dans le SHELL de Thonny (la console en bas de la fenêtre).
# On tape les commandes une par une, l'ESP32 répond immédiatement.
#
# Cette fiche sert de référence — ne pas l'exécuter comme un programme.
# -----------------------------------------------------------------------

# === PARTIE 1 : Découverte du REPL ===

# Le REPL (Read-Eval-Print Loop) est la console interactive de MicroPython.
# Chaque instruction tapée est envoyée à l'ESP32 qui l'exécute instantanément.

# --- Opérations mathématiques ---
# >>> 1 + 1
# 2
# >>> 10 * 3
# 30
# >>> 2 ** 8                      # puissance : 2 exposant 8
# 256
# >>> 15 / 3 - 1                  # la division retourne un float
# 4.0
# >>> 13 // 4                     # division entière
# 3
# >>> 13 % 4                      # modulo : le reste de la division
# 1

# --- Variables (labels) ---
# >>> a = 4                       # on affecte le nombre 4 au label "a"
# >>> a + 1
# 5
# >>> vitesse1 = 36
# >>> vitesse2 = 42
# >>> print("Moyenne :", (vitesse1 + vitesse2) / 2)
# Moyenne : 39.0

# --- Types de données ---
# >>> type(42)                    # int : nombre entier
# >>> type(3.14)                  # float : nombre à virgule
# >>> type("Bonjour")            # str : chaîne de caractères
# >>> type(True)                  # bool : vrai ou faux

# --- Texte ---
# >>> print("Bonjour Polinno !")
# >>> nom = "Fablab"
# >>> print("Bienvenue au", nom)

# --- Boucle rapide ---
# >>> for i in range(5):
# ...     print("Compte :", i)
# ...                             # appuyer Entrée sur une ligne vide

# === PARTIE 2 : Contrôler la LED intégrée ===

# La LED bleue sur la carte est connectée au GPIO 2.
# On va la contrôler directement depuis le Shell.

# >>> from machine import Pin     # importer la classe Pin
# >>> led = Pin(2, Pin.OUT)       # GPIO 2 en sortie
# >>> led.value(1)                # allumer (3,3V sur la broche)
# >>> led.value(0)                # éteindre (0V)
# >>> led.on()                    # raccourci pour allumer
# >>> led.off()                   # raccourci pour éteindre

# On peut aussi créer et commander en une seule ligne :
# >>> Pin(2, Pin.OUT).value(1)    # allume la LED en une instruction

# -----------------------------------------------------------------------
# À RETENIR :
#   - Le Shell exécute chaque ligne immédiatement sur l'ESP32
#   - Ctrl+C  : arrête le programme en cours
#   - Ctrl+D  : redémarre l'ESP32 (soft reset)
#   - Flèche Haut : rappelle la dernière commande
#   - Pin(n, Pin.OUT) : broche n en sortie (on envoie du courant)
#   - value(1) = allumé (3,3V) / value(0) = éteint (0V)
# -----------------------------------------------------------------------
