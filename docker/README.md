# tasi_dialog docker

用于tasi_dialog的docker的使用说明。docker容器用来为tasi_dialog提供运行环境。



### 获取镜像

用docker build命令创建镜像：

```bash
sudo docker build -t tasitech/tasi_dialog:v0.1 .
```

创建docker镜像的时间有时会比较长，因此可以导入已创建的镜像。

镜像下载地址：oss://tasi-callcenter-audio-record/engine/docker/tasi_dialog_docker_0_1.tar。

下载好后，用docker load命令导入镜像：

```bash
sudo docker load < tasi_dialog_docker_0_1.tar
```

镜像的名字是tasitech/tasi_dialog:v0.1



### 启动容器

- 用docker-compose up命令为服务端启动一个容器：

  ```bash
  sudo docker-compose up -d server
  ```

  启动成功后，会返回容器的名字。容器此时在后台运行。

- 用docker-compose up命令为客户端启动一个容器：

  ```bash
  sudo docker-compose up -d client
  ```

- 用docker run命令可以启动一个自定义名字的容器

  ```
  sudo docker run --rm -itd -v $(pwd)/bots:/opt/dialog/bots -v $(pwd)/src:/opt/dialog/src --name {container_name} tasitech/tasi_dialog:v0.1
  ```

  你需要把{container_name}替换成您想给容器起的名字。



### 进入容器

用docker attach命令进入容器：

```bash
sudo docker attach {name_container}
```

您需要把{name_container}替换成容器的名字。

容器内已为tasi_dialog准备好了运行环境，可按照tasi_dialog的README中的说明使用tasi_dialog。



### 退出容器

按住CTRL的同时，先后按下P和Q，可退出容器，让容器在后台运行。
