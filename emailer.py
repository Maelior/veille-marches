"""
emailer.py
----------
Construit l'email HTML récapitulatif et l'envoie via Resend.
"""

import html
from datetime import date

import resend

import config
from boamp_client import lien_annonce

resend.api_key = config.RESEND_API_KEY


def _bloc_annonce(annonce, resume_texte):
    """Génère le HTML d'une annonce (titre + résumé + lien)."""
    objet = html.escape(annonce.get("objet", "Annonce sans objet"))
    acheteur = html.escape(annonce.get("nomacheteur", ""))
    dept = html.escape(str(annonce.get("code_departement", "")))
    lien = html.escape(lien_annonce(annonce))
    # on transforme les retours à la ligne du résumé en <br>
    resume_html = html.escape(resume_texte).replace("\n", "<br>")

    return f"""
    <div style="border:1px solid #e2e2e2; border-radius:8px; padding:16px; margin-bottom:16px;">
      <p style="margin:0 0 4px 0; font-weight:bold; font-size:15px; color:#1a1a1a;">{objet}</p>
      <p style="margin:0 0 10px 0; font-size:12px; color:#777;">{acheteur} — Dép. {dept}</p>
      <p style="margin:0 0 12px 0; font-size:14px; color:#333; line-height:1.5;">{resume_html}</p>
      <a href="{lien}" style="font-size:13px; color:#b8860b; text-decoration:none;">
        Voir l'annonce complète sur BOAMP &rarr;
      </a>
    </div>
    """


def construit_email(annonces_resumees):
    """
    annonces_resumees : liste de tuples (annonce, resume_texte)
    Renvoie (sujet, corps_html).
    """
    aujourdhui = date.today().strftime("%d/%m/%Y")
    nb = len(annonces_resumees)

    if nb == 0:
        sujet = f"Veille marchés publics — {aujourdhui} — aucune annonce"
        corps = f"""
        <div style="font-family:Arial,sans-serif; max-width:640px; margin:auto;">
          <h2 style="color:#1a1a1a;">Veille marchés publics</h2>
          <p style="color:#333;">Aucune nouvelle annonce correspondant à vos critères
          (terrassement / VRD / réseaux / voirie...) n'a été publiée.</p>
          <p style="font-size:12px; color:#999;">La veille fonctionne correctement —
          il n'y avait simplement rien aujourd'hui.</p>
        </div>
        """
        return sujet, corps

    sujet = f"Veille marchés publics — {aujourdhui} — {nb} annonce(s)"
    blocs = "".join(_bloc_annonce(a, r) for a, r in annonces_resumees)
    corps = f"""
    <div style="font-family:Arial,sans-serif; max-width:640px; margin:auto;">
      <h2 style="color:#1a1a1a;">Veille marchés publics — {aujourdhui}</h2>
      <p style="color:#333;">{nb} annonce(s) correspondant à vos critères&nbsp;:</p>
      {blocs}
      <p style="font-size:11px; color:#aaa; margin-top:24px;">
        Veille automatique réalisée par Maelior. Source : BOAMP (données ouvertes DILA).
      </p>
    </div>
    """
    return sujet, corps


def envoie(sujet, corps_html):
    """Envoie l'email. Renvoie l'ID Resend en cas de succès."""
    params = {
        "from": config.EMAIL_FROM,
        "to": config.EMAIL_TO,
        "subject": sujet,
        "html": corps_html,
    }
    reponse = resend.Emails.send(params)
    return reponse
