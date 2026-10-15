# Illustration source for the 2.5D lighting study

`yukimura-illustration-cutout.png` was prepared once with image_gen on 2026-10-15 from the left/front figure in `docs/routes/jigoku-2d/art/02-yukimura-model-reference.png`. The preparation requested one isolated, complete transparent character in the same relaxed standing pose, without the separate spear or reference panels. It is a generated derivative, not an exact pixel extraction of the earlier sheet.

The subsequent neutral/warm/cool files are Blender light-pass composites sharing this single source. They were not individually regenerated. `relight-surfaces.json` contains manually authored broad relief regions in top-left image coordinates, not model-predicted depth.

All source pixels, including the original alpha, are retained in this PNG. The image's original baked lighting remains part of the final art. See `docs/routes/jigoku-2d/RELIGHT_STUDY.md` for the method and limits.

## Spear motion study

`yukimura-yari-ready.png` (1536×1024 RGBA) was generated once with image_gen on 2026-10-15, referencing `yukimura-illustration-cutout.png`. The request preserved red lacquer, six coins, antlers, menpo, indigo cloth and chainmail; added a straight jumonji-yari with spaced two-handed grip and planted staggered stance; requested a transparent landscape cutout and elevated orthographic view. The actual image is a shallow three-quarter view, not a calibrated 30-degree isometric view. It is a newly generated pose, not a pixel-identical transformation of the original standing art. The generator supplied no reproducible seed. No third-party art was downloaded for this derivative.

`yari-surfaces.json` is a separate manually authored relief for this image. Three light plates were calculated in Blender before animation. The continuous frames in `YARI_MOTION.md` come from Blender shape-key deformation of these same image pixels, not independent image generation. The weapon is baked into the source image; it is not yet an independently swappable layer.
