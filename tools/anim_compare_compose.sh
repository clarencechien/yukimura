#!/usr/bin/env bash
# Compose the frames from anim_compare_modal.py into one 1080p video at 24 fps:
#   1. full body, game clips: open-source rig (left) vs Tripo auto-rig (right)
#   2. upper-body close-up of the same
#   3. Tripo auto-rig with Tripo's own preset animations
# Short clips are looped to at least ~2.5 s.
#   tools/anim_compare_compose.sh .tmp/animcmp out.mp4
set -euo pipefail
IN=$1; OUT=$2
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
TMP=$(mktemp -d); n=0
label="fontfile=$FONT:fontsize=32:fontcolor=white:box=1:boxcolor=black@0.45:boxborderw=12"
loops() { local f; f=$(ls "$1" | wc -l); echo $(( (60 + f - 1) / f - 1 )); }
for shot in full close; do
  for clip in idle run slash hurt; do
    L=$(loops "$IN/$shot/open/$clip"); n=$((n + 1))
    ffmpeg -hide_banner -loglevel error -y -framerate 24 -i "$IN/$shot/open/$clip/%04d.png" -framerate 24 -i "$IN/$shot/tripo/$clip/%04d.png" \
      -filter_complex "[0:v]drawtext=text='Open source  (Blender bone heat)':x=30:y=30:$label[l];[1:v]drawtext=text='Tripo auto-rig':x=30:y=30:$label[r];[l][r]hstack=inputs=2,drawtext=text='game clip\: $clip':x=(w-tw)/2:y=h-80:$label,loop=loop=$L:size=1000,format=yuv420p[v]" \
      -map "[v]" -c:v libx264 -preset slow -crf 18 -r 24 "$TMP/$(printf %02d $n).mp4"
  done
done
for clip in run slash hurt idle; do
  L=$(loops "$IN/wide/preset/$clip"); n=$((n + 1))
  ffmpeg -hide_banner -loglevel error -y -framerate 24 -i "$IN/wide/preset/$clip/%04d.png" \
    -vf "drawtext=text='Tripo auto-rig + Tripo preset animation':x=30:y=30:$label,drawtext=text='preset\: $clip':x=(w-tw)/2:y=h-80:$label,loop=loop=$L:size=1000,format=yuv420p" \
    -c:v libx264 -preset slow -crf 18 -r 24 "$TMP/$(printf %02d $n).mp4"
done
for f in "$TMP"/*.mp4; do echo "file '$f'"; done > "$TMP/list.txt"
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy -movflags +faststart "$OUT"
rm -rf "$TMP"
ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,r_frame_rate -of compact "$OUT"
