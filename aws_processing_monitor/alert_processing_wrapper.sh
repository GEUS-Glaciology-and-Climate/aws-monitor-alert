#!/usr/bin/env bash

source /home/aws/miniconda3/etc/profile.d/conda.sh
conda activate py39-monitor
echo "Running alert_processing.py at `date -u`"

base_config=$(dirname $0)/aws_azure.ini
python -m alert_processing.check_alerts \
  -c $base_config \
  -c /home/aws/aws-monitor-alert/credentials/credentials.ini

echo "FINISHED"