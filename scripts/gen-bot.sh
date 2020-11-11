read -p "Please input bot name: " botname
mkdir -p bots/$botname/dialog_config
mkdir -p bots/$botname/dialog_config/flows
mkdir -p bots/$botname/dialog_config/corpus

cat << EOF > bots/$botname/dialog_config/corpus/templates.json
{
  "拒绝交费": {
    "name": "拒绝交费",
    "templates": [
      "不交",
      "没钱交",
      "不想还钱",
    ]
  }
}
EOF

cat << EOF > bots/$botname/run_client_text.sh
#!/bin/bash
python ../../src/client_text.py
EOF

cat << EOF > bots/$botname/run_server_text.sh
#!/bin/bash
python ../../src/server_text.py
EOF

cat << EOF > bots/$botname/run_server_phone.sh
#!/bin/bash
python ../../src/server_phone.py
EOF

