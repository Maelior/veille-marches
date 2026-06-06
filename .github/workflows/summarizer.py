"""
summarizer.py
-------------
Pour chaque annonce retenue, on demande à Claude un résumé clair en français
(5 lignes max) : quel chantier, où, date limite de réponse, budget si dispo.
"""

import anthropic

import config

# On crée un client Anthropic réutilisable.
_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

SYSTEME = (
    "Tu es un assistant pour une entreprise de terrassement et travaux publics "
    "du Nord de la France. On te donne une annonce de marché public brute. "
    "Tu produis un résumé en français clair et professionnel, 5 lignes maximum, "
    "destiné au dirigeant qui doit décider en 10 secondes si le chantier l'intéresse. "
    "Structure le résumé ainsi, sans fioritures :\n"
    "• Chantier : (nature des travaux en une phrase)\n"
    "• Lieu : (ville / département)\n"
    "• Date limite de réponse : (date, ou 'non précisée')\n"
    "• Budget estimé : (montant si présent dans le texte, sinon 'non précisé')\n"
    "Ne réponds QUE le résumé, sans introduction ni commentaire."
)


def _texte_annonce(annonce):
    """Met en forme les champs utiles de l'annonce pour les envoyer à Claude."""
    descripteur = annonce.get("descripteur_libelle", "")
    if isinstance(descripteur, list):
        descripteur = ", ".join(str(x) for x in descripteur)
    champs = {
        "Objet": annonce.get("objet", ""),
        "Acheteur": annonce.get("nomacheteur", ""),
        "Département": annonce.get("code_departement", ""),
        "Date de parution": annonce.get("dateparution", ""),
        "Date limite de réponse": annonce.get("datelimitereponse", ""),
        "Catégories": descripteur,
        "Type de marché": annonce.get("famille_libelle", ""),
    }
    return "\n".join(f"{k} : {v}" for k, v in champs.items() if v)


def resume(annonce):
    """Renvoie le résumé texte d'une annonce. En cas d'erreur, renvoie un repli lisible."""
    contenu = _texte_annonce(annonce)
    try:
        reponse = _client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=400,
            temperature=0.2,
            system=SYSTEME,
            messages=[{"role": "user", "content": contenu}],
        )
        # la réponse peut contenir plusieurs blocs ; on garde le texte
        morceaux = [b.text for b in reponse.content if getattr(b, "type", "") == "text"]
        return "\n".join(morceaux).strip()
    except Exception as e:
        # si Claude échoue sur une annonce, on n'arrête pas tout le batch :
        # on renvoie au moins l'objet brut pour que le client ne perde rien.
        objet = annonce.get("objet", "(objet indisponible)")
        return f"[Résumé automatique indisponible - {e}]\nObjet brut : {objet}"
