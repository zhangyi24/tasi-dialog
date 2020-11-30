#!/usr/bin/env bash
PHONE_PORT=49998
TEXT_PORT=59998

read -p "Please input bot name: " botname
mkdir -p bots/$botname/dialog_config
mkdir -p bots/$botname/dialog_config/flows
mkdir -p bots/$botname/dialog_config/corpus

BOT_ROOT=bots/$botname
CONFIG_DIR=$BOT_ROOT/dialog_config
## 意图配置
INTENTS=$CONFIG_DIR/intents.json
## Slot配置
VALUE_SET=$CONFIG_DIR/value_sets.json
## 意图模板
CORPUS_TEMPLATE=$CONFIG_DIR/corpus/template.json

## 流程配置
FLOWS_DIR=$CONFIG_DIR/flows
## 全局变量
GLOBAL_VARS=$CONFIG_DIR/global_vars.json
## 回调函数
FUNCTIONS=$CONFIG_DIR/functions.py

## 问候语
SERVICE_LANGUAGE=$CONFIG_DIR/service_language.json

## 服务端口
SERVICE_CONFIG=bots/$botname/config.yml
ls 
cat << EOF > $SERVICE_CONFIG
phone:
  port: 49998
  bot:
    interruptable: False
text:
  port: 59998
EOF

cat << EOF > $CORPUS_TEMPLATE
{
  "refuse": {
    "name": "refuse",
    "templates": [
      "不交",
      "没钱交",
      "不想还钱"
    ]
  }
}
EOF

cat << EOF > $BOT_ROOT/run_client_text.sh
#!/bin/bash
python ../../src/client_text.py
EOF

cat << EOF > $BOT_ROOT/run_server_text.sh
#!/bin/bash
python ../../src/server_text.py
EOF

cat << EOF > $BOT_ROOT/run_server_phone.sh
#!/bin/bash
python ../../src/server_phone.py
EOF

start_service() {
  cd $BOT_ROOT && bash run_server_text.sh
}

start_service
