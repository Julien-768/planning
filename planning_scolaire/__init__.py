"""
planning_scolaire
==================

Génère des agendas .ics pour des activités extrascolaires hebdomadaires,
en excluant automatiquement les vacances scolaires (zones A, B, C) et,
au choix, les jours fériés.

Les dates de calendrier scolaire vivent dans data/calendars/<annee>.json
et ne dépendent pas du code : ajouter une nouvelle année scolaire ne
demande jamais de toucher à ce package.
"""

from .calendrier import CalendrierScolaire
from .activites import Activite
from .ics import generer_ics, generer_zip

__all__ = ["CalendrierScolaire", "Activite", "generer_ics", "generer_zip"]
__version__ = "1.0.0"
