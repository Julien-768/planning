"""Représentation d'une activité hebdomadaire et calcul de ses séances."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

JOURS_ISO = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def _lire_jour(valeur) -> int:
    """Accepte un nom de jour ('mercredi'), un entier, ou une chaîne numérique ('2')."""
    if isinstance(valeur, int):
        return valeur
    if isinstance(valeur, str) and valeur.strip().isdigit():
        return int(valeur)
    return JOURS_ISO.index(str(valeur).lower())


@dataclass
class Activite:
    nom: str
    jour: int  # 0 = lundi ... 6 = dimanche (convention date.weekday())
    heure_debut: time
    heure_fin: time
    lieu: str = ""
    premiere_seance: date | None = None  # None = début de l'année scolaire
    derniere_seance: date | None = None  # None = fin de l'année scolaire

    @classmethod
    def depuis_dict(cls, d: dict) -> "Activite":
        return cls(
            nom=d["nom"],
            jour=_lire_jour(d["jour"]),
            heure_debut=time.fromisoformat(d["heure_debut"]),
            heure_fin=time.fromisoformat(d["heure_fin"]),
            lieu=d.get("lieu", ""),
            premiere_seance=date.fromisoformat(d["premiere_seance"]) if d.get("premiere_seance") else None,
            derniere_seance=date.fromisoformat(d["derniere_seance"]) if d.get("derniere_seance") else None,
        )


@dataclass
class Seances:
    toutes: list[date] = field(default_factory=list)
    conservees: list[date] = field(default_factory=list)
    retirees: list[date] = field(default_factory=list)


def calculer_seances(
    activite: Activite,
    debut_annee: date,
    fin_annee: date,
    jours_exclus: set[date],
) -> Seances:
    """Liste toutes les occurrences du jour de la semaine sur la période,
    puis sépare celles à conserver de celles tombant sur un jour exclu."""
    debut = max(debut_annee, activite.premiere_seance or debut_annee)
    fin = min(fin_annee, activite.derniere_seance or fin_annee)

    # se caler sur la première occurrence du bon jour de semaine
    decalage = (activite.jour - debut.weekday()) % 7
    courant = debut + timedelta(days=decalage)

    toutes, conservees, retirees = [], [], []
    while courant <= fin:
        toutes.append(courant)
        (retirees if courant in jours_exclus else conservees).append(courant)
        courant += timedelta(days=7)

    return Seances(toutes=toutes, conservees=conservees, retirees=retirees)
