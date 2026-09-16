"""Construction de fichiers .ics (un par activité) et empaquetage en .zip."""

from __future__ import annotations

import io
import re
import unicodedata
import uuid
import zipfile
from datetime import date, datetime, time

from .activites import Activite, calculer_seances
from .calendrier import CalendrierScolaire

JOURS_ICS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]

_VTIMEZONE_PARIS = "\r\n".join([
    "BEGIN:VTIMEZONE",
    "TZID:Europe/Paris",
    "BEGIN:DAYLIGHT",
    "TZOFFSETFROM:+0100",
    "TZOFFSETTO:+0200",
    "TZNAME:CEST",
    "DTSTART:19700329T020000",
    "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
    "END:DAYLIGHT",
    "BEGIN:STANDARD",
    "TZOFFSETFROM:+0200",
    "TZOFFSETTO:+0100",
    "TZNAME:CET",
    "DTSTART:19701025T030000",
    "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
    "END:STANDARD",
    "END:VTIMEZONE",
])


def _echapper(texte: str) -> str:
    return (
        texte.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fmt_date(d: date) -> str:
    return d.strftime("%Y%m%d")


def _fmt_datetime(d: date, t: time) -> str:
    return f"{_fmt_date(d)}T{t.strftime('%H%M%S')}"


def slugifier(texte: str) -> str:
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    texte = re.sub(r"[^a-zA-Z0-9]+", "-", texte).strip("-").lower()
    return texte or "activite"


def generer_ics(activite: Activite, calendrier: CalendrierScolaire, feries_actifs: set[str] | None = None) -> str | None:
    """Retourne le contenu .ics de l'activité, ou None si aucune séance ne tombe hors vacances."""
    exclus = calendrier.jours_exclus(feries_actifs)
    seances = calculer_seances(activite, calendrier.debut_annee, calendrier.fin_annee, exclus)
    if not seances.conservees:
        return None

    premiere, derniere = seances.conservees[0], seances.conservees[-1]
    # exceptions internes : jours exclus strictement entre la 1re et la dernière séance conservée
    exceptions = [d for d in seances.toutes if premiere < d < derniere and d in exclus]

    uid = f"{uuid.uuid4()}@planning-scolaire"
    horodatage = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    byday = JOURS_ICS[activite.jour]

    lignes = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Planning activites scolaires//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_echapper(activite.nom)}",
        "X-WR-TIMEZONE:Europe/Paris",
        _VTIMEZONE_PARIS,
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{horodatage}",
        f"SUMMARY:{_echapper(activite.nom)}",
    ]
    if activite.lieu:
        lignes.append(f"LOCATION:{_echapper(activite.lieu)}")
    lignes.append(f"DTSTART;TZID=Europe/Paris:{_fmt_datetime(premiere, activite.heure_debut)}")
    lignes.append(f"DTEND;TZID=Europe/Paris:{_fmt_datetime(premiere, activite.heure_fin)}")
    lignes.append(f"RRULE:FREQ=WEEKLY;BYDAY={byday};UNTIL={_fmt_date(derniere)}T235959Z")
    for d in exceptions:
        lignes.append(f"EXDATE;TZID=Europe/Paris:{_fmt_datetime(d, activite.heure_debut)}")
    lignes.append(
        f"DESCRIPTION:{_echapper('Séances hors vacances scolaires — ' + calendrier.label_zone + ', année ' + calendrier.annee + '.')}"
    )
    lignes.append("END:VEVENT")
    lignes.append("END:VCALENDAR")
    return "\r\n".join(lignes) + "\r\n"


def generer_zip(activites: list[Activite], calendrier: CalendrierScolaire, feries_actifs: set[str] | None = None) -> bytes:
    """Génère une archive .zip en mémoire contenant un .ics par activité."""
    tampon = io.BytesIO()
    noms_utilises: dict[str, int] = {}
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as archive:
        for activite in activites:
            contenu = generer_ics(activite, calendrier, feries_actifs)
            if contenu is None:
                continue
            base = slugifier(activite.nom)
            noms_utilises[base] = noms_utilises.get(base, 0) + 1
            nom_fichier = base if noms_utilises[base] == 1 else f"{base}-{noms_utilises[base]}"
            archive.writestr(f"{nom_fichier}.ics", contenu)
    return tampon.getvalue()
