# Rigid illustration motion source

`body-clean.png` was prepared once with image_gen on 2026-10-15, referencing `../yukimura-yari-ready.png`. The request removed the spear and arms below the shoulder plates, filled the occluded waist, retained the same canvas/stance and transparent background. It is a generated cleanup, not a pixel-identical extraction. No reproducible generator seed was supplied.

`rig.json` contains manually marked projected shoulder/elbow/wrist and hip/knee/ankle/toe positions, cutout polygons, a waist pivot and motion/angle limits. These are image-space coordinates, not anatomical measurements or a recovered 3D skeleton.

`layers/` contains fifteen cropped rigid pieces for each of three baked lighting variants; `layers.json` records the original canvas boxes. Body pieces use the newly cleaned source and Blender lighting. Arms, hands and spear reuse the prior illustration light plates. Polygon masks remove spear contamination from forearm pieces, and connected Alpha islands smaller than 24 pixels are removed. No texture warp is applied.

The renderer positions these pieces using constant-length two-link IK and rigid transforms. No per-frame image generation, mesh warping or nonuniform scaling. See `docs/routes/jigoku-2d/YARI_RIGID_MOTION.md` for the rendering and validation workflow, and its limitations.

Lower-body revision: split the same clean body into pelvis/skirt, thighs, shins and feet using overlapping alpha polygons. No new generated art or hidden-surface reconstruction. Pelvis translation leads the arm stroke; front foot is planted, rear foot rotates 3 degrees around a fixed toe. Constant projected leg lengths and a 24-degree knee-change limit; these are authored motion constraints, not dynamic balance.

`static-lower-baseline.webp` preserves the neutral thrust atlas from commit `d932728` for reproducible before/after review.
