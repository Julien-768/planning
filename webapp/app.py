"""
Application web Flask.

Lancer en local :
    pip install -r requirements.txt
    python webapp/app.py
    → http://localhost:5000

Le formulaire réutilise exactement le package planning_scolaire :
aucune logique métier n'est dupliquée ici.
"""

from __future__ import annotations

import sys
from datetime import date, time
from pathlib import Path

from flask import Flask, render_template, request, send_file
import io

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from planning_scolaire.activites import Activite
from planning_scolaire.calendrier import CalendrierScolaire
from planning_scolaire.ics import generer_zip, generer_ics, slugifier

app = Flask(__name__)


@app.route("/", methods=["GET"])
def accueil():
    annees = CalendrierScolaire.annees_disponibles()
    annee_defaut = annees[-1] if annees else None
    calendrier_apercu = CalendrierScolaire.depuis_annee(annee_defaut, "B") if annee_defaut else None
    return render_template(
        "index.html",
        annees=annees,
        annee_defaut=annee_defaut,
        zones=["A", "B", "C"],
        feries=calendrier_apercu.feries_hors_vacances() if calendrier_apercu else [],
    )


@app.route("/calendrier/<annee>/<zone>")
def api_calendrier(annee: str, zone: str):
    """Renvoie les périodes de vacances et les fériés pertinents pour la zone (JSON, pour l'aperçu côté client)."""
    from flask import jsonify

    calendrier = CalendrierScolaire.depuis_annee(annee, zone)
    return jsonify({
        "label": calendrier.label_zone,
        "debut_annee": calendrier.debut_annee.isoformat(),
        "fin_annee": calendrier.fin_annee.isoformat(),
        "periodes": [
            {"nom": p.nom, "debut": p.debut.isoformat(), "fin": p.fin.isoformat()}
            for p in calendrier.periodes
        ],
        "feries": [
            {"id": f.id, "date": f.date.isoformat(), "nom": f.nom}
            for f in calendrier.feries_hors_vacances()
        ],
    })


@app.route("/generer", methods=["POST"])
def generer():
    form = request.form
    zone = form["zone"]
    annee = form["annee"]

    noms = form.getlist("nom")
    jours = form.getlist("jour")
    debuts = form.getlist("heure_debut")
    fins = form.getlist("heure_fin")
    lieux = form.getlist("lieu")
    premieres = form.getlist("premiere_seance")
    dernieres = form.getlist("derniere_seance")

    feries_actifs = set(form.getlist("ferie"))

    activites = [
        Activite(
            nom=nom,
            jour=int(jour),
            heure_debut=time.fromisoformat(hd),
            heure_fin=time.fromisoformat(hf),
            lieu=lieu,
            premiere_seance=date.fromisoformat(premiere) if premiere else None,
            derniere_seance=date.fromisoformat(derniere) if derniere else None,
        )
        for nom, jour, hd, hf, lieu, premiere, derniere in zip(
            noms, jours, debuts, fins, lieux, premieres, dernieres
        )
        if nom.strip()
    ]

    calendrier = CalendrierScolaire.depuis_annee(annee, zone)

    if len(activites) == 1:
        contenu = generer_ics(activites[0], calendrier, feries_actifs)
        return send_file(
            io.BytesIO(contenu.encode("utf-8")),
            mimetype="text/calendar",
            as_attachment=True,
            download_name=f"{slugifier(activites[0].nom)}.ics",
        )

    donnees_zip = generer_zip(activites, calendrier, feries_actifs)
    return send_file(
        io.BytesIO(donnees_zip),
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"agendas-{zone.lower()}-{annee}.zip",
    )


if __name__ == "__main__":
    app.run(debug=True)
