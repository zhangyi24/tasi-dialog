DOMAIN=8.131.253.223
PORT=40000
TEXT=$1
FILENAME=$(echo -n "$TEXT" | shasum | cut -c1-6)

echo $FILENAME

trans() {
  wget -O $FILENAME[$1].pcm "http://$DOMAIN:$PORT/tts?tex=$TEXT&aue=pcm&sr=8000&spkr=1&rate=1.0"
}

play() {
  ffplay  -autoexit -f s16le -ar 8000 $1
}

trans $1
play $FILENAME.pcm