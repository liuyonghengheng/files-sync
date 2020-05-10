from airflow import configuration
from files_sync import configuration as files_sync_configuration
import importlib


class Emailer:

    EMAIL_BODY = """
    Files Sync Failed <br/>
    <br/>
    <b>message:</b> {0}<br/>
    """

    def __init__(self, alert_to_email, logger, email_subject=None):
        logger.debug("Creating Emailer with Args - alert_to_email: {alert_to_email}, logger: {logger}, email_subject: {email_subject}".format(**locals()))
        self.alert_to_emails = alert_to_email
        self.logger = logger
        if email_subject:
            self.email_subject = email_subject
        else:
            self.email_subject = files_sync_configuration.DEFAULT_EMAIL_SUBJECT
            self.logger.debug("Email subject was not provided. Using Default value: " + str(self.email_subject))
        path, attr = configuration.get('email', 'EMAIL_BACKEND').rsplit('.', 1)
        module = importlib.import_module(path)
        self.email_backend = getattr(module, attr)
        if self.alert_to_emails is None:
            self.logger.warn("alert_to_email value isn't provided. The email will not be able to send alert emails.")

    def send_alert(self, message):
        self.logger.debug("Sending Email with Args - messages: {0}".format(message))

        if self.alert_to_emails and len(self.alert_to_emails) > 0:
            for alert_to_email in self.alert_to_emails:
                try:
                    self.email_backend(
                        alert_to_email,
                        self.email_subject,
                        self.EMAIL_BODY.format(message),
                        files=None,
                        dryrun=False
                    )
                    self.logger.info('Alert Email has been sent')
                except Exception as e:
                    self.logger.critical('Failed to Send Email: ' + str(e) + 'error')
        else:
            self.logger.critical("Couldn't send email since the alert_to_email config is not set")