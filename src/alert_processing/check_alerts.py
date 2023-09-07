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
import logging
import sys
from argparse import ArgumentParser
from configparser import ConfigParser
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping

from alert_processing.email_notification import (
    EmailNotificationClient,
    NotificationClient,
    LogNotificationClient,
)
from alert_processing.dmi_bufr import check_dmi_ftp
from alert_processing.file_system_status import check_update_time

logger = logging.getLogger(__name__)


def check_all_steps(
        current_time: datetime,
        notification_client: NotificationClient,
        bufr_out_path: Path,
        bufr_backup_path: Path,
        dmi_ftp_config: Mapping,
        l0_tx_path: Path,
        l3_tx_path: Path,
        l3_joined_path: Path,
):
    logger.info("Checking pipeline data status")

    # ==============================================================
    # DMI FTP
    # ==============================================================
    logger.info('Checking DMI FTP')
    if 'skip' in dmi_ftp_config:
        logger.info('DMI Alert: Skipping')
    else:
        dmi_alert = check_dmi_ftp(
            current_time=current_time,
            max_age=timedelta(hours=2),
            user=dmi_ftp_config['user'],
            passwd=dmi_ftp_config['password'],
            host=dmi_ftp_config['server'],
        )
        logger.info(f'DMI Alert: {dmi_alert}')
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
    if bufr_out_path:
        dmi_alert_1 = check_update_time(
            bufr_out_path,
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
            logger.info('BUFR_out files are current. No alert issued.')
    if bufr_backup_path:
        dmi_alert_2 = check_update_time(
            bufr_backup_path,
            current_time=current_time,
            max_age=timedelta(hours=2),
        )

        if dmi_alert_2:
            notification_client.send_alert_email(
                subject_text="ALERT: BUFR_backup files are not updating!",
                body_text='''
                The concatenated BUFR files in the BUFR_backup directory are not updating.
                We expect to have one file per hour, for the last 48 hrs.
                ''',
            )
        else:
            logger.info('BUFR_backup files are current. No alert issued.')

    # ==============================================================
    # L0 TX
    # ==============================================================
    if l0_tx_path:
        l0tx_alert = check_update_time(
            l0_tx_path,
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
            logger.info('aws-l0/tx files are current. No alert issued.')

    # ==============================================================
    # L3 TX
    # ==============================================================
    if l3_tx_path:
        l3tx_alert = check_update_time(
            l3_tx_path,
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
            logger.info('aws-l3/tx files are current. No alert issued.')

    # ==============================================================
    # L3 level_3 (joined)
    # ==============================================================
    if l3_joined_path:
        l3joined_alert = check_update_time(
            l3_joined_path,
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
            logger.info('aws-l3/level_3 files are current. No alert issued.')


def parse_arguments():
    parser = ArgumentParser(description="Monitor for aws processing")
    parser.add_argument('-c', '--config_files', type=Path, nargs='+',
                        help='Path to ini files with account and credential information')
    parser.add_argument('--l0-tx-path', help='Path to l0 tx directory')
    parser.add_argument('--l3-tx-path', help='Path to l3 tx directory')
    parser.add_argument('--l3-joined-path', help='Path to l3 level_3 (joined) directory')
    parser.add_argument('--bufr-out-path', help='Path to BUFR_out directory')
    parser.add_argument('--bufr-backup-path', help='Path to BUFR_backup directory')
    parser.add_argument("--receiver_emails")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    """Executed from the command line"""
    args = parse_arguments()

    # Set credential paths
    config_parser = ConfigParser(
        converters={
            'list': str.split,
            'path': Path,
        }
    )
    config_parser.read(args.config_files)

    if args.bufr_out_path:
        config_parser.set('local', 'bufr-out-path', args.bufr_out_path),
    if args.bufr_backup_path:
        config_parser.set('local', 'bufr-backup-path', args.bufr_backup_path),
    if args.l0_tx_path:
        config_parser.set('local', 'l0-tx-path', args.l0_tx_path),
    if args.l3_tx_path:
        config_parser.set('local', 'l3-tx-path', args.l3_tx_path),
    if args.l3_joined_path:
        config_parser.set('local', 'l3-joined-path', args.l3_joined_path),
    if args.receiver_emails:
        config_parser.set('monitoring', 'receiver_emails', args.receiver_emails),

    logging.basicConfig(
        format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
        level=logging.DEBUG,
        stream=sys.stdout,
    )

    # Define accounts and credentials ini file paths
    receiver_emails = config_parser.getlist('monitoring', 'receiver_emails')
    if any(receiver_emails):
        notification_client = EmailNotificationClient(
            receiver_emails=receiver_emails,
            account=config_parser.get('aws', 'account'),
            smtp_server=config_parser.get('aws', 'server'),
            port=config_parser.getint('aws', 'port'),
            password=config_parser.get('aws', 'password'),
        )
    else:
        logger.info("Not receiver")
        notification_client = LogNotificationClient()

    current_time = datetime.now(tz=timezone.utc)
    check_all_steps(
        current_time=current_time,
        notification_client=notification_client,
        dmi_ftp_config=config_parser['dmi'],
        bufr_out_path=config_parser.getpath('local', 'bufr-out-path'),
        bufr_backup_path=config_parser.getpath('local', 'bufr-backup-path'),
        l0_tx_path=config_parser.getpath('local', 'l0-tx-path'),
        l3_tx_path=config_parser.getpath('local', 'l3-tx-path'),
        l3_joined_path=config_parser.getpath('local', 'l3-joined-path'),
    )
