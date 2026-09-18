const hote = document.getElementById("activites");
const modele = document.getElementById("modele-activite");
const CLE_LOCALE = "planning-scolaire-formulaire";

function formaterDateFr(iso){
  const [y,m,d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function ligneActivite(valeurs = {}){
  const noeud = modele.content.cloneNode(true);
  const div = noeud.querySelector(".act");
  if (valeurs.nom) div.querySelector('[name="nom"]').value = valeurs.nom;
  if (valeurs.jour !== undefined) div.querySelector('[name="jour"]').value = valeurs.jour;
  if (valeurs.heure_debut) div.querySelector('[name="heure_debut"]').value = valeurs.heure_debut;
  if (valeurs.heure_fin) div.querySelector('[name="heure_fin"]').value = valeurs.heure_fin;
  if (valeurs.lieu) div.querySelector('[name="lieu"]').value = valeurs.lieu;
  if (valeurs.premiere_seance) div.querySelector('[name="premiere_seance"]').value = valeurs.premiere_seance;
  if (valeurs.derniere_seance) div.querySelector('[name="derniere_seance"]').value = valeurs.derniere_seance;
  div.querySelector(".supprimer").onclick = (e) => {
    e.target.closest(".act").remove();
    sauvegarderLocal();
    rafraichirSemaine();
  };
  div.querySelectorAll("input,select").forEach(el => {
    el.addEventListener("change", () => { sauvegarderLocal(); rafraichirSemaine(); });
    el.addEventListener("input", rafraichirSemaine);
  });
  hote.appendChild(noeud);
  rafraichirSemaine();
}

document.getElementById("ajouter").onclick = () => { ligneActivite(); sauvegarderLocal(); };

// --- Affichage des périodes de vacances + rafraîchissement des fériés ---
async function rafraichirCalendrier(){
  const zone = document.getElementById("zone").value;
  const annee = document.getElementById("annee").value;
  const res = await fetch(`/calendrier/${annee}/${zone}`);
  const data = await res.json();

  const tablePeriodes = document.getElementById("periodes");
  tablePeriodes.innerHTML = data.periodes.map(p =>
    `<tr><td>${p.nom}</td><td>du ${formaterDateFr(p.debut)} au ${formaterDateFr(p.fin)}</td></tr>`
  ).join("");

  const conteneurFeries = document.getElementById("feries");
  const feriesCoches = new Set([...conteneurFeries.querySelectorAll("input:checked")].map(i => i.value));
  const premierAffichage = conteneurFeries.dataset.rempli !== "1";
  conteneurFeries.innerHTML = data.feries.map(f =>
    `<label><input type="checkbox" name="ferie" value="${f.id}" ${premierAffichage || feriesCoches.has(f.id) ? "checked" : ""}> ${f.nom} — ${formaterDateFr(f.date)}</label>`
  ).join("");
  conteneurFeries.dataset.rempli = "1";
  conteneurFeries.querySelectorAll("input").forEach(el => el.addEventListener("change", sauvegarderLocal));
}
document.getElementById("zone").onchange = () => { rafraichirCalendrier(); sauvegarderLocal(); };
document.getElementById("annee").onchange = () => { rafraichirCalendrier(); sauvegarderLocal(); };

// --- Collecte / remplissage du formulaire ---
function collecterEtat(){
  const activites = [...document.querySelectorAll("#activites .act")].map(div => ({
    nom: div.querySelector('[name="nom"]').value,
    jour: div.querySelector('[name="jour"]').value,
    heure_debut: div.querySelector('[name="heure_debut"]').value,
    heure_fin: div.querySelector('[name="heure_fin"]').value,
    lieu: div.querySelector('[name="lieu"]').value,
    premiere_seance: div.querySelector('[name="premiere_seance"]').value,
    derniere_seance: div.querySelector('[name="derniere_seance"]').value,
  }));
  return {
    zone: document.getElementById("zone").value,
    annee: document.getElementById("annee").value,
    feries: [...document.querySelectorAll('#feries input:checked')].map(i => i.value),
    activites,
  };
}

function appliquerEtat(etat){
  if (etat.zone) document.getElementById("zone").value = etat.zone;
  if (etat.annee) document.getElementById("annee").value = etat.annee;
  hote.innerHTML = "";
  (etat.activites && etat.activites.length ? etat.activites : [{}]).forEach(ligneActivite);
  rafraichirCalendrier().then(() => {
    if (!etat.feries) return;
    document.querySelectorAll('#feries input').forEach(i => { i.checked = etat.feries.includes(i.value); });
  });
}

function sauvegarderLocal(){
  try { localStorage.setItem(CLE_LOCALE, JSON.stringify(collecterEtat())); } catch (e) {}
}

// --- Export / import en fichier ---
document.getElementById("exporter").onclick = () => {
  const blob = new Blob([JSON.stringify(collecterEtat(), null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sauvegarde-activites.json";
  a.click();
  URL.revokeObjectURL(url);
  document.getElementById("statut-sauvegarde").textContent = "Fichier téléchargé.";
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
    statut.textContent = "Fichier illisible : ce n'est pas une sauvegarde valide.";
  }
  e.target.value = "";
});

// --- Aperçu d'une semaine type (indépendant du calendrier scolaire : ---
// --- montre juste comment les activités s'articulent dans la semaine) ---
const NOMS_JOURS = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"];
const PX_PAR_MINUTE = 1.1;

function versMinutes(hhmm){
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
}

function rafraichirSemaine(){
  const conteneur = document.getElementById("calendrier-semaine");
  const lignes = [...document.querySelectorAll("#activites .act")];
  const activites = lignes.map(div => ({
    nom: div.querySelector('[name="nom"]').value.trim() || "Activité",
    jour: parseInt(div.querySelector('[name="jour"]').value, 10),
    debut: div.querySelector('[name="heure_debut"]').value,
    fin: div.querySelector('[name="heure_fin"]').value,
  })).filter(a => a.debut && a.fin && a.fin > a.debut);

  let minDepart = 8 * 60;
  let maxFin = 19 * 60;
  activites.forEach(a => {
    minDepart = Math.min(minDepart, versMinutes(a.debut));
    maxFin = Math.max(maxFin, versMinutes(a.fin));
  });
  minDepart = Math.floor(minDepart / 60) * 60;
  maxFin = Math.ceil(maxFin / 60) * 60;
  const hauteurTotale = (maxFin - minDepart) * PX_PAR_MINUTE;

  let heures = "";
  for (let h = minDepart; h <= maxFin; h += 60){
    const top = (h - minDepart) * PX_PAR_MINUTE;
    heures += `<div class="heure-etiquette" style="top:${top}px">${String(Math.floor(h/60)).padStart(2,"0")}h</div>`;
  }

  const colonnes = NOMS_JOURS.map((nomJour, idx) => {
    const blocs = activites.filter(a => a.jour === idx).map(a => {
      const top = (versMinutes(a.debut) - minDepart) * PX_PAR_MINUTE;
      const hauteur = Math.max((versMinutes(a.fin) - versMinutes(a.debut)) * PX_PAR_MINUTE, 16);
      return `<div class="bloc-activite" style="top:${top}px;height:${hauteur}px" title="${a.nom} — ${a.debut} à ${a.fin}">
        <b>${a.nom}</b><span>${a.debut}–${a.fin}</span>
      </div>`;
    }).join("");
    return `<div class="jour-colonne">
      <div class="jour-entete">${nomJour}</div>
      <div class="jour-corps" style="height:${hauteurTotale}px">${blocs}</div>
    </div>`;
  }).join("");

  conteneur.innerHTML = activites.length
    ? `<div class="semaine-grille">
         <div class="heures-colonne">
           <div class="jour-entete"></div>
           <div class="heures-corps" style="height:${hauteurTotale}px">${heures}</div>
         </div>
         ${colonnes}
       </div>`
    : `<p class="semaine-vide">Ajoutez une activité avec un jour et des horaires pour voir apparaître l'aperçu.</p>`;
}

// --- Initialisation : restaurer la sauvegarde locale si elle existe ---
(function initialiser(){
  let etat = null;
  try { etat = JSON.parse(localStorage.getItem(CLE_LOCALE)); } catch (e) {}
  if (etat && etat.activites && etat.activites.length) {
    appliquerEtat(etat);
  } else {
    ligneActivite();
    rafraichirCalendrier();
  }
})();
