## 部署相关文件

## 部署拓扑

* 有一个CRS客户端,背后接着所有的bots
* 每个bots产生的路径和路由关系在`src/config/config.yml`文件内

## Supervisor守护进程

* 通过`src/utils/supervisor.py`生成所有的supervisor配置文件.
* `Supervisorctl start all`就可以保证所有的crs和bots进程的守护. 