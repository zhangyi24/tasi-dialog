DOMAIN=47.93.120.246
PORT=40001
# for filename in ./data/*.wav; do
#   python2 ws.py -u ws://$DOMAIN:$PORT/client/ws/speech -r 8000 "$filename"
# done

str="$1"
find=".wav"
replace=".txt"
result=${str//$find/$replace}
echo $result 
python2 ws.py -u ws://$DOMAIN:$PORT/client/ws/speech -r 8000 "$1"
