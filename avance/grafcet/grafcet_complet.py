# =============================================================================
# grafcet_complet.py — Moteur GRAFCET complet pour MicroPython
# =============================================================================
# Implémentation conforme au standard IEC 60848 (GRAFCET / SFC)
# Auteur : Vincent — Fablab ESP32 Ardèche
#
# Ce fichier est la VERSION DE RÉFÉRENCE du moteur GRAFCET.
# Il intègre toutes les fonctionnalités dans un seul fichier :
#
# FONCTIONNALITÉS :
#   - Étapes, timers (tempo), compteurs (compt)
#   - Fronts d'étape : rising (activation) et falling (désactivation)
#   - Fronts d'entrée : fm (front montant) et fd (front descendant)
#   - Validation automatique des transitions (Règle 2 IEC 60848)
#   - Franchissement simultané en deux passes (Règle 4)
#   - Gestion des conflits activation/désactivation (Règle 5)
#   - Étapes initiales multiples (Règle 1)
#   - Réinitialisation (Règle 6) — arrêt d'urgence
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
#   Mode CONTINU (assignation) — sortie liée à UNE SEULE étape :
#     La sortie suit l'étape : active = ON, inactive = OFF.
#     Plus simple et sécuritaire (si le programme plante, tout s'éteint).
#     Code type :
#       led.value(g.etapes[i])
#       Descendre = g.etapes[1]
#
#   Mode MÉMORISÉ (affectation SET/RESET) — sortie qui TRAVERSE PLUSIEURS étapes :
#     La sortie prend une valeur à un instant précis et la conserve.
#     Nécessaire quand le SET et le RESET sont dans des étapes différentes.
#     Attention : si le programme plante entre SET et RESET, la sortie
#     reste dans son dernier état.
#     4 variantes :
#       - À l'activation :      if g.rising[i]: sortie = True
#       - À la désactivation :  if g.falling[i]: sortie = False
#       - Sur front d'entrée :  if g.etapes[i] and g.fm[j]: sortie = True
#       - Au franchissement :   action déclenchée sur un front
#     Code type :
#       if g.rising[1]:   alarme = True    # SET à l'entrée de l'étape 1
#       if g.falling[2]:  alarme = False   # RESET à la fin de l'étape 2
#
#   RÈGLE : une variable de sortie ne doit être utilisée que dans UN SEUL
#   mode (jamais continu ET mémorisé pour la même variable).
#
# DIVERGENCE EN OU (responsabilité du concepteur) :
#   Si deux transitions partent de la même étape, leurs réceptivités
#   DOIVENT être exclusives (jamais vraies en même temps). Le moteur
#   ne gère pas de priorité — si les deux sont vraies, les deux
#   branches seront activées (comportement non déterministe).
#
# CYCLE D'EXÉCUTION NORMALISÉ (à respecter dans la boucle principale) :
#   1. franchir(T, trans)        → franchissement des transitions validées
#   2. tick()                    → mise à jour des timers
#   3. gerer_actions()           → calcul des actions (fronts lisibles ici)
#   4. affecter_sorties()        → application sur les sorties physiques
#   5. lire_entrees()            → lecture des capteurs et boutons
#   6. detecter_fronts_entrees() → détection des fronts d'entrée (fm/fd)
#   7. calculer_transitions()    → réceptivités UNIQUEMENT
#
# NOTE : franchir() est en DÉBUT de cycle pour que les fronts d'étape
# soient visibles par gerer_actions() du même cycle.
# =============================================================================


class Grafcet:
    """
    Moteur d'exécution GRAFCET complet pour MicroPython.
    Conforme IEC 60848 : validation automatique, franchissement simultané,
    fronts d'étape et d'entrée, compteurs, réinitialisation.

    Usage :
        g = Grafcet(nb_etapes=3, nb_fronts=1)

        while True:
            g.franchir(T, transitions)
            g.tick(20)
            gerer_actions()
            affecter_sorties()
            lire_entrees()               # → remplir g.entrees[i]
            g.detecter_fronts_entrees()  # → calcule g.fm[i] / g.fd[i]
            calculer_transitions()       # → réceptivités pures
            synchro_ms(20)

    Attributs principaux :
        g.etapes[i]  — True si l'étape i est active
        g.tempo[i]   — durée en ms depuis l'activation de l'étape i
        g.compt[i]   — compteur libre, incrémentable dans gerer_actions()
        g.rising[i]  — True pendant 1 cycle à l'activation de l'étape i
        g.falling[i] — True pendant 1 cycle à la désactivation de l'étape i
        g.entrees[i] — état brut de l'entrée i (à remplir dans lire_entrees)
        g.fm[i]      — front montant de l'entrée i (1 cycle)
        g.fd[i]      — front descendant de l'entrée i (1 cycle)

    Modes de sortie dans gerer_actions() :
        Continu (1 sortie = 1 étape) :
            Descendre = g.etapes[1]
        Mémorisé (1 sortie traverse plusieurs étapes) :
            if g.rising[1]:   alarme = True      # SET
            if g.falling[2]:  alarme = False     # RESET
    """

    def __init__(self, nb_etapes, etape_initiale=0, nb_fronts=0):
        """
        Initialise le GRAFCET.

        :param nb_etapes:      nombre total d'étapes
        :param etape_initiale: étape(s) active(s) au démarrage — int ou liste
        :param nb_fronts:      nombre d'entrées à surveiller pour les fronts (défaut : 0)
        """

        self.nb_etapes = nb_etapes

        self.etapes  = [False] * nb_etapes    # activation des étapes
        self.tempo   = [0]     * nb_etapes    # timers (ms)
        self.compt   = [0]     * nb_etapes    # compteurs libres
        self.rising  = [False] * nb_etapes    # fronts montants d'étape
        self.falling = [False] * nb_etapes    # fronts descendants d'étape

        # Étapes initiales (Règle 1) — mémorisées pour reinitialiser()
        if isinstance(etape_initiale, int):
            self._init = [etape_initiale]
        else:
            self._init = list(etape_initiale)

        for s in self._init:
            self.etapes[s] = True
            self.rising[s] = True

        # Flag pour préserver les fronts posés par __init__ ou reinitialiser()
        # franchir() ne remet pas rising/falling à zéro au prochain appel
        self._skip_reset = True

        # Fronts d'entrée (optionnel)
        self.nb_fronts    = nb_fronts
        self.entrees      = [False] * nb_fronts
        self.entrees_prec = [False] * nb_fronts
        self.fm           = [False] * nb_fronts
        self.fd           = [False] * nb_fronts

    # -------------------------------------------------------------------------

    def tick(self, dt_ms=20):
        """Incrémente les timers des étapes actives."""
        for i in range(self.nb_etapes):
            if self.etapes[i]:
                self.tempo[i] += dt_ms

    # -------------------------------------------------------------------------

    def franchir(self, T, transitions):
        """
        Franchit les transitions validées (Règles 2, 4, 5 IEC 60848).

        Le moteur vérifie automatiquement que toutes les étapes sources sont
        actives. L'utilisateur ne fournit que les réceptivités.

        Deux passes : collecte puis application. Si une étape est à la fois
        désactivée et activée (Règle 5), elle reste active sans reset.

        :param T:           table de transitions (indice, sources, cibles)
        :param transitions: liste de booléens (réceptivités pures)
        """

        if self._skip_reset:
            self._skip_reset = False
        else:
            self.rising  = [False] * self.nb_etapes
            self.falling = [False] * self.nb_etapes

        # Passe 1 : collecte
        a_desactiver = set()
        a_activer    = set()

        for t_id, sources, cibles in T:
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

        # Règle 5 : conflits
        conflit = a_desactiver & a_activer
        a_desactiver -= conflit
        a_activer    -= conflit

        # Passe 2 : application
        for s in a_desactiver:
            self.falling[s] = True
            self.etapes[s]  = False
            self.tempo[s]   = 0
            self.compt[s]   = 0

        for s in a_activer:
            self.rising[s] = True
            self.etapes[s] = True

    # -------------------------------------------------------------------------

    def reinitialiser(self):
        """
        Remet le GRAFCET dans sa situation initiale (Règle 6 IEC 60848).
        Désactive toutes les étapes, réactive les étapes initiales,
        remet tous les timers et compteurs à 0.
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

        self._skip_reset = True  # préserver les fronts pour gerer_actions()

    # -------------------------------------------------------------------------

    def detecter_fronts_entrees(self):
        """
        Détecte les fronts montants (fm) et descendants (fd) des entrées.
        Compare entrees (état actuel) avec entrees_prec (cycle précédent).
        """
        for i in range(self.nb_fronts):
            self.fm[i] = self.entrees[i] and not self.entrees_prec[i]
            self.fd[i] = not self.entrees[i] and self.entrees_prec[i]
            self.entrees_prec[i] = self.entrees[i]
