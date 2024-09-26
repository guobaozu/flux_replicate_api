flask实现的flux api的接口。


## 端口
默认8055，直接写在了gunicorn_config文件里，请自行更改。

基本配置：gunicorn_config文件：
bind = '0.0.0.0:8055'  # 绑定的 IP 和端口
workers = 3  # 工作进程数量
loglevel = 'info'  # 日志级别
accesslog = '/home/ubuntu/my_dev/flux_api/access.log'  # 访问日志文件路径
errorlog = '/home/ubuntu/my_dev/flux_api/error.log'  # 错误日志文件路径
timeout = 120  # 超时时间

启动：
nohup /home/ubuntu/.local/bin/gunicorn --config /home/ubuntu/my_dev/flux_api/gunicorn_config.py main:app 2>&1 &
