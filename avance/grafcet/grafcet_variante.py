# =============================================================================
# grafcet_variante.py — Moteur GRAFCET pour MicroPython (variante IEC 60848)
# =============================================================================
# VARIANTE — version en cours de validation, voir grafcet.py et
# ascenseur_enim_led.py pour la version stable.
#
# Implémentation du standard IEC 60848 (GRAFCET / Sequential Function Chart)
# Auteur : Vincent — Fablab ESP32 Ardèche
#
# DIFFÉRENCES AVEC grafcet.py :
#
#   1. Validation automatique des transitions (Règle 2 IEC 60848)
#      Le moteur vérifie lui-même que toutes les étapes sources d'une
#      transition sont actives avant de la franchir. L'utilisateur n'écrit
#      que la réceptivité pure (capteurs, timers, etc.) sans répéter
#      g.etapes[i] dans calculer_transitions().
#
#   2. Franchissement simultané en deux passes (Règle 4 IEC 60848)
#      Toutes les transitions simultanément franchissables sont franchies
#      ensemble. Passe 1 : collecte. Passe 2 : application.
#      Règle 5 : si une étape est à la fois désactivée et activée
#      (activation/désactivation simultanées), elle reste active — son
#      tempo et son compteur ne sont PAS remis à 0, aucun front n'est posé.
#
#   3. Documentation des modes de sortie (IEC 60848 §3.2)
#      Voir section MODES DE SORTIE ci-dessous.
#
# PRINCIPE DU GRAFCET :
#   Un GRAFCET est une machine à états séquentielle composée de :
#     - étapes    : états stables du système (actives ou inactives)
#     - actions   : ce que fait le système quand une étape est active
#     - transitions : conditions logiques pour passer d'une étape à une autre
#     - réceptivités : la condition associée à chaque transition
#
# MODES DE SORTIE (IEC 60848 §3.2) :
#
#   Mode CONTINU (assignation) — la sortie suit l'état de l'étape :
#     La sortie est vraie tant que l'étape est active, fausse sinon.
#     C'est le mode par défaut, le plus simple et le plus sûr.
#     Code type :
#       led.value(g.etapes[i])
#       Descendre = g.etapes[1]
#
#   Mode MÉMORISÉ (affectation SET/RESET) — la sortie conserve sa valeur :
#     La sortie prend une valeur à un instant précis et la conserve
#     indépendamment de l'activité de l'étape. Utilise les fronts.
#     4 variantes :
#       - À l'activation (rising) :  if g.rising[i]: sortie = True
#       - À la désactivation (falling) : if g.falling[i]: sortie = False
#       - Sur événement d'entrée (fm) : if g.etapes[i] and g.fm[j]: sortie = True
#       - Au franchissement : action déclenchée dans gerer_actions() sur un front
#     Code type :
#       if g.rising[1]:  alarme = True    # SET à l'entrée de l'étape 1
#       if g.falling[2]: alarme = False   # RESET à la fin de l'étape 2
#
#   QUAND UTILISER QUEL MODE ?
#     - Sortie liée à UNE SEULE étape → CONTINU
#       La sortie suit l'étape : active = ON, inactive = OFF.
#       Plus simple, plus lisible, et sécuritaire : si le programme plante,
#       les sorties passent à 0 (état sûr).
#       Ex: un moteur tourne pendant l'étape 1, s'arrête en sortant.
#
#     - Sortie qui TRAVERSE PLUSIEURS étapes → MÉMORISÉ
#       La sortie est activée dans une étape et désactivée dans une autre.
#       Nécessaire quand le SET et le RESET sont dans des étapes différentes.
#       Attention : si le programme plante entre SET et RESET, la sortie
#       reste dans son dernier état (risque pour un moteur ou un actionneur).
#       Ex: une alarme démarre à l'étape 1 et s'arrête à la fin de l'étape 3.
#
#   RÈGLE : une variable de sortie ne doit être utilisée que dans UN SEUL
#   mode (jamais continu ET mémorisé pour la même variable).
#
#   LIMITATION : les évolutions fugaces ne sont pas gérées — une étape
#   traversée en 1 seul cycle verra ses actions continues appliquées
#   pendant 20 ms (la durée d'un cycle).
#
# DIVERGENCE EN OU (responsabilité du concepteur) :
#   Si deux transitions partent de la même étape, leurs réceptivités
#   DOIVENT être exclusives (jamais vraies en même temps). Le moteur
#   ne gère pas de priorité — si les deux sont vraies, les deux
#   branches seront activées (comportement non déterministe).
#
# RÉINITIALISATION (Règle 6 IEC 60848) :
#   g.reinitialiser() remet le GRAFCET dans sa situation initiale.
#   Utile pour arrêt d'urgence ou condition de forçage externe.
#
# ÉTAPES INITIALES MULTIPLES :
#   etape_initiale peut être un entier ou une liste d'entiers.
#   Ex: Grafcet(nb_etapes=6, etape_initiale=[0, 3])
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
#   7. calculer_transitions()    → évaluation des réceptivités UNIQUEMENT
#                                   (le moteur vérifie la validation des étapes)
#
# NOTE : franchir() est en DÉBUT de cycle (pas en fin) pour que les fronts
# d'étape qu'il pose soient visibles par gerer_actions() du même cycle.
# =============================================================================


class Grafcet:
    """
    Moteur d'exécution GRAFCET générique pour MicroPython.
    Variante conforme IEC 60848 : validation automatique + franchissement simultané.

    Usage sans fronts d'entrée :
        g = Grafcet(nb_etapes=3)

        while True:
            g.franchir(T, transitions)
            g.tick(20)
            gerer_actions()
            affecter_sorties()
            lire_entrees()
            calculer_transitions()       # réceptivités pures, sans g.etapes[i]
            synchro_ms(20)

    Usage avec fronts d'entrée (nb_fronts = nombre de boutons/capteurs à surveiller) :
        g = Grafcet(nb_etapes=3, nb_fronts=2)

        while True:
            g.franchir(T, transitions)
            g.tick(20)
            gerer_actions()
            affecter_sorties()
            lire_entrees()               # → remplir g.entrees[i]
            g.detecter_fronts_entrees()  # → calcule g.fm[i] / g.fd[i]
            calculer_transitions()       # → utiliser g.fm[i] pour les fronts
            synchro_ms(20)

    Différence clé avec grafcet.py :
        calculer_transitions() ne contient QUE les réceptivités (conditions
        logiques). La validation des étapes sources est faite automatiquement
        par franchir(). Exemple :
            transitions[0] = Start and (g.tempo[0] > 200)   # réceptivité pure
            # PAS BESOIN de : g.etapes[0] and Start and ...

    Modes de sortie dans gerer_actions() :
        Continu (1 sortie = 1 étape) :
            Descendre = g.etapes[1]              # ON tant que étape 1 active
        Mémorisé (1 sortie traverse plusieurs étapes) :
            if g.rising[1]:   alarme = True      # SET à l'entrée étape 1
            if g.falling[2]:  alarme = False     # RESET à la fin étape 2
    """

    def __init__(self, nb_etapes, etape_initiale=0, nb_fronts=0):
        """
        Initialise le GRAFCET.

        :param nb_etapes:      nombre total d'étapes (taille des tableaux internes)
        :param etape_initiale: étape(s) active(s) au démarrage — un entier (défaut : 0)
                               ou une liste d'entiers pour plusieurs étapes initiales
                               ex: etape_initiale=[0, 3] pour activer étapes 0 et 3
        :param nb_fronts:      nombre d'entrées à surveiller pour les fronts (défaut : 0)
        """

        self.nb_etapes = nb_etapes

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

        # --- Fronts montants d'étape (rising edge) ---
        # rising[i] = True pendant UN SEUL cycle, au moment où l'étape i s'active
        # Utilisation : actions mémorisées (SET) à l'entrée d'une étape
        self.rising = [False] * nb_etapes

        # --- Fronts descendants d'étape (falling edge) ---
        # falling[i] = True pendant UN SEUL cycle, au moment où l'étape i se désactive
        # Utilisation : actions mémorisées (RESET) à la sortie d'une étape
        self.falling = [False] * nb_etapes

        # Activation de l'étape initiale (Règle 1 IEC 60848)
        # Mémorise la situation initiale pour reinitialiser()
        if isinstance(etape_initiale, int):
            self._init = [etape_initiale]
        else:
            self._init = list(etape_initiale)

        for s in self._init:
            self.etapes[s] = True
            self.rising[s] = True   # front montant au démarrage (actions mémorisées)

        # --- Fronts d'entrée ---
        # Détection des changements d'état des capteurs/boutons
        # fm[i] = front montant d'entrée i (True pendant 1 cycle quand entrée passe False→True)
        # fd[i] = front descendant d'entrée i (True pendant 1 cycle quand entrée passe True→False)
        self.nb_fronts    = nb_fronts
        self.entrees      = [False] * nb_fronts  # état actuel (à remplir dans lire_entrees())
        self.entrees_prec = [False] * nb_fronts  # état du cycle précédent
        self.fm           = [False] * nb_fronts  # fronts montants d'entrée
        self.fd           = [False] * nb_fronts  # fronts descendants d'entrée

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
        Conforme aux règles IEC 60848 :
          - Règle 2 : vérifie automatiquement que TOUTES les étapes sources
            sont actives (validation). L'utilisateur ne fournit que la réceptivité.
          - Règle 4 : toutes les transitions simultanément franchissables sont
            franchies ensemble (deux passes : collecte puis application).
          - Règle 5 : si une étape est simultanément désactivée et activée,
            elle reste active (tempo et compt conservés, pas de front).

        :param T: table de transitions — liste de tuples de la forme :
                      (indice_transition, (étapes_sources,), (étapes_cibles,))

                  Les étapes_sources servent à la fois pour :
                    - la validation (le moteur vérifie qu'elles sont actives)
                    - la désactivation (elles sont désactivées au franchissement)

                  Exemple pour un GRAFCET à 3 étapes en boucle :
                      T = [
                          (0, (0,), (1,)),   # transition 0 : étape 0 → étape 1
                          (1, (1,), (2,)),   # transition 1 : étape 1 → étape 2
                          (2, (2,), (0,)),   # transition 2 : étape 2 → étape 0
                      ]

                  Pour une convergence ET :
                      (4, (3, 5), (0,)),   # transition 4 : étapes 3 ET 5 → étape 0
                      → franchie seulement si étapes 3 ET 5 sont TOUTES actives

        :param transitions: liste de booléens — transitions[i] = True si la
                            RÉCEPTIVITÉ de la transition i est satisfaite.
                            Ne PAS inclure g.etapes[i] — le moteur le vérifie.
        """

        # Reset des fronts d'étape AVANT de poser les nouveaux
        self.rising  = [False] * len(self.etapes)
        self.falling = [False] * len(self.etapes)

        # --- PASSE 1 : collecte des étapes à désactiver et à activer ---
        a_desactiver = set()
        a_activer    = set()

        for t_id, sources, cibles in T:

            # Règle 2 : la transition n'est franchissable que si
            # TOUTES les étapes sources sont actives ET la réceptivité est vraie
            toutes_actives = True
            for s in sources:
                if not self.etapes[s]:
                    toutes_actives = False
                    break

            if toutes_actives and transitions[t_id]:
                for s in sources:
                    a_desactiver.add(s)
                for s in cibles:
                    a_activer.add(s)

        # --- Règle 5 : activation/désactivation simultanées ---
        # Si une étape apparaît dans les deux ensembles, elle reste active
        # sans reset de tempo/compt et sans front
        conflit = a_desactiver & a_activer
        a_desactiver -= conflit
        a_activer    -= conflit

        # --- PASSE 2 : application ---

        # Désactivation des étapes sources
        for s in a_desactiver:
            self.falling[s] = True   # front descendant pour ce cycle
            self.etapes[s]  = False
            self.tempo[s]   = 0
            self.compt[s]   = 0

        # Activation des étapes cibles
        for s in a_activer:
            self.rising[s]  = True   # front montant pour ce cycle
            self.etapes[s]  = True

    # -------------------------------------------------------------------------

    def reinitialiser(self):
        """
        Remet le GRAFCET dans sa situation initiale (Règle 6 IEC 60848).

        - Désactive toutes les étapes (falling pour celles qui étaient actives)
        - Réactive uniquement les étapes initiales (rising)
        - Remet tous les timers et compteurs à 0

        Usage : appeler quand un arrêt d'urgence ou une condition externe
        impose de revenir à l'état de départ.
            if arret_urgence:
                g.reinitialiser()
        """
        for i in range(self.nb_etapes):
            if self.etapes[i] and i not in self._init:
                self.falling[i] = True
            self.etapes[i] = False
            self.tempo[i]  = 0
            self.compt[i]  = 0

        for s in self._init:
            self.etapes[s] = True
            self.rising[s] = True

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
        """
        for i in range(self.nb_fronts):
            self.fm[i] = self.entrees[i] and not self.entrees_prec[i]
            self.fd[i] = not self.entrees[i] and self.entrees_prec[i]
            self.entrees_prec[i] = self.entrees[i]
