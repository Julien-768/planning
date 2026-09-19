const hote = document.getElementById("activites");
const modele = document.getElementById("modele-activite");
const CLE_LOCALE = "planning-scolaire-formulaire";

function formaterDateFr(iso) {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function ligneActivite(valeurs = {}) {
  const noeud = modele.content.cloneNode(true);
  const div = noeud.querySelector(".act");
  if (valeurs.nom) div.querySelector('[name="nom"]').value = valeurs.nom;
  if (valeurs.jour !== undefined)
    div.querySelector('[name="jour"]').value = valeurs.jour;
  if (valeurs.heure_debut)
    div.querySelector('[name="heure_debut"]').value = valeurs.heure_debut;
  if (valeurs.heure_fin)
    div.querySelector('[name="heure_fin"]').value = valeurs.heure_fin;
  if (valeurs.lieu) div.querySelector('[name="lieu"]').value = valeurs.lieu;
  if (valeurs.premiere_seance)
    div.querySelector('[name="premiere_seance"]').value =
      valeurs.premiere_seance;
  if (valeurs.derniere_seance)
    div.querySelector('[name="derniere_seance"]').value =
      valeurs.derniere_seance;
  div.querySelector(".supprimer").onclick = (e) => {
    e.target.closest(".act").remove();
    sauvegarderLocal();
    rafraichirApercu();
  };
  div.querySelectorAll("input,select").forEach((el) => {
    el.addEventListener("change", () => {
      sauvegarderLocal();
      rafraichirApercu();
    });
    el.addEventListener("input", rafraichirApercuDifferee);
  });
  hote.appendChild(noeud);
  rafraichirApercuDifferee();
}

document.getElementById("ajouter").onclick = () => {
  ligneActivite();
  sauvegarderLocal();
};

// --- Affichage des périodes de vacances + rafraîchissement des fériés ---
async function rafraichirCalendrier() {
  const zone = document.getElementById("zone").value;
  const annee = document.getElementById("annee").value;
  const res = await fetch(`/calendrier/${annee}/${zone}`);
  const data = await res.json();

  const tablePeriodes = document.getElementById("periodes");
  tablePeriodes.innerHTML = data.periodes
    .map(
      (p) =>
        `<tr><td>${p.nom}</td><td>du ${formaterDateFr(p.debut)} au ${formaterDateFr(p.fin)}</td></tr>`,
    )
    .join("");

  const conteneurFeries = document.getElementById("feries");
  const feriesCoches = new Set(
    [...conteneurFeries.querySelectorAll("input:checked")].map((i) => i.value),
  );
  const premierAffichage = conteneurFeries.dataset.rempli !== "1";
  conteneurFeries.innerHTML = data.feries
    .map(
      (f) =>
        `<label><input type="checkbox" name="ferie" value="${f.id}" ${premierAffichage || feriesCoches.has(f.id) ? "checked" : ""}> ${f.nom} — ${formaterDateFr(f.date)}</label>`,
    )
    .join("");
  conteneurFeries.dataset.rempli = "1";
  conteneurFeries.querySelectorAll("input").forEach((el) =>
    el.addEventListener("change", () => {
      sauvegarderLocal();
      rafraichirApercu();
    }),
  );
}
document.getElementById("zone").onchange = () => {
  rafraichirCalendrier();
  sauvegarderLocal();
  rafraichirApercu();
};
document.getElementById("annee").onchange = () => {
  rafraichirCalendrier();
  sauvegarderLocal();
  rafraichirApercu();
};

// --- Collecte / remplissage du formulaire ---
function collecterEtat() {
  const activites = [...document.querySelectorAll("#activites .act")].map(
    (div) => ({
      nom: div.querySelector('[name="nom"]').value,
      jour: div.querySelector('[name="jour"]').value,
      heure_debut: div.querySelector('[name="heure_debut"]').value,
      heure_fin: div.querySelector('[name="heure_fin"]').value,
      lieu: div.querySelector('[name="lieu"]').value,
      premiere_seance: div.querySelector('[name="premiere_seance"]').value,
      derniere_seance: div.querySelector('[name="derniere_seance"]').value,
    }),
  );
  return {
    zone: document.getElementById("zone").value,
    annee: document.getElementById("annee").value,
    feries: [...document.querySelectorAll("#feries input:checked")].map(
      (i) => i.value,
    ),
    activites,
  };
}

function appliquerEtat(etat) {
  if (etat.zone) document.getElementById("zone").value = etat.zone;
  if (etat.annee) document.getElementById("annee").value = etat.annee;
  hote.innerHTML = "";
  (etat.activites && etat.activites.length ? etat.activites : [{}]).forEach(
    ligneActivite,
  );
  rafraichirCalendrier().then(() => {
    if (etat.feries) {
      document.querySelectorAll("#feries input").forEach((i) => {
        i.checked = etat.feries.includes(i.value);
      });
    }
    rafraichirApercu();
  });
}

function sauvegarderLocal() {
  try {
    localStorage.setItem(CLE_LOCALE, JSON.stringify(collecterEtat()));
  } catch (e) {}
}

// --- Export / import en fichier ---
document.getElementById("exporter").onclick = () => {
  const blob = new Blob([JSON.stringify(collecterEtat(), null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sauvegarde-activites.json";
  a.click();
  URL.revokeObjectURL(url);
  document.getElementById("statut-sauvegarde").textContent =
    "Fichier téléchargé.";
};

document.getElementById("importer").addEventListener("change", async (e) => {
  const fichier = e.target.files[0];
  const statut = document.getElementById("statut-sauvegarde");
  if (!fichier) return;
  try {
    const etat = JSON.parse(await fichier.text());
    appliquerEtat(etat);
    sauvegarderLocal();
    statut.textContent = "Sauvegarde restaurée.";
  } catch (err) {
    statut.textContent =
      "Fichier illisible : ce n'est pas une sauvegarde valide.";
  }
  e.target.value = "";
});

// --- Aperçu FullCalendar : vraies séances calculées côté serveur (même ---
// --- moteur que /generer), avec les vacances affichées en fond grisé.  ---
let calendrierFC = null;

function initFullCalendar() {
  const conteneur = document.getElementById("calendrier-fc");
  calendrierFC = new FullCalendar.Calendar(conteneur, {
    locale: "fr",
    height: 620,
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay",
    },
    initialView: "dayGridMonth",
    firstDay: 1,
    events: [],
    // Empêche les boutons internes (prev/next/today/vues) de se comporter
    // comme des boutons de soumission du formulaire qui les entoure — un
    // <button> HTML sans attribut type vaut "submit" par défaut.
    datesSet: () => neutraliserBoutonsCalendrier(),
  });
  calendrierFC.render();
  neutraliserBoutonsCalendrier();
}

function neutraliserBoutonsCalendrier() {
  document.querySelectorAll("#calendrier-fc button").forEach((b) => {
    b.type = "button";
  });
}

let delaiApercu = null;
function rafraichirApercuDifferee() {
  clearTimeout(delaiApercu);
  delaiApercu = setTimeout(rafraichirApercu, 350);
}

async function rafraichirApercu() {
  if (!calendrierFC) return;
  const form = document.getElementById("form");
  const donnees = new FormData(form);
  let reponse;
  try {
    reponse = await fetch("/previsualiser", { method: "POST", body: donnees });
  } catch (e) {
    return; // pas de réseau / serveur : l'aperçu reste tel quel, silencieusement
  }
  if (!reponse.ok) return;
  const { evenements, vacances } = await reponse.json();

  calendrierFC.removeAllEvents();
  calendrierFC.addEventSource(vacances);
  calendrierFC.addEventSource(
    evenements.map((e) => ({ ...e, color: "var(--school, #2E6B4F)" })),
  );
}

// --- Onglets ---
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document
      .querySelectorAll(".tab-btn")
      .forEach((b) => b.setAttribute("aria-selected", "false"));
    btn.setAttribute("aria-selected", "true");

    document.querySelectorAll(".tab-panel").forEach((p) => {
      p.hidden = true;
    });
    const panel = document.getElementById(`onglet-${btn.dataset.tab}`);
    panel.hidden = false;

    if (btn.dataset.tab === "3") {
      // FullCalendar s'initialise mal (voire pas du tout) s'il est construit
      // pendant que son conteneur est caché (hidden = display:none) : on ne
      // le crée qu'au premier passage sur cet onglet, jamais avant.
      if (!calendrierFC) {
        initFullCalendar();
        rafraichirApercu();
      } else {
        requestAnimationFrame(() => calendrierFC.updateSize());
      }
    }
  });
});

// --- Initialisation : restaurer la sauvegarde locale si elle existe ---
(function initialiser() {
  let etat = null;
  try {
    etat = JSON.parse(localStorage.getItem(CLE_LOCALE));
  } catch (e) {}
  if (etat && etat.activites && etat.activites.length) {
    appliquerEtat(etat);
  } else {
    ligneActivite();
    rafraichirCalendrier();
  }
})();
