

from datetime import date, timedelta

DUREE_PRET = 14          
LIMITE_PRETS = 3        
SEUIL_STOCK_FAIBLE = 1   



def est_actif(emprunt):
    """Un prêt est actif tant qu'il n'a pas de date de retour."""
    return emprunt["date_retour"] == ""


def nb_prets_actifs(emprunts, id_livre=None, id_adherent=None):
    """Compte les prêts actifs, éventuellement pour un livre ou un adhérent."""
    total = 0
    for e in emprunts:
        if not est_actif(e):
            continue
        if id_livre is not None and e["id_livre"] != id_livre:
            continue
        if id_adherent is not None and e["id_adherent"] != id_adherent:
            continue
        total += 1
    return total


def nb_emprunts(id_livre, emprunts):
    """Nombre total d'emprunts d'un livre (historique complet)."""
    return sum(1 for e in emprunts if e["id_livre"] == id_livre)


def exemplaires_disponibles(livre, emprunts):
    """Quantité totale moins les prêts actifs, jamais négatif."""
    dispo = livre["total"] - nb_prets_actifs(emprunts, id_livre=livre["id"])
    return max(dispo, 0)


def prochain_id_emprunt(emprunts):
    """Génère un identifiant du type E1, E2, ..."""
    numeros = [int(e["id"][1:]) for e in emprunts
               if e["id"][1:].isdigit()]
    return "E" + str(max(numeros, default=0) + 1)



def ajouter_livre(livres, id_livre, titre, auteur, categorie, annee, total):
    if not id_livre or not titre or not auteur or not categorie:
        raise ValueError("Tous les champs sont obligatoires.")
    if id_livre in livres:
        raise ValueError(f"L'identifiant {id_livre} existe déjà.")
    if total < 0:
        raise ValueError("Le nombre d'exemplaires ne peut pas être négatif.")
    if annee <= 0:
        raise ValueError("Année de publication invalide.")
    livres[id_livre] = {"id": id_livre, "titre": titre, "auteur": auteur,
                        "categorie": categorie, "annee": annee,
                        "total": total}


def modifier_livre(livres, emprunts, id_livre, champs):
    if id_livre not in livres:
        raise ValueError("Ouvrage introuvable.")
    if "total" in champs:
        if champs["total"] < 0:
            raise ValueError("Le nombre d'exemplaires ne peut pas être négatif.")
        # on ne peut pas descendre sous le nombre de prêts en cours
        if champs["total"] < nb_prets_actifs(emprunts, id_livre=id_livre):
            raise ValueError("Moins d'exemplaires que de prêts en cours.")
    if "annee" in champs and champs["annee"] <= 0:
        raise ValueError("Année de publication invalide.")
    livres[id_livre].update(champs)


def supprimer_livre(livres, emprunts, id_livre):
    if id_livre not in livres:
        raise ValueError("Ouvrage introuvable.")
    if nb_prets_actifs(emprunts, id_livre=id_livre) > 0:
        raise ValueError("Suppression refusée : des prêts sont en cours.")
    del livres[id_livre]



def ajouter_adherent(adherents, id_adh, nom, prenom, contact):
    if not id_adh or not nom or not prenom:
        raise ValueError("Identifiant, nom et prénom sont obligatoires.")
    if id_adh in adherents:
        raise ValueError(f"L'identifiant {id_adh} existe déjà.")
    adherents[id_adh] = {"id": id_adh, "nom": nom, "prenom": prenom,
                         "contact": contact, "actif": True}


def modifier_adherent(adherents, id_adh, champs):
    if id_adh not in adherents:
        raise ValueError("Adhérent introuvable.")
    adherents[id_adh].update(champs)


def desactiver_adherent(adherents, id_adh):
    if id_adh not in adherents:
        raise ValueError("Adhérent introuvable.")
    adherents[id_adh]["actif"] = False



def emprunter(livres, adherents, emprunts, id_livre, id_adherent,
              aujourdhui=None):
    if id_livre not in livres:
        raise ValueError("Ouvrage introuvable.")
    if id_adherent not in adherents:
        raise ValueError("Adhérent introuvable.")
    if not adherents[id_adherent]["actif"]:
        raise ValueError("Cet adhérent est désactivé.")
    if exemplaires_disponibles(livres[id_livre], emprunts) == 0:
        raise ValueError("Aucun exemplaire disponible.")
    if nb_prets_actifs(emprunts, id_adherent=id_adherent) >= LIMITE_PRETS:
        raise ValueError(f"Limite de {LIMITE_PRETS} prêts actifs atteinte.")

    if aujourdhui is None:
        aujourdhui = date.today()
    emprunt = {"id": prochain_id_emprunt(emprunts), "id_livre": id_livre,
               "id_adherent": id_adherent,
               "date_emprunt": aujourdhui.isoformat(), "date_retour": ""}
    emprunts.append(emprunt)
    return emprunt


def retourner(emprunts, id_emprunt, aujourdhui=None):
    for e in emprunts:
        if e["id"] == id_emprunt:
            if not est_actif(e):
                raise ValueError("Ce prêt a déjà été retourné.")
            if aujourdhui is None:
                aujourdhui = date.today()
            e["date_retour"] = aujourdhui.isoformat()
            return
    raise ValueError("Opération introuvable.")


def est_en_retard(emprunt, aujourdhui=None):
    if not est_actif(emprunt):
        return False
    if aujourdhui is None:
        aujourdhui = date.today()
    echeance = date.fromisoformat(emprunt["date_emprunt"]) + timedelta(days=DUREE_PRET)
    return aujourdhui > echeance


def emprunts_en_retard(emprunts, aujourdhui=None):
    return [e for e in emprunts if est_en_retard(e, aujourdhui)]



def rechercher(livres, emprunts, critere, texte, tri="titre"):
    """Recherche insensible à la casse. Partielle sur titre/auteur,
    exacte sur catégorie et identifiant."""
    texte = texte.strip().casefold()
    resultats = []
    for livre in livres.values():
        valeur = str(livre[critere]).casefold()
        if critere in ("titre", "auteur"):
            trouve = texte in valeur
        else:
            trouve = texte == valeur
        if trouve:
            resultats.append(livre)

    if tri == "emprunts":
        # du plus emprunté au moins emprunté, puis par titre
        resultats.sort(key=lambda l: (-nb_emprunts(l["id"], emprunts),
                                      l["titre"].casefold()))
    elif tri == "auteur":
        resultats.sort(key=lambda l: l["auteur"].casefold())
    else:
        resultats.sort(key=lambda l: l["titre"].casefold())
    return resultats



def recommander(livres, emprunts, categorie):
    """Jusqu'à 3 livres disponibles de la catégorie, par popularité
    puis par titre en cas d'égalité."""
    categorie = categorie.strip().casefold()
    candidats = [l for l in livres.values()
                 if l["categorie"].casefold() == categorie
                 and exemplaires_disponibles(l, emprunts) > 0]
    candidats.sort(key=lambda l: (-nb_emprunts(l["id"], emprunts),
                                  l["titre"].casefold()))
    return candidats[:3]



def calculer_statistiques(livres, emprunts, aujourdhui=None):
    nb_exemplaires = sum(l["total"] for l in livres.values())
    nb_dispo = sum(exemplaires_disponibles(l, emprunts) for l in livres.values())
    actifs = nb_prets_actifs(emprunts)

    # emprunts par livre et par catégorie
    par_livre = {}
    par_categorie = {}
    for e in emprunts:
        livre = livres.get(e["id_livre"])
        if livre is None:   # livre supprimé depuis, on ignore l'historique
            continue
        par_livre[livre["titre"]] = par_livre.get(livre["titre"], 0) + 1
        cat = livre["categorie"]
        par_categorie[cat] = par_categorie.get(cat, 0) + 1

    top5 = sorted(par_livre.items(), key=lambda t: (-t[1], t[0].casefold()))[:5]

    alertes = []
    for livre in livres.values():
        dispo = exemplaires_disponibles(livre, emprunts)
        if dispo == 0:
            alertes.append(f"{livre['titre']} : tous les exemplaires sont empruntés")
        elif dispo <= SEUIL_STOCK_FAIBLE:
            alertes.append(f"{livre['titre']} : stock faible ({dispo} restant)")

    return {
        "nb_ouvrages": len(livres),
        "nb_exemplaires": nb_exemplaires,
        "nb_disponibles": nb_dispo,
        "nb_actifs": actifs,
        "nb_retards": len(emprunts_en_retard(emprunts, aujourdhui)),
        "nb_termines": len(emprunts) - actifs,
        "top5": top5,
        "par_categorie": par_categorie,
        "alertes": alertes,
    }