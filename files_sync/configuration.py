import logging
import os
import sys
import socket
from six.moves import configparser
import json
DEFAULT_MATCH_FILES_REGEXP = '.*'
# EXCEPT FILES, USE EXGREP
DEFAULT_IGNORE_FILES_REGEXP = None
#RETRY_TIMES = 0
#DEFAULT_EMAIL_LIST = None
DEFAULT_EMAIL_SUBJECT = "files sync"
DEFAULT_SEND_EMAIL_SYNC_FAILD = True
DEFAULT_SYNC_RETRY = 0
#SEND EMAIL PEROID_THRESHOLD
DEFAULT_EMAIL_PEROID_THRESHOLD = 60
DEFAULT_LOGGING_LEVEL = 'INFO'
DEFAULT_LOGGING_DIR = '/tmp'
DEFAULT_LOGGING_FILE_NAME = 'files_sync.log'
DEFAULT_LOGS_ROTATE_WHEN = 'midnight'
DEFAULT_LOGS_ROTATE_BACKUP_COUNT = 7

# config file content

default_config_file_content = """
[files-sync]

sync_nodes_in_cluster = 
src_path = 
dest_path = 
# match files, use regexp
match_files_regexp = 
# ignore files, use regexp
ignore_files_regexp = 
files_filter_backend = files_sync.files_filters.regex_filter
totally_sync_when_start = False
email_list = 
email_subject = files sync
send_email_sync_faild = True
sync_retry = 0
#send email peroid threshold,
email_peroid_threshold = 60
logging_level = INFO
logging_dir = /tmp
logging_file_name = files_sync.log
logs_rotate_when = midnight
logs_rotate_backup_count = 7
"""

default_config_file_content_smtp = """
[email]
email_backend = airflow.utils.email.send_email_smtp

[smtp]

# If you want airflow to send emails on retries, failure, and you want to use
# the airflow.utils.email.send_email_smtp function, you have to configure an
# smtp server here
smtp_host = localhost
smtp_starttls = True
smtp_ssl = False
# Example: smtp_user = airflow
# smtp_user =
# Example: smtp_password = airflow
# smtp_password =
smtp_port = 25
smtp_mail_from = airflow@example.com
#
"""


class Configuration(object):

    def __init__(self, config_file_path=None):
        if config_file_path:
            self.config_file_path = config_file_path
        else:
            self.config_file_path = self.get_files_sync_conf_dir()
        if not os.path.isfile(self.config_file_path):
            print("Cannot find files_sync Configuration file at '" + str(self.config_file_path) + "'!!!==")
            sys.exit(1)
        self.conf = configparser.RawConfigParser()
        self.conf.read(self.config_file_path)

    @staticmethod
    def get_current_host():
        return socket.gethostname()

    @staticmethod
    def get_files_sync_conf_dir():
        return os.environ['FILES_SYNC_CONF'] if "FILES_SYNC_CONF" in os.environ else os.path.expanduser(
            "./files_sync.cfg")

    def get_config(self, section, option, default=None):
        try:
            config_value = self.conf.get(section, option)
            return config_value if config_value is not None else default
        except Exception as e:
            pass
        return default

    def get_boolean_config(self, section, key, default=None):
        val = str(self.get_config(section, key, default=default)).lower().strip()
        if '#' in val:
            val = val.split('#')[0].strip()
        if val in ('t', 'true', '1'):
            return True
        elif val in ('f', 'false', '0'):
            return False
        else:
            raise ValueError(
                'The value for configuration option "{}:{}" is not a '
                'boolean (received "{}").'.format(section, key, val))

    def get_int_config(self, section, key, default=None):
        return int(self.get_config(section, key, default=default))

    def getf_loat_config(self, section, key, default=None):
        return float(self.get_config(section, key, default=default))

    def get_files_sync_config(self, option, default=None):
        return self.get_config('files-sync', option, default)

    @property
    def sync_nodes_in_cluster(self):
        sync_nodes_in_cluster = self.get_files_sync_config("SYNC_NODES_IN_CLUSTER")
        if sync_nodes_in_cluster is not None:
            sync_nodes_in_cluster = json.loads(sync_nodes_in_cluster)
        return sync_nodes_in_cluster

    @property
    def src_path(self):
        return self.get_files_sync_config("SRC_PATH")

    @property
    def dest_path(self):
        return self.get_files_sync_config("DEST_PATH")

    @property
    def match_files_regexp(self):
        return self.get_files_sync_config("MATCH_FILES_REGEXP")

    @property
    def ignore_files_regexp(self):
        return self.get_files_sync_config("IGNORE_FILES_REGEXP")

    @property
    def sync_retry(self):
        return int(self.get_files_sync_config("SYNC_RETRY", DEFAULT_SYNC_RETRY))

# smtp
    def get_smtp_config(self, option, default=None):
        return self.get_config("smtp", option, default)

    @property
    def smtp_host(self):
        return self.get_smtp_config("SMTP_HOST")

    @property
    def smtp_starttls(self):
        return self.get_smtp_config("SMTP_STARTTLS")

    @property
    def smtp_ssl(self):
        return self.get_smtp_config("SMTP_SSL")

    @property
    def smtp_user(self):
        return self.get_smtp_config("SMTP_USER")

    @property
    def smtp_port(self):
        return self.get_smtp_config("SMTP_PORT")

    @property
    def smtp_password(self):
        return self.get_smtp_config("SMTP_PASSWORD")

    @property
    def smtp_mail_from(self):
        return self.get_smtp_config("SMTP_MAIL_FROM")

    @property
    def email_list(self):
        email_list = self.get_files_sync_config("EMAIL_LIST")
        if email_list is not None:
            email_list = email_list.split(",")
        return email_list

    @property
    def alert_email_subject(self):
        return self.get_files_sync_config("EMAIL_SUBJECT", DEFAULT_EMAIL_SUBJECT)

    @property
    def send_email_sync_faild(self):
        return self.get_files_sync_config("SEND_EMAIL_SYNC_FAILD", DEFAULT_SEND_EMAIL_SYNC_FAILD)

    @property
    def email_peroid_threshold(self):
        return self.get_files_sync_config("EMAIL_PEROID_THRESHOLD", DEFAULT_EMAIL_PEROID_THRESHOLD)
# log
    @property
    def logging_level(self):
        return logging.getLevelName(self.get_files_sync_config("LOGGING_LEVEL", DEFAULT_LOGGING_LEVEL))

    @property
    def logs_rotate_when(self):
        return self.get_files_sync_config("LOGS_ROTATE_WHEN", DEFAULT_LOGS_ROTATE_WHEN)

    @property
    def logs_rotate_backup_count(self):
        return int(self.get_files_sync_config("LOGS_ROTATE_BACKUP_COUNT", DEFAULT_LOGS_ROTATE_BACKUP_COUNT))

    @property
    def logs_output_file_path(self):
        logging_dir = self.get_files_sync_config("LOGGING_DIR")
        logging_file_name = self.get_files_sync_config("LOGGING_FILE_NAME")
        return logging_dir + logging_file_name if logging_dir is not None and logging_file_name is not None else None

    def add_default_configs_to_config_file(self, venv_command):
        with open(self.config_file_path, 'r') as config_file:
            if "[files-sync]" not in config_file.read():
                print("Adding Files Sync configs to config file...")
                with open(self.config_file_path, "a") as config_file_to_append:
                    config_file_to_append.write(default_config_file_content.format(venv_command))
                    print("Finished adding Files Sync configs to config file.")
            else:
                print("[files-sync] section already exists. Skipping adding Files Sync configs.")

            if "[smtp]" not in config_file.read():
                print("Adding Files Sync configs to config file...")
                with open(self.config_file_path, "a") as config_file_to_append:
                    config_file_to_append.write(default_config_file_content_smtp.format(venv_command))
                    print("Finished adding Files Sync configs to config file.")
            else:
                print("[files-sync] section already exists. Skipping adding Files Sync configs.")

