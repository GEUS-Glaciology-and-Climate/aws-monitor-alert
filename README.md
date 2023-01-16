# aws-monitor-alert
Monitoring and alerting of processing resources for automatic weather stations (aws).

To develop with this code, you need to activate the `py39-monitor` conda environment on Azure.
If you are developing elsewhere setup a fresh py 3.9 conda env and install any additional needed requirements.
(`requirements.txt` coming soon...!)

A `credentials` directory containing `accounts.ini` and `credentials.ini` is required at the top-level directory of this repo (will be ignored with `.gitignore`).

Note that these scripts implement our own custom monitoring and alerting (sending emails from geus.aws@gmail.com), and are separate from any Azure monitoring tools. Metrics on the Azure virtual machine such as CPU, memory, disk space, etc are currently monitored using built-in Azure monitoring tools.

The following are currently implemented:

## glacio01 monitor
A simple monitoring tool to check if the glacio01 server is alive.

The `alert_glacio.py` monitoring script is intended to work with the following routine:

- glacio01 has an hourly (top-of-hour) cron (`ssh_to_azure.sh`) that touches a simple text file at
  Azure (`glacio01_monitor.txt`). This updates the last-updated time on the file.
- `alert_glacio.py` runs at 2 min after the hour on Azure VM, and checks the update time of the file.
- If time is older than an hour ago (and younger than two hours ago),
  we send out email alerts that glacio01 may be down. Checking two hours
  ago is to prevent repeated emails if the server is down for an extended time.

Run on Azure crontab as:

```
# Monitor/alert for glacio01
2 * * * * conda activate py39-monitor; cd /home/aws/aws-monitor-alert/glacio01_monitor/ && python alert_glacio.py > stdout 2>stderr; conda deactivate
```

Run on glacio01 crontab as:
```
# ssh to Azure and update .txt file, for monitoring of glacio01
0 * * * * . /home/aws/.bashrc; cd /home/aws/aws-monitor-alert/glacio01_monitor; ./ssh_to_azure.sh  > stdout 2>stderr
```

## AWS processing monitors

Multiple monitors for AWS processing (pypromice) are run from `alert_processing.py` at 10 minutes after the hour. Run on Azure crontab as:

```
# Monitor/alert for aws processing
10 * * * * conda activate py39-monitor; cd /home/aws/aws-monitor-alert/aws_processing_monitor/ && python alert_processing.py > stdout 2>stderr; conda deactivate
```
Individually monitored processes include the following:

### DMI BUFR upload

Log into the DMI ftp server and get the filename of the most recently updated file (files are named such as `'geus_20230116T1307.bufr'`). Parse the time string into an epoch (unix) time. If this time is >1 hr old (and <2 hrs old), send out alert emails. We should always have some stations reporting hourly all year round, therefore we should always have an hourly BUFR file upload.
