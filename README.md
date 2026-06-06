# Veille marchés publics — Maelior

Agent qui, chaque matin à 7h, récupère les nouveaux appels d'offres publics
(BOAMP) dans les départements 59 et 62, filtre par mots-clés travaux publics,
résume chaque annonce avec Claude, et envoie un email récapitulatif.

## Fichiers

| Fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée (exécuté par le cron) |
| `config.py` | Configuration via variables d'environnement |
| `boamp_client.py` | Récupération + filtrage des annonces BOAMP |
| `summarizer.py` | Résumé de chaque annonce via l'API Claude |
| `emailer.py` | Construction + envoi de l'email (Resend) |
| `.env.example` | Modèle de configuration locale |
| `.github/workflows/veille.yml` | Cron quotidien gratuit (GitHub Actions) |
| `railway.json` | Config de déploiement Railway |

## Lancer en local (test)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # puis remplir .env
python main.py
```

## Variables d'environnement

Voir `.env.example`. Obligatoires : `ANTHROPIC_API_KEY`, `RESEND_API_KEY`, `EMAIL_TO`.

## Déploiement

- **GitHub Actions (recommandé, gratuit)** : pousser le repo, ajouter les secrets
  dans Settings → Secrets and variables → Actions. Le cron tourne tout seul.
- **Railway** : nouveau projet depuis le repo, ajouter les variables, définir un
  Cron Schedule `0 5,6 * * *` (UTC) avec `ENFORCE_HOUR=true`.
