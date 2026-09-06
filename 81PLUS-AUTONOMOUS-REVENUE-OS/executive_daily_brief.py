"""
81PLUS-AUTONOMOUS-REVENUE-OS
executive_daily_brief.py — Entry point rapido per l'Autonomous CEO Daily Brief
"""
import os
import sys
import importlib

# Caricamento dinamico per cartella con prefisso numerico
ceo_mod = importlib.import_module("80_EXECUTIVE81.ceo_daily_brief")
generate_ceo_brief = ceo_mod.generate_ceo_brief

if __name__ == "__main__":
    generate_ceo_brief()
