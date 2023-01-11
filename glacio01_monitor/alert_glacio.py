#!/usr/bin/env python

'''
Monitor script for glacio01 server

This script is intended to work with the following routine:

- glacio01 has an hourly (top-of-hour) cron that updates the name
  and update time of a text file at Azure (ssh_to_azure.sh)
- alert_glacio.py (this script) runs at 5 min after the hour on Azure VM,
  and checks the update time of the file.
- If time is older than an hour ago (and younger than two hours ago),
  we send out email alerts that glacio01 may be down. Checking two hours
  ago is to prevent repeated emails if the server is down for an extended time.

Patrick Wright, GEUS
Jan 11, 2023
'''

from argparse import ArgumentParser
from configparser import ConfigParser
import smtplib, ssl
import glob
import os
from datetime import datetime

from IPython import embed

def parse_arguments():
    parser = ArgumentParser(description="Monitor for glacio01")       
    parser.add_argument('-a', '--account', default='/home/aws/monitoring/credentials/accounts.ini', type=str, required=False, help='Email account .ini file')
    parser.add_argument('-p', '--password', default='/home/aws/monitoring/credentials/credentials.ini', type=str, required=False, help='Email credentials .ini file')                      
    args = parser.parse_args()
    return args

def check_glacio_update_time(filepath):
    '''Check the update time of a file, return a status boolean if we
    pass certain time check thresholds

    Parameters
    ----------
    filepath : str
        path to the file to check

    Returns
    -------
    status : bool
        Result of the check. False (default) is passing, True is alert condition
    '''
    status = False

    if os.path.isfile(filepath):
        # all times are unix time (epoch seconds)
        update_time = os.path.getmtime(filepath)

        now = datetime.now().timestamp()
        one_hour_ago = now - (60 * 60)
        two_hours_ago = now - (60 * 60 * 2)

        if (update_time < one_hour_ago) and (update_time > two_hours_ago):
            status = True
    return status

def send_alert_email(receiver_emails):
    ''' Use smtp to login to gmail and send an alert email
    See: https://realpython.com/python-send-email/

    Parameters
    ----------
    receiver_emails : list
        List of email addresses to send alerts to

    Returns
    -------
    None
    '''
    # Set credential paths
    accounts_file = args.account
    credentials_file = args.password

    #----------------------------------

    # Define accounts and credentials ini file paths
    accounts_ini = ConfigParser()
    accounts_ini.readfp(open(accounts_file))    
    accounts_ini.read(credentials_file) 
  
    # Get credentials
    account = accounts_ini.get('aws-monitoring', 'account')
    smtp_server = accounts_ini.get('aws-monitoring', 'server')
    port = accounts_ini.getint('aws-monitoring', 'port')    
    password = accounts_ini.get('aws-monitoring', 'password')
    if not password:
        password = input('password for AWS email account: ')
    print('Logging into server %s, account %s' %(smtp_server, account))

    #----------------------------------

    body = '''
    glacio01 is no longer updating the monitor .txt file at Azure.

    If glacio01 is inaccessible, then email GEUS IT at geusithjaelp@geus.dk
    '''
    headers = f"From: {account}\r\n"
    headers += f"To: {', '.join(receiver_emails)}\r\n" 
    headers += f"Subject: ALERT: glacio01 down!\r\n"
    email_message = headers + "\r\n" + body  # Blank line needed between headers and body

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

    glacio_file = glob.glob("glacio01_*.txt")

    glacio_alert = check_glacio_update_time(glacio_file[0])

    receiver_emails = ["pajwr@geus.dk"]
    # receiver_emails = ["pajwr@geus.dk","pho@geus.dk","rsf@geus.dk","aso@geus.dk","shl@geus.dk"]

    if glacio_alert is True:
        send_alert_email(receiver_emails)
    else:
        print('{} is current. No alert issued.'.format(glacio_file[0]))

else:
    """Executed on import"""
    pass
