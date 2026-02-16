#!/bin/bash
# Simple log generator - creates basic logs for testing

LOG_DIR="$HOME/logs"
mkdir -p "$LOG_DIR"

HOSTNAME=$(hostname)
LOG_FILE="$LOG_DIR/app.log"

echo "Simple log generator started on $HOSTNAME"
echo "Writing to: $LOG_FILE"
echo ""

counter=1

while true; do
    # Write a simple log entry
    echo "$(date) - [INFO] [$HOSTNAME] Log entry #$counter" >> "$LOG_FILE"
    
    # Random log level every few entries
    if [ $((counter % 5)) -eq 0 ]; then
        echo "$(date) - [DEBUG] [$HOSTNAME] Debug message $counter" >> "$LOG_FILE"
    fi
    
    if [ $((counter % 7)) -eq 0 ]; then
        echo "$(date) - [WARN] [$HOSTNAME] Warning message $counter" >> "$LOG_FILE"
    fi
    
    if [ $((counter % 20)) -eq 0 ]; then
        echo "$(date) - [ERROR] [$HOSTNAME] Error occurred at entry $counter" >> "$LOG_FILE"
    fi
    
    counter=$((counter + 1))
    sleep 5
done
