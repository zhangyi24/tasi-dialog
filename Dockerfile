FROM ubuntu:18.04
LABEL maintainer="tasitech"
ARG PIP_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /opt/dialog
COPY sources.list /etc/apt
RUN apt-get update && apt-get install -y \
        curl \
        libpq-dev \
        python3 \
        python3-pip && \
    rm -rf /var/lib/apt/lists

COPY requirements.txt .
RUN python3 -m pip install -i $PIP_MIRROR --no-cache-dir --upgrade \
        pip \
        setuptools && \
    python3 -m pip install -i $PIP_MIRROR --no-cache-dir -r requirements.txt

EXPOSE 59998
EXPOSE 59999

CMD ["/bin/bash"]