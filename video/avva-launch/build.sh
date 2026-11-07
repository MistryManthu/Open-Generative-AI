#!/usr/bin/env bash
# Builds the 15s Avva Signage launch videos with voice + music.
#   ./build.sh            -> avva-launch.mp4 (1920x1080) and avva-launch-vertical.mp4 (1080x1920)
# Audio comes from make_audio.py (audio/voice.wav, audio/music.wav).
set -e
cd "$(dirname "$0")"; mkdir -p tmp
B=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
CREAM=0xFDF4E3

build() { # name W H boxW boxH logoH capY endLogoH noWy urlY urlSize capSize
 local N=$1 W=$2 H=$3 BW=$4 BH=$5 CY=$6 ELH=$7 NY=$8 UY=$9 US=${10} CS=${11} AUDIO=${12}
 local W2=$((W*2)) H2=$((H*2))
 comp() { ffmpeg -y -v error -i "$1" -filter_complex \
  "[0]split[a][b];[a]scale=$W2:$H2:force_original_aspect_ratio=increase,crop=$W2:$H2,boxblur=40:5,eq=brightness=-0.15[bg];[b]scale=$BW:$BH:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" -frames:v 1 "$2"; }
 comp src/2-sign.png tmp/$N-1.png; comp src/3-birthday.jpg tmp/$N-2.png
 comp src/4-beautybar.jpg tmp/$N-3.png; comp src/5-treat.jpg tmp/$N-4.png
 clip() { ffmpeg -y -v error -loop 1 -framerate 30 -i "$1" -t $2 -vf \
  "zoompan=z='$4':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=${W}x${H}:fps=30${5:+,$5}" -pix_fmt yuv420p -r 30 "$3"; }
 CAP() { echo "drawtext=fontfile=$B:text='$1':fontcolor=white:fontsize=$CS:x=(w-text_w)/2:y=h-$CY:box=1:boxcolor=0x3A0D0Dcc:boxborderw=24:enable='between(t,0.5,$2)'"; }
 clip tmp/$N-1.png 3.5 tmp/$N-c1.mp4 "1.12-0.08*on/105" "$(CAP 'Signage that makes you shine' 3.4)"
 clip tmp/$N-2.png 3   tmp/$N-c2.mp4 "1+0.08*on/90" "$(CAP 'Neon' 2.9)"
 clip tmp/$N-3.png 3   tmp/$N-c3.mp4 "1+0.08*on/90" "$(CAP 'LED' 2.9)"
 clip tmp/$N-4.png 3   tmp/$N-c4.mp4 "1.1-0.06*on/90" "$(CAP 'Custom made for you' 2.9)"
 ffmpeg -y -v error -f lavfi -i color=c=$CREAM:s=${W}x${H}:r=30 -i src/1-logo.png -filter_complex \
 "[1]scale=-2:$ELH[l];[0][l]overlay=(W-w)/2:$((H/20)),\
 drawtext=fontfile=$B:text='NOW LIVE':fontcolor=0x6B1F1F:fontsize=$((US/2)):x=(w-text_w)/2:y=$NY,\
 drawtext=fontfile=$B:text='avvasignage.com':fontcolor=0x6B1F1F:fontsize=$US:x=(w-text_w)/2:y=$UY" \
  -t 4.5 -pix_fmt yuv420p tmp/$N-c5.mp4
 # clips 3.5,3,3,3,4.5 with 0.5s crossfades = 15s
 ffmpeg -y -v error -i tmp/$N-c1.mp4 -i tmp/$N-c2.mp4 -i tmp/$N-c3.mp4 -i tmp/$N-c4.mp4 -i tmp/$N-c5.mp4 -i audio/voice.wav -i audio/music.wav -filter_complex \
 "[0][1]xfade=fade:0.5:3[a];[a][2]xfade=slideleft:0.5:5.5[b];[b][3]xfade=slideleft:0.5:8[c];[c][4]xfade=fade:0.5:10.5[d];[d]fade=t=out:st=14.5:d=0.5[v];\
  [5]asplit[vo1][vo2];[6][vo1]sidechaincompress=threshold=0.02:ratio=10:attack=20:release=500[duck];\
  [duck]volume=0.55[mu];[vo2]volume=1.6[vo];[mu][vo]amix=inputs=2:duration=first:normalize=0,afade=t=out:st=13.8:d=1.2,alimiter=limit=0.95[a]" \
  -map "[v]" -map "[a]" -t 15 -c:v libx264 -crf 18 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k $AUDIO
}
#      name  W    H    boxW boxH capY endLogoH noWy urlY urlSize capSize out
build  land  1920 1080 3600 2000 130  760      830  900  96      64     avva-launch.mp4
build  vert  1080 1920 2100 3000 340  900      1130 1230 80      56     avva-launch-vertical.mp4
for f in avva-launch.mp4 avva-launch-vertical.mp4; do ffprobe -v error -show_entries format=duration:stream=width,height,codec_name -of csv=p=0 $f | tr '\n' ' '; echo; done
