filename=$(basename -- "$1")
extension="${filename##*.}"
stem="${filename%.*}"

# ffmpeg -y -f s16le -ar 8k -ac 1 -i $1 $stem.wav
ffmpeg -i $1 $stem.wav