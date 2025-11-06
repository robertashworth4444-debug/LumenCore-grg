#!/bin/bash
TEMP_FILE="/sys/class/thermal/thermal_zone0/temp"
if [[ ! -f "$TEMP_FILE" ]]; then echo "no temp sensor"; exit 1; fi
while true; do
  T=$(( $(cat "$TEMP_FILE") / 1000 ))
  echo "$(date +%T)  Temp: ${T}°C"
  sleep 5
done
