@echo off
REM ==============================================================================
REM 81+ AUTONOMOUS REVENUE OS — LOCAL H24 SCRAPER SERVICE (ZERO GITHUB MINUTI)
REM ==============================================================================
cd /d "c:\81PLUS_GLOBAL_MASTER\81plus.net\GITHUB_81PLUS_AUTOMATION\81PLUS-AUTONOMOUS-REVENUE-OS"

"C:\Users\piano\AppData\Local\Programs\Python\Python312\python.exe" services\discover\continuous_scraper_daemon.py >> services\discover\h24_scraper.log 2>&1
