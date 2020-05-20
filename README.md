# Files Sync

#### 简介
基于python的简单的远程文件同步工具，可以实现把一台机器上指定目录下的文件实时同步到多台远程机器上的指定目录中。
底层基于 watchdog（inotify）和 ssh。
（项目的目的是同步airflow的dags，所以现在依赖airflow的包去读取配置文件，不过这一部分后面可以改掉）

#### 安装
```
git clone git@github.com:liuyonghengheng/files-sync.git
cd files-sync
pip install -e .
```

#### 使用

##### 设置配置文件

/opt/files-sync/files-sync.cfg

内容如下：

```
[files-sync]

sync_nodes_in_cluster = [{"hostname":"172.18.0.3","port":22,"username":"root"},{"hostname":"172.18.0.4","port":22,"username":"root"}]
src_path = /opt/files-sync/test
dest_path = /opt/files-sync/test
# match files, use regexp
match_files_regexp = .*
# ignore files, use regexp
ignore_files_regexp = .*\.swp$|.*\.swx$|.*\.swpx$|.*/4913$|.*/__pycache__/.*|.*~$
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
# Example: smtp_user = files_sync
# smtp_user =
# Example: smtp_password = files_sync
# smtp_password =
smtp_port = 25
smtp_mail_from = files_sync@example.com
```

设置环境变量：
```
export FILES_SYNC_CONF=/opt/files-sync/files-sync.cfg
```

启动

python -m files_sync.do_files_sync