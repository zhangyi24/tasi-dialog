FROM ubuntu:18.04
LABEL maintainer="tasitech"

ARG PIP_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
ARG DEBIAN_FRONTEND=noninteractive

ENV LANG C.UTF-8
ENV TZ Asia/Shanghai

WORKDIR /opt/dialog

COPY sources.list /etc/apt
RUN apt-get update && apt-get install -y \
        apt-utils \
        curl \
        libpq-dev \
        python3 \
        python3-pip \
        tzdata && \
    rm -rf /var/lib/apt/lists

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN dpkg-reconfigure --frontend noninteractive tzdata

RUN ln -s $(which python3) /usr/local/bin/python

COPY requirements.txt .
RUN python3 -m pip install -i $PIP_MIRROR --no-cache-dir --upgrade \
        pip \
        setuptools && \
    python3 -m pip install -i $PIP_MIRROR --no-cache-dir -r requirements.txt

EXPOSE 59998
EXPOSE 59999

CMD ["/bin/bash"]