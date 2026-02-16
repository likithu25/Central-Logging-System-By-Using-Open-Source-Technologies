#!/bin/bash
# Advanced log generator for VM clients
# Simulates IoT sensors and application scenarios

LOG_DIR="$HOME/logs"
mkdir -p "$LOG_DIR"

APP_LOG="$LOG_DIR/app.log"
ERROR_LOG="$LOG_DIR/error.log"
ACCESS_LOG="$LOG_DIR/access.log"
SENSOR_LOG="$LOG_DIR/sensor.log"

HOSTNAME=$(hostname)
counter=1

# Initialize sensor values
TEMP=22.0
HUMIDITY=50.0
MOTION_STATE="IDLE"

echo "Starting IoT log generator on $HOSTNAME..."
echo "Logs will be written to: $LOG_DIR"
echo "Press Ctrl+C to stop"
echo ""

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # IoT Sensor readings (every cycle)
    # Temperature: varies between 18-28°C
    TEMP_CHANGE=$(awk -v seed="$RANDOM" 'BEGIN{srand(seed); printf "%.2f", (rand()-0.5)*2}')
    TEMP=$(awk -v t="$TEMP" -v c="$TEMP_CHANGE" 'BEGIN{printf "%.2f", t+c}')
    if (( $(awk -v t="$TEMP" 'BEGIN{print (t<18)}') )); then TEMP=18.0; fi
    if (( $(awk -v t="$TEMP" 'BEGIN{print (t>28)}') )); then TEMP=28.0; fi
    
    # Humidity: varies between 30-70%
    HUMIDITY_CHANGE=$(awk -v seed="$RANDOM" 'BEGIN{srand(seed); printf "%.2f", (rand()-0.5)*4}')
    HUMIDITY=$(awk -v h="$HUMIDITY" -v c="$HUMIDITY_CHANGE" 'BEGIN{printf "%.2f", h+c}')
    if (( $(awk -v h="$HUMIDITY" 'BEGIN{print (h<30)}') )); then HUMIDITY=30.0; fi
    if (( $(awk -v h="$HUMIDITY" 'BEGIN{print (h>70)}') )); then HUMIDITY=70.0; fi
    
    # Motion detection (random)
    if [ $((RANDOM % 10)) -lt 3 ]; then
        MOTION_STATE="DETECTED"
    else
        MOTION_STATE="IDLE"
    fi
    
    # Log sensor data
    echo "$TIMESTAMP - [SENSOR] [$HOSTNAME] Temperature: ${TEMP}°C" >> "$SENSOR_LOG"
    echo "$TIMESTAMP - [SENSOR] [$HOSTNAME] Humidity: ${HUMIDITY}%" >> "$SENSOR_LOG"
    echo "$TIMESTAMP - [SENSOR] [$HOSTNAME] Motion: $MOTION_STATE" >> "$SENSOR_LOG"
    
    # Also log combined sensor data to app log
    echo "$TIMESTAMP - [INFO] [$HOSTNAME] TEMP=${TEMP}°C HUMIDITY=${HUMIDITY}% STATUS=OK" >> "$APP_LOG"
    
    # Check for sensor alerts
    if (( $(awk -v t="$TEMP" 'BEGIN{print (t>26)}') )); then
        echo "$TIMESTAMP - [WARN] [$HOSTNAME] High temperature alert: ${TEMP}°C" >> "$APP_LOG"
    fi
    if (( $(awk -v h="$HUMIDITY" 'BEGIN{print (h>65)}') )); then
        echo "$TIMESTAMP - [WARN] [$HOSTNAME] High humidity alert: ${HUMIDITY}%" >> "$APP_LOG"
    fi
    if [ "$MOTION_STATE" = "DETECTED" ]; then
        echo "$TIMESTAMP - [INFO] [$HOSTNAME] Motion detected in zone" >> "$APP_LOG"
    fi
    
    # Application logs (every 5 seconds)
    RAND_ACTION=$((RANDOM % 6))
    case $RAND_ACTION in
        0) 
            echo "$TIMESTAMP - [INFO] [$HOSTNAME] Processing user request #$counter" >> "$APP_LOG"
            ;;
        1)
            MEMORY=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
            echo "$TIMESTAMP - [DEBUG] [$HOSTNAME] Memory usage: $MEMORY" >> "$APP_LOG"
            ;;
        2)
            CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
            echo "$TIMESTAMP - [INFO] [$HOSTNAME] CPU usage: ${CPU}%" >> "$APP_LOG"
            ;;
        3)
            echo "$TIMESTAMP - [INFO] [$HOSTNAME] Database query executed successfully (${RANDOM}ms)" >> "$APP_LOG"
            ;;
        4)
            echo "$TIMESTAMP - [WARN] [$HOSTNAME] Cache miss - fetching from database" >> "$APP_LOG"
            ;;
        5)
            echo "$TIMESTAMP - [INFO] [$HOSTNAME] Background job completed: task_$((RANDOM % 100))" >> "$APP_LOG"
            ;;
    esac
    
    # Simulate access logs (web server style)
    if [ $((counter % 3)) -eq 0 ]; then
        HTTP_CODES=(200 200 200 200 304 404 500)
        RANDOM_CODE=${HTTP_CODES[$RANDOM % ${#HTTP_CODES[@]}]}
        PATHS=("/api/users" "/api/products" "/api/orders" "/health" "/metrics" "/login" "/dashboard")
        RANDOM_PATH=${PATHS[$RANDOM % ${#PATHS[@]}]}
        METHODS=("GET" "POST" "PUT" "DELETE")
        RANDOM_METHOD=${METHODS[$RANDOM % ${#METHODS[@]}]}
        IP="192.168.1.$((RANDOM % 255))"
        RESPONSE_TIME=$((RANDOM % 500))
        
        echo "$TIMESTAMP - $IP - \"$RANDOM_METHOD $RANDOM_PATH HTTP/1.1\" $RANDOM_CODE ${RESPONSE_TIME}ms" >> "$ACCESS_LOG"
    fi
    
    # Simulate errors (less frequent)
    if [ $((counter % 15)) -eq 0 ]; then
        ERROR_TYPES=(
            "Connection timeout to database server"
            "Failed to authenticate user: invalid token"
            "Disk space low: 85% used"
            "Network latency exceeded threshold: 500ms"
            "Failed to send notification: service unavailable"
            "Rate limit exceeded for IP 192.168.1.$((RANDOM % 255))"
            "Sensor communication timeout"
            "IoT device offline: sensor_$((RANDOM % 10))"
        )
        RANDOM_ERROR=${ERROR_TYPES[$RANDOM % ${#ERROR_TYPES[@]}]}
        echo "$TIMESTAMP - [ERROR] [$HOSTNAME] $RANDOM_ERROR" >> "$ERROR_LOG"
        echo "$TIMESTAMP - [ERROR] [$HOSTNAME] $RANDOM_ERROR" >> "$APP_LOG"
    fi
    
    # Simulate warnings (occasional)
    if [ $((counter % 8)) -eq 0 ]; then
        WARN_TYPES=(
            "High memory usage detected: 75%"
            "Slow query detected: 1200ms"
            "Connection pool nearly exhausted: 18/20"
            "API rate limit approaching: 80% of quota"
        )
        RANDOM_WARN=${WARN_TYPES[$RANDOM % ${#WARN_TYPES[@]}]}
        echo "$TIMESTAMP - [WARN] [$HOSTNAME] $RANDOM_WARN" >> "$APP_LOG"
    fi
    
    counter=$((counter + 1))
    sleep 5
done
