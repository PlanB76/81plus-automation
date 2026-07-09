#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wrapper email 81+ — replica struttura/visual dei template in MARKETING81+ (header nero,
barra arancione, ribbon riprova sociale, corpo bianco, footer con WhatsApp/unsubscribe)."""
import html
def wrap(cfg, subject, inner_html, cta_url=None, cta_text=None):
    L=cfg["links"]
    cta=""
    if cta_url and cta_text:
        cta=(f'<tr><td style="padding:6px 30px 26px;"><a href="{cta_url}" '
             f'style="display:inline-block;background:#FB6B00;color:#080808;font-weight:800;text-decoration:none;'
             f'padding:14px 26px;border-radius:8px;font-size:16px;">{html.escape(cta_text)} &rarr;</a></td></tr>')
    return f'''<!DOCTYPE html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<!-- OGGETTO: {html.escape(subject)} --></head>
<body style="margin:0;padding:0;background:#e9e9e9;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#e9e9e9;padding:24px 0;"><tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background:#ffffff;">
  <tr><td style="background:#080808;padding:18px 28px;">
    <span style="font-size:24px;font-weight:800;color:#FB6B00;letter-spacing:1px;">81+</span>
    <span style="font-size:13px;color:#ffffff;letter-spacing:2px;">SICURISSIMO</span></td></tr>
  <tr><td style="height:4px;background:#FB6B00;line-height:4px;font-size:0;">&nbsp;</td></tr>
  <tr><td style="background:#0c0c0c;padding:11px 26px;color:#cfcfcf;font-size:11px;line-height:1.6;text-align:center;">
    Oltre 8.000 aziende con membership 81+ &nbsp;&bull;&nbsp; Oltre 32.000 aziende hanno scelto Sicurissimo &nbsp;&bull;&nbsp; Oltre 225.000 persone formate</td></tr>
  <tr><td style="padding:28px 30px 8px;color:#111111;font-size:15px;line-height:1.65;">{inner_html}</td></tr>
  {cta}
  <tr><td style="background:#0c0c0c;padding:20px 28px;color:#9a9a9a;font-size:12px;line-height:1.7;text-align:center;">
    Hai bisogno di aiuto? Scrivici su <a href="https://wa.me/393388771737" style="color:#FB6B00;text-decoration:none;">WhatsApp 338 877 1737</a><br>
    <a href="{cfg['site_base']}" style="color:#FB6B00;text-decoration:none;">81plus.net</a> &nbsp;&bull;&nbsp;
    <a href="{L['youtube']}" style="color:#FB6B00;text-decoration:none;">YouTube</a> &nbsp;&bull;&nbsp;
    <a href="{L['telegram_channel']}" style="color:#FB6B00;text-decoration:none;">Telegram</a><br>
    <span style="color:#666;">{cfg['legal']['vendor']}</span><br>
    <a href="{{{{ unsubscribe }}}}" style="color:#777;">Annulla iscrizione</a></td></tr>
</table></td></tr></table></body></html>'''
