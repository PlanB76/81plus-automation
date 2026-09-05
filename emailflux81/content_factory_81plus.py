#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
content_factory_81plus.py — Motore Creativo ed Esecutivo 81+
Generatore di Immagini Brandizzate, Copywriting Persuasivo (EPPPA, AIDA, PAS, PNL)
e Dispatcher Multicanale per Email Marketing & Social Media.

Caratteristiche:
  - Generazione grafica brand 81+ (Pillow): Colori nero/arancio/bianco, logo 81+, badge, metriche trust.
  - Formati: Banner Email (1200x630) e Post Social (1080x1080 quadrato).
  - Copywriting magnetico alternato sui 3 pilastri:
      1. Sicurezza sul Lavoro D.Lgs. 81/08 & Patente a Crediti
      2. HACCP & Igiene Alimentare (Controlli NAS/ASL)
      3. Privacy GDPR 679/16 (Videosorveglianza & Sanzioni Garante)
      + Campagna Promozione Settembre 2026 (50 Posti)
  - Invio Email HTML con immagine incorporata (SMTP Hostinger info@81plus.net).
  - Pubblicazione automatica su Telegram (Bot @sicurissimo81_bot, canale @sicurissimoonline).
"""

import os
import sys
import ssl
import json
import time
import ftplib
import smtplib
import argparse
import datetime
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formataddr

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image, ImageDraw, ImageFont

# ══════════════════════════════════════════════════════════════════
# CONFIGURAZIONE GENERALE & PATHS
# ══════════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_ASSETS_DIR = r"C:\81PLUS_GLOBAL_MASTER\81plus.net\81plus.net - new\assets\campaigns"
LOCAL_OUT_DIR = os.path.join(BASE_DIR, "generated_campaigns")
os.makedirs(SITE_ASSETS_DIR, exist_ok=True)
os.makedirs(LOCAL_OUT_DIR, exist_ok=True)

# SMTP Hostinger
SMTP_HOST = "smtp.hostinger.com"
SMTP_PORT = 465
SMTP_USER = "info@81plus.net"
SMTP_PASS = "h29031976T."
SMTP_FROM_NAME = "81+ · Presidio Tecnico Nazionale"

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
C_SURFACE = "#10101A"      # Superficie card
C_BORDER = "#202030"       # Bordo sottile
C_SEGNALE = "#FB6B00"      # Arancione Segnale 81+
C_WHITE = "#FFFFFF"        # Bianco puro
C_MUTED = "#A5A196"        # Grigio tecnico
C_GREEN = "#25D366"        # Verde Safety
C_RED = "#FF453A"          # Rosso Emergenza/Sanzioni

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
# 1. GENERATORE IMMAGINI BRANDIZZATE 81+
# ══════════════════════════════════════════════════════════════════
class BrandImageGenerator:
    """Generatore di grafiche ad alto impatto per email e social con palette ufficiale 81+."""

    @staticmethod
    def create_image(topic, format_type="email_banner", title="", highlight="", subtitle="", stat_badge=""):
        """
        format_type: 'email_banner' (1200x630) o 'social_post' (1080x1080)
        """
        is_square = (format_type == "social_post")
        w, h = (1080, 1080) if is_square else (1200, 630)

        img = Image.new("RGB", (w, h), color=C_BG)
        draw = ImageDraw.Draw(img)

        # 1. Griglia di sfondo tecnica (overlay geometrico sottile)
        grid_step = 60
        for x in range(0, w, grid_step):
            draw.line([(x, 0), (x, h)], fill="#0D0D16", width=1)
        for y in range(0, h, grid_step):
            draw.line([(0, y), (w, y)], fill="#0D0D16", width=1)

        # 2. Cornice perimetrale brand con accento arancione in alto
        draw.rectangle([(16, 16), (w - 16, h - 16)], outline="#1C1C2A", width=2)
        draw.line([(16, 16), (w - 16, 16)], fill=C_SEGNALE, width=6)

        # 3. Logo 81+ Badge (quadrato arancione con scritta 81+ bianca)
        logo_x, logo_y = 50, 45
        logo_size = 64
        draw.rounded_rectangle([(logo_x, logo_y), (logo_x + logo_size, logo_y + logo_size)], radius=8, fill=C_SEGNALE)
        font_logo = get_font(34, bold=True)
        draw.text((logo_x + 8, logo_y + 12), "81+", fill=C_WHITE, font=font_logo)

        # Titolo Testata a fianco al logo
        font_brand = get_font(24, bold=True)
        font_brand_sub = get_font(15, bold=False)
        draw.text((logo_x + 80, logo_y + 8), "81plus.net", fill=C_WHITE, font=font_brand)
        draw.text((logo_x + 80, logo_y + 38), "Labo Tecnic Studio · Presidio Tecnico Nazionale (dal 2003)", fill=C_MUTED, font=font_brand_sub)

        # 4. Badge Categoria / Pilastro (in alto a destra)
        font_badge = get_font(15, bold=True)
        topic_labels = {
            "sicurezza": ("D.LGS. 81/08 · PATENTE A CREDITI", C_RED),
            "haccp": ("HACCP · CONTROLLI NAS & ASL", C_SEGNALE),
            "privacy": ("GDPR 679/16 · GARANTE PRIVACY", "#388BFD"),
            "promo_settembre": ("PROMO SETTEMBRE 2026 · 50 POSTI", C_GREEN)
        }
        badge_label, badge_color = topic_labels.get(topic, ("81+ PRESIDIO IMPRESE", C_SEGNALE))
        
        # Calcolo dimensioni badge
        badge_pad_x, badge_pad_y = 16, 8
        badge_w = 360
        badge_x = w - 50 - badge_w
        draw.rounded_rectangle([(badge_x, logo_y + 6), (badge_x + badge_w, logo_y + 52)], radius=6, fill="#12121E", outline=badge_color, width=2)
        draw.text((badge_x + 18, logo_y + 18), badge_label, fill=badge_color, font=font_badge)

        # 5. Box Centrale Notifica / Allarme
        center_y = 150 if not is_square else 200
        card_h = (h - center_y - 140) if not is_square else 560
        draw.rounded_rectangle([(50, center_y), (w - 50, center_y + card_h)], radius=12, fill=C_SURFACE, outline="#262638", width=2)

        # Stat Badge interna se presente (es. "SANZIONE € 12.000 NON DIFFIDABILE")
        if stat_badge:
            font_stat = get_font(15, bold=True)
            draw.rounded_rectangle([(75, center_y + 24), (75 + 460, center_y + 58)], radius=4, fill="#251015", outline=C_RED, width=1)
            draw.text((90, center_y + 30), f"⚡ {stat_badge}", fill=C_RED, font=font_stat)
            title_offset_y = center_y + 75
        else:
            title_offset_y = center_y + 35

        # 6. Titolo Principale ad altissimo impatto (con wrapping e keyword evidenziata)
        font_title = get_font(38 if not is_square else 44, bold=True)
        words = title.split()
        lines = []
        cur_line = []
        for word in words:
            cur_line.append(word)
            test_line = " ".join(cur_line)
            if len(test_line) > (38 if not is_square else 28):
                cur_line.pop()
                lines.append(" ".join(cur_line))
                cur_line = [word]
        if cur_line:
            lines.append(" ".join(cur_line))

        ty = title_offset_y
        for line in lines[:3]: # Max 3 righe
            # Se la riga contiene la highlight word, la coloriamo
            if highlight and highlight.lower() in line.lower():
                draw.text((75, ty), line, fill=C_SEGNALE, font=font_title)
            else:
                draw.text((75, ty), line, fill=C_WHITE, font=font_title)
            ty += (50 if not is_square else 60)

        # 7. Sottotitolo / Dettaglio Cogente
        if subtitle:
            font_sub = get_font(18 if not is_square else 22, bold=False)
            sub_words = subtitle.split()
            sub_lines = []
            cur_sub = []
            for sw in sub_words:
                cur_sub.append(sw)
                if len(" ".join(cur_sub)) > (65 if not is_square else 45):
                    cur_sub.pop()
                    sub_lines.append(" ".join(cur_sub))
                    cur_sub = [sw]
            if cur_sub:
                sub_lines.append(" ".join(cur_sub))

            ty += 15
            for sline in sub_lines[:3]:
                draw.text((75, ty), sline, fill=C_MUTED, font=font_sub)
                ty += 30

        # Se è formato quadrato per i social, aggiungiamo una callout visiva centrale
        if is_square:
            box_cta_y = center_y + card_h - 100
            draw.rounded_rectangle([(75, box_cta_y), (w - 75, box_cta_y + 70)], radius=8, fill="#1B1B2A", outline=C_SEGNALE, width=2)
            font_cta = get_font(20, bold=True)
            draw.text((105, box_cta_y + 22), "👉 TUTELA COMPLETA: Visita 81plus.net · Zero Sanzioni", fill=C_WHITE, font=font_cta)

        # 8. Barra di Garanzia Inferiore (Trust Metrics 81+)
        bot_y = h - 90
        draw.line([(50, bot_y), (w - 50, bot_y)], fill="#1E1E2C", width=1)
        font_metrics = get_font(15, bold=True)
        metrics_text = "35k+ Aziende Seguite  |  295k+ Formati  |  5k+ Partners  |  Dal 2003  |  100% SAFETY"
        draw.text((50, bot_y + 15), metrics_text, fill=C_MUTED, font=font_metrics)

        draw.text((w - 230, bot_y + 15), "www.81plus.net", fill=C_SEGNALE, font=font_metrics)

        # Salvataggio file
        filename = f"{topic}_{format_type}_{int(time.time())}.png"
        out_path_local = os.path.join(LOCAL_OUT_DIR, filename)
        out_path_site = os.path.join(SITE_ASSETS_DIR, filename)

        img.save(out_path_local, format="PNG", optimize=True)
        img.save(out_path_site, format="PNG", optimize=True)
        print(f"[IMG] Grafica generata con successo: {filename} ({w}x{h})")
        return out_path_site, filename


# ══════════════════════════════════════════════════════════════════
# 2. GENERATORE DI COPYWRITING PERSUASIVO (EPPPA, AIDA, PAS, PNL)
# ══════════════════════════════════════════════════════════════════
class PersuasiveCopyFactory:
    """Generatore di testi persuasivi magnetici calibrati su EPPPA, AIDA, PAS e PNL."""

    CAMPAIGNS = {
        "sicurezza": {
            "badge": "EMERGENZA CANTIERI & D.L. 159/2025",
            "stat_badge": "SANZIONE MINIMA € 12.000 NON DIFFIDABILE",
            "img_title": "Basta 1 solo documento mancante per fermare i tuoi cantieri",
            "img_highlight": "fermare i tuoi cantieri",
            "img_sub": "Con la Patente a Crediti sotto 15 e i nuovi 300 ispettori tecnici INL, il rischio penale è personale del Datore di Lavoro.",
            
            # Framework AIDA & EPPPA per Email
            "email_subject": "⚠️ {nome}, la sanzione da € 12.000 che scatta anche se hai il consulente",
            "preview_text": "Non è una diffida: dal 2026 le multe sono immediate e bloccano i SAL.",
            "hook_pnl": "Mentre leggi queste righe, immagina per un istante cosa accadrebbe se domani mattina un ispettore INL o ASL varcasse i cancelli della tua azienda con la nuova checklist 2026.",
            
            "emozione_epppa": "Quella morsa allo stomaco quando ti chiedono un verbale di conformità o una nomina aggiornata e il tuo consulente abituale «ti farà sapere in settimana».",
            "pensiero_epppa": "Molti imprenditori pensano ancora: «Pago già qualcuno, quindi sono coperto». Ma la legge è spietata: la responsabilità penale non è delegabile.",
            "parole_epppa": "«E se avessero ragione loro? Se quel subappalto o quel corso scaduto mi costasse la revoca della patente a crediti e il blocco dei pagamenti?»",
            "persone_epppa": "Non riguarda solo i documenti: riguarda la tua famiglia, il tuo patrimonio personale e gli operai che ogni giorno salgono sui tuoi ponteggi.",
            "azione_epppa": "Blocca subito il rischio prima che sia un ispettore a contestartelo.",
            
            "soluzione_cta": "Richiedi Il Collaudo 81 in 48 ore (€ 497)",
            "soluzione_url": "https://81plus.net/collaudo81.html",
            "garanzia_text": "Coperto dalla garanzia scritta del Patto dei 30 Giorni: zero sanzioni, zero pensieri, 100% SAFETY.",

            # Social Post PNL
            "social_hook": "«Tanto il controllo a noi non capita mai». Poi arriva la raccomandata da 12.000 euro.",
            "social_body": """Ieri un imprenditore edile con 18 dipendenti mi ha confessato:
«Mirco, ero convinto di essere a posto. Pagavo 2.500 euro all'anno per il servizio sicurezza. Poi l'ispettore ha aperto il cantiere e ha trovato un POS fotocopia e 3 attestati non conformi agli Accordi Stato-Regioni. Risultato: -10 crediti dalla patente e cantiere sospeso per 20 giorni».

In Italia nel 2025/2026 ci sono stati 597.710 infortuni e 1.093 morti sul lavoro. Il Governo ha risposto con il D.L. 159/2025:
❌ Sanzioni minime raddoppiate a 12.000 € non diffidabili
❌ Stop immediato ai lavori sotto 15 crediti
❌ Arresto immediato fino a 8 mesi per il titolare

Non lasciare che una dimenticanza burocratica distrugga 20 anni di sacrifici.

Con 81plus.net (Labo Tecnic Studio) siamo sul campo dal 2003: oltre 35.000 aziende protette, 295.000 persone formate e ZERO sanzioni ricevute.

Tu sai esattamente cosa trovera' l'ispettore se entra domani mattina nella tua sede?

👇 Fai il check in 48 ore o richiedi il Collaudo 81 su www.81plus.net""",
            "hashtags": "#SicurezzaSulLavoro #PatenteACrediti #DLgs8108 #CantieriSicuri #ImprenditoriEdili #INAIL #ZeroInfortuni #81plus"
        },

        "haccp": {
            "badge": "HACCP & IGIENE ALIMENTARE · REPRESSIONE FRODI",
            "stat_badge": "CHIUSURA LOCALE E MULTE FINO A € 24.000",
            "img_title": "Controlli NAS e ASL: il tuo manuale è davvero a prova di sigilli?",
            "img_highlight": "prova di sigilli?",
            "img_sub": "Allergeni non tracciati, schede temperature saltate e attestati alimentaristi scaduti. Basta un'ispezione per fermare l'attività.",
            
            "email_subject": "🍽️ {nome}, il controllo NAS da € 6.000 che si evita con 1 semplice foglio",
            "preview_text": "Non rischiare la sospensione dell'attività per una scheda non compilata.",
            "hook_pnl": "Ti sei mai chiesto come reagiresti se due ispettori in divisa entrassero in cucina durante il pieno servizio del venerdì sera?",
            
            "emozione_epppa": "La paura improvvisa di vedere sequestrata la merce in cella frigo davanti ai clienti in sala.",
            "pensiero_epppa": "«Ma noi puliamo tutti i giorni, siamo attentissimi!» La pulizia è fondamentale, ma per la legge conta solo ciò che è documentato e rintracciabile.",
            "parole_epppa": "«Spero che non guardino il registro allergeni del menu o l'ultimo attestato del nuovo aiuto cuoco...»",
            "persone_epppa": "Un'intossicazione alimentare o un'allergia mal gestita non è solo un danno d'immagine: è un procedimento penale con sequestro cautelare immediato.",
            "azione_epppa": "Metti in sicurezza il tuo locale e la tua cucina oggi stesso senza spendere fortune.",
            
            "soluzione_cta": "Forma la tua Squadra Gratis con il Metodo 'Prova Prima'",
            "soluzione_url": "https://81plus.net/corsi.html",
            "garanzia_text": "Tutti i corsi alimentaristi HACCP sono accreditati e validi su tutto il territorio nazionale.",

            # Social Post PNL
            "social_hook": "Venerdì sera, locale pieno. Entrano i NAS. Cosa trovano nella tua cucina?",
            "social_body": """Il 68% delle sanzioni nella ristorazione e nell'agroalimentare NON riguarda cibi avariati, ma vizi documentali formali:
1. Schede di monitoraggio temperature mai firmate
2. Matrice allergeni non conforme al Reg. UE 1169/2011
3. Attestati alimentaristi del personale privi di codice di verifica nazionale
4. Mancata notifica sanitaria aggiornata per modifiche locali

Le sanzioni partono da 3.000 € fino a 24.000 € con sospensione immediata della licenza.

La conformità HACCP non deve essere un incubo da compilare a notte fonda. Deve essere un protocollo automatico, semplice e blindato.

Su 81plus.net formi i tuoi collaboratori con la formula PROVA PRIMA: studiano gratis online, superano i quiz e acquisti l'attestato ufficiale solo ad esame passato.

Proteggi il tuo ristorante, la tua reputazione e la salute dei tuoi clienti.

👉 Entra nel presidio su www.81plus.net""",
            "hashtags": "#HACCP #RistorazioneItalia #SicurezzaAlimentare #ChefItaliani #NAS #BarRistoranti #CorsiAlimentaristi #81plus"
        },

        "privacy": {
            "badge": "PRIVACY GDPR 679/16 & ISPETTORATO LAVORO",
            "stat_badge": "SANZIONI PENALI STATUTO LAVORATORI ART. 4",
            "img_title": "Telecamere in azienda? Rischi una condanna penale e multe al 4%",
            "img_highlight": "condanna penale",
            "img_sub": "Installare impianti di videosorveglianza o controllare email e GPS senza autorizzazione dell'ITL costa il penale immediato al titolare.",
            
            "email_subject": "🔒 {nome}, le telecamere in azienda possono costarti il penale (anche se per furto)",
            "preview_text": "L'accordo sindacale o l'autorizzazione ITL sono obbligatori prima dell'accensione.",
            "hook_pnl": "Molti titolari ignorano che proteggere i propri beni con una videocamera può trasformarsi nell'imputazione penale più rapida della loro carriera.",
            
            "emozione_epppa": "L'incredulità e la rabbia quando scopri che un ex dipendente ti ha denunciato all'Ispettorato del Lavoro per aver installato telecamere sul piazzale.",
            "pensiero_epppa": "«Ma le ho messe per difendermi dai ladri, le ho pagate io!» Per la legge, il controllo a distanza del lavoratore è reato penale (Art. 4 Legge 300/1970).",
            "parole_epppa": "«Non posso credere che per due telecamere da 100 euro rischi una sanzione del 4% del fatturato e una fedina penale sporca.»",
            "persone_epppa": "I dati dei tuoi dipendenti, le email aziendali e le immagini registrate sono sotto la lente del Garante della Privacy e della Guardia di Finanza.",
            "azione_epppa": "Regolarizza l'istanza ITL e l'adeguamento GDPR prima che scatti l'ispezione congiunta.",
            
            "soluzione_cta": "Metti a Norma Videosorveglianza & GDPR con 81+",
            "soluzione_url": "https://81plus.net/offerta.html",
            "garanzia_text": "Pratiche asseverate e conformi al 100%: zero sanzioni, zero contenziosi.",

            # Social Post PNL
            "social_hook": "Hai montato le telecamere in officina o in magazzino? Potresti essere penalmente perseguibile.",
            "social_body": """Sembra assurdo, ma succede ogni settimana:
Un imprenditore subisce un furto, chiama l'installatore e mette 4 telecamere per sorvegliare l'ingresso e il capannone.
Due mesi dopo, durante un controllo dell'Ispettorato del Lavoro o per la segnalazione di un lavoratore, arriva la contestazione:
🔴 Violazione dell'Art. 4 Statuto dei Lavoratori (controllo a distanza non autorizzato)
🔴 Ammenda penale diretta e sanzione GDPR fino a 20 milioni di euro o 4% del fatturato
🔴 Obbligo di disattivazione immediata dell'impianto

Il Garante Privacy e l'INL non ammettono scuse: senza accordo sindacale o specifica autorizzazione preventiva dell'Ispettorato Territoriale del Lavoro (ITL), l'impianto è ILLEGALE.

Blindare la tua azienda richiede pochi giorni, purché la procedura sia asseverata da tecnici esperti.

Non rischiare la fedina penale per un'installazione improvvisata.

👉 Metti in sicurezza la tua azienda su www.81plus.net""",
            "hashtags": "#PrivacyGDPR #Videosorveglianza #StatutoDeiLavoratori #GarantePrivacy #Imprenditori #PMIItaliane #ConsulenzaAziendale #81plus"
        },

        "promo_settembre": {
            "badge": "CAMPAGNA NAZIONALE SETTEMBRE 2026",
            "stat_badge": "SOLI 50 POSTI DISPONIBILI · ASSEGNAZIONE CRONOLOGICA",
            "img_title": "Doppio Scudo di Settembre: Il Collaudo 81 a € 497 e Corsi FAD Gratuiti",
            "img_highlight": "Corsi FAD Gratuiti",
            "img_sub": "Proteggi la tua impresa con la perizia 1-a-1 di Mirco Pregnolato e forma la tua squadra senza anticipare un euro.",
            
            "email_subject": "🎯 {nome}, soli 12 posti rimasti per il Collaudo 81 di Settembre",
            "preview_text": "Edizione limitata a 50 imprese per blindare contratti e patente a crediti.",
            "hook_pnl": "Settembre è il mese in cui ripartono i cantieri e si firmano gli appalti più importanti dell'anno. La domanda che devi farti è una sola: la tua azienda è pronta a superare qualsiasi verifica?",
            
            "emozione_epppa": "L'urgenza di non rimanere fuori mentre i concorrenti vengono esclusi per patente sotto 15 crediti o periti non abilitati.",
            "pensiero_epppa": "«Posso rimandare al mese prossimo?» No, perché il D.L. 159/2025 non aspetta e i posti disponibili a tariffa agevolata sono tassativamente 50.",
            "parole_epppa": "«Voglio dormire sonni tranquilli e avere in mano un fascicolo che nessun ispettore possa contestare.»",
            "persone_epppa": "Mirco Pregnolato (sul campo dal 2003) mette a disposizione 23 anni di esperienza per passare al setaccio la tua documentazione 1-a-1.",
            "azione_epppa": "Blocca uno dei 12 slot rimasti prima dell'esaurimento della coorte.",
            
            "soluzione_cta": "Riserva 1 dei 12 Slot Rimasti per Settembre →",
            "soluzione_url": "https://81plus.net/promo-settembre.html",
            "garanzia_text": "Coperto dal Patto dei 30 Giorni: se non trovi valore reale, ti rimborsiamo al 100%.",

            # Social Post PNL
            "social_hook": "Settembre 2026: Riaprono i cantieri, ma per molte PMI sarà l'anno dello stop.",
            "social_body": """Con le nuove regole sulla Patente a Crediti e le sanzioni minime da 12.000 euro non diffidabili, entrare in cantiere «sperando che vada bene» è un suicidio economico.

Abbiamo aperto una coorte straordinaria di SOLI 50 POSTI per Settembre:
🛡️ 1. IL COLLAUDO 81 (Sessione 1-a-1 di 90 minuti con Mirco Pregnolato, audit di conformità a 30 normative e fascicolo scritto asseverato a 497 €).
🎓 2. ACCADEMIA CORSI 81+ (Formula 'Prova Prima': fai formare operai e preposti gratis online 24/7 su oltre 2.000 corsi certificati, paghi solo all'esame superato).

⚠️ STATO AGGIORNATO: 38 posti già assegnati, rimangono solo 12 slot.

Non aspettare la contestazione formale del committente o dell'ispettore per correre ai ripari.

👉 Blocca il tuo posto su www.81plus.net/promo-settembre.html""",
            "hashtags": "#PromoSettembre #Collaudo81 #PatenteACrediti #CorsiFAD #SicurezzaLavoro #ImpreseEdili #PMI #81plus"
        }
    }

    @classmethod
    def get_campaign(cls, topic):
        return cls.CAMPAIGNS.get(topic, cls.CAMPAIGNS["sicurezza"])

    @classmethod
    def build_email_html(cls, topic, recipient_name="Imprenditore", img_url=""):
        """Costruisce il template email HTML responsive ad alto contrasto con branding 81+."""
        c = cls.get_campaign(topic)

        subject = c["email_subject"].replace("{nome}", recipient_name)
        preview = c["preview_text"]

        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
  <style>
    body {{ margin:0; padding:0; background-color:#05050A; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color:#ECE8DE; -webkit-font-smoothing:antialiased; }}
    table {{ border-collapse:collapse; }}
    .container {{ max-width:600px; margin:0 auto; background-color:#0A0A12; border:1px solid #1F1F2E; border-radius:8px; overflow:hidden; }}
    .header {{ padding:24px 30px; background-color:#07070C; border-bottom:1px solid #1C1C28; }}
    .brand-badge {{ background-color:#FB6B00; color:#FFFFFF; font-size:18px; font-weight:900; padding:6px 12px; border-radius:4px; display:inline-block; margin-right:12px; vertical-align:middle; }}
    .brand-title {{ font-size:20px; font-weight:800; color:#FFFFFF; vertical-align:middle; }}
    .banner-img {{ width:100%; max-width:600px; height:auto; display:block; border-bottom:2px solid #FB6B00; }}
    .content {{ padding:32px 30px; line-height:1.6; font-size:15px; color:#C8C5BD; }}
    .h-alert {{ background-color:rgba(255,69,58,0.12); border-left:4px solid #FF453A; padding:14px 18px; color:#FFFFFF; margin:20px 0; border-radius:0 4px 4px 0; font-size:14px; font-weight:600; }}
    .btn-cta {{ display:block; text-align:center; background-color:#FB6B00; color:#FFFFFF !important; font-weight:900; font-size:16px; padding:16px 28px; text-decoration:none; border-radius:4px; margin:28px 0 16px 0; text-transform:uppercase; letter-spacing:0.04em; }}
    .guarantee-box {{ background-color:#12121E; border:1px solid #28283C; padding:16px; border-radius:6px; font-size:13px; color:#A5A196; text-align:center; margin-top:20px; }}
    .footer {{ padding:24px 30px; background-color:#05050A; border-top:1px solid #181824; font-size:12px; color:#78756E; text-align:center; line-height:1.5; }}
  </style>
</head>
<body>
  <!-- Preview Text Hack -->
  <div style="display:none; font-size:1px; color:#05050A; line-height:1px; max-height:0px; max-width:0px; opacity:0; overflow:hidden;">
    {preview} &zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
  </div>

  <table width="100%" bgcolor="#05050A" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:20px 10px;">
        <table class="container" width="100%" cellpadding="0" cellspacing="0">
          <!-- Testata Brand -->
          <tr>
            <td class="header">
              <span class="brand-badge">81+</span>
              <span class="brand-title">81plus.net · Presidio Nazionale</span>
            </td>
          </tr>

          <!-- Banner Immagine Brandizzata -->
          {f'<tr><td><img src="{img_url}" alt="{c["img_title"]}" class="banner-img"></td></tr>' if img_url else ''}

          <!-- Corpo Persuasivo (EPPPA / PNL) -->
          <tr>
            <td class="content">
              <p style="font-size:16px; color:#FFFFFF; margin-top:0;"><strong>Ciao {recipient_name},</strong></p>

              <p>{c["hook_pnl"]}</p>

              <div class="h-alert">
                ⚡ <strong>FATTO NORMATIVO:</strong> {c["stat_badge"]}
              </div>

              <p>{c["emozione_epppa"]}</p>

              <p><strong style="color:#FFFFFF;">Il problema di fondo:</strong> {c["pensiero_epppa"]}</p>

              <p style="font-style:italic; color:#E0DED7; border-left:2px solid #FB6B00; padding-left:14px; margin:18px 0;">
                {c["parole_epppa"]}
              </p>

              <p>{c["persone_epppa"]}</p>

              <p><strong style="color:#FFFFFF;">Cosa puoi fare adesso:</strong> {c["azione_epppa"]}</p>

              <!-- Bottone CTA -->
              <a href="{c["soluzione_url"]}" class="btn-cta" target="_blank">
                {c["soluzione_cta"]}
              </a>

              <div class="guarantee-box">
                🛡️ <strong>GARANZIA 81+:</strong> {c["garanzia_text"]}
              </div>

              <p style="margin-top:28px; font-size:14px; color:#A5A196;">
                Sul campo dal 2003 con <strong>Labo Tecnic Studio</strong> (Mirco Pregnolato).<br>
                <em>35k+ Aziende Seguite · 295k+ Persone Formate · ZERO Sanzioni.</em>
              </p>
            </td>
          </tr>

          <!-- Footer Legale & Disiscrizione -->
          <tr>
            <td class="footer">
              81plus.net · Labo Tecnic Studio di Mirco Pregnolato · P.IVA 01504180298 · ITALY<br>
              Presidio Tecnico Nazionale D.Lgs. 81/08, HACCP e Privacy.<br>
              Ricevi questa comunicazione perché hai richiesto una checklist o un servizio del nostro ecosistema.<br>
              <a href="https://81plus.net" style="color:#FB6B00; text-decoration:underline;">Visita il Sito Ufficiale</a> · 
              <a href="mailto:info@81plus.net?subject=Disiscrizione" style="color:#8E8A7E; text-decoration:underline;">Disiscriviti</a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
        return subject, html


# ══════════════════════════════════════════════════════════════════
# 3. DISPATCHER: INVIO EMAIL SMTP & PUBBLICAZIONE TELEGRAM
# ══════════════════════════════════════════════════════════════════
class MultiChannelDispatcher:
    """Motore di invio combinato Email SMTP Hostinger e Telegram Bot API."""

    @staticmethod
    def send_email(to_email, subject, html_content, image_attachment_path=None, from_name=SMTP_FROM_NAME):
        """Invia email con supporto immagini inline via Hostinger SSL 465."""
        try:
            msg = MIMEMultipart("related")
            msg["Subject"] = subject
            msg["From"] = formataddr((from_name, SMTP_USER))
            msg["To"] = to_email

            # Parte alternativa HTML
            msg_alt = MIMEMultipart("alternative")
            msg.attach(msg_alt)

            # Se abbiamo immagine locale e vogliamo fare CID inline
            if image_attachment_path and os.path.exists(image_attachment_path):
                cid = "banner_img_81"
                # Sostituiamo nel body l'eventuale placeholder o aggiungiamo
                html_content = html_content.replace('src=""', f'src="cid:{cid}"')
                if f'cid:{cid}' not in html_content:
                    html_content = html_content.replace('<table class="container"', f'<table class="container"><tr><td><img src="cid:{cid}" style="width:100%;max-width:600px;display:block;"></td></tr>')

                part_html = MIMEText(html_content, "html", "utf-8")
                msg_alt.attach(part_html)

                with open(image_attachment_path, "rb") as f:
                    img_part = MIMEImage(f.read())
                    img_part.add_header("Content-ID", f"<{cid}>")
                    img_part.add_header("Content-Disposition", "inline", filename=os.path.basename(image_attachment_path))
                    msg.attach(img_part)
            else:
                part_html = MIMEText(html_content, "html", "utf-8")
                msg_alt.attach(part_html)

            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=25) as server:
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, [to_email], msg.as_string())

            print(f"[SUCCESS] Email inviata con successo a: {to_email}")
            return True
        except Exception as e:
            print(f"[-] Errore invio email a {to_email}: {e}")
            return False

    @staticmethod
    def send_telegram_photo(chat_id, caption, image_path):
        """Invia foto con caption persuasiva via Telegram Bot API."""
        try:
            url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
            boundary = "----WebKitFormBoundary81PlusAutomation"
            
            with open(image_path, "rb") as f:
                img_data = f.read()

            body = bytearray()
            # Chat ID
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode())
            # Caption
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode())
            # Photo File
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(f'Content-Disposition: form-data; name="photo"; filename="{os.path.basename(image_path)}"\r\n'.encode())
            body.extend(b"Content-Type: image/png\r\n\r\n")
            body.extend(img_data)
            body.extend(b"\r\n")
            body.extend(f"--{boundary}--\r\n".encode())

            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                res = json.loads(resp.read().decode())
                if res.get("ok"):
                    print(f"[SUCCESS] Post Telegram inviato su {chat_id}!")
                    return True
                else:
                    print(f"[-] Errore risposta Telegram: {res}")
                    return False
        except Exception as e:
            print(f"[-] Errore invio Telegram su {chat_id}: {e}")
            return False

    @staticmethod
    def upload_image_to_ftp(local_image_path):
        """Carica l'immagine generata sull'hosting via FTP per renderla accessibile via HTTPS."""
        try:
            ftp = ftplib.FTP()
            ftp.connect(FTP_HOST, FTP_PORT, timeout=25)
            ftp.login(FTP_USER, FTP_PASS)
            
            # Navighiamo in assets/campaigns
            for d in ["assets", "campaigns"]:
                try:
                    ftp.cwd(d)
                except Exception:
                    ftp.mkd(d)
                    ftp.cwd(d)

            fname = os.path.basename(local_image_path)
            with open(local_image_path, "rb") as f:
                ftp.storbinary(f"STOR {fname}", f)
            ftp.quit()

            public_url = f"https://81plus.net/assets/campaigns/{fname}"
            print(f"[FTP] Immagine caricata online: {public_url}")
            return public_url
        except Exception as e:
            print(f"[-] Errore upload FTP immagine: {e}")
            return None


# ══════════════════════════════════════════════════════════════════
# 4. CLI INTERACTION & ORCHESTRAZIONE
# ══════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="81+ Content & Campaign Factory (Email, Immagini, Social, Telegram)")
    parser.add_argument("--list-topics", action="store_true", help="Elenca i pilastri disponibili")
    parser.add_argument("--generate-all", action="store_true", help="Genera l'intero pacchetto grafiche e testi per tutti i pilastri")
    parser.add_argument("--topic", choices=["sicurezza", "haccp", "privacy", "promo_settembre"], default="sicurezza", help="Pilastro tematico")
    parser.add_argument("--test-email", type=str, help="Invia email di test all'indirizzo specificato")
    parser.add_argument("--tg-channel", action="store_true", help="Pubblica il post sul canale Telegram ufficiale")
    parser.add_argument("--tg-admin", action="store_true", help="Invia anteprima del post su Telegram all'Admin")
    parser.add_argument("--ftp-upload", action="store_true", help="Carica immagini generate sul server FTP pubblico")

    args = parser.parse_args()

    if args.list_topics:
        print("\n=== PILASTRI TEMATICI 81+ ===")
        for k, v in PersuasiveCopyFactory.CAMPAIGNS.items():
            print(f" • [{k.upper()}] {v['badge']}")
            print(f"   Titolo Immagine: {v['img_title']}")
            print(f"   Oggetto Email: {v['email_subject']}\n")
        return

    # Se richiesto batch generation di tutti i pilastri
    if args.generate_all:
        print("\n[*] GENERAZIONE COMPLETA MULTI-PILASTRO 81+...")
        manifest = {}
        for top in ["sicurezza", "haccp", "privacy", "promo_settembre"]:
            camp = PersuasiveCopyFactory.get_campaign(top)
            # 1. Banner Email
            p_email, f_email = BrandImageGenerator.create_image(
                top, "email_banner", camp["img_title"], camp["img_highlight"], camp["img_sub"], camp["stat_badge"]
            )
            # 2. Post Social Quadrato
            p_soc, f_soc = BrandImageGenerator.create_image(
                top, "social_post", camp["img_title"], camp["img_highlight"], camp["img_sub"], camp["stat_badge"]
            )
            # 3. Testi
            subj, html = PersuasiveCopyFactory.build_email_html(top, img_url=f"https://81plus.net/assets/campaigns/{f_email}")
            
            # Salvataggio pacchetto HTML e TXT
            with open(os.path.join(LOCAL_OUT_DIR, f"{top}_email.html"), "w", encoding="utf-8") as f:
                f.write(html)
            with open(os.path.join(LOCAL_OUT_DIR, f"{top}_social.txt"), "w", encoding="utf-8") as f:
                f.write(f"{camp['social_hook']}\n\n{camp['social_body']}\n\n{camp['hashtags']}")

            manifest[top] = {
                "banner": f_email,
                "social_img": f_soc,
                "subject": subj,
                "social_hook": camp["social_hook"]
            }

        print(f"\n[SUCCESS] Pacchetto generato con successo in: {LOCAL_OUT_DIR}")
        print(json.dumps(manifest, indent=2))
        return

    # Singolo pilastro
    camp = PersuasiveCopyFactory.get_campaign(args.topic)
    print(f"\n[*] Elaborazione Pilastro: {args.topic.upper()} — {camp['badge']}")

    # 1. Genera Banner Email e Post Social
    p_banner, f_banner = BrandImageGenerator.create_image(
        args.topic, "email_banner", camp["img_title"], camp["img_highlight"], camp["img_sub"], camp["stat_badge"]
    )
    p_social, f_social = BrandImageGenerator.create_image(
        args.topic, "social_post", camp["img_title"], camp["img_highlight"], camp["img_sub"], camp["stat_badge"]
    )

    # 2. Upload FTP se richiesto
    img_url = ""
    if args.ftp_upload:
        img_url = MultiChannelDispatcher.upload_image_to_ftp(p_banner)
        MultiChannelDispatcher.upload_image_to_ftp(p_social)
    else:
        img_url = f"https://81plus.net/assets/campaigns/{f_banner}"

    # 3. Costruzione Email HTML
    subject, html_email = PersuasiveCopyFactory.build_email_html(args.topic, img_url=img_url)

    # 4. Invio Email Test se specificato
    if args.test_email:
        print(f"[*] Invio email di test a: {args.test_email}...")
        MultiChannelDispatcher.send_email(args.test_email, subject, html_email, image_attachment_path=p_banner)

    # 5. Telegram
    caption = f"*{camp['social_hook']}*\n\n{camp['social_body']}\n\n{camp['hashtags']}"
    if args.tg_admin:
        print(f"[*] Invio anteprima Telegram all'Admin ID: {TG_ADMIN_ID}...")
        MultiChannelDispatcher.send_telegram_photo(TG_ADMIN_ID, caption[:1024], p_social)

    if args.tg_channel:
        print(f"[*] Pubblicazione sul Canale Telegram {TG_CHANNEL}...")
        MultiChannelDispatcher.send_telegram_photo(TG_CHANNEL, caption[:1024], p_social)

    print("\n[OK] OPERAZIONE COMPLETATA CON SUCCESSO!")

if __name__ == "__main__":
    main()
