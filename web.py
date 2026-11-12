# web.py : interface web en bonus (HTML + Bootstrap)
# Réutilise library.py et storage.py sans les modifier.
# Lancer avec : python web.py puis ouvrir http://localhost:8000
# Bootstrap est chargé depuis un CDN, il faut donc une connexion internet.

import os
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import library
import storage

DOSSIER_DATA = "data"
PORT = 8000

# Bootstrap installé avec npm (npm install bootstrap) : on le sert depuis node_modules.
# S'il n'est pas trouvé, on retombe sur le CDN.
DOSSIER_BOOTSTRAP = os.path.join("node_modules", "bootstrap", "dist")
CSS_URL = ("/static/css/bootstrap.min.css"
           if os.path.exists(os.path.join(DOSSIER_BOOTSTRAP, "css", "bootstrap.min.css"))
           else "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css")
JS_URL = ("/static/js/bootstrap.bundle.min.js"
          if CSS_URL.startswith("/static")
          else "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js")
TYPES_FICHIERS = {".css": "text/css", ".js": "text/javascript", ".map": "application/json"}

donnees, avertissements = storage.charger_donnees(DOSSIER_DATA)

PAGES = [("/", "Tableau de bord"), ("/livres", "Catalogue"),
         ("/adherents", "Adhérents"), ("/emprunts", "Emprunts"),
         ("/recherche", "Recherche"), ("/recommandation", "Recommandation")]


def esc(valeur):
    return escape(str(valeur))


# ---------- Morceaux de HTML ----------

def mise_en_page(titre, corps, msg="", ok=True):
    liens = "".join(f'<li class="nav-item"><a class="nav-link" href="{u}">{t}</a></li>'
                    for u, t in PAGES)
    alerte = ""
    if msg:
        couleur = "success" if ok else "danger"
        alerte = f'<div class="alert alert-{couleur}">{esc(msg)}</div>'
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titre)} - Bibliothèque</title>
<link href="{CSS_URL}" rel="stylesheet">
</head><body class="bg-light">
<nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4"><div class="container">
<a class="navbar-brand" href="/">Bibliothèque</a>
<ul class="navbar-nav">{liens}</ul></div></nav>
<div class="container pb-5"><h1 class="h3 mb-3">{esc(titre)}</h1>{alerte}{corps}</div>
<script src="{JS_URL}"></script>
</body></html>"""


def tableau(entetes, lignes):
    if not lignes:
        return '<p class="text-muted">Aucun résultat.</p>'
    tete = "".join(f"<th>{e}</th>" for e in entetes)
    corps = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in l) + "</tr>" for l in lignes)
    return (f'<div class="table-responsive"><table class="table table-striped bg-white">'
            f"<thead><tr>{tete}</tr></thead><tbody>{corps}</tbody></table></div>")


def champ(nom, label, type_="text", col="col-md-2"):
    return (f'<div class="{col}"><label class="form-label">{label}</label>'
            f'<input class="form-control" name="{nom}" type="{type_}" required></div>')


def formulaire(action, contenu, bouton, style="primary"):
    return (f'<form method="post" action="{action}" class="row g-2 align-items-end mb-4">'
            f'{contenu}<div class="col-auto"><button class="btn btn-{style}">{bouton}</button>'
            f"</div></form>")


def bouton_post(action, nom, valeur, texte, style):
    return (f'<form method="post" action="{action}" class="d-inline">'
            f'<input type="hidden" name="{nom}" value="{esc(valeur)}">'
            f'<button class="btn btn-sm btn-outline-{style}">{texte}</button></form>')


def options(paires):
    return "".join(f'<option value="{esc(v)}">{esc(t)}</option>' for v, t in paires)


def lignes_livres(livres):
    return [[esc(l["id"]), esc(l["titre"]), esc(l["auteur"]), esc(l["categorie"]),
             esc(l["annee"]),
             f'{library.exemplaires_disponibles(l, donnees["emprunts"])} / {l["total"]}']
            for l in livres]


# ---------- Pages ----------

def page_accueil():
    s = library.calculer_statistiques(donnees["livres"], donnees["emprunts"])
    cartes = [("Ouvrages", s["nb_ouvrages"], "primary"),
              ("Exemplaires disponibles", f'{s["nb_disponibles"]} / {s["nb_exemplaires"]}', "success"),
              ("Prêts actifs", s["nb_actifs"], "info"),
              ("Retards", s["nb_retards"], "danger"),
              ("Prêts terminés", s["nb_termines"], "secondary")]
    html_cartes = "".join(
        f'<div class="col-md"><div class="card text-bg-{c} text-center"><div class="card-body">'
        f'<div class="fs-3">{esc(v)}</div>{t}</div></div></div>' for t, v, c in cartes)
    alertes = "".join(f'<div class="alert alert-warning py-2">{esc(a)}</div>' for a in s["alertes"])
    top = tableau(["Ouvrage", "Emprunts"], [[esc(t), n] for t, n in s["top5"]])
    cats = tableau(["Catégorie", "Emprunts"], [[esc(c), n] for c, n in s["par_categorie"].items()])
    reset = bouton_post("/reinitialiser", "x", "1", "Réinitialiser (données de démo)", "danger")
    return ("Tableau de bord",
            f'<div class="row g-3 mb-4">{html_cartes}</div>{alertes}'
            f'<div class="row"><div class="col-md-6"><h2 class="h5">Top 5</h2>{top}</div>'
            f'<div class="col-md-6"><h2 class="h5">Par catégorie</h2>{cats}</div></div>{reset}')


def page_livres():
    form = formulaire("/livres/ajouter",
                      champ("id", "Identifiant") + champ("titre", "Titre", col="col-md-3")
                      + champ("auteur", "Auteur") + champ("categorie", "Catégorie")
                      + champ("annee", "Année", "number", "col-md-1")
                      + champ("total", "Exemplaires", "number", "col-md-1"), "Ajouter")
    lignes = lignes_livres(donnees["livres"].values())
    for ligne, l in zip(lignes, donnees["livres"].values()):
        ligne.append(bouton_post("/livres/supprimer", "id", l["id"], "Supprimer", "danger"))
    return "Catalogue", form + tableau(
        ["ID", "Titre", "Auteur", "Catégorie", "Année", "Dispo", ""], lignes)


def page_adherents():
    form = formulaire("/adherents/ajouter",
                      champ("id", "Identifiant") + champ("nom", "Nom") + champ("prenom", "Prénom")
                      + champ("contact", "Contact", col="col-md-3"), "Ajouter")
    lignes = []
    for a in donnees["adherents"].values():
        etat = ('<span class="badge text-bg-success">Actif</span>' if a["actif"]
                else '<span class="badge text-bg-secondary">Désactivé</span>')
        action = bouton_post("/adherents/desactiver", "id", a["id"], "Désactiver", "warning") if a["actif"] else ""
        lignes.append([esc(a["id"]), esc(a["nom"]), esc(a["prenom"]), esc(a["contact"]), etat, action])
    return "Adhérents", form + tableau(["ID", "Nom", "Prénom", "Contact", "État", ""], lignes)


def page_emprunts():
    actifs = [(a["id"], f'{a["prenom"]} {a["nom"]}') for a in donnees["adherents"].values() if a["actif"]]
    livres = [(l["id"], f'{l["titre"]} ({library.exemplaires_disponibles(l, donnees["emprunts"])} dispo)')
              for l in donnees["livres"].values()]
    form = formulaire(
        "/emprunter",
        f'<div class="col-md-3"><label class="form-label">Adhérent</label>'
        f'<select class="form-select" name="id_adherent">{options(actifs)}</select></div>'
        f'<div class="col-md-4"><label class="form-label">Ouvrage</label>'
        f'<select class="form-select" name="id_livre">{options(livres)}</select></div>',
        "Emprunter")
    lignes = []
    for e in reversed(donnees["emprunts"]):
        livre = donnees["livres"].get(e["id_livre"], {}).get("titre", e["id_livre"])
        adh = donnees["adherents"].get(e["id_adherent"])
        nom = f'{adh["prenom"]} {adh["nom"]}' if adh else e["id_adherent"]
        if not library.est_actif(e):
            etat, action = '<span class="badge text-bg-secondary">Rendu</span>', ""
        else:
            retard = library.est_en_retard(e)
            etat = ('<span class="badge text-bg-danger">En retard</span>' if retard
                    else '<span class="badge text-bg-primary">En cours</span>')
            action = bouton_post("/retourner", "id", e["id"], "Retourner", "success")
        lignes.append([esc(e["id"]), esc(livre), esc(nom), esc(e["date_emprunt"]),
                       esc(e["date_retour"]), etat, action])
    return "Emprunts et retours", form + tableau(
        ["Op.", "Ouvrage", "Adhérent", "Emprunté le", "Rendu le", "État", ""], lignes)


def page_recherche(p):
    critere = p.get("critere", ["titre"])[0]
    texte = p.get("q", [""])[0]
    tri = p.get("tri", ["titre"])[0]

    def liste(choix, actuel):
        return "".join(f'<option value="{v}"{" selected" if v == actuel else ""}>{t}</option>'
                       for v, t in choix)
    form = (f'<form method="get" class="row g-2 align-items-end mb-4">'
            f'<div class="col-md-2"><label class="form-label">Critère</label><select class="form-select" name="critere">'
            + liste([("titre", "Titre"), ("auteur", "Auteur"), ("categorie", "Catégorie"), ("id", "Identifiant")], critere)
            + f'</select></div><div class="col-md-4"><label class="form-label">Texte</label>'
            f'<input class="form-control" name="q" value="{esc(texte)}"></div>'
            f'<div class="col-md-3"><label class="form-label">Tri</label><select class="form-select" name="tri">'
            + liste([("titre", "Titre"), ("auteur", "Auteur"), ("emprunts", "Nombre d\'emprunts")], tri)
            + '</select></div><div class="col-auto"><button class="btn btn-primary">Rechercher</button></div></form>')
    resultat = ""
    if "q" in p:
        trouves = library.rechercher(donnees["livres"], donnees["emprunts"], critere, texte, tri)
        resultat = tableau(["ID", "Titre", "Auteur", "Catégorie", "Année", "Dispo"], lignes_livres(trouves))
    return "Recherche", form + resultat


def page_recommandation(p):
    categories = sorted({l["categorie"] for l in donnees["livres"].values()})
    form = (f'<form method="get" class="row g-2 align-items-end mb-4"><div class="col-md-3">'
            f'<label class="form-label">Catégorie</label><select class="form-select" name="categorie">'
            f'{options([(c, c) for c in categories])}</select></div>'
            f'<div class="col-auto"><button class="btn btn-primary">Recommander</button></div></form>')
    resultat = ""
    if "categorie" in p:
        reco = library.recommander(donnees["livres"], donnees["emprunts"], p["categorie"][0])
        if reco:
            resultat = tableau(["ID", "Titre", "Auteur", "Catégorie", "Année", "Dispo"], lignes_livres(reco))
        else:
            resultat = '<div class="alert alert-info">Aucun ouvrage disponible dans cette catégorie.</div>'
    return "Recommandation", form + resultat


# ---------- Actions (POST) ----------

def reinitialiser():
    storage.reinitialiser_donnees(DOSSIER_DATA)
    nouvelles, _ = storage.charger_donnees(DOSSIER_DATA)
    donnees.update(nouvelles)


ACTIONS = {
    "/livres/ajouter": ("/livres", "Ouvrage ajouté.", lambda f: library.ajouter_livre(
        donnees["livres"], f["id"], f["titre"], f["auteur"], f["categorie"],
        int(f["annee"]), int(f["total"]))),
    "/livres/supprimer": ("/livres", "Ouvrage supprimé.", lambda f: library.supprimer_livre(
        donnees["livres"], donnees["emprunts"], f["id"])),
    "/adherents/ajouter": ("/adherents", "Adhérent ajouté.", lambda f: library.ajouter_adherent(
        donnees["adherents"], f["id"], f["nom"], f["prenom"], f["contact"])),
    "/adherents/desactiver": ("/adherents", "Adhérent désactivé.", lambda f: library.desactiver_adherent(
        donnees["adherents"], f["id"])),
    "/emprunter": ("/emprunts", "Emprunt enregistré.", lambda f: library.emprunter(
        donnees["livres"], donnees["adherents"], donnees["emprunts"], f["id_livre"], f["id_adherent"])),
    "/retourner": ("/emprunts", "Retour enregistré.", lambda f: library.retourner(
        donnees["emprunts"], f["id"])),
    "/reinitialiser": ("/", "Données de démonstration rechargées.", lambda f: reinitialiser()),
}


class Serveur(BaseHTTPRequestHandler):

    def repondre(self, titre, corps, msg="", ok=True):
        contenu = mise_en_page(titre, corps, msg, ok).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(contenu)))
        self.end_headers()
        self.wfile.write(contenu)

    def envoyer_statique(self, chemin):
        # on ne sert que des fichiers css/js de dist, sans sortir du dossier
        relatif = os.path.normpath(chemin[len("/static/"):])
        complet = os.path.join(DOSSIER_BOOTSTRAP, relatif)
        extension = os.path.splitext(complet)[1]
        if relatif.startswith("..") or extension not in TYPES_FICHIERS or not os.path.isfile(complet):
            self.send_error(404)
            return
        with open(complet, "rb") as f:
            contenu = f.read()
        self.send_response(200)
        self.send_header("Content-Type", TYPES_FICHIERS[extension])
        self.send_header("Content-Length", str(len(contenu)))
        self.end_headers()
        self.wfile.write(contenu)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path.startswith("/static/"):
            self.envoyer_statique(url.path)
            return
        p = parse_qs(url.query)
        msg = p.get("msg", [""])[0]
        ok = p.get("ok", ["1"])[0] == "1"
        pages = {"/": page_accueil, "/livres": page_livres, "/adherents": page_adherents,
                 "/emprunts": page_emprunts, "/recherche": lambda: page_recherche(p),
                 "/recommandation": lambda: page_recommandation(p)}
        if url.path not in pages:
            self.send_error(404)
            return
        titre, corps = pages[url.path]()
        if url.path == "/" and avertissements and not msg:
            msg, ok = "Chargement : " + " | ".join(avertissements[:3]), False
        self.repondre(titre, corps, msg, ok)

    def do_POST(self):
        route = urlparse(self.path).path
        if route not in ACTIONS:
            self.send_error(404)
            return
        longueur = int(self.headers.get("Content-Length", 0))
        form = {k: v[0].strip() for k, v in
                parse_qs(self.rfile.read(longueur).decode("utf-8")).items()}
        retour, succes, action = ACTIONS[route]
        try:
            action(form)
            storage.sauvegarder_donnees(donnees, DOSSIER_DATA)
            resultat = {"msg": succes, "ok": "1"}
        except (ValueError, KeyError) as erreur:
            resultat = {"msg": f"Erreur : {erreur}", "ok": "0"}
        self.send_response(303)
        self.send_header("Location", retour + "?" + urlencode(resultat))
        self.end_headers()


if __name__ == "__main__":
    print("Bootstrap :", "local (node_modules)" if CSS_URL.startswith("/static") else "CDN")
    print(f"Serveur lancé sur http://localhost:{PORT} (Ctrl+C pour arrêter)")
    HTTPServer(("localhost", PORT), Serveur).serve_forever()