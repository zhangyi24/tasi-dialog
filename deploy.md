## 部署相关文件

## 部署拓扑

* 有一个CRS客户端,背后接着所有的bots
* 每个bots产生的路径和路由关系在`src/config/config.yml`文件内

## Supervisor守护进程

* 通过`src/utils/supervisor.py`生成所有的supervisor配置文件.
* `Supervisorctl start all`就可以保证所有的crs和bots进程的守护. 


# bot总控脚本(未完成)
## bot 生成
bot new `$folder_path` #从路径下的配置文件中生成一个新的bot.
bot derive `data.json` #以某个bot为模板派生出一个bot来,用于调查问卷的bot生成,返回bot_id

## bot 配置
bot config # 配置bot的各种参数

## bot 状态管理
bot status # bot状态
bot cli `$bot_id` # 启动某个bot的文字版会话
bot crs # 从crs启动会话测试