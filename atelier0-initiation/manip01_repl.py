# Manipulation 01 — Le REPL : dialogue avec l'ESP32
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# Le REPL (Read-Eval-Print Loop) est la console interactive de MicroPython.
# On tape une instruction, l'ESP32 l'exécute immédiatement et affiche le résultat.
# C'est comme une calculatrice programmable branchée sur un microcontrôleur.
#
# COMMENT FAIRE :
#   1. Brancher l'ESP32 sur l'ordinateur avec le câble USB
#   2. Ouvrir Thonny → connecter l'ESP32 (menu bas à droite)
#   3. Cliquer dans la zone "Shell" en bas
#   4. Taper les commandes ci-dessous une par une, appuyer sur Entrée
#
# Rien à brancher — tout se passe dans la console.
# -----------------------------------------------------------------------

# === COMMANDES À TAPER DANS LE SHELL DE THONNY ===

# --- Calculs simples ---
# >>> 1 + 1
# >>> 10 * 3
# >>> 2 ** 8          # 2 puissance 8 = 256

# --- Texte ---
# >>> print("Bonjour Polinno !")
# >>> nom = "Fablab"
# >>> print("Bienvenue au", nom)

# --- Variables ---
# >>> temperature = 22.5
# >>> print("Il fait", temperature, "degrés")

# --- Listes ---
# >>> couleurs = ["rouge", "vert", "bleu"]
# >>> print(couleurs[0])     # premier élément : "rouge"
# >>> len(couleurs)          # nombre d'éléments : 3

# --- Boucle rapide ---
# >>> for i in range(5):
# ...     print("Compte :", i)
# ...                        # appuyer Entrée sur une ligne vide pour exécuter

# --- Voir ce qui est disponible sur l'ESP32 ---
# >>> import machine
# >>> help(machine)          # liste tous les modules disponibles

# -----------------------------------------------------------------------
# À RETENIR :
#   - Ctrl+C  : arrête le programme en cours
#   - Ctrl+D  : redémarre l'ESP32 (soft reset)
#   - Flèche Haut : rappelle la dernière commande
# -----------------------------------------------------------------------
