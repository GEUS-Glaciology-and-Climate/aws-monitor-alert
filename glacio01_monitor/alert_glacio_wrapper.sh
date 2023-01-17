#!/usr/bin/env bash

source /home/aws/miniconda3/etc/profile.d/conda.sh
conda activate py39-monitor
echo "Running alert_glacio.py at `date -u`"

python /home/aws/aws-monitor-alert/glacio01_monitor/alert_glacio.py

echo "FINISHED"