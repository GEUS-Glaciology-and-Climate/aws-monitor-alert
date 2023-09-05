#!/usr/bin/env bash

source /home/aws/miniconda3/etc/profile.d/conda.sh
conda activate py39-monitor
echo "Running alert_processing.py at `date -u`"

python /home/aws/aws-monitor-alert/src/alert_processing/check_alerts.py

echo "FINISHED"