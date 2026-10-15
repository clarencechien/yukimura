"""Fixed-view illustration motion study. No per-frame generation or 3D body.

Run after the parameterized render_illustration_relight.py command documented
in YARI_MOTION.md. Cached Blender light plates are animated using identical UVs.
"""
import bpy, math, json, time, hashlib
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/routes/jigoku-2d/yari-motion'
TMP = ROOT / '.tmp/yari-motion'
TMP.mkdir(parents=True, exist_ok=True)
W, H = 1536, 1024
NX, NY = 256, 172
SCALE = 512  # source pixels per Blender world unit
FRAME_SIZE = (512, 320)
PRESETS = ['neutral', 'warm-left', 'cool-right']

def smooth(a, b, x):
    t = max(0., min(1., (x-a)/(b-a)))
    return t*t*(3-2*t)

def disk(x, y, cx, cy, inner, outer):
    return 1-smooth(inner, outer, math.hypot(x-cx, y-cy))

def weights(x, y):
    # The entire shaft, blade and both gripping hands share ONE translation.
    shaft = 1-smooth(29, 100, abs(y-(573-.147*x)))
    blade = smooth(1030, 1150, x)
    hands = max(disk(x,y,330,517,54,115), disk(x,y,858,456,53,114))
    weapon = max(shaft, blade, hands)
    torso = .55*(1-smooth(580, 850, y))
    attack = torso*(1-weapon)+weapon
    breathe = (1-smooth(540, 850, y))*(1-weapon)+weapon
    # Small delayed cloth motion, outside the grip/weapon and foot regions.
    cloth = disk(x,y,678,737,28,92)*(1-weapon)
    return attack, breathe, cloth, weapon

def displacement(x, y, kind):
    a,b,c,_ = weights(x,y)
    if kind == 'Thrust': return 100*a, -14.7*a
    if kind == 'Breath': return 0, -3*b
    return 10*c, 4*c

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
verts, faces = [], []
pixels=[]
for j in range(NY+1):
    for i in range(NX+1):
        x,y=i*W/NX,j*H/NY
        pixels.append((x,y));verts.append(((x-W/2)/SCALE,(H/2-y)/SCALE,0))
for j in range(NY):
    for i in range(NX):
        n=j*(NX+1)+i
        faces.append((n,n+NX+1,n+NX+2,n+1))
mesh=bpy.data.meshes.new('Continuous illustration cage - no detached image seams')
mesh.from_pydata(verts,[],faces);mesh.update()
uv=mesh.uv_layers.new(name='Fixed source pixels')
for poly in mesh.polygons:
    for li in poly.loop_indices:
        x,y=pixels[mesh.loops[li].vertex_index];uv.data[li].uv=(x/W,1-y/H)
obj=bpy.data.objects.new('Yukimura illustration deformation study',mesh)
scene.collection.objects.link(obj)
obj.shape_key_add(name='Basis')
for kind in ['Thrust','Breath','Cloth']:
    key=obj.shape_key_add(name=kind);key.slider_min=-1;key.slider_max=1.2
    group=obj.vertex_groups.new(name=kind)
    for i,(x,y) in enumerate(pixels):
        dx,dy=displacement(x,y,kind)
        key.data[i].co.x+=dx/SCALE;key.data[i].co.y-=dy/SCALE
        weight=weights(x,y)[['Thrust','Breath','Cloth'].index(kind)]
        if weight>0:group.add([i],weight,'REPLACE')
keys=mesh.shape_keys.key_blocks
# Complete attack then a separate breathing loop. Repeated end poses intentional.
curves={'Thrust':[(1,0),(5,-.28),(8,-.32),(10,1),(11,1),(14,.65),(18,.16),(24,0),(25,0),(48,0)],
        'Breath':[(1,0),(24,0),(25,0),(31,1),(37,0),(43,-1),(48,0)],
        'Cloth':[(1,0),(8,-.12),(10,0),(13,1),(18,-.25),(24,0),(25,0),(31,.15),(37,0),(43,-.15),(48,0)]}
for name,points in curves.items():
    for frame,value in points:
        keys[name].value=value;keys[name].keyframe_insert('value',frame=frame)
for fc in mesh.shape_keys.animation_data.action.fcurves:
    for k in fc.keyframe_points:
        k.interpolation='BEZIER';k.handle_left_type=k.handle_right_type='AUTO_CLAMPED'
for label,frame in [('ready',1),('windup',8),('thrust / contact',10),('recover',18),('idle start',25)]:
    scene.timeline_markers.new(label,frame=frame)

mat=bpy.data.materials.new('Cached Blender light plate - illustration emission');mat.use_nodes=True
n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear()
out=n.new('ShaderNodeOutputMaterial');tex=n.new('ShaderNodeTexImage');tex.interpolation='Linear'
em=n.new('ShaderNodeEmission');transparent=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
l.new(tex.outputs['Color'],em.inputs['Color']);l.new(tex.outputs['Alpha'],mix.inputs[0])
l.new(transparent.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0]);mesh.materials.append(mat)
plates={}
for preset in PRESETS:
    im=bpy.data.images.load(str(OUT/'lights'/f'{preset}.png'));im.alpha_mode='STRAIGHT';im.pack();plates[preset]=im
tex.image=plates['neutral']
camera_data=bpy.data.cameras.new('Fixed source view, padded for thrust');camera_data.type='ORTHO';camera_data.ortho_scale=2048/SCALE;camera_data.sensor_fit='HORIZONTAL'
camera=bpy.data.objects.new('Fixed source view, padded for thrust',camera_data);scene.collection.objects.link(camera)
camera.location=(0,0,6);camera.rotation_euler=(0,0,0);scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
scene.cycles.use_denoising=False;scene.cycles.use_animated_seed=False;scene.cycles.seed=1615;scene.cycles.adaptive_threshold=0
scene.cycles.max_bounces=1;scene.cycles.transparent_max_bounces=4
scene.render.film_transparent=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.frame_start=1;scene.frame_end=48;scene.render.fps=20

# Validate the evaluated cage at EVERY exported frame: no inverted triangles,
# both hands/shaft translate together, feet stay planted. Not anatomical IK.
points=np.array(pixels);quads=np.array(faces)
triangles=np.concatenate((quads[:,[0,1,2]],quads[:,[0,2,3]]))
def areas(p):
    t=p[triangles];a=t[:,1]-t[:,0];b=t[:,2]-t[:,0]
    return a[:,0]*b[:,1]-a[:,1]*b[:,0]
base_area=areas(points)
deltas={k:np.array([displacement(x,y,k) for x,y in pixels]) for k in curves}
report={'method':'one illustration, continuous 2D deformation cage, rigid shared grip/shaft translation; cached Blender lighting plates',
        'not_anatomical_ik':True,'device':'CPU','blender':bpy.app.version_string,'source_size':[W,H],
        'frame_size':list(FRAME_SIZE),'fps':20,'clips':{'thrust':[1,24],'idle':[25,48]},
        'source':'assets/source/jigoku-2d/yukimura-yari-ready.png',
        'source_sha256':hashlib.sha256((ROOT/'assets/source/jigoku-2d/yukimura-yari-ready.png').read_bytes()).hexdigest(),
        'frames':[],'limits':['One fixed source view; no reconstructed back side.',
        'Small planar thrust only; no skeletal IK, independent fingers, sliding grip or large shoulder rotation.',
        'Lighting baked in source pose, not recalculated on a 3D animated body.',
        'Painted original shadows remain. The source view is shallow three-quarter, not a calibrated isometric camera.']}
for frame in range(1,49):
    scene.frame_set(frame);values={k:keys[k].value for k in curves}
    deformed=points+sum(deltas[k]*values[k] for k in curves)
    ratio=areas(deformed)/base_area
    assert ratio.min()>.1, (frame,ratio.min())
    # Points are defined in original art coordinates.
    def move(x,y):return np.sum([np.array(displacement(x,y,k))*values[k] for k in curves],axis=0)
    weapon_points=[(50,565.65),(330,517),(858,456),(1490,353.97),(1290,320)]
    grip=np.array([move(*p) for p in weapon_points])
    err=float(np.max(np.linalg.norm(grip-grip[0],axis=1)));assert err<1e-5
    feet=np.array([move(202,970),move(975,880)]);drift=float(np.max(np.linalg.norm(feet,axis=1)));assert drift<1e-5
    report['frames'].append({'frame':frame,'values':values,'min_triangle_area_ratio':float(ratio.min()),'weapon_hand_translation_error_source_px':err,'foot_anchor_drift_source_px':drift})

start=time.perf_counter()
for preset in PRESETS:
    tex.image=plates[preset];folder=TMP/preset;folder.mkdir(exist_ok=True)
    scene.render.resolution_x,scene.render.resolution_y=FRAME_SIZE
    for frame in range(1,49):
        scene.frame_set(frame);scene.render.filepath=str(folder/f'{frame:03}.png')
        bpy.ops.render.render(write_still=True)
    # Optional desktop inspection sprites, separate from the mobile atlas.
    hd_folder=TMP/(preset+'-hd');hd_folder.mkdir(exist_ok=True)
    scene.render.resolution_x=1024;scene.render.resolution_y=640
    for frame in range(1,49):
        scene.frame_set(frame);scene.render.filepath=str(hd_folder/f'{frame:03}.png')
        bpy.ops.render.render(write_still=True)
    scene.render.resolution_x=2048;scene.render.resolution_y=1280
    for frame in [1,8,10,18]:
        scene.frame_set(frame);scene.render.filepath=str(OUT/f'{preset}-{frame:02}.png')
        bpy.ops.render.render(write_still=True)
    print('YARI_MOTION_PRESET_DONE',preset,flush=True)
report['render_seconds']=round(time.perf_counter()-start,3)
tex.image=plates['warm-left'];scene.frame_set(10);scene.render.resolution_x,scene.render.resolution_y=FRAME_SIZE
info=bpy.data.texts.new('README - fixed illustration motion')
info.write('Frames 1-24: short thrust. Frames 25-48: idle. Three packed Blender light plates: swap material texture. Thrust/Breath/Cloth shape keys + matching vertex groups. This is planar image deformation, not skeletal IK. Light is baked before motion. All reference pixels and weapon are one source image; no independently replaceable weapon yet. Camera must remain fixed. Rebuild with tools/animate_yari_illustration.py.\n')
target=ROOT/'assets/optimized/jigoku-2d/yari-motion.blend'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
report['scene']=str(target.relative_to(ROOT));report['scene_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
(OUT/'motion-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('YARI_MOTION_DONE',report['render_seconds'],flush=True)
