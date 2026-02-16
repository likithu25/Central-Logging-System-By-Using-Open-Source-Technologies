@echo off
echo ============================================================
echo Starting Professional Light Theme Dashboard
echo ============================================================
echo.
echo Dashboard Features:
echo   - Clean light theme with professional styling
echo   - All graphs: Temperature, Humidity, System Health, Motion
echo   - Network devices monitoring
echo   - Real-time alerts with search functionality
echo   - Minimal padding and margins for maximum space
echo.
echo ============================================================

cd /d "%~dp0\.."

echo Starting dashboard server...
python dashboard\dashboard_light_professional.py

pause
