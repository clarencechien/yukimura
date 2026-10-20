#!/usr/bin/env bash
# Shrink a generated GLB (TRELLIS.2 / Tripo, ~70 MB) for Git: Draco geometry and WebP textures at the
# original 4096 resolution, no simplification. About 8 MB; renders match the original (mean abs diff
# 0.3/255). Viewers need Draco + EXT_texture_webp (three.js, Babylon.js, official Blender builds);
# tools/glb_decode.mjs turns it back into a plain GLB.
#   tools/glb_compress.sh in.glb out.glb
set -euo pipefail
npx -y @gltf-transform/cli@4.1.1 optimize "$1" "$2" --compress draco --texture-compress webp --texture-size 4096 --simplify false
