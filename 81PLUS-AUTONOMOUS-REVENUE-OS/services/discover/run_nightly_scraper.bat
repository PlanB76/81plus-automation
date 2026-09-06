@echo off
REM ==============================================================================
REM 81+ AUTONOMOUS REVENUE OS — NIGHTLY LEAD FACTORY SCRAPER (03:00 AM)
REM Zero Mani: Estrae aziende da dataset pubblici (Registro Imprese, INI-PEC, PG),
REM cataloga per codice ATECO 6 cifre e classe di rischio D.Lgs. 81/08,
REM classifica PEC vs email classiche e alimenta il Golden Record locale.
REM ==============================================================================

cd /d "c:\81PLUS_GLOBAL_MASTER\81plus.net\GITHUB_81PLUS_AUTOMATION\81PLUS-AUTONOMOUS-REVENUE-OS"
echo [%date% %time%] Avvio Nightly Lead Scraper 81+ >> services\discover\nightly_scraper.log

"C:\Users\piano\AppData\Local\Programs\Python\Python312\python.exe" services\discover\public_dataset_scraper.py >> services\discover\nightly_scraper.log 2>&1

echo [%date% %time%] Esecuzione completata con codice %ERRORLEVEL% >> services\discover\nightly_scraper.log
