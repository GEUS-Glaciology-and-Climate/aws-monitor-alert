#!/usr/bin/env bash

# Intended to be run as hourly cron job from glacio01

# ssh to the Azure aws server (using ssh config), then
# (optionally) rename the glacio01_* file with current datetime.
# touch the file to reset the update time for the file

# The file at Azure can then be monitored for update time
# as a way to check that glacio01 is alive and well!

# Patrick Wright, GEUS
# Jan 11, 2023

# Rename the monitor file with a current timestamp, then touch to update the last update time:
# filename="glacio01_$(date -u +"%Y%m%dT%H%M").txt"
# ssh azure-aws -T "cd /home/aws/aws-monitor-alert/glacio01_monitor; mv glacio01_*.txt $filename; touch $filename"

# Create a generic monitor file, and simply touch the file to update the last updated time
filename="glacio01_monitor.txt"
ssh azure-aws -T "cd /home/aws/aws-monitor-alert/glacio01_monitor; touch -m $filename"

