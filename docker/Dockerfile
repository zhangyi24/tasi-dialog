FROM pytorch/pytorch:1.6.0-cuda10.1-cudnn7-devel
LABEL maintainer="tasitech"

# Needed for string substitution
SHELL ["/bin/bash", "-c"]

ARG PIP_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
ARG DEBIAN_FRONTEND=noninteractive

ENV LANG C.UTF-8
ENV TZ Asia/Shanghai

RUN echo $'deb http://mirrors.aliyun.com/ubuntu/ bionic main restricted universe multiverse\n\
deb-src http://mirrors.aliyun.com/ubuntu/ bionic main restricted universe multiverse\n\
deb http://mirrors.aliyun.com/ubuntu/ bionic-security main restricted universe multiverse\n\
deb-src http://mirrors.aliyun.com/ubuntu/ bionic-security main restricted universe multiverse\n\
deb http://mirrors.aliyun.com/ubuntu/ bionic-updates main restricted universe multiverse\n\
deb-src http://mirrors.aliyun.com/ubuntu/ bionic-updates main restricted universe multiverse\n\
deb http://mirrors.aliyun.com/ubuntu/ bionic-proposed main restricted universe multiverse\n\
deb-src http://mirrors.aliyun.com/ubuntu/ bionic-proposed main restricted universe multiverse\n\
deb http://mirrors.aliyun.com/ubuntu/ bionic-backports main restricted universe multiverse\n\
deb-src http://mirrors.aliyun.com/ubuntu/ bionic-backports main restricted universe multiverse' > /etc/apt/sources.list

RUN mv /etc/apt/sources.list.d /etc/apt/sources.list.d.bak

RUN apt-get update && apt-get install -y \
        apt-utils \
        curl \
        libpq-dev \
        tzdata && \
    rm -rf /var/lib/apt/lists

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN dpkg-reconfigure --frontend noninteractive tzdata

RUN python -m pip install -i $PIP_MIRROR --no-cache-dir --upgrade pip setuptools && \
    python -m pip install -i $PIP_MIRROR --no-cache-dir \
        elasticsearch \
        jieba \
        ltp \
        mysql-connector-python \
        PyYAML \
        psycopg2-binary \
        py2neo \
        pypinyin \
        pytorch-lightning==0.9.0 \
        requests \
        scikit-learn \
        scipy \
        tornado \
        supervisor \
        jsonpath_ng \
        expiringdict \
        sqlalchemy \
        transformers==3.1.0

EXPOSE 49999
EXPOSE 59999

WORKDIR /opt/dialog

CMD ["/bin/bash"]
