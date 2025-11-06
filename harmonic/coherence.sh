#!/bin/bash
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then VAR=$(cat /sys/class/thermal/thermal_zone0/temp); else VAR=50000; fi
LOAD=$(awk '{print $1}' /proc/loadavg)
echo "scale=4; 1/(1+($LOAD*($VAR/100000)))" | bc -l
