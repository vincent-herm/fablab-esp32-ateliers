# =============================================================================
# neoprog.py — Affichage progressif sur bandeau NeoPixel
# =============================================================================
# Classe NeoProgressif : affiche une valeur numérique sur un bandeau WS2812
# avec interpolation douce entre les LEDs (pas de saut visible).
#
# PRINCIPE :
#   Une valeur x dans [0, max] est mappée sur n LEDs.
#   La position tombe en général ENTRE deux LEDs.
#   → les deux LEDs adjacentes sont allumées proportionnellement,
#     avec correction gamma pour que l'œil perçoive une transition régulière.
#
# USAGE :
#   from neoprog import NeoProgressif
#
#   neo = NeoProgressif(pin=26, n=8)   # bandeau sur Pin 26, 8 LEDs
#   neo.afficher(500)                  # position milieu
#   neo.eteindre()                     # tout éteindre
# =============================================================================

from neopixel import NeoPixel    # pilotage des LEDs WS2812
from machine  import Pin         # accès aux broches ESP32


class NeoProgressif:
    """
    Affichage progressif d'une valeur sur un bandeau NeoPixel.
    Interpole la luminosité entre deux LEDs adjacentes pour un rendu fluide.
    """

    def __init__(self, pin, n=8, coef=1.8, couleur=(0, 0, 255)):
        """
        Initialise le bandeau NeoPixel.

        :param pin:     numéro de broche GPIO (ex: 26 sur la carte ENIM)
        :param n:       nombre de LEDs du bandeau (défaut : 8)
        :param coef:    exposant de correction gamma (défaut : 1.8)
                        — compense la perception non-linéaire de l'œil
                        — augmenter pour une transition plus "en douceur"
        :param couleur: tuple RGB de la couleur d'affichage (défaut : bleu)
        """
        self.np     = NeoPixel(Pin(pin), n)   # objet NeoPixel sur la broche
        self.n      = n                        # nombre de LEDs
        self.coef   = coef                     # coefficient gamma
        self.couleur = couleur                 # couleur RGB (0-255 par canal)
        self.eteindre()                        # éteindre toutes les LEDs au démarrage


    def afficher(self, x, max=1000):
        """
        Affiche la valeur x sur le bandeau avec interpolation douce.

        :param x:   valeur à afficher, dans [0, max]
        :param max: valeur maximale de l'échelle (défaut : 1000)

        Exemple :
            neo.afficher(0)     → bandeau éteint (position 0)
            neo.afficher(500)   → position centrale, 2 LEDs à 50%
            neo.afficher(1000)  → bandeau plein
        """

        # --- Calcul de la position ---
        # entier : index de la LED "juste avant" la position (0 à n-1)
        entier = x * self.n // max

        # frac2 : fraction de la LED suivante (0 = pas allumée, 255 = pleine)
        # représente à quel % on est entre entier et entier+1
        frac2 = int((x * self.n / max - entier) * 255)

        # frac1 : complément — luminosité de la LED courante
        frac1 = 255 - frac2

        # --- Correction gamma ---
        # Sans correction, l'œil perçoit les transitions de façon non-linéaire.
        # La courbe en puissance (** coef) rend la progression perçue régulière.
        c2 = int((frac2 / 255) ** self.coef * 255)   # luminosité LED suivante
        c1 = int((frac1 / 255) ** self.coef * 255)   # luminosité LED courante

        # --- Calcul des couleurs avec luminosité appliquée ---
        r, g, b = self.couleur
        couleur2 = (r * c2 // 255, g * c2 // 255, b * c2 // 255)   # LED suivante
        couleur1 = (r * c1 // 255, g * c1 // 255, b * c1 // 255)   # LED courante

        # --- Éteindre tout le bandeau ---
        for i in range(self.n):
            self.np[i] = (0, 0, 0)

        # --- Allumer les deux LEDs de la transition ---
        if entier != self.n:             # évite le débordement en fin de bandeau
            self.np[entier] = couleur2
        if entier > 0:                   # évite l'index -1 en début de bandeau
            self.np[entier - 1] = couleur1

        self.np.write()                  # envoyer les données au bandeau


    def eteindre(self):
        """Éteint toutes les LEDs du bandeau."""
        for i in range(self.n):
            self.np[i] = (0, 0, 0)
        self.np.write()
