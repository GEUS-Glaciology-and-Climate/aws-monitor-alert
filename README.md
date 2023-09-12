# aws-monitor-alert

Monitoring and alerting of processing resources for automatic weather stations (aws).

These repository implement our own custom monitoring and alerting scripts (sending emails from geus.aws@gmail.com), and
are
separate from any Azure monitoring tools. Metrics on the Azure virtual machine such as CPU, memory, disk space, etc are
currently monitored using built-in Azure monitoring tools.

## Installation

It is implemented as a python package and can be installed using pip

```
pip install .
```

## Structure

The module `alert_processing` contains all main functionality for querying file status in the pipeline and for sending
email notifications. The source code is located in `./src/alert_processing`.

## Check alerts

The script `alert_processing.check_alerts` reads and validates datetime information from

* latest BUFR file timestamp at DMI ftp upload directory
* latest BUFR file timestamp bufr out path
* latest BUFR file timestamp bufr backup path
* latest aws-l0/tx file update times
* latest aws-l3/tx file update times
* latest aws-l3/level_3 file update times

It uses one or many ini-files for configuring the local environment and credentials. See [AWS Azure](#aws-azure) for
example.

```bash
python -m alert_processing.check_alerts -c path/to/environment_config.ini path/to/credentials.ini
```

### Logs

The script writes log messages to stdout.
It is also possible to prove a log path to the configuration file which
will be updated
using [TimedRotatingFileHandler](https://docs.python.org/3.10/library/logging.handlers.html#logging.handlers.TimedRotatingFileHandler)
keeping log files from the last 10 days.

### AWS Azure

The directory `aws_processing_monitor` contains the environment configuration for aws_azure and a wrapper script to
invoke `check_alerts`:

* [aws_processing_monitor/aws_azure.ini](aws_processing_monitor/aws_azure.ini)
* [aws_processing_monitor/alert_processing_wrapper.sh](aws_processing_monitor/alert_processing_wrapper.sh)

## Crontab configurations

### AWS Azure

Contab configuration on the AWS Azure server. It is configured to run at 11 minutes after the hour.

```cronexp
11 * * * * . /home/aws/.bashrc; cd /home/aws/aws-monitor-alert/aws_processing_monitor; ./alert_processing_wrapper.sh > stdout 2>stderr
```

# glacio01 monitor

This section contains the original readme entry related to glacio01 monitoring. This functionality has not been changed
in the newest updates.

A simple monitoring tool to check if the glacio01 server is alive.

The `alert_glacio.py` monitoring script is intended to work with the following routine:

- glacio01 has an hourly (top-of-hour) cron (`ssh_to_azure.sh`) that touches a simple text file at
  Azure (`glacio01_monitor.txt`). This updates the last-updated time on the file.
- `alert_glacio.py` runs at 2 min after the hour on Azure VM, and checks the update time of the file.
- If time is older than an hour ago (and younger than two hours ago),
  we send out email alerts that glacio01 may be down. Checking two hours
  ago is to prevent repeated emails if the server is down for an extended time.

Run with `alert_glacio_wrappper.sh` on Azure crontab as:

```
# Monitor/alert for glacio01
2 * * * * . /home/aws/.bashrc; cd /home/aws/aws-monitor-alert/glacio01_monitor; ./alert_glacio_wrapper.sh > stdout 2>stder
```

`ssh_to_azure.sh` is run on glacio01 crontab as:

```
# ssh to Azure and update .txt file, for monitoring of glacio01
0 * * * * . /home/aws/.bashrc; cd /home/aws/aws-monitor-alert/glacio01_monitor; ./ssh_to_azure.sh  > stdout 2>stderr
```

A successful run with no alerts issued will appear in `~/aws-monitor-alert/glacio01_monitor/stdout` as:

```
Running alert_glacio.py at Tue Jan 17 13:32:26 UTC 2023
glacio01_monitor.txt is current. No alert issued.
FINISHED
```
