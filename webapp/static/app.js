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
  div.querySelector(".supprimer").onclick = (e) => { e.target.closest(".act").remove(); sauvegarderLocal(); };
  div.querySelectorAll("input,select").forEach(el => el.addEventListener("change", sauvegarderLocal));
  hote.appendChild(noeud);
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
