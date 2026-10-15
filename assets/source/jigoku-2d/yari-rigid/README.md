# Rigid illustration motion source

`body-clean.png` was prepared once with image_gen on 2026-10-15, referencing `../yukimura-yari-ready.png`. The request removed the spear and arms below the shoulder plates, filled the occluded waist, retained the same canvas/stance and transparent background. It is a generated cleanup, not a pixel-identical extraction. No reproducible generator seed was supplied.

`rig.json` contains manually marked projected shoulder/elbow/wrist positions, cutout polygons, a waist pivot and motion/angle limits. These are image-space coordinates, not anatomical measurements or a recovered 3D skeleton.

`layers/` contains nine cropped rigid pieces for each of three baked lighting variants; `layers.json` records the original canvas boxes. Body pieces use the newly cleaned source and Blender lighting. Arms, hands and spear reuse the prior illustration light plates. Polygon masks remove spear contamination from forearm pieces, and connected Alpha islands smaller than 24 pixels are removed. No texture warp is applied.

The renderer positions these pieces using constant-length two-link IK and rigid transforms. No per-frame image generation, mesh warping or nonuniform scaling. See `docs/routes/jigoku-2d/YARI_RIGID_MOTION.md` for the rendering and validation workflow, and its limitations.
