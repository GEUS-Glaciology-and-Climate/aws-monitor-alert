#!/usr/bin/env python

'''
Monitor and alert based on metrics related to AWS processing.

Currently implemented:
- Check latest BUFR file timestamp at DMI ftp upload directory
- Check aws-l0/tx file update times
- Check aws-l3/tx file update times
- Check aws-l3/level_3 file update times

Patrick Wright, GEUS
Jan 16, 2023
'''

from argparse import ArgumentParser
from configparser import ConfigParser
from datetime import datetime, timedelta, timezone
from pathlib import Path

from alert_processing.email_notification import EmailNotificationClient
from alert_processing.dmi_bufr import check_dmi_ftp
from alert_processing.file_system_status import check_update_time


def parse_arguments():
    parser = ArgumentParser(description="Monitor for aws processing")

    parser.add_argument('-a', '--account', default='/home/aws/aws-monitor-alert/credentials/accounts.ini',
                        type=str, required=False, help='account .ini file')
    parser.add_argument('-p', '--password', default='/home/aws/aws-monitor-alert/credentials/credentials.ini',
                        type=str, required=False, help='credentials .ini file')

    parser.add_argument('--l0-tx-path', default='/data/pypromice_aws/aws-l0/tx',
                        type=Path, required=False, help='Path to l0 tx directory')
    parser.add_argument('--l3-tx-path', default='/data/pypromice_aws/aws-l3/tx',
                        type=Path, required=False, help='Path to l3 tx directory')
    parser.add_argument('--l3-joined-path', default='/data/pypromice_aws/aws-l3/level_3',
                        type=Path, required=False, help='Path to l3 level_3 (joined) directory')
    parser.add_argument('--bufr-out-path',
                        default='/data/pypromice_aws/pypromice/last_modified_utils/pypromice/postprocess/BUFR_out',
                        type=Path, required=False, help='Path to BUFR_out directory')
    parser.add_argument('--bufr-backup-path',
                        default='/data/pypromice_aws/pypromice/last_modified_utils/pypromice/postprocess/BUFR_backup',
                        type=Path, required=False, help='Path to BUFR_backup directory')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    """Executed from the command line"""
    args = parse_arguments()

    # Set credential paths
    accounts_file = args.account
    credentials_file = args.password

    # Define accounts and credentials ini file paths
    accounts_ini = ConfigParser()
    accounts_ini.read_file(open(accounts_file))
    accounts_ini.read(credentials_file)

    receiver_emails = [
        "pajwr@geus.dk",
        "pho@geus.dk",
        "rsf@geus.dk",
        "rabni@geus.dk",
        "syhsv@geus.dk",
        "aso@geus.dk",
        "shl@geus.dk",
        "bav@geus.dk",
        "maclu@geus.dk",
    ]

    notification_client = EmailNotificationClient(
        receiver_emails=receiver_emails,
        account=accounts_ini.get('aws', 'account'),
        smtp_server=accounts_ini.get('aws', 'server'),
        port=accounts_ini.getint('aws', 'port'),
        password=accounts_ini.get('aws', 'password'),
    )

    # Reference time for activating alarms
    current_time = datetime.now(tz=timezone.utc)

    # ==============================================================
    # DMI FTP
    # ==============================================================
    dmi_alert = check_dmi_ftp(
        current_time=current_time,
        max_age=timedelta(hours=2),
        user=accounts_ini.get('dmi', 'user'),
        passwd=accounts_ini.get('dmi', 'passwd'),
        host=accounts_ini.get('dmi', 'host'),
    )
    if dmi_alert:
        notification_client.send_alert_email(
            subject_text="ALERT: BUFR ftp server is not updated!",
            body_text='''The most recent concatenated BUFR file at the DMI ftp upload directory is >1 hr old (should be ~3 minutes old).
            There could be a problem with pypromice processing or the ftp upload itself.
            '''
        )

    # ==============================================================
    # BUFR FILES
    # ==============================================================
    dmi_alert_1 = check_update_time(
        args.bufr_out_path,
        current_time=current_time,
        max_age=timedelta(hours=2),
    )
    dmi_alert_2 = check_update_time(
        args.bufr_backup_path,
        current_time=current_time,
        max_age=timedelta(hours=2),
    )
    if dmi_alert_1:
        notification_client.send_alert_email(
            subject_text="ALERT: BUFR_out files are not updating!",
            body_text='''
            The individual station BUFR files and/or the concatenated BUFR file are not updating.
            Expected behavior is for the BUFR_out directory to be emptied and re-populated every hour.
            ''',
        )
    else:
        print('BUFR_out files are current. No alert issued.')

    if dmi_alert_2:
        notification_client.send_alert_email(
            subject_text="ALERT: BUFR_backup files are not updating!",
            body_text='''
            The concatenated BUFR files in the BUFR_backup directory are not updating.
            We expect to have one file per hour, for the last 48 hrs.
            ''',
        )
    else:
        print('BUFR_backup files are current. No alert issued.')

    # ==============================================================
    # L0 TX
    # ==============================================================
    l0tx_alert = check_update_time(
        args.l0_tx_path,
        current_time=current_time,
        max_age=timedelta(hours=1),
    )
    if l0tx_alert:
        notification_client.send_alert_email(
            subject_text="ALERT: aws-l0/tx files are not updating!",
            body_text='''
                The most recently updated file at aws-l0/tx on Azure is >1 hr old.
                There could be a problem with pypromice processing.
                '''
        )
    else:
        print('aws-l0/tx files are current. No alert issued.')

    # ==============================================================
    # L3 TX
    # ==============================================================
    l3tx_alert = check_update_time(
        args.l3_tx_path,
        current_time=current_time,
        max_age=timedelta(hours=1),
    )
    if l3tx_alert:
        notification_client.send_alert_email(
            subject_text="ALERT: aws-l3/tx files are not updating!",
            body_text='''
            The most recently updated file at aws-l3/tx on Azure is >1 hr old.
            There could be a problem with pypromice processing.
            ''',
        )
    else:
        print('aws-l3/tx files are current. No alert issued.')

    # ==============================================================
    # L3 level_3 (joined)
    # ==============================================================
    l3joined_alert = check_update_time(
        args.l3_joined_path,
        current_time=current_time,
        max_age=timedelta(hours=1),
    )

    if l3joined_alert:
        notification_client.send_alert_email(
            subject_text="ALERT: aws-l3/level_3 joined files are not updating!",
            body_text='''
            The most recently updated file at aws-l3/level_3 on Azure is >1 hr old.
            There could be a problem with pypromice processing.
            ''',
        )
    else:
        print('aws-l3/level_3 files are current. No alert issued.')

else:
    """Executed on import"""
    pass
