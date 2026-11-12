
import os
import tempfile
import unittest
from datetime import date

import library
import storage


def preparer_donnees():
    """Petit jeu de données neuf pour chaque test."""
    livres, adherents, emprunts = {}, {}, []
    library.ajouter_livre(livres, "L1", "Python Facile", "Marie Dupont", "Informatique", 2020, 2)
    library.ajouter_livre(livres, "L2", "Algorithmique", "Paul Martin", "Informatique", 2018, 1)
    library.ajouter_livre(livres, "L3", "Cosmos", "Carl Sagan", "Sciences", 1980, 3)
    library.ajouter_adherent(adherents, "A1", "Ben Salah", "Sami", "sami@mail.com")
    library.ajouter_adherent(adherents, "A2", "Trabelsi", "Lina", "lina@mail.com")
    return livres, adherents, emprunts


class TestCatalogue(unittest.TestCase):

    def test_ajout_valide_et_id_en_double(self):
        livres, _, _ = preparer_donnees()
        library.ajouter_livre(livres, "L9", "Nouveau", "Auteur", "Roman", 2022, 1)
        self.assertIn("L9", livres)
        with self.assertRaises(ValueError):
            library.ajouter_livre(livres, "L9", "Autre", "Auteur", "Roman", 2022, 1)

    def test_quantite_negative_refusee(self):
        livres, _, _ = preparer_donnees()
        with self.assertRaises(ValueError):
            library.ajouter_livre(livres, "L8", "Titre", "Auteur", "Roman", 2022, -1)

    def test_suppression_refusee_si_pret_en_cours(self):
        livres, adherents, emprunts = preparer_donnees()
        library.emprunter(livres, adherents, emprunts, "L1", "A1")
        with self.assertRaises(ValueError):
            library.supprimer_livre(livres, emprunts, "L1")
        library.supprimer_livre(livres, emprunts, "L3")   # pas de prêt : accepté
        self.assertNotIn("L3", livres)


class TestRecherche(unittest.TestCase):

    def test_recherche_casse_differente_et_partielle(self):
        livres, _, emprunts = preparer_donnees()
        resultats = library.rechercher(livres, emprunts, "titre", "pYtHoN", "titre")
        self.assertEqual([l["id"] for l in resultats], ["L1"])
        resultats = library.rechercher(livres, emprunts, "auteur", "dupo", "titre")
        self.assertEqual(len(resultats), 1)

    def test_recherche_sans_resultat(self):
        livres, _, emprunts = preparer_donnees()
        self.assertEqual(library.rechercher(livres, emprunts, "titre", "zzz", "titre"), [])


class TestEmpruntsRetours(unittest.TestCase):

    def test_emprunt_autorise(self):
        livres, adherents, emprunts = preparer_donnees()
        e = library.emprunter(livres, adherents, emprunts, "L1", "A1")
        self.assertEqual(len(emprunts), 1)
        self.assertEqual(e["date_retour"], "")

    def test_refus_stock_epuise(self):
        livres, adherents, emprunts = preparer_donnees()
        library.emprunter(livres, adherents, emprunts, "L2", "A1")   # L2 : 1 seul exemplaire
        with self.assertRaises(ValueError):
            library.emprunter(livres, adherents, emprunts, "L2", "A2")

    def test_refus_limite_de_prets(self):
        livres, adherents, emprunts = preparer_donnees()
        for i in range(library.LIMITE_PRETS):
            library.ajouter_livre(livres, f"X{i}", f"Livre {i}", "Auteur", "Roman", 2000, 1)
            library.emprunter(livres, adherents, emprunts, f"X{i}", "A1")
        with self.assertRaises(ValueError):
            library.emprunter(livres, adherents, emprunts, "L3", "A1")

    def test_adherent_desactive_refuse(self):
        livres, adherents, emprunts = preparer_donnees()
        library.desactiver_adherent(adherents, "A1")
        with self.assertRaises(ValueError):
            library.emprunter(livres, adherents, emprunts, "L1", "A1")

    def test_retour_valide_puis_second_retour_refuse(self):
        livres, adherents, emprunts = preparer_donnees()
        e = library.emprunter(livres, adherents, emprunts, "L1", "A1")
        library.retourner(emprunts, e["id"])
        self.assertNotEqual(emprunts[0]["date_retour"], "")
        with self.assertRaises(ValueError):
            library.retourner(emprunts, e["id"])

    def test_exemplaires_disponibles(self):
        livres, adherents, emprunts = preparer_donnees()
        self.assertEqual(library.exemplaires_disponibles(livres["L1"], emprunts), 2)
        e = library.emprunter(livres, adherents, emprunts, "L1", "A1")
        self.assertEqual(library.exemplaires_disponibles(livres["L1"], emprunts), 1)
        library.retourner(emprunts, e["id"])
        self.assertEqual(library.exemplaires_disponibles(livres["L1"], emprunts), 2)

    def test_detection_retard(self):
        livres, adherents, emprunts = preparer_donnees()
        library.emprunter(livres, adherents, emprunts, "L1", "A1", aujourdhui=date(2026, 10, 1))
        # 14 jours après : pas encore en retard, 15 jours : en retard
        self.assertEqual(library.emprunts_en_retard(emprunts, date(2026, 10, 15)), [])
        self.assertEqual(len(library.emprunts_en_retard(emprunts, date(2026, 10, 16))), 1)


class TestStatistiquesEtRecommandation(unittest.TestCase):

    def test_statistiques_coherentes(self):
        livres, adherents, emprunts = preparer_donnees()
        e1 = library.emprunter(livres, adherents, emprunts, "L1", "A1")
        library.emprunter(livres, adherents, emprunts, "L2", "A2")
        library.retourner(emprunts, e1["id"])
        stats = library.calculer_statistiques(livres, emprunts)
        self.assertEqual(stats["nb_ouvrages"], 3)
        self.assertEqual(stats["nb_exemplaires"], 6)
        self.assertEqual(stats["nb_disponibles"], 5)
        self.assertEqual(stats["nb_actifs"], 1)
        self.assertEqual(stats["nb_termines"], 1)
        self.assertEqual(stats["par_categorie"], {"Informatique": 2})
        # L2 n'a plus d'exemplaire : une alerte doit être présente
        self.assertTrue(any("Algorithmique" in a for a in stats["alertes"]))

    def test_recommandation_classement_et_egalite(self):
        livres, adherents, emprunts = preparer_donnees()
        library.ajouter_livre(livres, "L4", "Backend", "Auteur", "Informatique", 2021, 5)
        # L4 emprunté 2 fois puis rendu, L1 une fois, L2 zéro
        for _ in range(2):
            e = library.emprunter(livres, adherents, emprunts, "L4", "A1")
            library.retourner(emprunts, e["id"])
        e = library.emprunter(livres, adherents, emprunts, "L1", "A1")
        library.retourner(emprunts, e["id"])
        reco = library.recommander(livres, emprunts, "informatique")
        self.assertEqual([l["id"] for l in reco], ["L4", "L1", "L2"])

    def test_recommandation_egalite_par_titre(self):
        livres, _, emprunts = preparer_donnees()
        # aucun emprunt : égalité à 0, donc ordre alphabétique des titres
        reco = library.recommander(livres, emprunts, "Informatique")
        self.assertEqual([l["titre"] for l in reco], ["Algorithmique", "Python Facile"])

    def test_recommandation_aucun_disponible(self):
        livres, adherents, emprunts = preparer_donnees()
        library.emprunter(livres, adherents, emprunts, "L2", "A1")
        library.emprunter(livres, adherents, emprunts, "L1", "A1")
        library.emprunter(livres, adherents, emprunts, "L1", "A2")
        self.assertEqual(library.recommander(livres, emprunts, "Informatique"), [])


class TestStockage(unittest.TestCase):

    def test_fichiers_absents(self):
        with tempfile.TemporaryDirectory() as dossier:
            donnees, avertissements = storage.charger_donnees(dossier)
            self.assertEqual(donnees["livres"], {})
            self.assertEqual(donnees["emprunts"], [])
            self.assertTrue(avertissements)

    def test_donnees_mal_formees(self):
        with tempfile.TemporaryDirectory() as dossier:
            with open(os.path.join(dossier, "livres.csv"), "w", encoding="utf-8") as f:
                f.write("id,titre,auteur,categorie,annee,total\n")
                f.write("L1,Bon livre,Auteur,Roman,2000,2\n")
                f.write("L1,Doublon,Auteur,Roman,2000,2\n")        # id en double
                f.write("L2,Mauvaise année,Auteur,Roman,abc,2\n")  # non numérique
                f.write("L3,Négatif,Auteur,Roman,2000,-4\n")       # quantité négative
                f.write("L4,Ligne courte\n")                       # colonnes manquantes
            with open(os.path.join(dossier, "emprunts.csv"), "w", encoding="utf-8") as f:
                f.write("id,id_livre,id_adherent,date_emprunt,date_retour\n")
                f.write("E1,L1,A9,2026-10-01,\n")                  # adhérent inexistant
            donnees, avertissements = storage.charger_donnees(dossier)
            self.assertEqual(list(donnees["livres"]), ["L1"])
            self.assertEqual(donnees["emprunts"], [])
            self.assertGreaterEqual(len(avertissements), 4)

    def test_sauvegarde_puis_rechargement(self):
        with tempfile.TemporaryDirectory() as dossier:
            storage.reinitialiser_donnees(dossier)
            donnees, avertissements = storage.charger_donnees(dossier)
            self.assertEqual(avertissements, [])
            self.assertEqual(donnees, storage.donnees_demo())


if __name__ == "__main__":
    unittest.main()