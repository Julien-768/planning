"""
Interface en ligne de commande.

Exemples :
    python -m planning_scolaire.cli --zone B --annee 2026-2027 \\
        --activites exemples/activites.json --sortie dossier_ics/

    python -m planning_scolaire.cli --annees-disponibles
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .activites import Activite
from .calendrier import CalendrierScolaire
from .ics import generer_ics, slugifier


def _annee_courante_par_defaut() -> str | None:
    disponibles = CalendrierScolaire.annees_disponibles()
    return disponibles[-1] if disponibles else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Génère des agendas .ics hors vacances scolaires.")
    parser.add_argument("--zone", choices=["A", "B", "C"], help="Zone scolaire (A, B ou C). Déduite du fichier --activites s'il s'agit d'une sauvegarde exportée depuis l'app web.")
    parser.add_argument("--annee", help="Année scolaire, ex. 2026-2027. Par défaut : la plus récente disponible, ou celle indiquée dans une sauvegarde.")
    parser.add_argument("--activites", type=Path, help="Fichier JSON : soit une simple liste d'activités (exemples/activites.json), soit une sauvegarde exportée depuis l'app web.")
    parser.add_argument("--sortie", type=Path, default=Path("agendas"), help="Dossier de sortie pour les .ics.")
    parser.add_argument("--annees-disponibles", action="store_true", help="Liste les années de calendrier connues et quitte.")

    args = parser.parse_args(argv)

    if args.annees_disponibles:
        for a in CalendrierScolaire.annees_disponibles():
            print(a)
        return 0

    if not args.activites:
        parser.error("--activites est requis (sauf avec --annees-disponibles).")

    with open(args.activites, encoding="utf-8") as fh:
        brut = json.load(fh)

    # Deux formats acceptés : une simple liste d'activités, ou une sauvegarde
    # exportée depuis l'app web (dict avec zone / annee / feries / activites).
    feries_actifs: set[str] | None = None
    if isinstance(brut, dict):
        zone = args.zone or brut.get("zone")
        annee = args.annee or brut.get("annee")
        if "feries" in brut:
            feries_actifs = set(brut["feries"])
        liste_activites = brut.get("activites", [])
    else:
        zone = args.zone
        annee = args.annee
        liste_activites = brut

    if not zone:
        parser.error("--zone est requis (le fichier fourni n'en précise pas).")

    annee = annee or _annee_courante_par_defaut()
    if annee is None:
        print("Aucun calendrier trouvé dans data/calendars/. Ajoutez-en un (voir README).", file=sys.stderr)
        return 1

    calendrier = CalendrierScolaire.depuis_annee(annee, zone)
    activites = [Activite.depuis_dict(d) for d in liste_activites]

    args.sortie.mkdir(parents=True, exist_ok=True)
    generees = 0
    for activite in activites:
        contenu = generer_ics(activite, calendrier, feries_actifs)
        if contenu is None:
            print(f"⚠  {activite.nom} : aucune séance hors vacances sur la période demandée, ignorée.")
            continue
        chemin = args.sortie / f"{slugifier(activite.nom)}.ics"
        chemin.write_text(contenu, encoding="utf-8")
        print(f"✓ {activite.nom} → {chemin}")
        generees += 1

    print(f"\n{generees} agenda(s) généré(s) dans {args.sortie}/ pour {calendrier.label_zone}, année {annee}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
