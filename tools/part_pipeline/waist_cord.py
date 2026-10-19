"""The red waist cord of the concept: a braided band around the cuirass waist, a ball knot at the
front and two short tails with tassels. Built in body space from the assembled cuirass: the band
follows the outline of the do at the waist height, pushed out by the cord radius.

  blender-python tools/part_pipeline/waist_cord.py --assembled .tmp/stage4/assembled.blend --output .tmp/parts/waist-cord/waist-cord.glb
"""
from pathlib import Path
import argparse, json, math, sys
import bpy, bmesh
import numpy as np
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cord_geometry import braid_tube, monkey_fist, kumihimo, tube, resample, catmull

p = argparse.ArgumentParser(); p.add_argument('--assembled', required=True); p.add_argument('--output', required=True)
p.add_argument('--z', type=float, default=1.105); p.add_argument('--radius', type=float, default=.017)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
bpy.ops.wm.open_mainfile(filepath=str(Path(a.assembled).resolve()))
do = [o for o in bpy.context.scene.objects if o.name.startswith(('Part / do-front', 'Part / do-back'))]
pts = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in do])
band = pts[np.abs(pts[:, 2] - a.z) < .015]
cx, cy = band[:, 0].mean(), (band[:, 1].min() + band[:, 1].max()) / 2
# Outline by angle: farthest do vertex in each angular bin, then smoothed and pushed out.
ang = np.arctan2(band[:, 1] - cy, band[:, 0] - cx); rad = np.hypot(band[:, 0] - cx, band[:, 1] - cy)
bins = np.linspace(-np.pi, np.pi, 73); r = np.array([rad[(ang >= b0) & (ang < b1)].max() if ((ang >= b0) & (ang < b1)).any() else np.nan for b0, b1 in zip(bins[:-1], bins[1:])])
idx = np.arange(len(r)); r = np.interp(idx, idx[~np.isnan(r)], r[~np.isnan(r)], period=len(r))
r = np.convolve(np.concatenate([r[-3:], r, r[:3]]), np.ones(7) / 7, 'valid') + a.radius * 1.1
mid = (bins[:-1] + bins[1:]) / 2
ring = np.array([[cx + rr * math.cos(t), cy + rr * math.sin(t), a.z] for rr, t in zip(r, mid)])
front = ring[np.argmin(ring[:, 1])]

bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new(); R = a.radius
# Wrapped twice, the second turn one cord-width lower and slightly further out.
for dz, grow in ((0, 0), (-1.9 * R, .6 * R)):
    c = np.array([cx, cy, 0]); turn = c + (ring - c) * (1 + grow / np.linalg.norm((ring - c)[:, :2], axis=1))[:, None] + [0, 0, dz]
    braid_tube(bm, np.concatenate([turn, turn[:1]]), R, cap=False)
K = front + np.array([0, -R * 2.2, -.005])
monkey_fist(bm, K + [0, 0, -R], np.array([1., 0, 0]), np.array([0, 0, 1.]), np.array([0, -1., 0]), R * 1.15)
tails = []
for sgn in (-1, 1):
    tail = np.array([K + [sgn * .02, -.004, -.02], K + [sgn * .045, -.012, -.09], K + [sgn * .05, -.014, -.16]])
    braid_tube(bm, catmull(list(tail), 6), R * .85)
    end = tail[-1]
    # Tassel: a bound head and a skirt of threads.
    tube(bm, np.array([end, end + [0, 0, -.018]]), R * 1.25, sides=12)
    rng = np.random.default_rng(int(sgn + 2))
    for k in range(60):
        phi = rng.uniform(0, 2 * np.pi); rr = R * 1.1 * math.sqrt(rng.uniform(.2, 1)); L = rng.uniform(.07, .09)
        top = end + [rr * math.cos(phi), rr * math.sin(phi), -.018]
        tube(bm, np.array([top, top + [rr * .3 * math.cos(phi), rr * .3 * math.sin(phi), -L]]), .0011, sides=3, cap=False)
mesh = bpy.data.meshes.new('waist cord'); bm.to_mesh(mesh); bm.free()
for poly in mesh.polygons: poly.use_smooth = True
obj = bpy.data.objects.new('Waist cord', mesh); bpy.context.collection.objects.link(obj)
m = bpy.data.materials.new('Red braided silk'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (.22, .012, .012, 1); b.inputs['Roughness'].default_value = .7   # no sheen: glTF round-trips it at full white strength
wave = nt.nodes.new('ShaderNodeTexWave'); wave.inputs['Scale'].default_value = 400; wave.bands_direction = 'DIAGONAL'
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .5
nt.links.new(wave.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
obj.data.materials.append(m)
out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.export_scene.gltf(filepath=str(out.resolve()), export_format='GLB', use_selection=True)
print(json.dumps({'output': str(out), 'centre': [round(cx, 3), round(cy, 3)], 'radius_range': [round(r.min(), 3), round(r.max(), 3)], 'triangles': sum(len(f.vertices) - 2 for f in mesh.polygons)}))
