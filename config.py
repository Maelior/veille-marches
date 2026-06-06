"""
config.py
---------
Toute la configuration de l'agent passe par des variables d'environnement.
On ne met JAMAIS de clé API en dur dans le code (sécurité + déploiement propre).

En local : ces variables sont lues depuis le fichier .env (voir charge_env() ci-dessous).
En production (GitHub Actions / Railway) : elles sont définies dans l'interface de l'hébergeur.
"""

import os


def charge_env():
    """
    Charge le fichier .env s'il existe (utile uniquement en local).
    En production, les variables sont déjà injectées par l'hébergeur, donc
    ce fichier n'existe pas et on ne fait rien : c'est normal.
    """
    chemin = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(chemin):
        return
    with open(chemin, "r", encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, valeur = ligne.split("=", 1)
            # on ne remplace pas une variable déjà définie par l'environnement
            os.environ.setdefault(cle.strip(), valeur.strip().strip('"').strip("'"))


charge_env()


def _liste(nom, defaut):
    """Lit une variable du type 'a,b,c' et renvoie ['a', 'b', 'c']."""
    brut = os.environ.get(nom, defaut)
    return [x.strip() for x in brut.split(",") if x.strip()]


# --- Clés API (obligatoires) ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

# --- Email ---
# Expéditeur : doit être une adresse d'un domaine vérifié chez Resend.
# Pour tester rapidement, Resend autorise "onboarding@resend.dev".
EMAIL_FROM = os.environ.get("EMAIL_FROM", "Veille Maelior <onboarding@resend.dev>")
# Destinataire(s) : l'email du client (plusieurs séparés par des virgules).
EMAIL_TO = _liste("EMAIL_TO", "")
# Envoyer un email même s'il n'y a aucune annonce ? (pour prouver que ça tourne)
SEND_IF_EMPTY = os.environ.get("SEND_IF_EMPTY", "true").lower() == "true"

# --- Filtres métier ---
DEPARTEMENTS = _liste("DEPARTEMENTS", "59,62")
MOTS_CLES = _liste(
    "MOTS_CLES",
    "terrassement,VRD,réseaux,réseau,voirie,voiries,fondation,fondations,"
    "gros oeuvre,gros œuvre,assainissement,canalisation,canalisations,"
    "génie civil,enrobé,enrobés,tranchée,remblai,déblai",
)
# Nombre de jours à remonter (1 = uniquement la veille).
# Mettre 3 ou 4 le lundi peut être utile pour rattraper le week-end (voir README).
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "1"))

# --- Modèle Claude ---
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# --- Garde-fou horaire (pour GitHub Actions qui tourne en UTC) ---
# GitHub Actions ne connaît que l'heure UTC, et l'heure de Paris change avec
# l'heure d'été/hiver. On lance donc le job à 5h ET 6h UTC, mais le script ne
# s'exécute réellement que si l'heure locale de Paris == TARGET_HOUR.
# Résultat : exactement un envoi par jour à 7h, toute l'année.
TARGET_HOUR = int(os.environ.get("TARGET_HOUR", "7"))
# Mettre "true" uniquement pour les lancements planifiés. Pour un lancement
# manuel (test), on laisse "false" pour que ça s'exécute tout de suite.
ENFORCE_HOUR = os.environ.get("ENFORCE_HOUR", "false").lower() == "true"


def verifie_config():
    """Vérifie que le minimum vital est présent. Lève une erreur claire sinon."""
    manquant = []
    if not ANTHROPIC_API_KEY:
        manquant.append("ANTHROPIC_API_KEY")
    if not RESEND_API_KEY:
        manquant.append("RESEND_API_KEY")
    if not EMAIL_TO:
        manquant.append("EMAIL_TO")
    if manquant:
        raise RuntimeError(
            "Variables d'environnement manquantes : " + ", ".join(manquant)
            + ". Renseigne-les dans .env (local) ou chez ton hébergeur (production)."
        )
