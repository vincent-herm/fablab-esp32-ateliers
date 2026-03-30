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
#   1. franchir(T, trans)        → franchissement des transitions validées
#                                   (reset des fronts d'étape, puis pose des nouveaux)
#   2. tick()                    → mise à jour des timers
#   3. gerer_actions()           → calcul des actions selon étapes actives
#                                   (les fronts d'étape rising/falling sont lisibles ici)
#   4. affecter_sorties()        → application des actions sur les sorties physiques
#   5. lire_entrees()            → lecture des capteurs et boutons
#   6. detecter_fronts_entrees() → détection des fronts montants/descendants d'entrée
#                                   (optionnel, seulement si nb_entrees > 0)
#   7. calculer_transitions()    → évaluation des conditions de transition
#
# NOTE : franchir() est en DÉBUT de cycle (pas en fin) pour que les fronts
# d'étape qu'il pose soient visibles par gerer_actions() du même cycle.
# =============================================================================


class Grafcet:
    """
    Moteur d'exécution GRAFCET générique pour MicroPython.

    Usage minimal :
        g = Grafcet(nb_etapes=3, etape_initiale=0)

        while True:
            g.franchir(T, transitions)   # 1. évolution + fronts d'étape
            g.tick(20)                   # 2. timers
            # gerer_actions()            # 3. actions (fronts lisibles ici !)
            # affecter_sorties()         # 4. sorties physiques
            # lire_entrees()             # 5. capteurs/boutons
            # g.detecter_fronts_entrees()# 6. fronts d'entrée (optionnel)
            # calculer_transitions()     # 7. conditions
            synchro_ms(20)

    Avec fronts d'entrée (optionnel) :
        g = Grafcet(nb_etapes=3, etape_initiale=0, nb_entrees=4)

        # Dans lire_entrees(), remplir g.entrees[i] avec l'état des capteurs
        # Puis g.detecter_fronts_entrees() calcule g.fm[i] et g.fd[i]
        # Dans calculer_transitions(), utiliser g.fm[i] pour les fronts montants
    """

    def __init__(self, nb_etapes, etape_initiale=0, nb_entrees=0):
        """
        Initialise le GRAFCET.

        :param nb_etapes:      nombre total d'étapes (taille des tableaux internes)
        :param etape_initiale: indice de l'étape active au démarrage (défaut : 0)
        :param nb_entrees:     nombre d'entrées à surveiller pour les fronts (défaut : 0 = désactivé)
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

        # --- Fronts d'entrée (optionnel) ---
        # Si nb_entrees > 0, détection des changements d'état des capteurs/boutons
        # fm[i] = front montant d'entrée i (True pendant 1 cycle quand entrée passe False→True)
        # fd[i] = front descendant d'entrée i (True pendant 1 cycle quand entrée passe True→False)
        self.nb_entrees = nb_entrees
        if nb_entrees > 0:
            self.entrees      = [False] * nb_entrees  # état actuel (à remplir dans lire_entrees())
            self.entrees_prec = [False] * nb_entrees  # état du cycle précédent
            self.fm           = [False] * nb_entrees  # fronts montants d'entrée
            self.fd           = [False] * nb_entrees  # fronts descendants d'entrée

    # -------------------------------------------------------------------------

    def tick(self, dt_ms=20):
        """
        Met à jour les timers internes. À appeler UNE FOIS par cycle de boucle,
        APRÈS franchir() et AVANT gerer_actions().

        - Incrémente tempo[i] pour chaque étape active
        - Ne touche PAS aux fronts (rising/falling) — ceux-ci sont gérés par franchir()

        :param dt_ms: durée du cycle en millisecondes — doit correspondre
                      à la valeur passée à synchro_ms() dans la boucle principale
        """

        # Incrémente le timer de chaque étape actuellement active
        for i in range(len(self.etapes)):
            if self.etapes[i]:
                self.tempo[i] += dt_ms  # ex: après 10 cycles à 20ms → tempo[i] = 200

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

        # Reset des fronts d'étape AVANT de poser les nouveaux
        # Les fronts posés par le cycle précédent ont été lus par gerer_actions()
        self.rising  = [False] * len(self.etapes)
        self.falling = [False] * len(self.etapes)

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

    # -------------------------------------------------------------------------

    def detecter_fronts_entrees(self):
        """
        Détecte les fronts montants et descendants des entrées.
        À appeler APRÈS lire_entrees() et AVANT calculer_transitions().

        Compare self.entrees (état actuel, rempli par l'utilisateur dans
        lire_entrees()) avec self.entrees_prec (état du cycle précédent).

        Résultat :
          - self.fm[i] = True si l'entrée i vient de passer de False à True
          - self.fd[i] = True si l'entrée i vient de passer de True à False

        Ne fait rien si nb_entrees == 0 (rétrocompatibilité).
        """
        if self.nb_entrees == 0:
            return

        for i in range(self.nb_entrees):
            self.fm[i] = self.entrees[i] and not self.entrees_prec[i]
            self.fd[i] = not self.entrees[i] and self.entrees_prec[i]
            self.entrees_prec[i] = self.entrees[i]
