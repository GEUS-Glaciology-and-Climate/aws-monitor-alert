#!/usr/bin/env python

'''
Monitor and alert based on metrics related to AWS processing.

Currently implemented:
-- Check latest BUFR file timestamp at DMI ftp upload directory

Patrick Wright, GEUS
Jan 16, 2023
'''

from argparse import ArgumentParser
from configparser import ConfigParser
import smtplib, ssl
import glob
import os
from datetime import datetime
from ftplib import FTP

from IPython import embed

def parse_arguments():
    parser = ArgumentParser(description="Monitor for glacio01")

    parser.add_argument('-a', '--account', default='/home/aws/aws-monitor-alert/credentials/accounts.ini',
        type=str, required=False, help='account .ini file')
    parser.add_argument('-p', '--password', default='/home/aws/aws-monitor-alert/credentials/credentials.ini',
        type=str, required=False, help='credentials .ini file')
    args = parser.parse_args()
    return args

def check_dmi_ftp_update_time():
    '''Check the timestamp of the most recent BUFR file at DMI upload directory,
    return a status boolean if we pass certain time check thresholds

    Parameters
    ----------
    None

    Returns
    -------
    status : bool
        Result of the check. False (default) is passing, True is alert condition
    '''
    status = False

    # Get credentials
    HOST = accounts_ini.get('dmi-monitoring', 'server')
    USER = accounts_ini.get('dmi-monitoring', 'user')    
    PASSWD = accounts_ini.get('dmi-monitoring', 'password')
    if not PASSWD:
        PASSWD = input('password for dmi ftp account: ')
    print('Logging into {}'.format(HOST))

    ftp = FTP(HOST)
    ftp.login(USER,PASSWD)
    ftp.cwd('upload')
    lines = ftp.nlst("-t")
    latest_name = lines[-1]
    print('Latest BUFR: {}'.format(latest_name))
    # Parse the time string out of the filename
    latest_time_str = latest_name.split('_')[1].split('.')[0]

    # all times are unix time (epoch seconds)
    latest_time = datetime.strptime(latest_time_str, "%Y%m%dT%H%M").timestamp()
    now = datetime.now().timestamp()
    one_hour_ago = now - (60 * 60)
    two_hours_ago = now - (60 * 60 * 2)

    if (latest_time < one_hour_ago) and (latest_time > two_hours_ago):
        status = True
    return status

def send_alert_email(receiver_emails, subject_text, body_text):
    ''' Use smtp to login to gmail and send an alert email
    See: https://realpython.com/python-send-email/

    Parameters
    ----------
    receiver_emails : list
        List of email addresses to send alerts to
    subject_text : str
        The email subject
    body_text : str
        Message for the email body

    Returns
    -------
    None
    '''
    # Get credentials
    account = accounts_ini.get('aws-monitoring', 'account')
    smtp_server = accounts_ini.get('aws-monitoring', 'server')
    port = accounts_ini.getint('aws-monitoring', 'port')    
    password = accounts_ini.get('aws-monitoring', 'password')
    if not password:
        password = input('password for AWS email account: ')
    print('Logging into server %s, account %s' %(smtp_server, account))

    #----------------------------------

    headers = f"From: {account}\r\n"
    headers += f"To: {', '.join(receiver_emails)}\r\n" 
    headers += f"Subject: {subject_text}\r\n"
    email_message = headers + "\r\n" + body_text  # Blank line needed between headers and body

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(account, password)
        # server.set_debuglevel(1)  # Show SMTP server interactions
        server.sendmail(account, receiver_emails, email_message)
        server.quit() # may not be necessary?
    print('Alert email sent!')
    return

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

    dmi_alert = check_dmi_ftp_update_time()

    if dmi_alert is True:

        receiver_emails = ["pajwr@geus.dk",
                           "pho@geus.dk"
                           ]

        subject_text = "ALERT: DMI ftp BUFR upload!"

        body_text = '''
        The most recent concatenated BUFR file at the DMI ftp upload directory is >1 hr old (should be ~3 minutes old).
        There could be a problem with pypromice processing or the ftp upload itself.
        '''

        send_alert_email(receiver_emails, subject_text, body_text)
    else:
        print('DMI BUFR file is current. No alert issued.')

else:
    """Executed on import"""
    pass
