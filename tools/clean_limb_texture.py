"""Clean the generated texture on the mechanical limb plates (knees, shins, boots, gauntlets).

Their geometry is already clean (clay renders); the lumpy look is TRELLIS's blotchy albedo: dark
smears across the red lacquer. In those regions each texel is classed lacquer / gilt / dark
(trellis_body_materials.masks); lacquer and dark texels are replaced by an edge-preserving
smoothing of their own class (smears removed, plate edges and gold trims kept), gilt is lightly
smoothed. A little of the original variation is mixed back so the lacquer is not plastic.
"""
from pathlib import Path
import argparse, json, sys
import bpy
import numpy as np
import cv2
from scipy import ndimage
from mathutils import Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
from uv_raster import rasterize
from trellis_body_materials import masks

p = argparse.ArgumentParser()
p.add_argument('--model', required=True)
p.add_argument('--output', required=True)
a = p.parse_args()

def limb_region(P):
    x, z = P[..., 0], P[..., 2]
    return (z < .70) | ((np.abs(x) > .25) & (z > .74) & (z < 1.30))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        world = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix.Identity(4); o.data.transform(world)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
body = next(o for o in bpy.context.scene.objects if o.data.materials and o.data.materials[0].name.startswith('Body v2'))
mat = body.data.materials[0]; bsdf = mat.node_tree.nodes['Principled BSDF']
cnode = bsdf.inputs['Base Color'].links[0].from_node; mnode = bsdf.inputs['Metallic'].links[0].from_node
while mnode.type != 'TEX_IMAGE': mnode = mnode.inputs[0].links[0].from_node
img = cnode.image; size = img.size[0]
col = np.empty(size * size * 4, np.float32); img.pixels.foreach_get(col); col = col.reshape(size, size, 4)
mi = mnode.image; msz = mi.size[0]
mr = np.empty(msz * msz * 4, np.float32); mi.pixels.foreach_get(mr); mr = mr.reshape(msz, msz, 4)
metal = cv2.resize(mr[..., 2], (size, size), interpolation=cv2.INTER_LINEAR)
pos, _ = rasterize(body.data, size)
region = (pos[..., 3] > .5) & limb_region(pos)
region = ndimage.binary_dilation(region, iterations=2) & (pos[..., 3] > .5)
rgb = col[..., :3]
h, s, v, red, gold, dark = masks(rgb, metal)
out = rgb.copy()
srgb8 = np.clip(rgb * 255, 0, 255).astype(np.uint8)
def classwise(weight, d, sc, ss, iters):
    """Edge-preserving smoothing within one class: normalized bilateral of (colour x weight)."""
    acc = srgb8.astype(np.float32) * weight[..., None]; w = weight.astype(np.float32).copy()
    for _ in range(iters):
        acc = cv2.bilateralFilter(acc, d, sc, ss); w = cv2.bilateralFilter(w, d, 1e3, ss)
    return acc / np.maximum(w, 1e-3)[..., None] / 255
red_s = classwise(red, 15, 60, 9, 3)
dark_s = classwise(dark, 11, 40, 6, 2)
gold_s = classwise(gold, 5, 30, 3, 1)
clean = (red_s * red[..., None] + dark_s * dark[..., None] + gold_s * gold[..., None]) / np.maximum(red + dark + gold, 1e-3)[..., None]
known = (red + dark + gold) > .3
mix = np.where(known, .9, .4)[..., None]
out = rgb * (1 - mix) + np.where(known[..., None], clean, rgb) * mix
col[..., :3] = np.where(region[..., None], out, rgb)
img.pixels.foreach_set(col.ravel()); img.pack()
Path(a.output).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()), export_format='GLB', use_selection=True)
rep = {'texels_in_region': int(region.sum()), 'red': float(red[region].mean()), 'gold': float(gold[region].mean()), 'dark': float(dark[region].mean()),
       'filters': {'lacquer': 'bilateral d15 c60 s9 x3', 'dark': 'bilateral d11 c40 s6 x2', 'gilt': 'bilateral d5 c30 s3', 'mix_back_original': .10}}
Path(a.output).with_name('limb-texture-report.json').write_text(json.dumps(rep, indent=2) + '\n'); print(json.dumps(rep))
