@echo off
REM ==============================================================================
REM 81+ ANFOS NIGHTLY VALIDATION EXECUTOR
REM Task: 5 nuove validazioni corso ogni notte su centri.anfos.it
REM ==============================================================================
setlocal
cd /d "c:\81PLUS_GLOBAL_MASTER\81plus.net\GITHUB_81PLUS_AUTOMATION\81PLUS-AUTONOMOUS-REVENUE-OS\services\srv_compliance"

echo [%date% %time%] Avvio esecuzione notturna ANFOS Bot >> "anfos_nightly_run.log"
python anfos_validation_bot.py >> "anfos_nightly_run.log" 2>&1
echo [%date% %time%] Conclusione esecuzione ANFOS Bot >> "anfos_nightly_run.log"

exit /b 0
