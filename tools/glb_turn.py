"""Turn a GLB about the vertical axis and re-export it (Tripo exports face +X; our renders expect -Y).

  blender-python tools/glb_turn.py in.glb out.glb [--degrees -90]
"""
import argparse, math, sys
import bpy
from mathutils import Matrix
p = argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('output'); p.add_argument('--degrees', type=float, default=-90)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.input)
turn = Matrix.Rotation(math.radians(a.degrees), 4, 'Z')
for o in [o for o in bpy.context.scene.objects if o.parent is None]: o.matrix_world = turn @ o.matrix_world
bpy.ops.export_scene.gltf(filepath=a.output, export_format='GLB')
