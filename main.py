
import library
import storage

DOSSIER_DATA = "data"


def lire_entier(message):
    """Redemande la saisie tant que ce n'est pas un entier."""
    while True:
        try:
            return int(input(message).strip())
        except ValueError:
            print("Erreur : entrez un nombre entier.")


def afficher_livres(livres, emprunts):
    """Affiche une liste de livres avec les exemplaires disponibles."""
    if not livres:
        print("Aucun résultat.")
        return
    for livre in livres:
        dispo = library.exemplaires_disponibles(livre, emprunts)
        print(f"[{livre['id']}] {livre['titre']} - {livre['auteur']} "
              f"({livre['categorie']}, {livre['annee']}) "
              f"dispo : {dispo}/{livre['total']}")



def menu_ajouter_livre(donnees):
    id_livre = input("Identifiant : ").strip()
    titre = input("Titre : ").strip()
    auteur = input("Auteur : ").strip()
    categorie = input("Catégorie : ").strip()
    annee = lire_entier("Année de publication : ")
    total = lire_entier("Nombre d'exemplaires : ")
    library.ajouter_livre(donnees["livres"], id_livre, titre, auteur,
                          categorie, annee, total)
    print("Ouvrage ajouté.")


def menu_modifier_livre(donnees):
    id_livre = input("Identifiant de l'ouvrage : ").strip()
    print("Laissez vide pour garder la valeur actuelle.")
    champs = {}
    for cle in ("titre", "auteur", "categorie"):
        valeur = input(f"Nouveau {cle} : ").strip()
        if valeur:
            champs[cle] = valeur
    annee = input("Nouvelle année : ").strip()
    if annee:
        champs["annee"] = int(annee)
    total = input("Nouveau nombre d'exemplaires : ").strip()
    if total:
        champs["total"] = int(total)
    library.modifier_livre(donnees["livres"], donnees["emprunts"],
                           id_livre, champs)
    print("Ouvrage modifié.")


def menu_supprimer_livre(donnees):
    id_livre = input("Identifiant de l'ouvrage : ").strip()
    library.supprimer_livre(donnees["livres"], donnees["emprunts"], id_livre)
    print("Ouvrage supprimé.")


def menu_afficher_catalogue(donnees):
    afficher_livres(list(donnees["livres"].values()), donnees["emprunts"])



def menu_ajouter_adherent(donnees):
    id_adh = input("Identifiant : ").strip()
    nom = input("Nom : ").strip()
    prenom = input("Prénom : ").strip()
    contact = input("Contact : ").strip()
    library.ajouter_adherent(donnees["adherents"], id_adh, nom, prenom, contact)
    print("Adhérent ajouté.")


def menu_modifier_adherent(donnees):
    id_adh = input("Identifiant de l'adhérent : ").strip()
    print("Laissez vide pour garder la valeur actuelle.")
    champs = {}
    for cle in ("nom", "prenom", "contact"):
        valeur = input(f"Nouveau {cle} : ").strip()
        if valeur:
            champs[cle] = valeur
    library.modifier_adherent(donnees["adherents"], id_adh, champs)
    print("Adhérent modifié.")


def menu_desactiver_adherent(donnees):
    id_adh = input("Identifiant de l'adhérent : ").strip()
    library.desactiver_adherent(donnees["adherents"], id_adh)
    print("Adhérent désactivé.")


def menu_afficher_adherents(donnees):
    if not donnees["adherents"]:
        print("Aucun adhérent.")
        return
    for adh in donnees["adherents"].values():
        etat = "actif" if adh["actif"] else "désactivé"
        print(f"[{adh['id']}] {adh['prenom']} {adh['nom']} - "
              f"{adh['contact']} ({etat})")



def menu_emprunter(donnees):
    id_adh = input("Identifiant de l'adhérent : ").strip()
    id_livre = input("Identifiant de l'ouvrage : ").strip()
    emprunt = library.emprunter(donnees["livres"], donnees["adherents"],
                                donnees["emprunts"], id_livre, id_adh)
    print(f"Emprunt enregistré (opération {emprunt['id']}).")


def menu_retourner(donnees):
    id_emprunt = input("Identifiant de l'opération : ").strip()
    library.retourner(donnees["emprunts"], id_emprunt)
    print("Retour enregistré.")


def menu_retards(donnees):
    retards = library.emprunts_en_retard(donnees["emprunts"])
    if not retards:
        print("Aucun prêt en retard.")
        return
    for e in retards:
        print(f"Opération {e['id']} : livre {e['id_livre']}, "
              f"adhérent {e['id_adherent']}, emprunté le {e['date_emprunt']}")



def menu_recherche(donnees):
    print("Critère : 1) titre  2) auteur  3) catégorie  4) identifiant")
    critere = {1: "titre", 2: "auteur", 3: "categorie", 4: "id"}.get(
        lire_entier("Choix : "))
    if critere is None:
        print("Critère invalide.")
        return
    texte = input("Texte recherché : ").strip()
    print("Tri : 1) titre  2) auteur  3) nombre d'emprunts")
    tri = {1: "titre", 2: "auteur", 3: "emprunts"}.get(lire_entier("Choix : "))
    if tri is None:
        print("Tri invalide.")
        return
    resultats = library.rechercher(donnees["livres"], donnees["emprunts"],
                                   critere, texte, tri)
    if not resultats:
        print("Aucun ouvrage ne correspond à la recherche.")
    else:
        afficher_livres(resultats, donnees["emprunts"])


def menu_recommandation(donnees):
    categorie = input("Catégorie : ").strip()
    reco = library.recommander(donnees["livres"], donnees["emprunts"], categorie)
    if not reco:
        print("Aucun ouvrage disponible dans cette catégorie.")
    else:
        print("Ouvrages recommandés :")
        afficher_livres(reco, donnees["emprunts"])



def menu_statistiques(donnees):
    stats = library.calculer_statistiques(donnees["livres"], donnees["emprunts"])
    print("----- Tableau de bord -----")
    print(f"Ouvrages : {stats['nb_ouvrages']}")
    print(f"Exemplaires : {stats['nb_exemplaires']} "
          f"(disponibles : {stats['nb_disponibles']})")
    print(f"Prêts actifs : {stats['nb_actifs']} | "
          f"retards : {stats['nb_retards']} | "
          f"terminés : {stats['nb_termines']}")
    print("Top 5 des ouvrages les plus empruntés :")
    for titre, nb in stats["top5"]:
        print(f"  - {titre} ({nb})")
    print("Emprunts par catégorie :")
    for cat, nb in stats["par_categorie"].items():
        print(f"  - {cat} : {nb}")
    for alerte in stats["alertes"]:
        print("ALERTE :", alerte)



def menu_reinitialiser(donnees):
    confirmation = input("Remplacer toutes les données par la démo ? (o/n) : ")
    if confirmation.strip().lower() == "o":
        storage.reinitialiser_donnees(DOSSIER_DATA)
        nouvelles, _ = storage.charger_donnees(DOSSIER_DATA)
        donnees.update(nouvelles)
        print("Données de démonstration rechargées.")


MENU = {
    "1": ("Ajouter un ouvrage", menu_ajouter_livre, True),
    "2": ("Modifier un ouvrage", menu_modifier_livre, True),
    "3": ("Supprimer un ouvrage", menu_supprimer_livre, True),
    "4": ("Afficher le catalogue", menu_afficher_catalogue, False),
    "5": ("Ajouter un adhérent", menu_ajouter_adherent, True),
    "6": ("Modifier un adhérent", menu_modifier_adherent, True),
    "7": ("Désactiver un adhérent", menu_desactiver_adherent, True),
    "8": ("Afficher les adhérents", menu_afficher_adherents, False),
    "9": ("Enregistrer un emprunt", menu_emprunter, True),
    "10": ("Enregistrer un retour", menu_retourner, True),
    "11": ("Prêts en retard", menu_retards, False),
    "12": ("Rechercher un ouvrage", menu_recherche, False),
    "13": ("Recommandation par catégorie", menu_recommandation, False),
    "14": ("Tableau de bord", menu_statistiques, False),
    "15": ("Réinitialiser les données (démo)", menu_reinitialiser, False),
    "0": ("Quitter", None, False),
}


def afficher_menu():
    print("\n===== BIBLIOTHÈQUE =====")
    for cle, (texte, _, _) in MENU.items():
        print(f"{cle}. {texte}")


def main():
    donnees, avertissements = storage.charger_donnees(DOSSIER_DATA)
    for message in avertissements:
        print("Attention :", message)

    while True:
        afficher_menu()
        choix = input("Votre choix : ").strip()
        if choix == "0":
            storage.sauvegarder_donnees(donnees, DOSSIER_DATA)
            print("Au revoir.")
            break
        if choix not in MENU:
            print("Choix invalide.")
            continue

        _, action, modifie = MENU[choix]
        try:
            action(donnees)
            if modifie:
                storage.sauvegarder_donnees(donnees, DOSSIER_DATA)
        except ValueError as erreur:
            # les règles métier lèvent des ValueError avec un message clair
            print("Erreur :", erreur)


if __name__ == "__main__":
    main()