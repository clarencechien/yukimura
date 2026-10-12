"""Editable high-poly hero and real Cycles selected-to-active texture baking.

The high mesh never ships to the browser. Exploded matching parts prevent a ray
from picking up a neighbouring plate, finger or the opposite side of a cape.
"""
import bpy
import math
import time
import numpy as np
from mathutils import Vector

SIZE = 2048

def activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True);bpy.context.view_layer.objects.active=obj

def sculpt(obj, name, role):
    """Dense forged edges, engraved borders and secondary gathered cloth folds."""
    activate(obj)
    broad=name.startswith(('cuirass.hero.','menpo.hero.','kabuto.hero.dome','cape.hero.drape','thigh.hero.hakama'))
    tiny=any(word in name for word in ('lace','rivet','cord','binding','braid','coin'))
    sub=obj.modifiers.new('sculpt support grid','SUBSURF')
    sub.subdivision_type='SIMPLE';sub.levels=1 if tiny else 3 if broad else 2
    bpy.ops.object.modifier_apply(modifier=sub.name)
    # Round physical plate edges. This is evaluated geometry, not a render-only
    # bevel shader; the baked tangent normals contain the changed surface.
    if role in ('armor','gold','steel') and not tiny:
        bevel=obj.modifiers.new('forged edge radius','BEVEL')
        bevel.width=.0018 if role=='armor' else .0008;bevel.segments=3;bevel.angle_limit=.5
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    obj.data.update()
    uv=obj.data.uv_layers.active
    coords=np.zeros((len(obj.data.vertices),2));counts=np.zeros(len(coords))
    for loop in obj.data.loops:
        coords[loop.vertex_index]+=uv.data[loop.index].uv;counts[loop.vertex_index]+=1
    coords/=np.maximum(counts[:,None],1)
    ornament=obj.data.attributes.new('Engraving','FLOAT','POINT')
    rest=obj.data.attributes.new('RestPosition','FLOAT_VECTOR','POINT')
    # Capture normals before changing positions. Reading v.normal after each
    # mutation invalidates/recomputes the entire dense mesh (quadratic work).
    normals=[v.normal.normalized() for v in obj.data.vertices]
    max_delta=0
    decorated=name.startswith(('cuirass.hero.','sode.hero.','forearm.hero.')) and role=='armor' and not tiny
    fabric=name.startswith(('cape.hero.drape','thigh.hero.hakama','upper_arm.hero'))
    for i,v in enumerate(obj.data.vertices):
        p=v.co.copy();u,w=(coords[i]*4)%1
        border=math.exp(-((u-.075)/.016)**2)+math.exp(-((u-.925)/.016)**2)
        band=math.exp(-((w-.15)/.018)**2)+math.exp(-((w-.85)/.018)**2)
        # Restrained wave engraving inset from the edge, leaving large red planes.
        wave=math.exp(-((w-(.24+.027*math.sin(u*math.tau*5)))/.012)**2)
        mark=min(1,(border*.7+band*.65+wave*.55)) if decorated else 0
        delta=0
        if role=='armor':
            delta=.00028*math.sin(p.x*391+p.z*123)*math.sin(p.y*317-p.z*173)
            delta+=.0016*mark
            if name.startswith('menpo.hero.base'):
                # Cheek/chin tension creases, deliberately symmetric at the mouth.
                delta+=.0028*math.exp(-((abs(p.x)-.057)/.018)**2)*math.sin(p.z*92)
        elif fabric:
            edge=math.sin(math.pi*min(1,max(0,u)))**2
            delta=.0032*edge*math.sin(u*math.tau*13+w*7)*(.35+.65*math.sin(w*math.pi)**2)
        elif role=='horn':delta=.0009*math.sin(p.z*207+p.x*31)
        elif role=='gold':delta=.00025*math.sin(u*73+w*41)
        v.co+=normals[i]*delta;max_delta=max(max_delta,abs(delta))
        rest.data[i].vector=p;ornament.data[i].value=mark
    for p in obj.data.polygons:p.use_smooth=True
    obj.data.update()
    obj['sculpted_relief_max_m']=max_delta
    return max_delta

def high_material(role,color):
    mat=bpy.data.materials.new('high/'+role);mat.use_nodes=True;mat.diffuse_color=color
    ns=mat.node_tree.nodes;ls=mat.node_tree.links;bs=ns.get('Principled BSDF')
    def node(kind):return ns.new(kind)
    rest=node('ShaderNodeAttribute');rest.attribute_name='RestPosition'
    noise=node('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=19;noise.inputs['Detail'].default_value=3
    ls.new(rest.outputs['Vector'],noise.inputs['Vector'])
    ramp=node('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[1].position=.84
    ramp.color_ramp.elements[0].color=(*(c*.62 for c in color[:3]),1)
    ramp.color_ramp.elements[1].color=(*(min(1,c*1.24) for c in color[:3]),1)
    ls.new(noise.outputs['Fac'],ramp.inputs[0])
    mark=node('ShaderNodeAttribute');mark.attribute_name='Engraving'
    mix=node('ShaderNodeMixRGB');mix.inputs[2].default_value=(.30,.18,.054,1)
    ls.new(mark.outputs['Fac'],mix.inputs[0]);ls.new(ramp.outputs['Color'],mix.inputs[1]);ls.new(mix.outputs[0],bs.inputs['Base Color'])
    # Fine weave and hammered lacquer become normal-map detail during baking.
    fine=node('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=440 if role in ('cloth','cape','lace') else 260
    fine.inputs['Detail'].default_value=2;ls.new(rest.outputs['Vector'],fine.inputs['Vector'])
    bump=node('ShaderNodeBump');bump.inputs['Strength'].default_value=.24
    bump.inputs['Distance'].default_value=.001 if role in ('cloth','cape','lace') else .00045
    ls.new(fine.outputs['Fac'],bump.inputs['Height']);ls.new(bump.outputs['Normal'],bs.inputs['Normal'])
    rough={'armor':.48,'gold':.43,'steel':.28,'cloth':.92,'cape':.91}.get(role,.78)
    multiply=node('ShaderNodeMath');multiply.operation='MULTIPLY_ADD';multiply.inputs[1].default_value=.16;multiply.inputs[2].default_value=rough-.08
    ls.new(noise.outputs['Fac'],multiply.inputs[0]);ls.new(multiply.outputs[0],bs.inputs['Roughness'])
    metal={'armor':.10,'gold':.52,'steel':.88}.get(role,0);bs.inputs['Metallic'].default_value=metal
    packed=node('ShaderNodeCombineColor');packed.name='BAKE_SURFACE';packed.inputs[0].default_value=1;packed.inputs[2].default_value=metal
    ls.new(multiply.outputs[0],packed.inputs[1])
    emission=node('ShaderNodeEmission');emission.name='BAKE_EMIT';ls.new(packed.outputs[0],emission.inputs[0])
    return mat

def bake_hero(low,parts,colors,output):
    started=time.time();scene=bpy.context.scene
    print('HIGH MASTER: sculpting',len(parts),'parts',flush=True)
    collection=bpy.data.collections.new('20_YUKIMURA_HIGH — sculpt master / not exported')
    scene.collection.children.link(collection)
    materials={role:high_material(role,color) for role,color in colors.items()}
    offsets=[Vector(((i%24)*4,(i//24)*4,0)) for i in range(len(parts))]
    high_parts=[];max_relief=0
    for i,part in enumerate(parts):
        if i%100==0:print('HIGH MASTER part',i,flush=True)
        obj=part.copy();obj.data=part.data.copy();obj.parent=None;obj.name='HIGH/'+part['part_name'];collection.objects.link(obj)
        obj.data.materials.clear();obj.data.materials.append(materials[part['palette_role']]);obj.material_slots[0].link='DATA'
        max_relief=max(max_relief,sculpt(obj,part['part_name'],part['palette_role']))
        obj['bake_part']=i
        # Retain each sculpted mesh as a separately editable master.
        high_parts.append(obj)
    # Unique, non-overlapping UVs belong to the game mesh only.
    activate(low)
    for layer in list(low.data.uv_layers):low.data.uv_layers.remove(layer)
    low.data.uv_layers.new(name='HeroBake')
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.0025,area_weight=.5,correct_aspect=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    # Copy masters into an exploded bake scene, preserving the clean source.
    bpy.ops.object.select_all(action='DESELECT');bake_parts=[]
    for i,source in enumerate(high_parts):
        obj=source.copy();obj.data=source.data.copy();scene.collection.objects.link(obj)
        obj.location=offsets[i];obj.select_set(True);bake_parts.append(obj)
    bpy.context.view_layer.objects.active=bake_parts[0];bpy.ops.object.join();high=bpy.context.object;high.name='HIGH_BAKE'
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    high.data.calc_loop_triangles();high_triangles=len(high.data.loop_triangles)
    for source in high_parts:source.hide_render=True;source.hide_set(True)
    # Hide all unrelated assemblies so they cannot occlude the bake.
    old_render={obj:obj.hide_render for obj in scene.objects}
    for obj in scene.objects:obj.hide_render=obj not in (low,high)
    ids=low.data.attributes['BakePart']
    for i,v in enumerate(low.data.vertices):v.co+=offsets[ids.data[i].value]
    low.data.update()
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.bake.use_selected_to_active=True;scene.render.bake.use_cage=False
    scene.render.bake.cage_extrusion=.022;scene.render.bake.max_ray_distance=.045
    scene.render.bake.margin=8;scene.render.bake.margin_type='EXTEND'
    target=bpy.data.materials.new('hero bake target');target.use_nodes=True
    low.data.materials.clear();low.data.materials.append(target)
    target_node=target.node_tree.nodes.new('ShaderNodeTexImage');target.node_tree.nodes.active=target_node
    images={}
    for label,kind,space in [('pigment','DIFFUSE','sRGB'),('normal','NORMAL','Non-Color'),('surface','EMIT','Non-Color'),('ao','AO','Non-Color')]:
        image=bpy.data.images.new('hero_baked_'+label,SIZE,SIZE,alpha=False);image.colorspace_settings.name=space
        image.generated_color=(.5,.5,1,1) if kind=='NORMAL' else (0,0,0,1)
        target_node.image=image
        if kind=='EMIT':
            for m in materials.values():m.node_tree.links.new(m.node_tree.nodes['BAKE_EMIT'].outputs[0],m.node_tree.nodes.get('Material Output').inputs['Surface'])
        if kind=='AO':
            for m in materials.values():m.node_tree.links.new(m.node_tree.nodes.get('Principled BSDF').outputs[0],m.node_tree.nodes.get('Material Output').inputs['Surface'])
        activate(low);high.select_set(True)
        print('HIGH BAKE',label,'triangles',high_triangles,flush=True)
        bpy.ops.object.bake(type=kind,pass_filter={'COLOR'} if kind=='DIFFUSE' else set())
        images[label]=image
    # Multiply local baked occlusion into albedo; assembly AO stays in vertex color.
    pigment=np.empty(SIZE*SIZE*4,dtype=np.float32);images['pigment'].pixels.foreach_get(pigment)
    ao=np.empty_like(pigment);images['ao'].pixels.foreach_get(ao)
    pigment= pigment.reshape(-1,4);ao=ao.reshape(-1,4)
    pigment[:,:3]*=(.7+.3*ao[:,:1]);images['pigment'].pixels.foreach_set(pigment.ravel())
    surface=np.empty(SIZE*SIZE*4,dtype=np.float32);images['surface'].pixels.foreach_get(surface);surface=surface.reshape(-1,4)
    surface[:,0]=ao[:,0];images['surface'].pixels.foreach_set(surface.ravel())
    for label in ('pigment','normal','surface'):images[label].pack()
    bpy.data.images.remove(images['ao'])
    for i,v in enumerate(low.data.vertices):v.co-=offsets[ids.data[i].value]
    low.data.attributes.remove(ids);low.data.update()
    for obj,hidden in old_render.items():
        if obj!=high:obj.hide_render=hidden
    bpy.data.objects.remove(high,do_unlink=True)
    for source in high_parts:source.hide_render=True;source.hide_set(True)
    activate(low)
    # Atlas now contains the actual palette; preserve only assembly occlusion in
    # the vertex multiplier, avoiding a second red tint on the already red bake.
    attr=low.data.color_attributes['Color'];occlusion=low.data.attributes['HeroOcclusion']
    for loop in low.data.loops:
        value=occlusion.data[loop.vertex_index].value;attr.data[loop.index].color=(value,value,value,1)
    low.data.attributes.remove(occlusion)
    mat=bpy.data.materials.new('runtime/hero high bake');mat.use_nodes=True;mat.use_backface_culling=False
    ns=mat.node_tree.nodes;ls=mat.node_tree.links;bs=ns.get('Principled BSDF')
    tex=ns.new('ShaderNodeTexImage');tex.image=images['pigment']
    vc=ns.new('ShaderNodeVertexColor');vc.layer_name='Color'
    mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
    ls.new(vc.outputs['Color'],mix.inputs[1]);ls.new(tex.outputs[0],mix.inputs[2]);ls.new(mix.outputs[0],bs.inputs['Base Color'])
    tex=ns.new('ShaderNodeTexImage');tex.image=images['normal'];normal=ns.new('ShaderNodeNormalMap')
    ls.new(tex.outputs[0],normal.inputs['Color']);ls.new(normal.outputs[0],bs.inputs['Normal'])
    tex=ns.new('ShaderNodeTexImage');tex.image=images['surface'];separate=ns.new('ShaderNodeSeparateColor')
    ls.new(tex.outputs[0],separate.inputs[0]);ls.new(separate.outputs['Green'],bs.inputs['Roughness']);ls.new(separate.outputs['Blue'],bs.inputs['Metallic'])
    low.data.materials.clear();low.data.materials.append(mat)
    low.data.calc_loop_triangles()
    report={'method':'Cycles selected-to-active / exploded matching parts','high_triangles':high_triangles,'high_parts':len(high_parts),'low_triangles':len(low.data.loop_triangles),'resolution':SIZE,'samples':16,'cpu_threads':2,'max_sculpt_relief_m':max_relief,'bake_seconds':round(time.time()-started,1),'passes':['diffuse_color','tangent_normal','roughness_metallic','ambient_occlusion'],'paid_api_calls':0}
    import json
    (output/'hero-bake.json').write_text(json.dumps(report,indent=2)+'\n')
    collection['README']='Editable sculpt masters. Unhide to inspect; rest pose at origin. Excluded from runtime GLB. HeroBake UV and Cycles maps live on yukimura_runtime.'
    print('HIGH BAKE COMPLETE',json.dumps(report),flush=True)
    return report
