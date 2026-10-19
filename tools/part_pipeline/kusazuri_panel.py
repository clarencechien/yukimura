"""Procedural kusazuri panel textured with the stage-2 drawing.

TRELLIS breaks a flat, straight-on panel into fragments (no depth cue), and a lamellar panel is a
regular object anyway: five level lames, each a curved strip that leans out at the bottom and
tucks its top behind the lame above, with a rolled gold edge on the bottom lame. Every vertex
samples the drawing through the panel's trapezoid in the image, so the painted lacing, scratches
and gold waves land on the matching lame.

  blender-python tools/part_pipeline/kusazuri_panel.py --output .tmp/parts/kusazuri-proc/seed-0/kusazuri-proc-high.glb
"""
from pathlib import Path
import argparse, json
import bpy, bmesh
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument('--image', default=str(ROOT / 'docs/experiments/future-sanada/part-pipeline/images/part-kusazuri.png'))
p.add_argument('--output', required=True)
a = p.parse_args()
bpy.ops.wm.read_factory_settings(use_empty=True)

# Panel outline in the drawing (image fractions, top-left, top-right, bottom-right, bottom-left)
# and the lame boundaries as fractions of the panel height, read off the drawing.
QUAD = [(.362, .262), (.708, .262), (.762, .830), (.352, .830)]
EDGES = [0, .168, .336, .504, .673, 1.]
H, W_TOP, W_BOT = .30, .225, .262        # metres
R = .34                                  # hip curvature radius across the panel
LEAN, TUCK, THICK = .010, .006, .0035    # outward lean over one lame, tuck of a lame top, plate thickness
NS, NT = 28, 8

def image_uv(s, v):
    """Panel coords (s across 0..1, v down 0..1) -> UV in the drawing (bilinear in the quad)."""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = QUAD
    top = np.array([x0 + (x1 - x0) * s, y0 + (y1 - y0) * s]); bot = np.array([x3 + (x2 - x3) * s, y3 + (y2 - y3) * s])
    x, y = top + (bot - top) * v
    return x, 1 - y

def point(s, v, t):
    """3D point: s across, v down the panel, t down the current lame (0..1)."""
    w = W_TOP + (W_BOT - W_TOP) * v; x = (s - .5) * w
    y_back = x * x / (2 * R)                                    # sides curve back around the hip
    out = LEAN * t - TUCK * (1 - t) ** 3                        # lean out at the bottom, tuck at the top
    return (x, -(out - y_back), H * (1 - v))                    # Blender: -Y is the front

bm = bmesh.new(); uv_layer = bm.loops.layers.uv.new('UVMap')
lame_faces = []
for i in range(len(EDGES) - 1):
    v0, v1 = EDGES[i], EDGES[i + 1] + (.012 if i < len(EDGES) - 2 else 0)   # each lame runs a little under the next
    grid = [[bm.verts.new(point(s, v0 + (v1 - v0) * t, t)) for s in np.linspace(0, 1, NS + 1)] for t in np.linspace(0, 1, NT + 1)]
    for r in range(NT):
        for c in range(NS):
            f = bm.faces.new((grid[r][c], grid[r + 1][c], grid[r + 1][c + 1], grid[r][c + 1]))   # wound so normals face the front (-Y)
            for loop, (rr, cc) in zip(f.loops, ((r, c), (r + 1, c), (r + 1, c + 1), (r, c + 1))):
                s, t = cc / NS, rr / NT                         # sample inside the drawn lame only: no grey margin, no trim of the lame above
                loop[uv_layer].uv = image_uv(.015 + .97 * s, EDGES[i] + .012 + (EDGES[i + 1] - EDGES[i] - (.035 if i == len(EDGES) - 2 else .016)) * t)
            lame_faces.append(f)
mesh = bpy.data.meshes.new('kusazuri'); bm.to_mesh(mesh); bm.free()
obj = bpy.data.objects.new('Kusazuri / lames', mesh); bpy.context.collection.objects.link(obj)
mod = obj.modifiers.new('thickness', 'SOLIDIFY'); mod.thickness = THICK; mod.offset = -1; mod.use_even_offset = True
mat = bpy.data.materials.new('Kusazuri lacquer'); mat.use_nodes = True; nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(a.image); tex.extension = 'EXTEND'
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value = .38; bsdf.inputs['Coat Weight'].default_value = .5
obj.data.materials.append(mat)
back = bpy.data.materials.new('Kusazuri back'); back.use_nodes = True; b = back.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (.035, .022, .02, 1); b.inputs['Roughness'].default_value = .7
obj.data.materials.append(back); mod.material_offset = 1; mod.material_offset_rim = 1   # dark lacquered back and edges

# Gold rolled edge: bottom and sides of the bottom lame, bottom of each upper lame.
gold = bpy.data.materials.new('Gold edging'); gold.use_nodes = True; g = gold.node_tree.nodes['Principled BSDF']
g.inputs['Base Color'].default_value = (.78, .55, .25, 1); g.inputs['Metallic'].default_value = 1; g.inputs['Roughness'].default_value = .32
def tube(points, radius, name):
    curve = bpy.data.curves.new(name, 'CURVE'); curve.dimensions = '3D'; curve.bevel_depth = radius; curve.bevel_resolution = 3
    sp = curve.splines.new('POLY'); sp.points.add(len(points) - 1)
    for q, co in zip(sp.points, points): q.co = (*co, 1)
    o = bpy.data.objects.new(name, curve); bpy.context.collection.objects.link(o); o.data.materials.append(gold); return o
edges = []
for i in range(1, len(EDGES)):
    edges.append(tube([point(s, EDGES[i], 1) for s in np.linspace(0, 1, 40)], .0026 if i == len(EDGES) - 1 else .0016, f'Kusazuri / edge {i}'))
for s in (0, 1):
    edges.append(tube([point(s, v, (v - EDGES[-2]) / (1 - EDGES[-2])) for v in np.linspace(EDGES[-2], 1, 12)], .0026, f'Kusazuri / side {s}'))
bpy.context.view_layer.update()
for o in [obj] + edges:
    o.select_set(True); bpy.context.view_layer.objects.active = o
    if o.type == 'CURVE': bpy.ops.object.convert(target='MESH')
    else: bpy.ops.object.modifier_apply(modifier='thickness')
    o.select_set(False)
out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(out.resolve()), export_format='GLB')
tris = sum(len(f.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for f in o.data.polygons)
print(json.dumps({'output': str(out), 'triangles': tris, 'lames': len(EDGES) - 1, 'size_m': [W_BOT, H]}))
