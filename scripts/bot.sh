read -r bot_id port<<<$(python modify-crs-config.py | tail -1)
echo "get result $result"
SUPERVISOR=/usr/local/etc/supervisor.d/