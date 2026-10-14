"""Replace v16's geometric masks with a shared, licensed human head.

Uses the pinned Rocketbox candidate already in the repository (MIT). Preserves
the 92-bone battle rig and all clips; no second runtime skeleton or morph system.
"""
import bpy
import bmesh
import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gltf_assets import share_images

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / '.tmp/face-v17'
OUT = STAGE / 'models'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT / 'public/review/candidates/rocketbox.glb'
SOURCE_SHA = '142e74c396085ae990391803f28d178b2f41266e153f454d23ebebfe7f51e6e7'


def source_head():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    source = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and len(o.data.materials) == 3)
    index = next(i for i, m in enumerate(source.data.materials) if m.name == 'm024_head')
    faces = [p for p in source.data.polygons if p.material_index == index]
    ids = sorted({i for p in faces for i in p.vertices})
    remap = {old: new for new, old in enumerate(ids)}
    coords = []
    for i in ids:
        v = source.data.vertices[i].co.copy()
        # Authored brow-down target: a restrained concentrated expression.
        for key in source.data.shape_keys.key_blocks:
            if 'BrowDown' in key.name:
                v += (key.data[i].co - source.data.vertices[i].co) * .22
        coords.append(source.matrix_world @ v)
    data = bpy.data.meshes.new('Rocketbox shared head topology')
    data.from_pydata(coords, [], [[remap[i] for i in p.vertices] for p in faces])
    data.update()
    ob = bpy.data.objects.new('shared human head', data)
    bpy.context.scene.collection.objects.link(ob)
    uv = data.uv_layers.new(name='UVMap')
    for a, b in zip(data.polygons, faces):
        a.use_smooth = True
        for dst, src in zip(a.loop_indices, b.loop_indices):
            uv.data[dst].uv = source.data.uv_layers.active.data[src].uv
    mat = source.data.materials[index]
    bs = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    color = bs.inputs['Base Color'].links[0].from_node.image
    normal_node = bs.inputs['Normal'].links[0].from_node
    normal = normal_node.inputs['Color'].links[0].from_node.image
    # Embedded images have no external path. Make owned, packed pixel copies;
    # repacking their imported lazy buffers can discard data in bpy 4.3.
    def owned(image, name):
        w,h=image.size;assert w>0 and h>0
        pixels=np.empty(w*h*4,dtype=np.float32);image.pixels.foreach_get(pixels)
        copy=bpy.data.images.new(name,width=w,height=h,alpha=True)
        copy.colorspace_settings.name=image.colorspace_settings.name
        copy.pixels.foreach_set(pixels);copy.pack();return copy
    color=owned(color,'Rocketbox skin color source')
    normal=owned(normal,'Rocketbox shared skin normal')
    clean = bpy.data.materials.new('human skin source'); clean.use_nodes = True
    bs = clean.node_tree.nodes.get('Principled BSDF')
    for image, socket in [(color, 'Base Color'), (normal, 'Normal')]:
        tex = clean.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = image
        if socket == 'Normal':
            n = clean.node_tree.nodes.new('ShaderNodeNormalMap')
            n.inputs['Strength'].default_value = .65
            clean.node_tree.links.new(tex.outputs['Color'], n.inputs['Color'])
            clean.node_tree.links.new(n.outputs['Normal'], bs.inputs[socket])
        else:clean.node_tree.links.new(tex.outputs['Color'], bs.inputs[socket])
    bs.inputs['Roughness'].default_value = .64
    bs.inputs['Specular IOR Level'].default_value = .28
    data.materials.append(clean)
    for o in list(bpy.context.scene.objects):
        if o != ob:bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(STAGE / 'shared-head.blend'), compress=True)


def components(mesh):
    # Logical welding only. Preserve the armour's UV seams and split normals.
    verts = mesh.data.vertices
    parent = list(range(len(verts)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    positions = {}
    for v in verts:
        key = tuple(round(x, 5) for x in v.co)
        if key in positions:parent[find(v.index)] = find(positions[key])
        else:positions[key] = v.index
    for edge in mesh.data.edges:parent[find(edge.vertices[0])] = find(edge.vertices[1])
    groups = {}
    for v in verts:groups.setdefault(find(v.index), []).append(v)
    return list(groups.values())


def remove_old_face(mesh):
    selected = set(); pieces = []
    for comp in components(mesh):
        lo = [min(v.co[i] for v in comp) for i in range(3)]
        hi = [max(v.co[i] for v in comp) for i in range(3)]
        # Includes skin sphere, cheek/nose mask, black eye bars, chin laces and
        # Ieyasu's metal whiskers. Excludes kabuto, six coins and lower gorget.
        face = 1.74 < lo[2] < 1.96 and hi[2] < 2.04 and lo[1] < -.10 and max(abs(lo[0]), abs(hi[0])) < .14
        neck = len(comp) == 54 and lo[2] < 1.61 and 1.85 < hi[2] < 1.86
        if face or neck:
            selected.update(v.index for v in comp)
            pieces.append({'vertices': len(comp), 'min': lo, 'max': hi})
    assert 2300 < len(selected) < 2700, f'Unexpected old face selection: {len(selected)}'
    bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in selected], context='VERTS')
    bm.to_mesh(mesh.data); bm.free(); mesh.data.update()
    return pieces


def gauss(x, c, width):
    return np.exp(-((x-c)/width)**2)


def complexion(head, kind):
    """Map restrained stubble/age tones in anatomical space, preserving source UVs."""
    mat = head.data.materials[0].copy(); mat.name = f'human skin / {kind}'
    head.data.materials[0] = mat
    tex = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image.name.startswith('Rocketbox skin color'))
    image = tex.image
    w, h = image.size
    pixels = np.empty(w*h*4, dtype=np.float32); image.pixels.foreach_get(pixels); pixels = pixels.reshape(h,w,4)
    positions = np.zeros((h,w,3), dtype=np.float32); valid = np.zeros((h,w), dtype=bool)
    # Rasterize anatomical positions to the existing UV chart. No UV repacking.
    head.data.calc_loop_triangles(); uv = head.data.uv_layers.active
    for tri in head.data.loop_triangles:
        t = np.array([uv.data[i].uv for i in tri.loops]) * [w-1,h-1]
        a,b,c = t
        det = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
        if abs(det) < 1e-7:continue
        low = np.maximum(0,np.floor(t.min(axis=0)).astype(int)); high = np.minimum([w-1,h-1],np.ceil(t.max(axis=0)).astype(int))
        xx,yy = np.meshgrid(np.arange(low[0],high[0]+1),np.arange(low[1],high[1]+1))
        u = ((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/det
        v = ((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/det
        inside = (u>=-1e-5)&(v>=-1e-5)&(u+v<=1.00001)
        p = np.array([head.data.vertices[i].co for i in tri.vertices])
        interp = u[...,None]*p[0] + v[...,None]*p[1] + (1-u-v)[...,None]*p[2]
        positions[yy[inside],xx[inside]] = interp[inside]; valid[yy[inside],xx[inside]] = True
    x,y,z = positions.transpose(2,0,1)
    front = np.clip((-y-.025)/.045,0,1)*valid
    # The mouth/lips and eye whites remain uncovered. Hair is a tint of the skin
    # atlas, not a stack of opaque polygon moustache rods.
    # Landmarks measured on this mesh: eye centers 1.706, nose tip 1.663,
    # upper lip 1.635, chin 1.598 (meters before fitting).
    moustache = gauss(z,1.645,.0045)*np.exp(-(x/.034)**6)*(1-gauss(x,0,.005))
    chin = gauss(z,1.602,.011)*np.exp(-(x/.032)**4)
    jaw = gauss(z,1.622,.024)*gauss(abs(x),.047,.017)
    grain = np.random.default_rng(1717).uniform(.45,1,(h,w))
    beard = np.clip(moustache*.90 + chin*.75 + jaw*.33,0,1)*front*grain
    old = kind == 'ieyasu'
    hair_color = np.array([.32,.30,.26]) if old else np.array([.023,.017,.014])
    strength = beard*(.95 if old else .52)
    pixels[:,:,:3] = pixels[:,:,:3]*(1-strength[:,:,None]) + hair_color*strength[:,:,None]
    eye = gauss(abs(x),.034,.018)*gauss(z,1.690,.005)*front
    cheek = gauss(abs(x),.050,.025)*gauss(z,1.664,.02)*front
    pixels[:,:,:3] *= 1-eye[:,:,None]*(.18 if old else .08)
    pixels[:,:,:3] *= (1-cheek[:,:,None]*np.array([.015,.045,.06]))
    if old:
        # Fine nasolabial and under-eye creases; source pores/normals are retained.
        crease = gauss(abs(x),.019+(1.660-z)*.55,.0014)*gauss(z,1.644,.015)*front
        pixels[:,:,:3] *= 1-crease[:,:,None]*.16
        forehead=(gauss(z,1.730+.05*x*x,.0009)+gauss(z,1.740+.05*x*x,.0009))*gauss(x,0,.060)*front
        pixels[:,:,:3] *= 1-forehead[:,:,None]*.14
    out = bpy.data.images.new(f'{kind} mature complexion',width=w,height=h,alpha=True)
    out.colorspace_settings.name='sRGB';out.pixels.foreach_set(np.clip(pixels,0,1).ravel());out.pack()
    tex.image = out
    return mat


def fit(head, rig, kind):
    old = kind == 'ieyasu'
    vg_head = head.vertex_groups.new(name='body.head')
    vg_chest = head.vertex_groups.new(name='body.spine02')
    positions=[]
    for v in head.data.vertices:
        x,y,z = v.co
        front = max(0,min(1,(-y-.02)/.045))
        jaw = math.exp(-((z-1.618)/.030)**2)
        cheek = math.exp(-((abs(x)-.052)/.023)**2 - ((z-1.664)/.025)**2)*front
        x *= (1.28 if old else 1.22)*(1+(0.11 if old else .02)*jaw)
        y = y*1.10-.13 - cheek*(.004 if old else -.002)
        z = (z-1.8431213)*1.30+2.08 - cheek*(.005 if old else 0)
        v.co=(x,y,z);positions.append([x,y,z])
        # Neck base blends into the upper torso; cranium follows the exact same
        # deform bone as the helmet, so both normal skinning and boss BVA work.
        t = max(0,min(1,(z-1.68)/.13));t=t*t*(3-2*t)
        if t>0:vg_head.add([v.index],t,'REPLACE')
        if t<1:vg_chest.add([v.index],1-t,'REPLACE')
    head.data.update()
    return {'vertices':len(positions),'min':[min(p[i] for p in positions) for i in range(3)],
            'max':[max(p[i] for p in positions) for i in range(3)],'deform_bones':['body.head','body.spine02']}


def attachments(mesh, head):
    """Shared padded brim and cheek straps; reuse the existing leather material."""
    verts=[];faces=[];sides=24
    for rx,ry,z in [(.151,.170,1.991),(.151,.170,2.018),(.145,.164,1.991),(.145,.164,2.018)]:
        verts.extend([(rx*math.cos(i*math.tau/sides),-.085+ry*math.sin(i*math.tau/sides),z) for i in range(sides)])
    for a,b in [(0,1),(1,3),(3,2),(2,0)]:
        for i in range(sides):
            j=(i+1)%sides;faces.append((a*sides+i,a*sides+j,b*sides+j,b*sides+i))
    surface=BVHTree.FromPolygons([v.co for v in head.data.vertices],[list(p.vertices) for p in head.data.polygons])
    for sign in [-1,1]:
        path=[(sign*.128,-.130,1.944),(sign*.126,-.161,1.885),
              (sign*.114,-.195,1.815),(sign*.071,-.229,1.772),(sign*.023,-.228,1.758)]
        start=len(verts)
        for x,y,z in path:
            # Fit against the actual face, rather than leaving a polygonal loop
            # hanging away from the cheeks. Move inward if outside its silhouette.
            for shrink in [1,.96,.92,.88,.84,.80,.76]:
                hit,normal,_,_=surface.ray_cast(Vector((x*shrink,-1,z)),Vector((0,1,0)),2)
                if hit is not None:
                    x,y,z=hit+normal*.0025;break
            verts.extend([(x-.003,y-.001,z),(x+.003,y-.001,z)])
        for i in range(len(path)-1):faces.append(tuple(start+v for v in (i*2,i*2+1,i*2+3,i*2+2)))
    data=bpy.data.meshes.new('shared helmet padding and chin straps');data.from_pydata(verts,[],faces);data.update()
    ob=bpy.data.objects.new(data.name,data);bpy.context.scene.collection.objects.link(ob)
    data.materials.append(next(m for m in mesh.data.materials if m.name=='commander deerskin and cloth'))
    uv=data.uv_layers.new(name=mesh.data.uv_layers.active.name)
    for p in data.polygons:
        p.use_smooth=True
        for li,(u,v) in zip(p.loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=(u,v)
    ob.vertex_groups.new(name='body.head').add(list(range(len(verts))),1,'REPLACE')
    return ob


def run(kind):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/optimized/commanders'/f'{kind}-detail.blend'))
    scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE')
    mesh=next(o for o in scene.objects if o.type=='MESH' and o.parent==rig)
    removed=remove_old_face(mesh)
    with bpy.data.libraries.load(str(STAGE/'shared-head.blend'),link=False) as (src,dst):
        dst.objects=['shared human head']
    head=dst.objects[0];scene.collection.objects.link(head)
    complexion(head,kind);fitting=fit(head,rig,kind)
    head.data.uv_layers.active.name=mesh.data.uv_layers.active.name
    straps=attachments(mesh,head)
    for ob in [head,straps]:
        for attr in mesh.data.color_attributes:
            a=ob.data.color_attributes.new(name=attr.name,type=attr.data_type,domain=attr.domain)
            for c in a.data:c.color=(1,1,1,1)
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);head.select_set(True);straps.select_set(True)
    bpy.context.view_layer.objects.active=mesh;bpy.ops.object.join()
    mesh.data.calc_loop_triangles()
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.file.pack_all()
    mesh['head_source']='Microsoft Rocketbox Male Adult 10 / MIT'
    mesh['head_modifications']='Extracted head; fitted neck weights; mature complexion; variant jaw/cheeks'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/optimized/commanders'/f'{kind}-face.blend'),compress=True)
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=mesh
    target=OUT/f'{kind}.glb'
    bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_yup=True,
        export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,
        export_vertex_color='ACTIVE',export_all_vertex_colors=False,export_extras=True)
    images=share_images(target)
    report={'triangles':len(mesh.data.loop_triangles),'bones':len(rig.data.bones),'materials':len(mesh.data.materials),
            'bytes':target.stat().st_size,'textures':images,'source_sha256':SOURCE_SHA,'removed_components':removed,
            'head':fitting,'source_license':'MIT','version':'human-head-v17'}
    (STAGE/f'{kind}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(kind,report['triangles'],report['bytes'],flush=True)


if __name__=='__main__':
    source_head()
    for name in ['yukimura','ieyasu']:run(name)
