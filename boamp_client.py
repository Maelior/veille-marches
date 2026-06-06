"""
boamp_client.py
---------------
Récupère les annonces de marchés publics depuis l'API ouverte BOAMP (DILA),
puis les filtre par mots-clés métier côté Python.

API utilisée : Opendatasoft Explore API v2.1
  https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records

Pas de clé API nécessaire pour la lecture. C'est gratuit et public.
"""

import time
import unicodedata
from datetime import date, timedelta

import requests

BASE_URL = (
    "https://boamp-datadila.opendatasoft.com"
    "/api/explore/v2.1/catalog/datasets/boamp/records"
)
PAGE_SIZE = 100          # maximum autorisé par l'API par page
MAX_PAGES = 20           # garde-fou : 20 x 100 = 2000 annonces max par exécution
TIMEOUT = 30             # secondes


def _normalise(texte):
    """Minuscule + suppression des accents, pour comparer sans se soucier de 'réseau' vs 'reseau'."""
    if not texte:
        return ""
    texte = texte.lower()
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return texte


def _appel_api(params, tentatives=3):
    """Appelle l'API avec quelques essais en cas de pépin réseau temporaire."""
    derniere_erreur = None
    for essai in range(1, tentatives + 1):
        try:
            r = requests.get(BASE_URL, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            derniere_erreur = e
            # on attend un peu plus longtemps à chaque essai (1s, 2s, 3s)
            time.sleep(essai)
    raise RuntimeError(f"Échec de l'appel BOAMP après {tentatives} essais : {derniere_erreur}")


def recupere_annonces(departements, lookback_days):
    """
    Récupère TOUTES les annonces parues depuis 'lookback_days' jours
    dans les départements demandés. Filtre les mots-clés se fait ensuite.

    Renvoie une liste de dictionnaires (champs bruts de l'API).
    """
    depuis = (date.today() - timedelta(days=lookback_days)).isoformat()

    # Clause de filtre côté serveur (langage ODSQL de Opendatasoft) :
    # - date de parution récente
    # - dans l'un des départements visés
    clause_dept = " or ".join(f'code_departement = "{d}"' for d in departements)
    where = f'dateparution >= "{depuis}" and ({clause_dept})'

    toutes = []
    for page in range(MAX_PAGES):
        params = {
            "where": where,
            "limit": PAGE_SIZE,
            "offset": page * PAGE_SIZE,
            "order_by": "dateparution desc",
        }
        data = _appel_api(params)
        lot = data.get("results", [])
        toutes.extend(lot)
        # si on a reçu moins qu'une page pleine, c'est qu'il n'y a plus rien après
        if len(lot) < PAGE_SIZE:
            break
    return toutes


def _est_avis_de_marche(annonce):
    """
    On veut les nouveaux appels d'offres, pas les résultats/attributions de marchés
    déjà passés. On exclut donc tout ce qui ressemble à un résultat.
    """
    libelle = _normalise(annonce.get("nature_categorise_libelle", ""))
    if "resultat" in libelle or "attribution" in libelle:
        return False
    return True


def filtre_par_mots_cles(annonces, mots_cles):
    """
    Garde uniquement les annonces dont l'objet OU les descripteurs contiennent
    au moins un des mots-clés métier. Insensible aux accents et à la casse.
    """
    mots_norm = [_normalise(m) for m in mots_cles]
    retenues = []
    for a in annonces:
        if not _est_avis_de_marche(a):
            continue
        # on concatène les champs textuels où le métier peut apparaître
        descripteur = a.get("descripteur_libelle", "")
        if isinstance(descripteur, list):
            descripteur = " ".join(str(x) for x in descripteur)
        texte = _normalise(
            " ".join(
                [
                    str(a.get("objet", "")),
                    str(descripteur),
                    str(a.get("nomacheteur", "")),
                ]
            )
        )
        if any(m in texte for m in mots_norm):
            retenues.append(a)
    return retenues


def lien_annonce(annonce):
    """Construit un lien cliquable vers l'annonce sur boamp.fr."""
    url = annonce.get("url_avis")
    if url:
        return url
    idweb = annonce.get("idweb", "")
    return f"https://www.boamp.fr/avis/detail/{idweb}"
