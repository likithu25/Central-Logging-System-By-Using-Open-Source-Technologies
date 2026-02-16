@echo off
echo ============================================================
echo Starting ALL IoT Simulators + Network Devices
echo ============================================================
echo.
echo Starting 7 simulators:
echo  [1] Temperature Sensor
echo  [2] Humidity Sensor
echo  [3] Motion Sensor
echo  [4] System Health Monitor
echo  [5] Security Logger
echo  [6] Application Logger
echo  [7] Network Devices (Router, Switch, Firewall, Hub, Modem)
echo.
echo ============================================================

cd /d "%~dp0\.."

start "Temperature Sensor" cmd /k python simulators\temperature_sensor_cloud.py
timeout /t 2 >nul

start "Humidity Sensor" cmd /k python simulators\humidity_sensor_cloud.py
timeout /t 2 >nul

start "Motion Sensor" cmd /k python simulators\motion_sensor_cloud.py
timeout /t 2 >nul

start "System Health" cmd /k python simulators\system_health_cloud.py
timeout /t 2 >nul

start "Security Logger" cmd /k python simulators\security_logger_cloud.py
timeout /t 2 >nul

start "Application Logger" cmd /k python simulators\application_logger_cloud.py
timeout /t 2 >nul

start "Network Devices" cmd /k python simulators\network_devices_cloud.py

echo.
echo ============================================================
echo All 7 simulators are now running!
echo Close individual windows to stop specific simulators
echo ============================================================
pause
