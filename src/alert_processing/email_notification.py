import abc
import logging
import smtplib
import ssl
from typing import List

import attr

__all__ = [
    'NotificationClient',
    'EmailNotificationClient',
    'LogNotificationClient',
]


class NotificationClient(abc.ABC):

    @abc.abstractmethod
    def send_alert_email(
            self,
            subject_text: str,
            body_text: str,
    ):
        pass


@attr.s
class LogNotificationClient(NotificationClient):
    logger = attr.ib(default=logging.getLogger('DummyNotificationClient'))

    def send_alert_email(
            self,
            subject_text: str,
            body_text: str,
    ):
        self.logger.info(f"{subject_text}. {body_text}")


@attr.s
class EmailNotificationClient(NotificationClient):
    receiver_emails: List[str] = attr.ib()
    account: str = attr.ib()
    smtp_server: str = attr.ib()
    port: int = attr.ib()
    password: str = attr.ib(repr=False)
    logger = attr.ib(default=logging.getLogger('EmailNotificationClient'))

    def send_alert_email(
            self,
            subject_text: str,
            body_text: str,
    ):
        headers = f"From: {self.account}\r\n"
        headers += f"To: {', '.join(self.receiver_emails)}\r\n"
        headers += f"Subject: {subject_text}\r\n"
        email_message = headers + "\r\n" + body_text  # Blank line needed between headers and body

        self.logger.info(f"{subject_text}. {body_text}")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
            server.login(self.account, self.password)
            server.sendmail(self.account, self.receiver_emails, email_message)
            server.quit()  # may not be necessary?
        logging.info('Alert email sent!')
