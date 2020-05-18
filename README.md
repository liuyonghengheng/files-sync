#Files Sync

基于python的简单的远程文件同步工具，可以实现把一台机器上指定目录下的文件实时同步到多台远程机器上的指定目录中。
底层基于 watchdog（inotify）和 ssh。
（项目的目的是同步airflow的dags，所以现在依赖airflow的包去读取配置文件，不过这一部分后面可以改掉）

####使用方式
首先设置配置文件：

```
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
```
