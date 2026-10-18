"""Render rigid illustrated pieces driven by fixed-length planar shoulder/elbow IK.

--preview renders four neutral stills before the full sequence is approved by eye.
No vertex deformation, nonuniform scaling, per-frame generation or old 3D model.
"""
import sys,math,json,time,hashlib
from pathlib import Path
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from yari_rigid_pose import pose
SOURCE=ROOT/'assets/source/jigoku-2d/yari-rigid'
OUT=ROOT/'docs/routes/jigoku-2d/yari-rigid';OUT.mkdir(exist_ok=True)
TMP=ROOT/'.tmp/yari-rigid';TMP.mkdir(exist_ok=True)
config=json.loads((SOURCE/'rig.json').read_text())
layers=json.loads((SOURCE/'layers.json').read_text())['layers']
preview='--preview' in sys.argv
W,H=config['canvas'];SCALE=512
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
objects={};textures={};images={};pivots={}
order=['rear_foot','front_foot','rear_shin','front_shin','rear_thigh','front_thigh','pelvis','rear_upper','front_upper','rear_forearm','front_forearm','torso','weapon','rear_hand','front_hand']
for name in order:
    pivot=config['hip'] if name in ['torso','pelvis'] else [0,0]
    for side,arm in config['arms'].items():
        if name==side+'_upper':pivot=arm['shoulder']
        if name==side+'_forearm':pivot=arm['elbow']
        if name==side+'_hand':pivot=arm['wrist']
    for side,leg in config['legs'].items():
        for part,joint in [('thigh','hip'),('shin','knee'),('foot','toe')]:
            if name==side+'_'+part:pivot=leg[joint]
    pivots[name]=np.array(pivot,float)
    x0,y0,x1,y1=layers[name]['box']
    verts=[((x-pivot[0])/SCALE,-(y-pivot[1])/SCALE,0) for x,y in [(x0,y1),(x1,y1),(x1,y0),(x0,y0)]]
    mesh=bpy.data.meshes.new(name+' rigid quad');mesh.from_pydata(verts,[],[(0,1,2,3)]);mesh.update()
    uv=mesh.uv_layers.new()
    for i,xy in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[i].uv=xy
    ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob);objects[name]=ob
    mat=bpy.data.materials.new(name+' baked illustration');mat.use_nodes=True
    n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputMaterial');tex=n.new('ShaderNodeTexImage');textures[name]=tex
    em=n.new('ShaderNodeEmission');tr=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
    l.new(tex.outputs['Color'],em.inputs['Color']);l.new(tex.outputs['Alpha'],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0]);mesh.materials.append(mat)
    images[name]={}
    for light,file in layers[name]['files'].items():
        im=bpy.data.images.load(str(SOURCE/'layers'/file));im.alpha_mode='STRAIGHT';im.pack();images[name][light]=im
    tex.image=images[name]['neutral']
report={'method':'Fifteen rigid cutouts; fixed-length arm and leg IK; pelvis drive leads hands; rear toe pivot; constant scale.',
 'fps':30,'frames_per_clip':36,'duration_ms':1200,'clips':{'thrust':[1,36],'idle':[37,72]},'device':'CPU','blender':bpy.app.version_string,
 'source':'assets/source/jigoku-2d/yari-rigid/body-clean.png','source_sha256':hashlib.sha256((SOURCE/'body-clean.png').read_bytes()).hexdigest(),
 'rig_config_sha256':hashlib.sha256((SOURCE/'rig.json').read_bytes()).hexdigest(),'frames':[],
 'limitations':['Planar cutout rig, not a 3D anatomical or dynamics simulation.','Projected joints are manually placed. Authored pelvis shift and heel lift, not force/center-of-mass simulation or footstep.','Clean torso/waist generated once; other cutouts reuse the original illustration.','Lighting baked before animation; rigid rotations do not recalculate material highlights.','Only a small planted-foot thrust; larger movements need additional views and occlusion art.']}
for frame in range(1,73):
    transforms,measures,joints=pose(frame,config)
    for name,ob in objects.items():
        point,angle=transforms[name]
        ob.location=((point[0]-W/2)/SCALE,(H/2-point[1])/SCALE,order.index(name)*.008)
        ob.rotation_euler=(0,0,-angle);ob.scale=(1,1,1)
        ob.keyframe_insert('location',frame=frame);ob.keyframe_insert('rotation_euler',frame=frame)
    # Endpoints computed from the ACTUAL object matrices, independent of IK report.
    bpy.context.view_layer.update()
    from mathutils import Vector
    def mapped(name,p):
        q=(np.array(p)-pivots[name])/SCALE
        v=objects[name].matrix_world@Vector((q[0],-q[1],0))
        return np.array([v.x*SCALE+W/2,H/2-v.y*SCALE])
    seam=[];grip=[];rigid=[]
    for side,arm in config['arms'].items():
        seam.extend([np.linalg.norm(mapped('torso',arm['shoulder'])-mapped(side+'_upper',arm['shoulder'])),np.linalg.norm(mapped(side+'_upper',arm['elbow'])-mapped(side+'_forearm',arm['elbow'])),np.linalg.norm(mapped(side+'_forearm',arm['wrist'])-mapped(side+'_hand',arm['wrist']))])
        grip.append(float(np.linalg.norm(mapped(side+'_hand',arm['grip'])-mapped('weapon',arm['grip']))))
    for side,leg in config['legs'].items():
        seam.extend([np.linalg.norm(mapped('pelvis',leg['hip'])-mapped(side+'_thigh',leg['hip'])),np.linalg.norm(mapped(side+'_thigh',leg['knee'])-mapped(side+'_shin',leg['knee'])),np.linalg.norm(mapped(side+'_shin',leg['ankle'])-mapped(side+'_foot',leg['ankle']))])
    for ob in objects.values():
        rigid.append(float(np.max(abs(np.array(ob.matrix_world.to_3x3().transposed()@ob.matrix_world.to_3x3())-np.eye(3)))))
    assert max(seam)<.001 and max(grip)<.001 and max(rigid)<1e-5
    report['frames'].append({'frame':frame,'arms':measures,'joints':joints,'max_joint_gap_source_px':float(max(seam)),'max_grip_error_source_px':max(grip),'max_rigid_matrix_error':max(rigid)})
for ob in objects.values():
    for curve in ob.animation_data.action.fcurves:
        for key in curve.keyframe_points:key.interpolation='LINEAR'
for row in report['frames']:
    scene.frame_set(row['frame']);expected,_,_=pose(row['frame'],config)
    errors=[float(np.linalg.norm(mapped(name,pivots[name])-point)) for name,(point,_) in expected.items()]
    feet=[float(np.linalg.norm(mapped(side+'_foot',leg['toe'])-np.array(leg['toe']))) for side,leg in config['legs'].items()]
    feet.append(float(np.linalg.norm(mapped('front_foot',config['legs']['front']['ankle'])-np.array(config['legs']['front']['ankle']))))
    leg_errors=[]
    for side,leg in config['legs'].items():
        for part,a,b in [('thigh','hip','knee'),('shin','knee','ankle')]:
            leg_errors.append(abs(float(np.linalg.norm(mapped(side+'_'+part,leg[b])-mapped(side+'_'+part,leg[a]))-np.linalg.norm(np.array(leg[b])-np.array(leg[a])))))
    assert max(leg_errors)<.001
    row['max_leg_length_error_source_px']=max(leg_errors)
    row['pelvis_offset_source_px']=(expected['pelvis'][0]-np.array(config['hip'])).tolist()
    row['rear_heel_lift_source_px']=float(config['legs']['rear']['ankle'][1]-mapped('rear_foot',config['legs']['rear']['ankle'])[1])
    assert max(errors)<.001 and max(feet)<.001
    row['evaluated_transform_error_source_px']=max(errors);row['foot_anchor_drift_source_px']=max(feet)
camdata=bpy.data.cameras.new('Fixed illustrated view');camdata.type='ORTHO';camdata.ortho_scale=4;camdata.sensor_fit='HORIZONTAL'
camera=bpy.data.objects.new('Fixed illustrated view',camdata);scene.collection.objects.link(camera);camera.location=(0,0,6);scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.cycles.use_animated_seed=False;scene.cycles.seed=1615;scene.cycles.adaptive_threshold=0;scene.cycles.transparent_max_bounces=16;scene.cycles.max_bounces=2
scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.frame_start=1;scene.frame_end=72;scene.render.fps=30
for label,frame in [('guard',1),('windup',11),('contact',15),('recover',27),('idle',37)]:scene.timeline_markers.new(label,frame=frame)
start=time.perf_counter()
for light in (['neutral'] if preview else ['neutral','warm-left','cool-right']):
    for name,tex in textures.items():tex.image=images[name][light]
    if not preview:
        for suffix,size in [('',(512,320)),('-hd',(1024,640))]:
            folder=TMP/(light+suffix);folder.mkdir(exist_ok=True)
            scene.render.resolution_x,scene.render.resolution_y=size
            for frame in range(1,73):
                scene.frame_set(frame);scene.render.filepath=str(folder/f'{frame:03}.png');bpy.ops.render.render(write_still=True)
    scene.render.resolution_x=2048;scene.render.resolution_y=1280
    for frame in [1,11,15,27]:
        scene.frame_set(frame);scene.render.filepath=str(OUT/f'{light}-{frame:02}.png');bpy.ops.render.render(write_still=True)
scene.frame_set(15)
text=bpy.data.texts.new('README - rigid illustration rig');text.write('30 fps; frames 1-36 short thrust, 37-72 idle. Fifteen alpha cutouts including pelvis, thighs, shins and feet. Objects are keyed with rigid transforms from fixed-length projected two-link IK. No mesh warping, stretch, scale or full 3D dynamics. Rebuild with tools/render_yari_rigid.py. Three lighting plates per part packed. Coordinates, masks, wrist limits and movement envelope: assets/source/jigoku-2d/yari-rigid/rig.json.\n')
target=ROOT/'assets/optimized/jigoku-2d/yari-rigid-motion.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
report['scene']=str(target.relative_to(ROOT));report['scene_sha256']=hashlib.sha256(target.read_bytes()).hexdigest();report['render_seconds']=round(time.perf_counter()-start,3);report['preview_only']=preview
(OUT/'motion-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('RIGID_DONE',report['render_seconds'],flush=True)
