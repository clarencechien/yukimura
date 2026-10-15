"""Actual Blender light passes over a hand-authored shallow image-space relief.

Preserves the same illustration/UV/camera for every variant. No v22 character,
no colour-to-depth heuristic, no per-variant generation. This ADDS constrained
lighting to existing painted illumination; it is not intrinsic decomposition.

blender -b -t 4 --python-exit-code 1 --python tools/render_illustration_relight.py
"""
import bpy, json, math, time, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/source/jigoku-2d/yukimura-illustration-cutout.png'
CONFIG=ROOT/'assets/source/jigoku-2d/relight-surfaces.json'
OUT=ROOT/'docs/routes/jigoku-2d/relight';OUT.mkdir(parents=True,exist_ok=True)
TMP=ROOT/'.tmp/jigoku-relight';TMP.mkdir(parents=True,exist_ok=True)
config=json.loads(CONFIG.read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
source=bpy.data.images.load(str(SOURCE));source.name='Source illustration - all light variants share these pixels';source.alpha_mode='STRAIGHT';source.pack()
w,h=source.size;world_w=config['canvas_world_width'];world_h=world_w*h/w
nx=config['grid_columns'];ny=round(nx*h/w)
vertices=[];faces=[]
for j in range(ny+1):
    v=j/ny
    for i in range(nx+1):
        u=i/nx;z=0
        for s in config['surfaces']:
            q=((u-s['center'][0])/s['radius'][0])**2+((v-s['center'][1])/s['radius'][1])**2
            if q<6:z+=s['height']*math.exp(-2.5*q)
        vertices.append(((u-.5)*world_w,(.5-v)*world_h,z))
for j in range(ny):
    for i in range(nx):
        a=j*(nx+1)+i;faces.append((a,a+nx+1,a+nx+2,a+1))
mesh=bpy.data.meshes.new('image-aligned shallow relief');mesh.from_pydata(vertices,[],faces);mesh.update()
uv=mesh.uv_layers.new(name='Original illustration UV')
for p in mesh.polygons:
    p.use_smooth=True
    for li in p.loop_indices:
        co=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(co.x/world_w+.5,co.y/world_h+.5)
obj=bpy.data.objects.new('Lighting proxy - not a complete character model',mesh);scene.collection.objects.link(obj)
material=bpy.data.materials.new('White diffuse proxy masked by source alpha');material.use_nodes=True
n=material.node_tree.nodes;l=material.node_tree.links;n.clear()
out=n.new('ShaderNodeOutputMaterial');diff=n.new('ShaderNodeBsdfDiffuse');diff.inputs['Color'].default_value=(.8,.8,.8,1);diff.inputs['Roughness'].default_value=.2
tex=n.new('ShaderNodeTexImage');tex.image=source;transparent=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
l.new(tex.outputs['Alpha'],mix.inputs[0]);l.new(transparent.outputs[0],mix.inputs[1]);l.new(diff.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0]);mesh.materials.append(material)
world=bpy.data.worlds.new('neutral low ambient');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.2;scene.world=world

def area(name,location,power,color,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=location;o.rotation_euler=(Vector((0,0,.05))-o.location).to_track_quat('-Z','Y').to_euler();return o
key=area('Neutral broad softbox',(0,1,4),210,(1,1,1),4)
warm=area('Left warm fire',(-1.8,.5,1.8),0,(1,.32,.075),1.9)
cool=area('Right cold spirit light',(1.8,.5,1.8),0,(.10,.48,1),1.9)
cam_data=bpy.data.cameras.new('locked front camera');cam_data.type='ORTHO';cam_data.ortho_scale=world_w
cam=bpy.data.objects.new('locked front camera',cam_data);scene.collection.objects.link(cam);cam.location=(0,0,6);cam.rotation_euler=(0,0,0);scene.camera=cam
# Blender's orthographic scale is the horizontal span for this setup.
# Explicit sensor fit avoids a portrait/aspect-dependent UV crop.
cam.data.sensor_fit='HORIZONTAL'
scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=64;scene.cycles.use_denoising=False;scene.cycles.seed=1615;scene.cycles.use_animated_seed=False;scene.cycles.adaptive_threshold=0
scene.cycles.max_bounces=3;scene.cycles.transparent_max_bounces=4
scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.film_transparent=True
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='32';scene.render.image_settings.exr_codec='ZIP'
scene.use_nodes=False
neutral_path=TMP/'neutral-reference.exr';scene.render.filepath=str(neutral_path)
started=time.perf_counter();bpy.ops.render.render(write_still=True);reference_seconds=time.perf_counter()-started
reference=bpy.data.images.load(str(neutral_path));reference.name='Neutral diffuse reference (linear)';reference.pack()
# Export a diagnostic of the actual light-catching proxy, clearly separate from art.
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_depth='8';scene.render.filepath=str(OUT/'surface-proxy.png');bpy.ops.render.render(write_still=True)
scene.use_nodes=True;n=scene.node_tree.nodes;l=scene.node_tree.links;n.clear()
render=n.new('CompositorNodeRLayers');render.label='Actual Blender light response'
neutral=n.new('CompositorNodeImage');neutral.image=reference;neutral.label='Fixed neutral response'
original=n.new('CompositorNodeImage');original.image=source;original.label='Same original illustration, never re-generated per variant'
sep_lit=n.new('CompositorNodeSepRGBA');sep_ref=n.new('CompositorNodeSepRGBA');sep_base=n.new('CompositorNodeSepRGBA');combine=n.new('CompositorNodeCombRGBA')
l.new(render.outputs['Image'],sep_lit.inputs[0]);l.new(neutral.outputs['Image'],sep_ref.inputs[0]);l.new(original.outputs['Image'],sep_base.inputs[0]);l.new(sep_base.outputs['A'],combine.inputs['A'])
def mathnode(operation,a,b):
    node=n.new('CompositorNodeMath');node.operation=operation
    for i,v in enumerate((a,b)):
        if isinstance(v,(float,int)):node.inputs[i].default_value=v
        else:l.new(v,node.inputs[i])
    return node.outputs[0]
# bounded gain in LINEAR colour; approximate, not a recovered BRDF/albedo.
for channel in 'RGB':
    ratio=mathnode('DIVIDE',sep_lit.outputs[channel],mathnode('MAXIMUM',sep_ref.outputs[channel],.00001))
    gain=mathnode('ADD',mathnode('MULTIPLY',mathnode('SUBTRACT',ratio,1),.72),1)
    gain=mathnode('MINIMUM',mathnode('MAXIMUM',gain,.72),2.15)
    color=mathnode('MULTIPLY',sep_base.outputs[channel],gain);l.new(color,combine.inputs[channel])
comp=n.new('CompositorNodeComposite');l.new(combine.outputs[0],comp.inputs[0])
# Presets are stored as constant keyframes for an editable light study.
presets=[('neutral',1,210,0,0),('warm-left',2,170,180,0),('cool-right',3,170,0,180)]
for name,frame,keypower,warmpower,coolpower in presets:
    for lamp,power in [(key,keypower),(warm,warmpower),(cool,coolpower)]:
        lamp.data.energy=power;lamp.data.keyframe_insert('energy',frame=frame)
    marker=scene.timeline_markers.new(name,frame=frame)
for lamp in (key,warm,cool):
    for fc in lamp.data.animation_data.action.fcurves:
        for point in fc.keyframe_points:point.interpolation='CONSTANT'
scene.frame_start=1;scene.frame_end=3
report={'date':'2026-10-15','timezone':'Asia/Taipei','method':'fixed illustration multiplied by bounded linear RGB gain from Blender diffuse-light passes on a manually authored image-aligned relief','source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'surface_config':str(CONFIG.relative_to(ROOT)),'surface_config_sha256':hashlib.sha256(CONFIG.read_bytes()).hexdigest(),'source_dimensions':[w,h],'source_cleanup':'image_gen derived transparent cutout from original reference sheet; not pixel-identical extraction','engine':'Cycles','device':'CPU','blender':bpy.app.version_string,'samples':64,'threads':4,'denoising':False,'camera':{'type':'ORTHO','scale':world_w,'sensor_fit':'HORIZONTAL','locked':True},'proxy':{'vertices':len(vertices),'triangles':len(faces)*2,'maximum_relief':max(v[2] for v in vertices),'estimated_by_neural_model':False},'gain':{'strength':.72,'minimum':.72,'maximum':2.15,'color_space':'linear'},'reference_render_seconds':reference_seconds,'files':[],'limitations':['Original painted shadows and highlights remain.','Broad hand-authored surface directions, not recovered material or true depth.','Single fixed view; no new perspective or body animation.','No Marigold, IC-Light, Modal or GPU inference was used.']}
for name,frame,*_ in presets:
    scene.frame_set(frame);scene.render.filepath=str(OUT/(name+'.png'))
    started=time.perf_counter();print('ILLUSTRATION_RELIGHT',name,flush=True);bpy.ops.render.render(write_still=True)
    report['files'].append({'name':name,'file':name+'.png','frame':frame,'seconds':round(time.perf_counter()-started,3),'sha256':hashlib.sha256((OUT/(name+'.png')).read_bytes()).hexdigest()})
    (OUT/'render-report.json').write_text(json.dumps(report,indent=2)+'\n')
scene.frame_set(2);scene.render.filepath=str(OUT/'warm-left.png')
block=bpy.data.texts.new('README - illustration relight');block.write('Original illustration + manual shallow relief + bounded light gain. Frames 1/2/3: neutral/warm/cool. Do not rotate camera expecting a full body. Rebuild script recalculates the neutral reference if geometry changes. No v22 mesh is used.\n')
target=ROOT/'assets/optimized/jigoku-2d/illustration-relight.blend';target.parent.mkdir(parents=True,exist_ok=True);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
report['scene']=str(target.relative_to(ROOT));report['scene_sha256']=hashlib.sha256(target.read_bytes()).hexdigest();(OUT/'render-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('ILLUSTRATION_RELIGHT_DONE',flush=True)
