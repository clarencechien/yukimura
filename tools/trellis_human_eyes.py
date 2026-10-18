"""Fit the repository's licensed Rocketbox orbital region beneath the kabuto.

Preserves the source UVs, skin normal map and textured eye geometry. This is a
static expression bake; the resulting patch is not a complete facial rig.
"""
from pathlib import Path
import hashlib, math
import bpy

SOURCE = Path('public/review/candidates/rocketbox.glb')
SOURCE_SHA = '142e74c396085ae990391803f28d178b2f41266e153f454d23ebebfe7f51e6e7'

def add_human_eyes():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
    previous = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE.resolve()))
    imported = set(bpy.context.scene.objects) - previous
    source = next(o for o in imported if o.type == 'MESH' and len(o.data.materials) == 3)
    material_index = next(i for i,m in enumerate(source.data.materials) if m.name.startswith('m024_head'))
    coordinates = []
    for i, vertex in enumerate(source.data.vertices):
        point = vertex.co.copy()
        for key in source.data.shape_keys.key_blocks:
            weight = .85 if 'BrowDown' in key.name else .08 if 'EyeBlink' in key.name else 0
            if weight:
                point += (key.data[i].co - vertex.co) * weight
        v = source.matrix_world @ point
        x,y,z = v.x*4.3, (v.y+.08)*3.4-.365, (v.z-1.706)*3.4+.747
        # Lower the inner brow and build the frown into the orbital tissue,
        # rather than drawing a dark diagonal over an unchanged eye.
        g = lambda value,center,width: math.exp(-((value-center)/width)**2)
        z -= .038*g(abs(x),.075,.075)*g(z,.81,.055)
        z += .14*(abs(x)-.155)*g(abs(x),.155,.085)*g(z,.755,.045)
        y -= .010*g(abs(x),.065,.035)*g(z,.81,.06)
        coordinates.append((x,y,z))
    faces = [p for p in source.data.polygons if p.material_index == material_index
             and all(.59 < coordinates[i][2] < .96 and abs(coordinates[i][0]) < .35
                     and coordinates[i][1] < -.16 for i in p.vertices)]
    ids = sorted({i for p in faces for i in p.vertices})
    remap = {old:new for new,old in enumerate(ids)}
    mesh = bpy.data.meshes.new('Rocketbox orbital topology with baked frown')
    mesh.from_pydata([coordinates[i] for i in ids],[],[[remap[i] for i in p.vertices] for p in faces])
    mesh.update()
    obj = bpy.data.objects.new('Human eyes and orbital skin / Rocketbox',mesh)
    bpy.context.collection.objects.link(obj)
    uv = mesh.uv_layers.new(name='Source UV')
    for target,original in zip(mesh.polygons,faces):
        target.use_smooth = True
        for dst,src in zip(target.loop_indices,original.loop_indices):
            uv.data[dst].uv = source.data.uv_layers.active.data[src].uv
    material = source.data.materials[material_index].copy()
    material.name = 'Human orbital skin and eyes / Rocketbox'
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Metallic'].default_value = 0
    shader.inputs['Roughness'].default_value = .62
    shader.inputs['Specular IOR Level'].default_value = .22
    color = shader.inputs['Base Color'].links[0].from_socket
    tint = material.node_tree.nodes.new('ShaderNodeMixRGB')
    tint.blend_type = 'MULTIPLY';tint.inputs[0].default_value=1
    tint.inputs[2].default_value=(.48,.36,.27,1)
    material.node_tree.links.new(color,tint.inputs[1])
    material.node_tree.links.new(tint.outputs[0],shader.inputs['Base Color'])
    mesh.materials.append(material)
    # Subdivision interpolates the existing anatomical surface; it is not
    # counted as new authored detail.
    modifier=obj.modifiers.new('Orbital surface interpolation','SUBSURF')
    modifier.levels=1;modifier.render_levels=1
    for o in imported:bpy.data.objects.remove(o,do_unlink=True)
    return {'source':str(SOURCE),'source_sha256':SOURCE_SHA,'license':'MIT',
            'brow_down':.85,'blink':.08,'source_patch_faces':len(faces),
            'method':'Source orbital skin and eye geometry, UV and normal map; static expression bake',
            'limitations':'No independent gaze controls, no complete anatomical eyeball reconstruction'}
