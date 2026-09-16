"""Chargement du calendrier scolaire depuis un fichier JSON annuel."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

DOSSIER_CALENDRIERS = Path(__file__).resolve().parent.parent / "data" / "calendars"


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


@dataclass(frozen=True)
class Periode:
    nom: str
    debut: date  # inclus
    fin: date    # exclu (jour de la reprise)


@dataclass(frozen=True)
class Ferie:
    id: str
    date: date
    nom: str


class CalendrierScolaire:
    """Représente une année scolaire pour une zone donnée."""

    def __init__(self, data: dict, zone: str):
        if zone not in data["zones"]:
            raise ValueError(f"Zone inconnue : {zone!r}. Zones disponibles : {list(data['zones'])}")

        self.annee: str = data["annee"]
        self.zone: str = zone
        self.label_zone: str = data["zones"][zone]["label"]
        self.academies: str = data["zones"][zone].get("academies", "")
        self.debut_annee: date = _parse_date(data["debut_annee"])
        self.fin_annee: date = _parse_date(data["fin_annee"])

        self.periodes: list[Periode] = [
            Periode(p["nom"], _parse_date(p["debut"]), _parse_date(p["fin"]))
            for p in data["zones"][zone]["periodes"]
        ]
        self.feries: list[Ferie] = [
            Ferie(f["id"], _parse_date(f["date"]), f["nom"]) for f in data.get("feries", [])
        ]

    @classmethod
    def depuis_fichier(cls, chemin: str | Path, zone: str) -> "CalendrierScolaire":
        with open(chemin, encoding="utf-8") as fh:
            return cls(json.load(fh), zone)

    @classmethod
    def depuis_annee(cls, annee: str, zone: str, dossier: Path = DOSSIER_CALENDRIERS) -> "CalendrierScolaire":
        """Charge data/calendars/<annee>.json, ex. annee='2026-2027'."""
        chemin = dossier / f"{annee}.json"
        if not chemin.exists():
            disponibles = sorted(p.stem for p in dossier.glob("*.json"))
            raise FileNotFoundError(
                f"Pas de calendrier pour {annee!r}. Années disponibles : {disponibles}. "
                f"Pour ajouter une année, déposez data/calendars/{annee}.json (voir README)."
            )
        return cls.depuis_fichier(chemin, zone)

    @staticmethod
    def annees_disponibles(dossier: Path = DOSSIER_CALENDRIERS) -> list[str]:
        return sorted(p.stem for p in dossier.glob("*.json"))

    def jours_exclus(self, feries_actifs: Iterable[str] | None = None) -> set[date]:
        """Ensemble des dates à retirer : toutes les vacances + fériés cochés."""
        exclus: set[date] = set()
        for p in self.periodes:
            d = p.debut
            while d < p.fin:
                exclus.add(d)
                d += timedelta(days=1)
        actifs = set(feries_actifs) if feries_actifs is not None else {f.id for f in self.feries}
        for f in self.feries:
            if f.id in actifs:
                exclus.add(f.date)
        return exclus

    def feries_hors_vacances(self) -> list[Ferie]:
        """Fériés qui ne tombent pas déjà dans une période de vacances (utiles à afficher/cocher)."""
        vacances = set()
        for p in self.periodes:
            d = p.debut
            while d < p.fin:
                vacances.add(d)
                d += timedelta(days=1)
        return [f for f in self.feries if f.date not in vacances]
