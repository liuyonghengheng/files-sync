# -*- coding: utf-8 -*-
import os
import paramiko
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from files_sync.configuration import Configuration
from files_sync.logger.logger import get_logger
from files_sync.emailer.emailer import Emailer
from files_sync.files_filters.regex_filter import RegexFilter


class FilesSync(object):
    def __init__(self, config, logger, emailer):
        self.config = config
        self.logger = logger
        self.emailer = emailer
        self.__sshclients = None

    def get_dest_path(self, path):
        if path and path.find(self.config.src_path) == 0:
            return path.replace(self.config.src_path, self.config.dest_path)
        else:
            pass

    def __gen_sshclient(self, conn_args):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(**conn_args)
        self.logger.debug('conn_args:{a}'.format(a=conn_args))
        return ssh

    def __gen_sshclients(self):
        return [self.__gen_sshclient(conn_args) for conn_args in self.config.sync_nodes_in_cluster]

    @property
    def sshclients(self):
        if self.__sshclients:
            self.logger.debug("new sshclients number:{n}".format(n=len(self.__sshclients)))
            return self.__sshclients
        else:
            self.__sshclients = self.__gen_sshclients()
            self.logger.debug("sshclients number:{n}".format(n=len(self.__sshclients)))
            return self.__sshclients

    def exec_remote_cmd(self, cmd, is_close=True):
        self.logger.info(cmd)
        for sshclient in self.sshclients:
            exec_count = 0
            while exec_count <= self.config.sync_retry:
                exec_count += 1
                try:
                    stdin, stdout, stderr = sshclient.exec_command(cmd)
                except Exception as e:
                    message = "exec remote cmd:{cmd} error in {cli}, retry count:{cnt}".format(
                            cmd=cmd,
                            cli=sshclient.get_transport(),
                            cnt=exec_count)
                    self.logger.error(message)
                    if exec_count > self.config.sync_retry:
                        self.emailer.send_alert(message)
                finally:
                    if is_close and self.__sshclients:
                        self.close_sshclients()

    def remote_cp(self, src_path, dest_path, is_close=True):
        for sshclient in self.sshclients:
            exec_count = 0
            while exec_count <= self.config.sync_retry:
                exec_count += 1
                try:
                    sftpclient = sshclient.open_sftp()
                    sftpclient.put(src_path, dest_path)
                    break
                except Exception as e:
                    message = "exec remote cp : from {src_path} to {dest_path} error in {cli},retry count:{cnt}".format(
                            src_path=src_path,
                            dest_path=dest_path,
                            cli=sshclient.get_transport(),
                            cnt=exec_count)
                    self.logger.error(message)
                    if exec_count > self.config.sync_retry:
                        self.emailer.send_alert(message)
                finally:
                    if is_close and self.__sshclients:
                        self.close_sshclients()

    def close_sshclients(self):
        for sshclient in self.sshclients:
            if sshclient:
                sshclient.close()
                self.__sshclients = None

    def close_sshclient(self, sshclient):
        sshclient.close()

    def remote_mkdir(self, path):
        dest_path = self.get_dest_path(path)
        cmd = 'if [ ! -d "{path}" ]; then mkdir -p "{path}"; fi '.format(path=dest_path)
        self.exec_remote_cmd(cmd)

    def remote_delete(self, path, is_directory):
        path_type = '-f'
        if is_directory:
            path_type = '-d'
        dest_path = self.get_dest_path(path)
        cmd = 'if [ {path_type} "{path}" ]; then rm -rf "{path}"; fi '.format(path_type=path_type, path=dest_path)
        self.exec_remote_cmd(cmd)

    def remote_cp_file(self, path):
        dest_path = self.get_dest_path(path)
        dir = os.path.dirname(dest_path)
        mkdir_cmd = 'if [ ! -d "{path}" ]; then mkdir -p "{path}"; fi '.format(path=dir)
        self.exec_remote_cmd(mkdir_cmd, is_close=False)
        self.remote_cp(path, dest_path)

    def remote_mv_file(self, src_path, dest_path):
        dest_path1 = self.get_dest_path(src_path)
        dest_path2 = self.get_dest_path(dest_path)
        dir = os.path.dirname(dest_path2)
        mkdir_cmd = 'if [ ! -d "{path}" ]; then mkdir -p "{path}"; fi '.format(path=dir)
        self.exec_remote_cmd(mkdir_cmd, is_close=False)
        self.remote_cp(dest_path, dest_path2, is_close=False)
        rm_cmd = 'if [ -f "{path}" ]; then rm -rf "{path}"; fi  '.format(path=dest_path1)
        self.exec_remote_cmd(rm_cmd)


class FilesMonitorHandler(FileSystemEventHandler):
    def __init__(self, file_filter, files_sync, logger, *args, **kwargs):
        super(FilesMonitorHandler, self).__init__()
        self.file_filter = file_filter
        self.files_sync = files_sync
        self.logger = logger

    def on_modified(self, event):
        if not event.is_directory:
            file_path = event.src_path
            self.files_sync.remote_cp_file(file_path)
        what = 'directory' if event.is_directory else 'file'
        self.logger.debug("FileSystemEvent Modified %s: %s", what, event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.files_sync.remote_mv_file(event.src_path, event.dest_path)
        what = 'directory' if event.is_directory else 'file'
        self.logger.debug("FileSystemEvent Moved %s: from %s to %s", what, event.src_path, event.dest_path)

    def on_created(self, event):
        if event.is_directory:
            self.files_sync.remote_mkdir(event.src_path)
        else:
            self.files_sync.remote_cp_file(event.src_path)
        what = 'directory' if event.is_directory else 'file'
        self.logger.debug("FileSystemEvent Created %s: %s" % ('directory' if event.is_directory else 'file', event.src_path))

    def on_deleted(self, event):
        self.files_sync.remote_delete(event.src_path, event.is_directory)
        self.logger.debug("FileSystemEvent Deleted %s: %s" % ('directory' if event.is_directory else 'file', event.src_path))

    def dispatch(self, event):
        if self.file_filter.filter(event):
            super(FilesMonitorHandler, self).dispatch(event)
        else:
            return


if __name__ == '__main__':
    conf = Configuration()
    logger = get_logger(conf.logging_level,
                        conf.logs_output_file_path,
                        conf.logs_rotate_when,
                        conf.logs_rotate_backup_count)
    emailer = Emailer(conf.email_list, logger, conf.alert_email_subject)
    print("match_files_regexp :" + conf.match_files_regexp)
    print("ignore_files_regexp : " + conf.ignore_files_regexp)
    file_filter = RegexFilter(logger,
                              regexes=[conf.match_files_regexp],
                              ignore_regexes=[conf.ignore_files_regexp],
                              ignore_directories=False,
                              case_sensitive=True)

    files_sync = FilesSync(conf, logger, emailer)
    event_handler = FilesMonitorHandler(file_filter, files_sync, logger)

    observer = Observer()
    observer.schedule(event_handler, path=conf.src_path, recursive=True)  # recursive递归的
    observer.start()
    observer.join()

