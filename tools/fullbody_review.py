"""Render an independent full-body rig proof with continuous wrist deformation."""
import bpy,math,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mathutils import Vector,Matrix
from mpfb_fullbody import Body,ROOT,material
bpy.ops.wm.read_factory_settings(use_empty=True);body=Body();rig=body.armature();mesh,ids=body.mesh(rig)
mesh.data.materials.append(material('neutral anatomical clay',(.22,.27,.29),.73))
sub=mesh.modifiers.new('review surface','SUBSURF');sub.levels=1
scene=bpy.context.scene;scene.render.fps=24;scene.frame_end=72
# Bend the elbow through its anatomical plane; roll is shared by two forearm bones.
for frame,bend,twist,flex in [(0,0,0,0),(24,75,0,0),(48,75,60,0),(72,75,30,20)]:
 for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0)
 for side in ('R','L'):
  sign=1 if side=='R' else -1
  arm=rig.pose.bones['lowerarm01.'+side]
  rest=arm.bone.matrix_local.to_3x3();axis=(rest.inverted()@Vector((0,1,0))).normalized()
  arm.rotation_quaternion=Matrix.Rotation(math.radians(bend*sign),3,axis).to_quaternion()
  # Rotation about local Y is longitudinal forearm roll.
  arm.rotation_quaternion=arm.rotation_quaternion@Matrix.Rotation(math.radians(twist*.35*sign),3,'Y').to_quaternion()
  rig.pose.bones['lowerarm02.'+side].rotation_quaternion=Matrix.Rotation(math.radians(twist*.65*sign),3,'Y').to_quaternion()
  rig.pose.bones['wrist.'+side].rotation_quaternion=Matrix.Rotation(math.radians(flex),3,'X').to_quaternion()
 for pb in rig.pose.bones:pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name)
rig.animation_data.action.name='neutral_elbow_forearm_roll_wrist'
for fc in rig.animation_data.action.fcurves:
 for k in fc.keyframe_points:k.interpolation='LINEAR'
scene.world=bpy.data.worlds.new('soft studio');scene.world.color=(.16,.16,.16)
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(2.3,-4.4,1.3));camera=bpy.context.object;camera.data.type='ORTHO';camera.data.ortho_scale=2.05;aim(camera,(0,0,.05));scene.camera=camera
for p,power,size,col in [((2,-3,3),350,3,(1,.86,.72)),((-2,-1,2),230,2,(.65,.8,1)),((0,2,2),400,2,(.9,.95,1))]:
 bpy.ops.object.light_add(type='AREA',location=p);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.data.color=col;aim(o,(0,0,.2))
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.818));bpy.context.object.data.materials.append(material('studio ground',(.025,.035,.044)))
scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.frame_set(0);bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/optimized/commanders/mpfb-fullbody.blend'),compress=True)
report={'source_bones':len(rig.data.bones),'source_body_vertices':len(ids),'weights':'top four, normalized; linear skinning matches game export','frames':[]}
for f,label in ([] if '--save-only' in sys.argv else [(0,'neutral'),(24,'elbow'),(48,'roll'),(72,'wrist')]):
 scene.frame_set(f);scene.render.filepath=str(ROOT/'renders/fullbody-v14'/f'body-{label}.png');bpy.ops.render.render(write_still=True)
 report['frames'].append({'frame':f,'file':f'body-{label}.png'})
if '--save-only' not in sys.argv:(ROOT/'renders/fullbody-v14/fullbody-proof.json').write_text(json.dumps(report,indent=2)+'\n')
