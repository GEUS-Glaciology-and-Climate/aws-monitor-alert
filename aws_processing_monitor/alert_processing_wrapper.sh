#!/usr/bin/env bash

source /home/aws/miniconda3/etc/profile.d/conda.sh
conda activate py39-monitor
echo "Running alert_processing.py at `date -u`"

python /home/aws/aws-monitor-alert/aws_processing_monitor/alert_processing.py

echo "FINISHED"