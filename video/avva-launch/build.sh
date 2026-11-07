#!/usr/bin/env bash
# Builds the 15s Avva Signage launch video (1920x1080, 30fps). Run from this folder.
set -e
cd "$(dirname "$0")"; mkdir -p tmp
B=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
CREAM=0xFDF4E3
# compose(img, out, mode): fit foreground over blurred cover background, 3840x2160
comp() { ffmpeg -y -v error -i "$1" -filter_complex \
 "[0]split[a][b];[a]scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,boxblur=40:5,eq=brightness=-0.15[bg];[b]scale=-2:2000[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" -frames:v 1 "$2"; }
comp_logo() { ffmpeg -y -v error -f lavfi -i color=c=$CREAM:s=3840x2160 -i "$1" -filter_complex "[1]scale=-2:1900[fg];[0][fg]overlay=(W-w)/2:(H-h)/2" -frames:v 1 "$2"; }
comp_logo src/1-logo.png tmp/1.png
comp src/2-sign.png tmp/2.png
comp src/3-birthday.jpg tmp/3.png
comp src/4-beautybar.jpg tmp/4.png
comp src/5-treat.jpg tmp/5.png
# clip(png, dur, out, zoom expr, caption)
clip() { local d=$2; ffmpeg -y -v error -loop 1 -framerate 30 -i "$1" -t $d -vf \
 "zoompan=z='$4':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30${5:+,$5}" -pix_fmt yuv420p -r 30 "$3"; }
CAP() { echo "drawtext=fontfile=$B:text='$1':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=h-130:box=1:boxcolor=0x3A0D0Dcc:boxborderw=24:enable='between(t,0.5,$2)'"; }
clip tmp/1.png 3 tmp/c1.mp4 "1+0.06*on/90"
clip tmp/2.png 3 tmp/c2.mp4 "1.15-0.1*on/90" "$(CAP 'Signage that makes you shine' 2.9)"
clip tmp/3.png 2.5 tmp/c3.mp4 "1+0.08*on/75" "$(CAP 'Neon' 2.4)"
clip tmp/4.png 2.5 tmp/c4.mp4 "1+0.08*on/75" "$(CAP 'LED' 2.4)"
clip tmp/5.png 3 tmp/c5.mp4 "1.1-0.06*on/90" "$(CAP 'Custom made for you' 2.9)"
# end card
ffmpeg -y -v error -f lavfi -i color=c=$CREAM:s=1920x1080:r=30 -i src/1-logo.png -filter_complex \
"[1]scale=-2:760[l];[0][l]overlay=(W-w)/2:30,\
drawtext=fontfile=$B:text='NOW LIVE':fontcolor=0x6B1F1F:fontsize=54:x=(w-text_w)/2:y=830,\
drawtext=fontfile=$B:text='avvasignage.com':fontcolor=0x6B1F1F:fontsize=96:x=(w-text_w)/2:y=900" \
 -t 3.5 -pix_fmt yuv420p tmp/c6.mp4
# clips 3,3,2.5,2.5,3,3.5 with 0.5s crossfades = 15s
ffmpeg -y -v error -i tmp/c1.mp4 -i tmp/c2.mp4 -i tmp/c3.mp4 -i tmp/c4.mp4 -i tmp/c5.mp4 -i tmp/c6.mp4 -filter_complex \
"[0][1]xfade=fade:0.5:2.5[a];[a][2]xfade=fade:0.5:5[b];[b][3]xfade=slideleft:0.5:7[c];[c][4]xfade=slideleft:0.5:9[d];[d][5]xfade=fade:0.5:11.5[e];[e]fade=t=out:st=14.5:d=0.5" \
 -c:v libx264 -crf 18 -pix_fmt yuv420p -r 30 avva-launch.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 avva-launch.mp4
