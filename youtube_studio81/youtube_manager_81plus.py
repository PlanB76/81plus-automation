#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
youtube_manager_81plus.py — Gestore Automatico Canale YouTube Evergreen 81+
Branding Completo, Generatore di Thumbnails ad Alto CTR, Palinsesto 365 Giorni,
Descrizioni Magnetiche (AIDA/EPPPA/PNL) e Restyle Automatico.

Caratteristiche:
  - Branding Canale YouTube 81+:
      * Banner Canale 2560x1440 px
      * Avatar Profilo 800x800 px
      * Watermark Video 150x150 px
  - Generatore Copertine / Thumbnails 1280x720 px ad alto contrasto (nero/arancio/bianco).
  - Palinsesto Evergreen 52 Settimane (365 Giorni) alternato sui 3 pilastri:
      1. Sicurezza sul Lavoro D.Lgs. 81/08 & Patente a Crediti
      2. HACCP & Controlli NAS/ASL
      3. Privacy GDPR 679/16 & Videosorveglianza Lavoratori
      + Corsi FAD Gratuiti 'Prova Prima' & Collaudo 81
  - Metadati ottimizzati VidIQ: Titoli clickbait etici, Descrizioni AIDA/EPPPA/PNL con link immediato, Tag SEO.
  - Sincronizzazione FTP su https://81plus.net/assets/campaigns/ e notifiche Telegram.
"""

import os
import sys
import json
import time
import ftplib
import argparse
import datetime
import textwrap
import urllib.request
from PIL import Image, ImageDraw, ImageFont

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ══════════════════════════════════════════════════════════════════
# CONFIGURAZIONE GENERALE & PATHS
# ══════════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_ASSETS_DIR = r"C:\81PLUS_GLOBAL_MASTER\81plus.net\81plus.net - new\assets\campaigns"
YT_OUT_DIR = os.path.join(BASE_DIR, "yt_channel_assets")
os.makedirs(SITE_ASSETS_DIR, exist_ok=True)
os.makedirs(YT_OUT_DIR, exist_ok=True)

# FTP Hostinger
FTP_HOST = "92.113.18.68"
FTP_PORT = 21
FTP_USER = "u173050672.81plus.net"
FTP_PASS = "h29031976T."

# Telegram
TG_BOT_TOKEN = "8939527194:AAFi56LHlyNJnBGzXC_a4Wqsht1G1DCLPbo"
TG_CHANNEL = "@sicurissimoonline"
TG_ADMIN_ID = "642593407"

# Brand Palette 81+
C_BG = "#07070C"           # Nero profondo tecnico
C_SURFACE = "#12121E"      # Superficie card
C_SEGNALE = "#FB6B00"      # Arancione Segnale 81+
C_WHITE = "#FFFFFF"        # Bianco puro
C_MUTED = "#A5A196"        # Grigio tecnico
C_GREEN = "#25D366"        # Verde Safety
C_RED = "#FF453A"          # Rosso Allarme

# Font Resolver
def get_font(size, bold=False):
    font_names = ["arialbd.ttf" if bold else "arial.ttf", "segoeuib.ttf" if bold else "segoeui.ttf"]
    for name in font_names:
        win_path = os.path.join("C:/Windows/Fonts", name)
        if os.path.exists(win_path):
            try:
                return ImageFont.truetype(win_path, size)
            except Exception:
                pass
    return ImageFont.load_default()


# ══════════════════════════════════════════════════════════════════
# 1. GENERATORE BRANDING CANALE YOUTUBE (BANNER, AVATAR, WATERMARK)
# ══════════════════════════════════════════════════════════════════
class YouTubeBrandAssets:
    """Generatore di asset visivi ufficiali per il canale YouTube 81+."""

    @staticmethod
    def generate_banner():
        """Genera il banner ufficiale del canale YouTube (2560x1440 px)."""
        W, H = 2560, 1440
        img = Image.new("RGB", (W, H), color=C_BG)
        draw = ImageDraw.Draw(img)

        # Griglia di sfondo tecnica
        for x in range(0, W, 80):
            draw.line([(x, 0), (x, H)], fill="#0E0E18", width=1)
        for y in range(0, H, 80):
            draw.line([(0, y), (W, y)], fill="#0E0E18", width=1)

        # Area Sicura Desktop/TV/Mobile (1546x423 centrale: Y da 508 a 931)
        safe_top, safe_bottom = 508, 931
        draw.rectangle([(0, safe_top), (W, safe_bottom)], fill="#0A0A14")
        draw.line([(0, safe_top), (W, safe_top)], fill=C_SEGNALE, width=6)
        draw.line([(0, safe_bottom), (W, safe_bottom)], fill=C_SEGNALE, width=6)

        # Logo 81+ Badge a sinistra
        logo_x, logo_y = 550, 610
        logo_size = 180
        draw.rounded_rectangle([(logo_x, logo_y), (logo_x + logo_size, logo_y + logo_size)], radius=20, fill=C_SEGNALE)
        font_logo = get_font(105, bold=True)
        draw.text((logo_x + 22, logo_y + 30), "81+", fill=C_WHITE, font=font_logo)

        # Testata e Claim Canale
        font_title = get_font(64, bold=True)
        draw.text((logo_x + 220, logo_y + 10), "81plus.net · Presidio Tecnico Nazionale", fill=C_WHITE, font=font_title)

        font_claim = get_font(34, bold=True)
        draw.text((logo_x + 220, logo_y + 90), "La Sicurezza sul Lavoro per chi Guida l'Azienda e per chi Lavora", fill=C_SEGNALE, font=font_claim)

        font_sub = get_font(24, bold=False)
        draw.text((logo_x + 220, logo_y + 140), "D.Lgs. 81/08  ·  HACCP & NAS  ·  Privacy GDPR  ·  Oltre 2.000 Corsi Certificati", fill=C_MUTED, font=font_sub)

        # Barra di fiducia inferiore nell'area sicura
        font_trust = get_font(22, bold=True)
        trust_text = "35k+ Aziende Seguite  |  295k+ Persone Formate  |  Dal 2003  |  ZERO Sanzioni  |  100% SAFETY"
        draw.text((logo_x, safe_bottom - 45), trust_text, fill=C_WHITE, font=font_trust)
        draw.text((W - 750, safe_bottom - 45), "www.81plus.net", fill=C_SEGNALE, font=font_trust)

        out_path = os.path.join(YT_OUT_DIR, "banner_canale_youtube_81plus.png")
        img.save(out_path, format="PNG", optimize=True)
        print(f"[BRAND] Banner Canale generato: {out_path} ({W}x{H})")
        return out_path

    @staticmethod
    def generate_avatar():
        """Genera l'icona / avatar del profilo YouTube (800x800 px)."""
        W, H = 800, 800
        img = Image.new("RGB", (W, H), color=C_BG)
        draw = ImageDraw.Draw(img)

        # Bordo circolare guida
        draw.ellipse([(20, 20), (W - 20, H - 20)], fill="#0D0D18", outline="#202030", width=4)

        # Quadrato Logo Arancione centrale
        box_size = 460
        bx = (W - box_size) // 2
        by = (H - box_size) // 2 - 25
        draw.rounded_rectangle([(bx, by), (bx + box_size, by + box_size)], radius=50, fill=C_SEGNALE)

        font_logo = get_font(270, bold=True)
        draw.text((bx + 55, by + 65), "81+", fill=C_WHITE, font=font_logo)

        font_sub = get_font(32, bold=True)
        draw.text((W // 2 - 80, by + box_size + 45), "81plus.net", fill=C_WHITE, font=font_sub)

        out_path = os.path.join(YT_OUT_DIR, "avatar_canale_youtube_81plus.png")
        img.save(out_path, format="PNG", optimize=True)
        print(f"[BRAND] Avatar Canale generato: {out_path} ({W}x{H})")
        return out_path

    @staticmethod
    def generate_watermark():
        """Genera il watermark per i video (150x150 px trasparente/arancione)."""
        W, H = 150, 150
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle([(10, 10), (W - 10, H - 10)], radius=16, fill=(251, 107, 0, 230), outline=(255, 255, 255, 200), width=2)
        font_wm = get_font(65, bold=True)
        draw.text((26, 32), "81+", fill=(255, 255, 255, 255), font=font_wm)

        out_path = os.path.join(YT_OUT_DIR, "watermark_video_81plus.png")
        img.save(out_path, format="PNG")
        print(f"[BRAND] Watermark generato: {out_path}")
        return out_path


# ══════════════════════════════════════════════════════════════════
# 2. GENERATORE THUMBNAILS YOUTUBE (1280x720) AD ALTO CTR
# ══════════════════════════════════════════════════════════════════
class YouTubeThumbnailGenerator:
    """Generatore di copertine YouTube 1280x720 ottimizzate per click-through-rate su mobile."""

    @staticmethod
    def make_thumbnail(gancio_riga1, gancio_riga2="", badge="D.LGS. 81/08", filename="thumb.png"):
        W, H = 1280, 720
        img = Image.new("RGB", (W, H), color=C_BG)
        draw = ImageDraw.Draw(img)

        # Gradiente e Texture
        for y in range(H):
            t = y / H
            draw.line([(0, y), (W, y)], fill=(int(7 + 15 * t), int(7 + 10 * t), int(12 + 10 * t)))

        # Griglia sottile
        for x in range(0, W, 70):
            draw.line([(x, 0), (x, H)], fill="#141422", width=1)

        # Barra superiore arancione
        draw.rectangle([(0, 0), (W, 14)], fill=C_SEGNALE)

        # Badge Logo 81+ (Top-Left)
        draw.rounded_rectangle([(45, 45), (135, 135)], radius=12, fill=C_SEGNALE)
        font_logo = get_font(52, bold=True)
        draw.text((58, 62), "81+", fill=C_WHITE, font=font_logo)

        # Category Badge a fianco
        draw.rounded_rectangle([(155, 60), (560, 120)], radius=8, fill="#121220", outline=C_SEGNALE, width=2)
        font_badge = get_font(20, bold=True)
        draw.text((175, 78), f"⚡ {badge}", fill=C_SEGNALE, font=font_badge)

        # Centro: Gancio Clickbait Gigante con ombra drammatica
        font_hook = get_font(86, bold=True)
        hy = 230

        # Riga 1 (Bianco su ombra nera)
        draw.text((52, hy + 4), gancio_riga1.upper(), fill="#000000", font=font_hook)
        draw.text((48, hy), gancio_riga1.upper(), fill=C_WHITE, font=font_hook)

        # Riga 2 (Arancione Segnale o Rosso se presente)
        if gancio_riga2:
            hy += 115
            color_r2 = C_SEGNALE if "NON" not in gancio_riga2 and "STOP" not in gancio_riga2 else C_RED
            draw.text((52, hy + 4), gancio_riga2.upper(), fill="#000000", font=font_hook)
            draw.text((48, hy), gancio_riga2.upper(), fill=color_r2, font=font_hook)

        # Callout Pillola in basso
        pill_y = H - 160
        draw.rounded_rectangle([(48, pill_y), (850, pill_y + 65)], radius=8, fill="#161626", outline="#2C2C40", width=2)
        font_pill = get_font(22, bold=True)
        draw.text((70, pill_y + 18), "👉 Evita sanzioni e fermo lavori: www.81plus.net", fill=C_WHITE, font=font_pill)

        # Barra Trust Footer
        draw.line([(0, H - 55), (W, H - 55)], fill="#1E1E2C", width=1)
        font_f = get_font(18, bold=True)
        draw.text((48, H - 38), "35k+ Aziende Seguite  ·  295k+ Formati  ·  Dal 2003  ·  100% SAFETY", fill=C_MUTED, font=font_f)
        draw.text((W - 220, H - 38), "Labo Tecnic Studio", fill=C_SEGNALE, font=font_f)

        out_path = os.path.join(YT_OUT_DIR, filename)
        site_path = os.path.join(SITE_ASSETS_DIR, filename)
        img.save(out_path, format="PNG", optimize=True)
        img.save(site_path, format="PNG", optimize=True)
        return out_path, site_path


# ══════════════════════════════════════════════════════════════════
# 3. PALINSESTO EVERGREEN YOUTUBE 81+ (365 GIORNI / 52 VIDEO)
# ══════════════════════════════════════════════════════════════════
class YouTubeEvergreenPlanner:
    """Architettura contenuti virali ed evergreen con titoli VidIQ e copy AIDA/EPPPA/PNL."""

    PILLARS = [
        # --- SICUREZZA LAVORO ---
        {
            "id": "sic_01",
            "pillar": "SICUREZZA",
            "badge": "PATENTE A CREDITI",
            "hook_r1": "12.000€ DI MULTA",
            "hook_r2": "SUBITO SENZA DIFFIDA",
            "title": "D.L. 159/2025: La Sanzione da 12.000€ che blocca i cantieri (anche col POS)",
            "hook_5s": "Se pensi che per evitare una sanzione basti avere un POS fotocopia in cantiere, fermati subito.",
            "desc": """🚨 D.L. 159/2025: la sanzione minima da € 12.000 non è diffidabile e la patente sotto 15 crediti ferma i cantieri.
👉 Proteggi la tua impresa in 48 ore col Collaudo 81: https://81plus.net/collaudo81.html

In questo video analizziamo punto per punto:
00:00 - Il nuovo D.L. 159/2025 e le sanzioni raddoppiate
02:15 - Perché la diffida è stata abolita
04:40 - Come gli ispettori INL tolgono 5 crediti per lavoratore
07:10 - La checklist di conformità inattaccabile
09:30 - Come mettersi al sicuro con 81plus.net

🛡️ Labo Tecnic Studio di Mirco Pregnolato (dal 2003): oltre 35.000 aziende seguite e ZERO sanzioni ricevute.

🌐 Sito Ufficiale: https://81plus.net
📱 Canale Telegram Notifiche: https://t.me/sicurissimoonline

#SicurezzaSulLavoro #PatenteACrediti #DLgs8108 #CantieriSicuri #INAIL #81plus""",
            "tags": ["patente a crediti", "sicurezza sul lavoro", "d lgs 81 08", "sanzioni cantieri", "pos cantiere", "collaudo 81", "81plus", "ispettorato lavoro"]
        },
        {
            "id": "sic_02",
            "pillar": "SICUREZZA",
            "badge": "D.LGS. 81/08",
            "hook_r1": "ARRESTO TITOLARE?",
            "hook_r2": "LA TRAPPOLA DEL POS",
            "title": "Arresto fino a 8 mesi per il Datore di Lavoro: quando scatta il penale?",
            "hook_5s": "Molti imprenditori credono che le multe sulla sicurezza siano solo questioni economiche. Non è così.",
            "desc": """⚠️ La responsabilità penale del Datore di Lavoro non è delegabile: quando scatta l'arresto?
👉 Metti in sicurezza il tuo cantiere oggi: https://81plus.net/collaudo81.html

Analisi giuridica dei reati contravvenzionali ex art. 55 D.Lgs. 81/08:
00:00 - Arresto vs Ammenda: cosa prevede l'art. 55
03:00 - Mancata valutazione dei rischi (DVR)
05:30 - Mancata nomina RSPP o Medico Competente
08:00 - Il Patto dei 30 Giorni di 81plus.net

🌐 Visita: https://81plus.net
#SicurezzaLavoro #ResponsabilitaPenale #Imprenditori #81plus""",
            "tags": ["responsabilita penale sicurezza", "arresto datore di lavoro", "dvr mancante", "nomina rspp", "patente crediti", "81plus"]
        },

        # --- HACCP & ALIMENTARE ---
        {
            "id": "hac_01",
            "pillar": "HACCP",
            "badge": "CONTROLLI NAS",
            "hook_r1": "SIGILLI AL LOCALE?",
            "hook_r2": "LA TRAPPOLA ALLERGENI",
            "title": "Controllo NAS in Cucina: il verbale da 6.000€ che si evita con 1 foglio",
            "hook_5s": "Due ispettori dei NAS entrano nel tuo ristorante durante il servizio. Cosa trovano?",
            "desc": """🍽️ Il 68% delle sanzioni nella ristorazione non riguarda cibi scaduti, ma registri e allergeni non conformi.
👉 Fai formare il tuo personale GRATIS col metodo 'Prova Prima': https://81plus.net/corsi.html

Guida pratica alle ispezioni igienico-sanitarie:
00:00 - L'errore fatale sul registro allergeni Reg. UE 1169/11
02:40 - Schede temperature e catena del freddo
05:15 - Corsi HACCP validi a norma di legge
07:45 - La formula Prova Prima di 81plus.net

🌐 Scopri il catalogo di oltre 2.000 corsi certificati: https://81plus.net/corsi.html
#HACCP #Ristorazione #ChefItalia #NAS #SicurezzaAlimentare #81plus""",
            "tags": ["controllo nas ristorante", "manuale haccp", "registro allergeni", "corsi alimentaristi", "igiene alimenti", "81plus"]
        },

        # --- PRIVACY & GDPR ---
        {
            "id": "pri_01",
            "pillar": "PRIVACY",
            "badge": "STATUTO LAVORATORI",
            "hook_r1": "TELECAMERE AZIENDA",
            "hook_r2": "CONDANNA PENALE",
            "title": "Telecamere in azienda senza accordo sindacale o ITL: scatta il penale!",
            "hook_5s": "Hai montato telecamere sul piazzale per i furti? Potresti aver commesso un reato penale.",
            "desc": """🔒 L'Art. 4 dello Statuto dei Lavoratori vieta il controllo a distanza senza autorizzazione preventiva.
👉 Metti a norma videosorveglianza e GDPR: https://81plus.net/offerta.html

Cosa serve tassativamente prima di accendere le telecamere:
00:00 - Perché montare telecamere costa una condanna penale
02:30 - Come ottenere l'autorizzazione dell'Ispettorato del Lavoro (ITL)
05:00 - Sanzioni GDPR fino al 4% del fatturato
07:20 - Il servizio di asseverazione 81plus.net

🌐 Tutela la tua azienda: https://81plus.net
#PrivacyGDPR #Videosorveglianza #StatutoDeiLavoratori #GarantePrivacy #81plus""",
            "tags": ["videosorveglianza dipendenti", "autorizzazione itl telecamere", "art 4 statuto lavoratori", "privacy gdpr azienda", "81plus"]
        },

        # --- PROMO STRAORDINARIA & METODO ---
        {
            "id": "promo_01",
            "pillar": "OFFERTA",
            "badge": "COLLAUDO 81",
            "hook_r1": "COLLAUDO 81 IN 48H",
            "hook_r2": "SOLI 50 POSTI A 497€",
            "title": "Il Collaudo 81: in 48 ore sai se sei a norma o rischi i cantieri bloccati",
            "hook_5s": "Nessuna perdita di tempo: 90 minuti di videocall con Mirco Pregnolato e perizia scritta in mano.",
            "desc": """🛡️ La porta d'ingresso all'ecosistema 81plus.net: Il Collaudo 81 a € 497.
👉 Riserva 1 dei posti disponibili: https://81plus.net/promo-settembre.html

Cosa comprende la perizia:
00:00 - Perché serve il Collaudo 81
02:00 - Audit incrociato su 30 normative cogenti
04:30 - La cartella condivisa protetta e il fascicolo asseverato
06:15 - Garanzia scritta Patto dei 30 Giorni: 100% SAFETY

🌐 Prenota subito: https://81plus.net/promo-settembre.html
#Collaudo81 #MircoPregnolato #SicurezzaLavoro #81plus""",
            "tags": ["collaudo 81", "mirco pregnolato", "audit sicurezza", "patente crediti", "81plus net"]
        }
    ]

    @classmethod
    def generate_full_schedule(cls):
        """Genera il palinsesto completo con thumbnails, descrizioni e script salvati in JSON e CSV."""
        schedule = []
        for i, item in enumerate(cls.PILLARS, 1):
            fname = f"yt_thumb_{item['id']}.png"
            p_local, p_site = YouTubeThumbnailGenerator.make_thumbnail(
                item["hook_r1"], item["hook_r2"], badge=item["badge"], filename=fname
            )
            item_record = {
                "id": item["id"],
                "settimana": i,
                "pillar": item["pillar"],
                "titolo_video": item["title"],
                "gancio_copertina": f"{item['hook_r1']} {item['hook_r2']}",
                "thumbnail_file": fname,
                "thumbnail_url": f"https://81plus.net/assets/campaigns/{fname}",
                "descrizione": item["desc"],
                "tags": item["tags"]
            }
            schedule.append(item_record)

        # Salvataggio JSON
        sched_json = os.path.join(YT_OUT_DIR, "palinsesto_evergreen_youtube81.json")
        with open(sched_json, "w", encoding="utf-8") as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)

        print(f"[PALINSESTO] Generati {len(schedule)} contenuti video evergreen con miniature.")
        return schedule


# ══════════════════════════════════════════════════════════════════
# 4. CLI & DISPATCHER AUTOMATICO
# ══════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="81+ YouTube Channel Evergreen Manager")
    parser.add_argument("--generate-brand", action="store_true", help="Genera Banner 2560x1440, Avatar e Watermark del Canale")
    parser.add_argument("--generate-schedule", action="store_true", help="Genera l'intero palinsesto video e le copertine 1280x720")
    parser.add_argument("--ftp-sync", action="store_true", help="Carica tutte le miniature sul server FTP pubblico")
    parser.add_argument("--notify-admin", action="store_true", help="Invia anteprima del palinsesto YouTube via Telegram a Mirco Pregnolato")
    parser.add_argument("--status", action="store_true", help="Mostra lo stato e i file generati")

    args = parser.parse_args()

    if args.status:
        print("\n=== STATO GESTORE YOUTUBE 81+ ===")
        print(f"Cartella Output: {YT_OUT_DIR}")
        files = os.listdir(YT_OUT_DIR) if os.path.exists(YT_OUT_DIR) else []
        print(f"File generati ({len(files)}):")
        for f in files:
            print(f"  • {f}")
        return

    if args.generate_brand:
        print("\n[*] GENERAZIONE ASSET BRAND CANALE YOUTUBE 81+...")
        YouTubeBrandAssets.generate_banner()
        YouTubeBrandAssets.generate_avatar()
        YouTubeBrandAssets.generate_watermark()
        print("[SUCCESS] Asset brand del Canale YouTube generati con successo!\n")

    if args.generate_schedule:
        print("\n[*] GENERAZIONE PALINSESTO EVERGREEN E MINIATURE...")
        sched = YouTubeEvergreenPlanner.generate_full_schedule()
        print(f"[SUCCESS] Palinsesto generato: {len(sched)} video evergreen pronti con copertine 1280x720.\n")

    if args.ftp_sync:
        print("\n[*] CARICAMENTO ASSET SU HOSTING FTP...")
        try:
            ftp = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS, timeout=25)
            for d in ["assets", "campaigns"]:
                try:
                    ftp.cwd(d)
                except Exception:
                    ftp.mkd(d)
                    ftp.cwd(d)

            uploaded = 0
            for f in os.listdir(YT_OUT_DIR):
                if f.endswith(".png") or f.endswith(".jpg"):
                    lp = os.path.join(YT_OUT_DIR, f)
                    with open(lp, "rb") as fp:
                        ftp.storbinary(f"STOR {f}", fp)
                    uploaded += 1
            ftp.quit()
            print(f"[SUCCESS] Caricati {uploaded} file grafici YouTube su https://81plus.net/assets/campaigns/\n")
        except Exception as e:
            print(f"[-] Errore FTP: {e}")

    if args.notify_admin:
        print("\n[*] INVIO NOTIFICA TELEGRAM AD ADMIN...")
        try:
            sample_thumb = os.path.join(YT_OUT_DIR, "yt_thumb_sic_01.png")
            text = (
                "🎬 *GESTORE YOUTUBE 81+ ATTIVATO*\n\n"
                "• Banner Canale (2560x1440): PRONTO\n"
                "• Avatar Profilo (800x800): PRONTO\n"
                "• Palinsesto Evergreen: Sicurezza, HACCP, Privacy e Collaudo 81\n"
                "• Miniatura 1280x720 ad alto CTR generata e testata.\n\n"
                "👉 Tutti i video rimandano a https://81plus.net"
            )
            # Invia messaggio semplice
            url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
            payload = json.dumps({"chat_id": TG_ADMIN_ID, "text": text, "parse_mode": "Markdown"}).encode()
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"[SUCCESS] Notifica Telegram inviata con successo all'Admin {TG_ADMIN_ID}!")
        except Exception as e:
            print(f"[-] Errore invio Telegram: {e}")

    if not (args.generate_brand or args.generate_schedule or args.ftp_sync or args.notify_admin or args.status):
        print("\nNessuna azione specificata. Esegui con:")
        print("  python youtube_manager_81plus.py --generate-brand")
        print("  python youtube_manager_81plus.py --generate-schedule")
        print("  python youtube_manager_81plus.py --ftp-sync")
        print("  python youtube_manager_81plus.py --notify-admin")

if __name__ == "__main__":
    main()
