"""Read the pinned CC0 MakeHuman mesh/rig/weights as one continuous body.

No addon code is loaded. Joint positions come from the matching OBJ helpers,
not the JSON's example morph. This module keeps the complete authoring rig.
"""
from pathlib import Path
import collections, hashlib, json
import bpy
from mathutils import Matrix, Vector
ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'assets/vendor/mpfb'

class Body:
    def __init__(self):
        provenance=json.loads((SOURCE/'provenance.json').read_text())
        for f in provenance['files']:
            assert hashlib.sha256((SOURCE/f['file']).read_bytes()).hexdigest()==f['sha256'],f['file']
        self.vertices=[];self.uv=[];self.faces=[];self.groups=collections.defaultdict(set)
        group=''
        for line in (SOURCE/'base.obj').read_text().splitlines():
            p=line.split()
            if not p:continue
            if p[0]=='v':self.vertices.append(Vector((float(p[1])*.1,-float(p[3])*.1,float(p[2])*.1)))
            elif p[0]=='vt':self.uv.append(tuple(map(float,p[1:3])))
            elif p[0]=='g':group=p[1]
            elif p[0]=='f':
                ids=[int(s.split('/')[0])-1 for s in p[1:]];self.groups[group].update(ids)
                if group=='body':self.faces.append((ids,[int(s.split('/')[1])-1 for s in p[1:]]))
        self.definition=json.loads((SOURCE/'rig.default.json').read_text())
        self.weights=json.loads((SOURCE/'weights.default.json').read_text())['weights']
        self.influences=collections.defaultdict(list)
        for name,weights in self.weights.items():
            for i,w in weights:
                if w>1e-6:self.influences[i].append((name,w))
        # glTF/mobile skinning uses four influences. Normalize the strongest four.
        self.original_influences={i:list(w) for i,w in self.influences.items()}
        for i,weights in self.influences.items():
            best=sorted(weights,key=lambda a:-a[1])[:4];total=sum(w for n,w in best)
            self.influences[i]=[(n,w/total) for n,w in best]
        self.heads={n:self.joint(d['head']) for n,d in self.definition.items()}
        self.tails={n:self.joint(d['tail']) for n,d in self.definition.items()}
    def joint(self,d):
        if d['strategy']=='CUBE':ids=self.groups[d['cube_name']]
        elif d['strategy']=='VERTEX':ids=[d['vertex_index']]
        elif d['strategy']=='MEAN':ids=d['vertex_indices']
        else:raise ValueError(d)
        return sum((self.vertices[i] for i in ids),Vector())/len(ids)
    def armature(self,name='MPFB full body — 163 CC0 bones'):
        bpy.ops.object.select_all(action='DESELECT')
        data=bpy.data.armatures.new(name);rig=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(rig)
        bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
        for n,d in self.definition.items():
            b=data.edit_bones.new(n);b.head=self.heads[n];b.tail=self.tails[n];b.roll=d['roll']
        for n,d in self.definition.items():
            if d['parent']:data.edit_bones[n].parent=data.edit_bones[d['parent']]
        bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
        return rig
    def mesh(self,rig,name='continuous CC0 body',positions=None,faces=None,prefix=''):
        faces=self.faces if faces is None else faces;ids=sorted({i for f,u in faces for i in f});remap={i:k for k,i in enumerate(ids)}
        mesh=bpy.data.meshes.new(name);mesh.from_pydata([positions[i] if positions else self.vertices[i] for i in ids],[],[[remap[i] for i in f] for f,u in faces]);mesh.update()
        obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
        uv=mesh.uv_layers.new(name='UVMap')
        for poly,(_,uvi) in zip(mesh.polygons,faces):
            poly.use_smooth=True
            for li,ui in zip(poly.loop_indices,uvi):uv.data[li].uv=self.uv[ui]
        for n in self.definition:obj.vertex_groups.new(name=prefix+n)
        for old,new in remap.items():
            for n,w in self.influences[old]:obj.vertex_groups[prefix+n].add([new],w,'REPLACE')
        mod=obj.modifiers.new('continuous anatomical skin','ARMATURE');mod.object=rig
        # Linear skinning here matches glTF/Babylon; do not validate only Blender DQS.
        obj.parent=rig
        return obj,ids

def material(name,color,roughness=.8,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=roughness;p.inputs['Metallic'].default_value=metal
    return m

def extract_hand_study():
    """Read the approved open/grip finger transforms and original fitted armor."""
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/cinema/open-hand-study.blend'))
    rig=bpy.data.objects['Open hand rig'];bpy.context.scene.frame_set(24);bpy.context.view_layer.update()
    deltas={b.name:(rig.pose.bones[b.name].matrix@b.matrix_local.inverted()).copy() for b in rig.data.bones}
    armor=[];deps=bpy.context.evaluated_depsgraph_get()
    for o in bpy.data.objects:
        if not (o.name.startswith('perforated red shino splint') or o.name=='fitted crimson tekko'):continue
        e=o.evaluated_get(deps);m=e.to_mesh();armor.append((o.name,[o.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons]));e.to_mesh_clear()
    return deltas,armor
