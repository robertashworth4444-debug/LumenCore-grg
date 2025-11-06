#!/bin/bash
LOGFILE="/var/log/lumencore_harmonics.log"
STATUS="/var/www/lumen-core/status.txt"
mkdir -p /var/log

timestamp=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
echo "[$timestamp] Starting harmonic cycle..." >> "$LOGFILE"

echo "=== LumenCore Node Report @ $timestamp ===" > "$STATUS"

# Record Coherence index
COH=$(bash /opt/lumen-core/harmonic/coherence.sh 2>/dev/null)
echo "Coherence Index: $COH" | tee -a "$LOGFILE" >> "$STATUS"

# Run harmonic simulations (short form)
echo "--- Harmony Trial ---" >> "$LOGFILE"
python3 /opt/lumen-core/harmonic/harmony_trial.py >> "$LOGFILE" 2>&1

echo "--- Self-Tuning AI ---" >> "$LOGFILE"
python3 /opt/lumen-core/harmonic/self_tune.py >> "$LOGFILE" 2>&1

# Append summary to web status
echo "Thermal sensor: $(if [ -f /sys/class/thermal/thermal_zone0/temp ]; then echo OK; else echo None; fi)" >> "$STATUS"
echo "Recent log tail:" >> "$STATUS"
tail -n 5 "$LOGFILE" >> "$STATUS"

echo "[$timestamp] ✅ LumenCore harmonic cycle complete" >> "$LOGFILE"
