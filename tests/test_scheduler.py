import sys
from datetime import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from planning_scolaire.activites import Activite, calculer_seances
from planning_scolaire.calendrier import CalendrierScolaire
from planning_scolaire.ics import generer_ics


def _calendrier_b():
    return CalendrierScolaire.depuis_annee("2026-2027", "B")


def test_toussaint_est_retiree():
    cal = _calendrier_b()
    act = Activite("Judo", jour=2, heure_debut=time(17, 0), heure_fin=time(18, 0))  # mercredi
    exclus = cal.jours_exclus()
    seances = calculer_seances(act, cal.debut_annee, cal.fin_annee, exclus)
    # le mercredi 21 octobre 2026 tombe pendant les vacances de la Toussaint
    from datetime import date
    assert date(2026, 10, 21) in seances.retirees
    assert date(2026, 10, 21) not in seances.conservees


def test_premiere_seance_conservee_hors_vacances():
    cal = _calendrier_b()
    act = Activite("Solfège", jour=4, heure_debut=time(16, 30), heure_fin=time(17, 15))  # vendredi
    exclus = cal.jours_exclus()
    seances = calculer_seances(act, cal.debut_annee, cal.fin_annee, exclus)
    assert seances.conservees[0].weekday() == 4
    assert seances.conservees[0] not in exclus


def test_ics_contient_exdate_pour_chaque_semaine_retiree():
    cal = _calendrier_b()
    act = Activite("Judo", jour=2, heure_debut=time(17, 0), heure_fin=time(18, 0))
    contenu = generer_ics(act, cal)
    assert contenu is not None
    assert "RRULE:FREQ=WEEKLY" in contenu
    assert contenu.count("EXDATE") > 0


def test_activite_sans_seance_retourne_none():
    cal = _calendrier_b()
    from datetime import date
    act = Activite(
        "Stage vacances", jour=2, heure_debut=time(17, 0), heure_fin=time(18, 0),
        premiere_seance=date(2026, 10, 19), derniere_seance=date(2026, 10, 30),
    )
    assert generer_ics(act, cal) is None


if __name__ == "__main__":
    for nom, fn in list(globals().items()):
        if nom.startswith("test_"):
            fn()
            print(f"✓ {nom}")
    print("\nTous les tests sont passés.")
