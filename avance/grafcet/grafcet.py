# =============================================================================
# grafcet.py — Moteur GRAFCET pour MicroPython
# =============================================================================
# Implémentation du standard IEC 60848 (GRAFCET / Sequential Function Chart)
# Auteur : Vincent — Fablab ESP32 Ardèche
#
# PRINCIPE DU GRAFCET :
#   Un GRAFCET est une machine à états séquentielle composée de :
#     - étapes    : états stables du système (actives ou inactives)
#     - actions   : ce que fait le système quand une étape est active
#     - transitions : conditions logiques pour passer d'une étape à une autre
#     - réceptivités : la condition associée à chaque transition
#
# CYCLE D'EXÉCUTION NORMALISÉ (à respecter dans la boucle principale) :
#   1. tick()               → mise à jour des timers
#   2. gerer_actions()      → calcul des actions selon étapes actives
#   3. affecter_sorties()   → application des actions sur les sorties physiques
#   4. lire_entrees()       → lecture des capteurs et boutons
#   5. calculer_transitions() → évaluation des conditions de transition
#   6. franchir(T, trans)   → franchissement des transitions validées
# =============================================================================


class Grafcet:
    """
    Moteur d'exécution GRAFCET générique pour MicroPython.

    Usage minimal :
        g = Grafcet(nb_etapes=3, etape_initiale=0)

        while True:
            g.tick(20)
            # ... vos fonctions gerer_actions, affecter_sorties, etc.
            g.franchir(T, transitions)
            synchro_ms(20)
    """

    def __init__(self, nb_etapes, etape_initiale=0):
        """
        Initialise le GRAFCET.

        :param nb_etapes:      nombre total d'étapes (taille des tableaux internes)
        :param etape_initiale: indice de l'étape active au démarrage (défaut : 0)
        """

        # --- Tableau d'activation des étapes ---
        # etapes[i] = True  → l'étape i est active
        # etapes[i] = False → l'étape i est inactive
        # Plusieurs étapes peuvent être simultanément actives (divergence ET)
        self.etapes = [False] * nb_etapes

        # --- Timers par étape (en millisecondes) ---
        # tempo[i] s'incrémente automatiquement tant que l'étape i est active
        # tempo[i] est remis à 0 lors de la désactivation de l'étape
        # Utilisation : transitions temporisées  ex: tempo[0] > 500  (500 ms)
        self.tempo = [0] * nb_etapes

        # --- Compteurs par étape ---
        # compt[i] peut être incrémenté manuellement dans gerer_actions()
        # compt[i] est remis à 0 lors de la désactivation de l'étape
        # Utilisation : compter des événements pendant qu'une étape est active
        self.compt = [0] * nb_etapes

        # --- Fronts montants (rising edge) ---
        # rising[i] = True pendant UN SEUL cycle, au moment où l'étape i s'active
        # Équivalent du StepRising dans les PLCs industriels
        # Utilisation : déclencher une action UNE SEULE FOIS à l'entrée d'une étape
        self.rising = [False] * nb_etapes

        # --- Fronts descendants (falling edge) ---
        # falling[i] = True pendant UN SEUL cycle, au moment où l'étape i se désactive
        # Équivalent du StepFalling dans les PLCs industriels
        # Utilisation : déclencher une action UNE SEULE FOIS à la sortie d'une étape
        self.falling = [False] * nb_etapes

        # Activation de l'étape initiale : seule étape active au démarrage
        self.etapes[etape_initiale] = True

    # -------------------------------------------------------------------------

    def tick(self, dt_ms=20):
        """
        Met à jour les timers internes. À appeler UNE FOIS par cycle de boucle,
        AVANT gerer_actions().

        - Incrémente tempo[i] pour chaque étape active
        - Remet à zéro les fronts montants et descendants (ils ne durent qu'un cycle)

        :param dt_ms: durée du cycle en millisecondes — doit correspondre
                      à la valeur passée à synchro_ms() dans la boucle principale
        """

        # Incrémente le timer de chaque étape actuellement active
        for i in range(len(self.etapes)):
            if self.etapes[i]:
                self.tempo[i] += dt_ms  # ex: après 10 cycles à 20ms → tempo[i] = 200

        # Efface les fronts : ils ne sont visibles QUE pendant le cycle
        # où l'étape vient de changer d'état
        self.rising  = [False] * len(self.etapes)   # remet tous les fronts montants à False
        self.falling = [False] * len(self.etapes)   # remet tous les fronts descendants à False

    # -------------------------------------------------------------------------

    def franchir(self, T, transitions):
        """
        Franchit les transitions validées et met à jour le tableau des étapes.

        Parcourt la table de transitions T. Pour chaque transition dont la
        réceptivité est True, désactive les étapes sources et active les étapes cibles.

        :param T: table de transitions — liste de tuples de la forme :
                      (indice_transition, (étapes_à_désactiver,), (étapes_à_activer,))

                  Exemple pour un GRAFCET à 3 étapes en boucle :
                      T = [
                          (0, (0,), (1,)),   # transition 0 : étape 0 → étape 1
                          (1, (1,), (2,)),   # transition 1 : étape 1 → étape 2
                          (2, (2,), (0,)),   # transition 2 : étape 2 → étape 0
                      ]

                  Pour une divergence ET (parallélisme) :
                      (0, (0,), (1, 2)),    # transition 0 active étapes 1 ET 2 simultanément

        :param transitions: liste de booléens — transitions[i] = True si la
                            réceptivité de la transition i est satisfaite
        """

        # Parcourt chaque règle de la table de transitions
        for t_id, desactiver, activer in T:

            # Ne franchit que si la condition de cette transition est vraie
            if transitions[t_id]:

                # Désactivation des étapes sources
                for s in desactiver:
                    self.falling[s] = True   # signale le front descendant pour ce cycle
                    self.etapes[s]  = False  # désactive l'étape
                    self.tempo[s]   = 0      # remet le timer à zéro (prêt pour la prochaine activation)
                    self.compt[s]   = 0      # remet le compteur à zéro

                # Activation des étapes cibles
                for s in activer:
                    self.rising[s]  = True   # signale le front montant pour ce cycle
                    self.etapes[s]  = True   # active l'étape
