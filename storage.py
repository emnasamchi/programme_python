
import csv
import os
from datetime import date

CHAMPS_LIVRES = ["id", "titre", "auteur", "categorie", "annee", "total"]
CHAMPS_ADHERENTS = ["id", "nom", "prenom", "contact", "actif"]
CHAMPS_EMPRUNTS = ["id", "id_livre", "id_adherent", "date_emprunt", "date_retour"]



def lire_csv(chemin, champs, avertissements):
    """Renvoie la liste des lignes (dicts) d'un CSV, ou [] si problème."""
    nom = os.path.basename(chemin)
    if not os.path.exists(chemin):
        avertissements.append(f"{nom} est absent, on part d'une liste vide.")
        return []
    try:
        with open(chemin, newline="", encoding="utf-8") as f:
            lecteur = csv.DictReader(f)
            if lecteur.fieldnames is None:   # fichier vide
                avertissements.append(f"{nom} est vide.")
                return []
            if any(c not in lecteur.fieldnames for c in champs):
                avertissements.append(f"{nom} : colonnes attendues {champs}, fichier ignoré.")
                return []
            lignes = []
            for numero, ligne in enumerate(lecteur, start=2):
                # ligne trop courte ou trop longue
                if None in ligne or None in ligne.values():
                    avertissements.append(f"{nom} ligne {numero} mal formée, ignorée.")
                    continue
                lignes.append({c: ligne[c].strip() for c in champs})
            return lignes
    except (OSError, UnicodeDecodeError, csv.Error) as erreur:
        avertissements.append(f"{nom} illisible ({erreur}).")
        return []


def date_valide(texte):
    try:
        date.fromisoformat(texte)
        return True
    except ValueError:
        return False


def charger_livres(dossier, avertissements):
    livres = {}
    for ligne in lire_csv(os.path.join(dossier, "livres.csv"), CHAMPS_LIVRES, avertissements):
        try:
            annee = int(ligne["annee"])
            total = int(ligne["total"])
        except ValueError:
            avertissements.append(f"Livre {ligne['id']} : année ou quantité non numérique, ignoré.")
            continue
        if not ligne["id"] or not ligne["titre"]:
            avertissements.append("Livre sans identifiant ou sans titre, ignoré.")
        elif ligne["id"] in livres:
            avertissements.append(f"Livre {ligne['id']} en double, ignoré.")
        elif total < 0 or annee <= 0:
            avertissements.append(f"Livre {ligne['id']} : valeurs invalides, ignoré.")
        else:
            ligne["annee"] = annee
            ligne["total"] = total
            livres[ligne["id"]] = ligne
    return livres


def charger_adherents(dossier, avertissements):
    adherents = {}
    for ligne in lire_csv(os.path.join(dossier, "adherents.csv"), CHAMPS_ADHERENTS, avertissements):
        if not ligne["id"] or not ligne["nom"] or not ligne["prenom"]:
            avertissements.append("Adhérent incomplet, ignoré.")
        elif ligne["id"] in adherents:
            avertissements.append(f"Adhérent {ligne['id']} en double, ignoré.")
        elif ligne["actif"] not in ("0", "1"):
            avertissements.append(f"Adhérent {ligne['id']} : champ actif invalide, ignoré.")
        else:
            ligne["actif"] = ligne["actif"] == "1"
            adherents[ligne["id"]] = ligne
    return adherents


def charger_emprunts(dossier, livres, adherents, avertissements):
    emprunts = []
    ids_vus = set()
    for ligne in lire_csv(os.path.join(dossier, "emprunts.csv"), CHAMPS_EMPRUNTS, avertissements):
        if not ligne["id"] or ligne["id"] in ids_vus:
            avertissements.append(f"Emprunt {ligne['id']!r} : identifiant vide ou en double, ignoré.")
        elif ligne["id_livre"] not in livres or ligne["id_adherent"] not in adherents:
            avertissements.append(f"Emprunt {ligne['id']} : livre ou adhérent inexistant, ignoré.")
        elif not date_valide(ligne["date_emprunt"]):
            avertissements.append(f"Emprunt {ligne['id']} : date d'emprunt invalide, ignoré.")
        elif ligne["date_retour"] != "" and not date_valide(ligne["date_retour"]):
            avertissements.append(f"Emprunt {ligne['id']} : date de retour invalide, ignoré.")
        else:
            ids_vus.add(ligne["id"])
            emprunts.append(ligne)
    return emprunts


def charger_donnees(dossier):
    """Renvoie (donnees, avertissements)."""
    avertissements = []
    livres = charger_livres(dossier, avertissements)
    adherents = charger_adherents(dossier, avertissements)
    emprunts = charger_emprunts(dossier, livres, adherents, avertissements)

    # cohérence : pas plus de prêts actifs que d'exemplaires
    for id_livre, livre in livres.items():
        actifs = sum(1 for e in emprunts if e["id_livre"] == id_livre and e["date_retour"] == "")
        if actifs > livre["total"]:
            avertissements.append(f"Livre {id_livre} : {actifs} prêts actifs pour {livre['total']} exemplaires.")

    donnees = {"livres": livres, "adherents": adherents, "emprunts": emprunts}
    return donnees, avertissements



def ecrire_csv(chemin, champs, lignes):
    # on écrit dans un fichier temporaire puis on remplace, pour ne pas
    # perdre l'ancien fichier si l'écriture plante en route
    temporaire = chemin + ".tmp"
    with open(temporaire, "w", newline="", encoding="utf-8") as f:
        ecrivain = csv.DictWriter(f, fieldnames=champs)
        ecrivain.writeheader()
        for ligne in lignes:
            ecrivain.writerow({c: ligne[c] for c in champs})
    os.replace(temporaire, chemin)


def sauvegarder_donnees(donnees, dossier):
    os.makedirs(dossier, exist_ok=True)
    ecrire_csv(os.path.join(dossier, "livres.csv"), CHAMPS_LIVRES,
               donnees["livres"].values())
    adherents = []
    for a in donnees["adherents"].values():
        adherents.append({**a, "actif": "1" if a["actif"] else "0"})
    ecrire_csv(os.path.join(dossier, "adherents.csv"), CHAMPS_ADHERENTS, adherents)
    ecrire_csv(os.path.join(dossier, "emprunts.csv"), CHAMPS_EMPRUNTS,
               donnees["emprunts"])



def donnees_demo():
    livres_demo = [
        ("L001", "Python pour les débutants", "Marie Dupont", "Informatique", 2020, 3),
        ("L002", "Algorithmique", "Paul Martin", "Informatique", 2018, 2),
        ("L003", "Les Misérables", "Victor Hugo", "Roman", 1862, 1),
        ("L004", "L'Étranger", "Albert Camus", "Roman", 1942, 2),
        ("L005", "Une brève histoire du temps", "Stephen Hawking", "Sciences", 1988, 2),
        ("L006", "Cosmos", "Carl Sagan", "Sciences", 1980, 1),
        ("L007", "Histoire de la Tunisie", "Ahmed Kassab", "Histoire", 2005, 2),
    ]
    adherents_demo = [
        ("A001", "Ben Salah", "Sami", "sami@mail.com", True),
        ("A002", "Trabelsi", "Lina", "lina@mail.com", True),
        ("A003", "Gharbi", "Omar", "omar@mail.com", True),
        ("A004", "Jlassi", "Nour", "nour@mail.com", False),
    ]
 
    emprunts_demo = [
        ("E1", "L001", "A001", "2026-09-01", "2026-09-10"),
        ("E2", "L001", "A002", "2026-09-05", "2026-09-15"),
        ("E3", "L004", "A001", "2026-09-20", "2026-10-01"),
        ("E4", "L002", "A002", "2026-10-01", ""),
        ("E5", "L003", "A003", "2026-11-05", ""),
        ("E6", "L001", "A003", "2026-11-08", ""),
    ]
    return {
        "livres": {l[0]: dict(zip(CHAMPS_LIVRES, l)) for l in livres_demo},
        "adherents": {a[0]: dict(zip(CHAMPS_ADHERENTS, a)) for a in adherents_demo},
        "emprunts": [dict(zip(CHAMPS_EMPRUNTS, e)) for e in emprunts_demo],
    }


def reinitialiser_donnees(dossier):
    """Remplace les CSV par le jeu de démonstration."""
    sauvegarder_donnees(donnees_demo(), dossier)