"""
main.py
-------
Point d'entrée. C'est CE fichier que le cron exécute chaque matin à 7h.

Déroulé :
  1. Vérifie la configuration
  2. Récupère les annonces BOAMP (veille, départements visés)
  3. Filtre par mots-clés métier
  4. Résume chaque annonce avec Claude
  5. Construit et envoie l'email récapitulatif
"""

import sys

import config
from boamp_client import recupere_annonces, filtre_par_mots_cles
from summarizer import resume
from emailer import construit_email, envoie


def _bonne_heure():
    """
    Renvoie True s'il est l'heure de tourner.
    Si ENFORCE_HOUR est faux (lancement manuel/local), on tourne toujours.
    Sinon, on ne tourne que si l'heure locale de Paris == TARGET_HOUR.
    """
    if not config.ENFORCE_HOUR:
        return True
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        heure_paris = datetime.now(ZoneInfo("Europe/Paris")).hour
        return heure_paris == config.TARGET_HOUR
    except Exception:
        # en cas de souci avec les fuseaux, on préfère tourner que rater l'envoi
        return True


def main():
    print("=== Veille marchés publics — démarrage ===")
    if not _bonne_heure():
        print(f"Ce n'est pas {config.TARGET_HOUR}h à Paris : on ne fait rien cette fois.")
        return
    config.verifie_config()

    print(f"Départements : {config.DEPARTEMENTS} | fenêtre : {config.LOOKBACK_DAYS} jour(s)")
    brutes = recupere_annonces(config.DEPARTEMENTS, config.LOOKBACK_DAYS)
    print(f"{len(brutes)} annonce(s) récupérée(s) sur la période/zone.")

    retenues = filtre_par_mots_cles(brutes, config.MOTS_CLES)
    print(f"{len(retenues)} annonce(s) retenue(s) après filtre mots-clés.")

    resumees = []
    for i, annonce in enumerate(retenues, 1):
        print(f"  Résumé {i}/{len(retenues)}...")
        resumees.append((annonce, resume(annonce)))

    if not resumees and not config.SEND_IF_EMPTY:
        print("Aucune annonce et SEND_IF_EMPTY=false : pas d'email envoyé.")
        return

    sujet, corps = construit_email(resumees)
    reponse = envoie(sujet, corps)
    print(f"Email envoyé à {config.EMAIL_TO}. Réponse Resend : {reponse}")
    print("=== Terminé ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # En cas d'erreur fatale, on logue clairement et on sort en code 1
        # (utile pour que GitHub Actions/Railway marquent l'exécution en échec).
        print(f"ERREUR FATALE : {e}", file=sys.stderr)
        sys.exit(1)
