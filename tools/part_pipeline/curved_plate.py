"""A single curved armour plate textured with a region of a stage-2 drawing.

For plates TRELLIS turns into something else (the upper-arm plate came back as a vest twice):
a cylindrical shell section around the local Z axis, its arc centred on -Y (the front), with a
gold rolled rim. Every vertex samples the drawing through the plate's quad in the image.

  blender-python tools/part_pipeline/curved_plate.py --image .../part-kote.png \
      --quad .335,.275,.70,.275,.69,.458,.345,.458 --width-deg 200 --radius .085 --height .2 --output X.glb
"""
from pathlib import Path
import argparse, json, math, sys
import bpy, bmesh
import numpy as np

p = argparse.ArgumentParser()
p.add_argument('--image', required=True); p.add_argument('--quad', required=True, help='x0,y0,x1,y1,x2,y2,x3,y3 image fractions: TL,TR,BR,BL')
p.add_argument('--width-deg', type=float, default=200); p.add_argument('--radius', type=float, default=.085); p.add_argument('--height', type=float, default=.2)
p.add_argument('--taper', type=float, default=1.0, help='bottom radius / top radius'); p.add_argument('--thickness', type=float, default=.004)
p.add_argument('--output', required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
q = [float(x) for x in a.quad.split(',')]; QUAD = list(zip(q[0::2], q[1::2]))
NS, NV = 40, 12

def image_uv(s, v):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = QUAD
    top = np.array([x0 + (x1 - x0) * s, y0 + (y1 - y0) * s]); bot = np.array([x3 + (x2 - x3) * s, y3 + (y2 - y3) * s])
    x, y = top + (bot - top) * v
    return x, 1 - y

def point(s, v):
    r = a.radius * (1 + (a.taper - 1) * v); ang = math.radians((s - .5) * a.width_deg)
    return (r * math.sin(ang), -r * math.cos(ang), a.height * (.5 - v))

bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
grid = [[bm.verts.new(point(s, v)) for s in np.linspace(0, 1, NS + 1)] for v in np.linspace(0, 1, NV + 1)]
for r in range(NV):
    for c in range(NS):
        f = bm.faces.new((grid[r][c], grid[r + 1][c], grid[r + 1][c + 1], grid[r][c + 1]))
        for loop, (rr, cc) in zip(f.loops, ((r, c), (r + 1, c), (r + 1, c + 1), (r, c + 1))):
            loop[uv].uv = image_uv(.02 + .96 * cc / NS, .02 + .96 * rr / NV)
mesh = bpy.data.meshes.new('plate'); bm.to_mesh(mesh); bm.free()
obj = bpy.data.objects.new('Plate', mesh); bpy.context.collection.objects.link(obj)
for poly in mesh.polygons: poly.use_smooth = True
mod = obj.modifiers.new('thickness', 'SOLIDIFY'); mod.thickness = a.thickness; mod.offset = -1; mod.material_offset = 1; mod.material_offset_rim = 1
mat = bpy.data.materials.new('Plate lacquer'); mat.use_nodes = True; nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(a.image); tex.extension = 'EXTEND'
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value = .38; bsdf.inputs['Coat Weight'].default_value = .5
back = bpy.data.materials.new('Plate back'); back.use_nodes = True; b = back.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (.035, .022, .02, 1); b.inputs['Roughness'].default_value = .7
obj.data.materials.append(mat); obj.data.materials.append(back)
gold = bpy.data.materials.new('Gold edging'); gold.use_nodes = True; g = gold.node_tree.nodes['Principled BSDF']
g.inputs['Base Color'].default_value = (.78, .55, .25, 1); g.inputs['Metallic'].default_value = 1; g.inputs['Roughness'].default_value = .32
rims = []
for v in (0, 1):
    curve = bpy.data.curves.new(f'rim {v}', 'CURVE'); curve.dimensions = '3D'; curve.bevel_depth = .0028; curve.bevel_resolution = 3
    sp = curve.splines.new('POLY'); pts = [point(s, v) for s in np.linspace(0, 1, 48)]; sp.points.add(len(pts) - 1)
    for pt, co in zip(sp.points, pts): pt.co = (*co, 1)
    o = bpy.data.objects.new(f'Rim {v}', curve); bpy.context.collection.objects.link(o); o.data.materials.append(gold); rims.append(o)
for o in [obj] + rims:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    if o.type == 'CURVE': bpy.ops.object.convert(target='MESH')
    else: bpy.ops.object.modifier_apply(modifier='thickness')
out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(out.resolve()), export_format='GLB', use_selection=True)
print(json.dumps({'output': str(out), 'triangles': sum(len(f.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for f in o.data.polygons)}))
