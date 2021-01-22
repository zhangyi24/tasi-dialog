#!/usr/bin/env bash
IMAGE=tasi_dialog_hnyc
GIT_VERSION=v2.0
LOCAL_IMAGE=tasitech/$IMAGE:${GIT_VERSION}
REMOTE=registry.cn-hangzhou.aliyuncs.com
docker tag  $LOCAL_IMAGE $REMOTE/$LOCAL_IMAGE
docker push $REMOTE/$LOCAL_IMAGE
