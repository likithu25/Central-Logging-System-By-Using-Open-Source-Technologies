#!/bin/bash
# IoT Sensor Log Generator - Temperature, Humidity, and more
# For VM clients to generate realistic sensor logs

LOG_DIR="$HOME/logs"
mkdir -p "$LOG_DIR"

TEMP_LOG="$LOG_DIR/temperature.log"
HUMIDITY_LOG="$LOG_DIR/humidity.log"
SENSOR_LOG="$LOG_DIR/sensors.log"
APP_LOG="$LOG_DIR/app.log"

HOSTNAME=$(hostname)
counter=1

# Temperature range: 15-35°C
# Humidity range: 30-80%

echo "Starting IoT sensor log generator on $HOSTNAME..."
echo "Logs directory: $LOG_DIR"
echo "Press Ctrl+C to stop"
echo ""

# Initialize sensor values
TEMP=22.5
HUMIDITY=50.0

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Temperature sensor (with realistic fluctuation)
    TEMP_CHANGE=$(awk -v min=-0.5 -v max=0.5 'BEGIN{srand(); print min+rand()*(max-min)}')
    TEMP=$(awk -v temp=$TEMP -v change=$TEMP_CHANGE 'BEGIN{printf "%.2f", temp + change}')
    
    # Keep temperature in realistic range
    if (( $(echo "$TEMP > 35" | bc -l) )); then
        TEMP=35.0
    elif (( $(echo "$TEMP < 15" | bc -l) )); then
        TEMP=15.0
    fi
    
    # Humidity sensor (with realistic fluctuation)
    HUM_CHANGE=$(awk -v min=-2 -v max=2 'BEGIN{srand(); print min+rand()*(max-min)}')
    HUMIDITY=$(awk -v hum=$HUMIDITY -v change=$HUM_CHANGE 'BEGIN{printf "%.2f", hum + change}')
    
    # Keep humidity in realistic range
    if (( $(echo "$HUMIDITY > 80" | bc -l) )); then
        HUMIDITY=80.0
    elif (( $(echo "$HUMIDITY < 30" | bc -l) )); then
        HUMIDITY=30.0
    fi
    
    # Temperature log
    echo "$TIMESTAMP - [SENSOR] [$HOSTNAME] Temperature: ${TEMP}°C" >> "$TEMP_LOG"
    
    # Humidity log
    echo "$TIMESTAMP - [SENSOR] [$HOSTNAME] Humidity: ${HUMIDITY}%" >> "$HUMIDITY_LOG"
    
    # Combined sensor log
    echo "$TIMESTAMP - [INFO] [$HOSTNAME] TEMP=${TEMP}°C HUMIDITY=${HUMIDITY}% STATUS=OK" >> "$SENSOR_LOG"
    
    # Temperature alerts
    if (( $(echo "$TEMP > 30" | bc -l) )); then
        echo "$TIMESTAMP - [WARN] [$HOSTNAME] High temperature detected: ${TEMP}°C" >> "$SENSOR_LOG"
        echo "$TIMESTAMP - [WARN] [$HOSTNAME] High temperature alert: ${TEMP}°C" >> "$APP_LOG"
    fi
    
    if (( $(echo "$TEMP < 18" | bc -l) )); then
        echo "$TIMESTAMP - [WARN] [$HOSTNAME] Low temperature detected: ${TEMP}°C" >> "$SENSOR_LOG"
        echo "$TIMESTAMP - [WARN] [$HOSTNAME] Low temperature alert: ${TEMP}°C" >> "$APP_LOG"
    fi
    
    # Humidity alerts
    if (( $(echo "$HUMIDITY > 70" | bc -l) )); then
        echo "$TIMESTAMP - [WARN] [$HOSTNAME] High humidity detected: ${HUMIDITY}%" >> "$SENSOR_LOG"
        echo "$TIMESTAMP - [WARN] [$HOSTNAME] High humidity alert: ${HUMIDITY}%" >> "$APP_LOG"
    fi
    
    if (( $(echo "$HUMIDITY < 35" | bc -l) )); then
        echo "$TIMESTAMP - [WARN] [$HOSTNAME] Low humidity detected: ${HUMIDITY}%" >> "$SENSOR_LOG"
        echo "$TIMESTAMP - [WARN] [$HOSTNAME] Low humidity alert: ${HUMIDITY}%" >> "$APP_LOG"
    fi
    
    # Occasional sensor errors (5% chance)
    RAND=$((RANDOM % 100))
    if [ $RAND -lt 5 ]; then
        ERROR_TYPES=(
            "Temperature sensor timeout - retrying"
            "Humidity sensor read error - CRC mismatch"
            "I2C communication error on sensor bus"
            "Sensor calibration drift detected"
        )
        RANDOM_ERROR=${ERROR_TYPES[$RANDOM % ${#ERROR_TYPES[@]}]}
        echo "$TIMESTAMP - [ERROR] [$HOSTNAME] $RANDOM_ERROR" >> "$SENSOR_LOG"
        echo "$TIMESTAMP - [ERROR] [$HOSTNAME] $RANDOM_ERROR" >> "$APP_LOG"
    fi
    
    # Application status logs (every 3rd iteration)
    if [ $((counter % 3)) -eq 0 ]; then
        echo "$TIMESTAMP - [INFO] [$HOSTNAME] Sensor data transmitted successfully" >> "$APP_LOG"
        echo "$TIMESTAMP - [DEBUG] [$HOSTNAME] Data point #$counter collected" >> "$APP_LOG"
    fi
    
    # Device status (every 10th iteration)
    if [ $((counter % 10)) -eq 0 ]; then
        CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
        MEM=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
        echo "$TIMESTAMP - [INFO] [$HOSTNAME] Device Status: CPU=${CPU}% MEM=$MEM" >> "$APP_LOG"
    fi
    
    counter=$((counter + 1))
    sleep 10
done
