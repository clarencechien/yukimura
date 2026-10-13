"""Blender study: import real third-party assets, repair textures, export and render.

Run fetch_character_candidates.py first. No game character is replaced.
"""
import bpy
import json
import struct
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.tmp/character-candidates'
OUT = ROOT / 'public/review/candidates'
OUT.mkdir(parents=True, exist_ok=True)


def prepare(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if name == 'rocketbox':
        bpy.ops.import_scene.fbx(filepath=str(CACHE / name / 'Export/Male_Adult_10_facial.fbx'))
        # FBX refers to the artist's Windows drive. Resolve only downloaded textures.
        for image in bpy.data.images:
            if image.source == 'FILE':
                image.filepath = str(CACHE / name / 'Textures' / Path(image.filepath.replace('\\', '/')).name)
                image.reload()
        for mat in bpy.data.materials:
            p = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
            p.inputs['Roughness'].default_value = .62
            p.inputs['Metallic'].default_value = 0
            # The legacy specular map is not a metallic map. Keep FBX's specular wiring.
    else:
        bpy.ops.import_scene.gltf(filepath=str(CACHE / name / 'scene.gltf'))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    # Uniformly fit a 1.85 m reference height, preserving the entire hierarchy.
    bounds = [o.matrix_world @ Vector(v) for o in meshes for v in o.bound_box]
    lo = Vector(tuple(min(v[i] for v in bounds) for i in range(3)))
    hi = Vector(tuple(max(v[i] for v in bounds) for i in range(3)))
    scale = 1.85 / (hi.z - lo.z)
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    root = bpy.context.object
    for o in list(bpy.context.scene.objects):
        if o != root and o.parent is None:
            world = o.matrix_world.copy()
            o.parent = root
            o.matrix_world = world
    root.scale = (scale,) * 3
    root.location = (-(lo.x + hi.x) * .5 * scale, -(lo.y + hi.y) * .5 * scale, -lo.z * scale)
    root['source'] = ('https://github.com/microsoft/Microsoft-Rocketbox' if name == 'rocketbox'
                      else 'https://sketchfab.com/3d-models/cyber-samurai-26ccafaddb2745ceb56ae5cfc65bfed5')
    root['author'] = 'Microsoft / Rocketbox' if name == 'rocketbox' else 'KhoaMinh'
    root['license'] = 'MIT' if name == 'rocketbox' else 'CC-BY-4.0'
    root['changes'] = 'Uniform scale; texture preview cap; FBX material path repair; selected facial targets.'
    # Access size first: imported Blender images load lazily; has_data is initially False.
    # Preview delivery cap, not a geometric LOD or a mobile optimization claim.
    sizes = []
    for image in bpy.data.images:
        if image.type != 'IMAGE':
            continue
        original = list(image.size)
        largest = max(original)
        if not largest:
            raise ValueError(f'Missing texture: {image.filepath}')
        if largest > 1024:
            image.scale(round(original[0] * 1024 / largest), round(original[1] * 1024 / largest))
        image.pack()
        sizes.append({'name': image.name, 'source_size': original, 'preview_size': list(image.size)})
    bpy.context.view_layer.update()
    triangles = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    rigs = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    stats = {'id': name, 'triangles': triangles, 'bones': sum(len(o.data.bones) for o in rigs),
             'morph_targets': sum(len(o.data.shape_keys.key_blocks) - 1 for o in meshes if o.data.shape_keys),
             'materials': len({m.name for o in meshes for m in o.data.materials if m}),
             'textures': sizes, 'source_actions': len(bpy.data.actions)}
    # Keep the complete editable rig in the source study; ship only useful example expressions.
    bpy.ops.wm.save_as_mainfile(filepath=str(CACHE / f'{name}-study.blend'))
    keep = {'Basis', 'AK_01_BrowDownLeft', 'AK_02_BrowDownRight',
            'AK_09_EyeBlinkLeft', 'AK_10_EyeBlinkRight', 'AK_25_JawOpen'}
    for ob in meshes:
        if ob.data.shape_keys:
            for key in list(ob.data.shape_keys.key_blocks)[::-1]:
                if key.name not in keep:
                    ob.shape_key_remove(key)
    bpy.ops.export_scene.gltf(filepath=str(OUT / f'{name}.glb'), export_format='GLB',
                              export_animations=False, export_yup=True, export_cameras=False,
                              export_lights=False, export_extras=True)
    stats['glb_bytes'] = (OUT / f'{name}.glb').stat().st_size
    raw = (OUT / f'{name}.glb').read_bytes()
    gltf = json.loads(raw[20:20 + struct.unpack_from('<I', raw, 12)[0]])
    stats['export_triangles'] = sum(gltf['accessors'][p['indices']]['count'] // 3
                                    for m in gltf['meshes'] for p in m['primitives'])
    stats['export_animations'] = len(gltf.get('animations', []))
    stats['export_morph_targets'] = max((len(p.get('targets', [])) for m in gltf['meshes']
                                       for p in m['primitives']), default=0)
    return stats


def render(name):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 8
    world = bpy.data.worlds.new('studio')
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.15, .19, .23, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .4
    scene.view_settings.view_transform = 'AgX'
    for pos, energy, color, size in [((-3, -4, 5), 650, (1, .85, .72), 3),
                                     ((2, 1, 3), 850, (.6, .77, 1), 2),
                                     ((2, -3, 2), 180, (.85, .9, 1), 3)]:
        bpy.ops.object.light_add(type='AREA', location=pos)
        light = bpy.context.object
        light.data.energy = energy
        light.data.color = color
        light.data.shape = 'DISK'
        light.data.size = size
        light.rotation_euler = (Vector((0, 0, 1.2)) - light.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.012))
    mat = bpy.data.materials.new('neutral stage')
    mat.diffuse_color = (.055, .069, .075, 1)
    bpy.context.object.data.materials.append(mat)
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    scene.camera = cam
    cam.data.type = 'ORTHO'
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    for label, pos, target, width in [('full', (2.5, -7, 2.8), (0, 0, .96), 2.25),
                                      ('detail', (.7, -4, 1.9), (0, 0, 1.62), .66)]:
        cam.location = pos
        cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = width
        scene.render.filepath = str(OUT / f'{name}-{label}.png')
        bpy.ops.render.render(write_still=True)


results = []
for name in ['rocketbox', 'cyber-samurai']:
    results.append(prepare(name))
    (OUT / 'validation.json').write_text(json.dumps(results, indent=2) + '\n')
    if '--export-only' not in sys.argv:
        render(name)
