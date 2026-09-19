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

import io
import sys
from datetime import date, time
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from planning_scolaire.activites import Activite, calculer_seances
from planning_scolaire.calendrier import CalendrierScolaire
from planning_scolaire.ics import generer_ics, generer_zip, slugifier

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = (
    0  # sans ça, le navigateur garde app.js/style.css en cache jusqu'à 12h
)


def _construire_activites(form) -> list[Activite]:
    """Reconstruit la liste d'activités à partir des champs répétés du
    formulaire. Utilisé à la fois par /generer et /previsualiser, pour ne
    jamais faire diverger ce que l'utilisateur voit et ce qu'il télécharge.
    """
    noms = form.getlist("nom")
    jours = form.getlist("jour")
    debuts = form.getlist("heure_debut")
    fins = form.getlist("heure_fin")
    lieux = form.getlist("lieu")
    premieres = form.getlist("premiere_seance")
    dernieres = form.getlist("derniere_seance")

    return [
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


@app.route("/", methods=["GET"])
def accueil():
    annees = CalendrierScolaire.annees_disponibles()
    annee_defaut = annees[-1] if annees else None
    calendrier_apercu = (
        CalendrierScolaire.depuis_annee(annee_defaut, "B") if annee_defaut else None
    )
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
    calendrier = CalendrierScolaire.depuis_annee(annee, zone)
    return jsonify(
        {
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
        }
    )


@app.route("/previsualiser", methods=["POST"])
def previsualiser():
    """Calcule les vraies séances (vacances déjà retirées) pour alimenter
    le calendrier FullCalendar côté client, sans générer de fichier.
    Même moteur de calcul que /generer et que la CLI : ce que montre
    l'aperçu est exactement ce que contiendront les .ics téléchargés.
    """
    form = request.form
    zone = form["zone"]
    annee = form["annee"]
    feries_actifs = set(form.getlist("ferie"))

    calendrier = CalendrierScolaire.depuis_annee(annee, zone)
    exclus = calendrier.jours_exclus(feries_actifs)

    evenements = []
    for activite in _construire_activites(form):
        seances = calculer_seances(
            activite, calendrier.debut_annee, calendrier.fin_annee, exclus
        )
        for jour in seances.conservees:
            evenements.append(
                {
                    "title": activite.nom,
                    "start": f"{jour.isoformat()}T{activite.heure_debut.isoformat()}",
                    "end": f"{jour.isoformat()}T{activite.heure_fin.isoformat()}",
                }
            )

    vacances = [
        {
            "title": p.nom,
            "start": p.debut.isoformat(),
            "end": p.fin.isoformat(),  # exclu, correspond au jour de la reprise : FullCalendar attend une borne exclusive
            "display": "background",
            "color": "#F0D8AE",
        }
        for p in calendrier.periodes
    ]

    return jsonify(
        {
            "evenements": evenements,
            "vacances": vacances,
            "debut_annee": calendrier.debut_annee.isoformat(),
            "fin_annee": calendrier.fin_annee.isoformat(),
        }
    )


@app.route("/generer", methods=["POST"])
def generer():
    form = request.form
    zone = form["zone"]
    annee = form["annee"]
    feries_actifs = set(form.getlist("ferie"))

    activites = _construire_activites(form)
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
