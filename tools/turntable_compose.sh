#!/usr/bin/env bash
# Compose the turntable frames from turntable_modal.py into one side-by-side 1080p video:
# full-body turn, then the upper-body close-up turn. Left/right labels burned in.
#   tools/turntable_compose.sh .tmp/turntable out.mp4 "TRELLIS.2 1536" "Tripo v3.1 Ultra"
set -euo pipefail
IN=$1; OUT=$2; LEFT=$3; RIGHT=$4
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
TMP=$(mktemp -d)
label="fontfile=$FONT:fontsize=34:fontcolor=white:box=1:boxcolor=black@0.45:boxborderw=12:y=36"
for shot in full close; do
  ffmpeg -hide_banner -loglevel error -y -framerate 30 -i "$IN/$shot/left/%04d.png" -framerate 30 -i "$IN/$shot/right/%04d.png" \
    -filter_complex "[0:v]drawtext=text='$LEFT':x=36:$label[l];[1:v]drawtext=text='$RIGHT':x=36:$label[r];[l][r]hstack=inputs=2,format=yuv420p[v]" \
    -map "[v]" -c:v libx264 -preset slow -crf 17 "$TMP/$shot.mp4"
done
printf "file '%s'\nfile '%s'\n" "$TMP/full.mp4" "$TMP/close.mp4" > "$TMP/list.txt"
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy -movflags +faststart "$OUT"
rm -rf "$TMP"
ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,r_frame_rate -of compact "$OUT"
