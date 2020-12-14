FROM pytorch/pytorch:1.6.0-cuda10.1-cudnn7-devel
LABEL maintainer="tasitech"

# Needed for string substitution
SHELL ["/bin/bash", "-c"]

WORKDIR /opt/dialog

ARG PIP_MIRROR=https://mirrors.aliyun.com/pypi/simple/
ARG DEBIAN_FRONTEND=noninteractive

ENV LANG C.UTF-8
ENV TZ Asia/Shanghai

RUN mv /etc/apt/sources.list.d /etc/apt/sources.list.d.bak
COPY docker/sources.list /etc/apt/sources.list

COPY src /opt/dialog/src
COPY bots /opt/dialog/bots
COPY requirements.txt /opt/dialog/requirements.txt

RUN apt-get update && apt-get install -y \
        apt-utils \
        curl \
        libpq-dev \
        vim \
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
        transformers==3.1.0

EXPOSE 49999
EXPOSE 59999

COPY docker/lite/docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["init"]
