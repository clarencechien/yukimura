"""Body v2 inspection renders: full turnaround plus close-ups, same studio as render_trellis_study.py."""
from pathlib import Path
import argparse,json,math,time
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--output',required=True);p.add_argument('--size',type=int,default=1000);p.add_argument('--samples',type=int,default=32);p.add_argument('--views',default='front,three-quarter,side,back,clay,neck,torso,hands,legs,back-detail');a=p.parse_args()
out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert meshes,'GLB has no meshes'

points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
low=Vector(tuple(min(v[i] for v in points) for i in range(3)));high=Vector(tuple(max(v[i] for v in points) for i in range(3)));height=high.z-low.z
assert height>0
# Normalize with a parent so all imported transformations remain intact.
root=bpy.data.objects.new('Asset normalization',None);bpy.context.collection.objects.link(root)
for o in list(bpy.context.scene.objects):
 if o!=root and o.parent is None:o.parent=root
scale=2.0/height;root.scale=(scale,)*3;root.location=(-(low.x+high.x)*.5*scale,-(low.y+high.y)*.5*scale,-low.z*scale)
bpy.context.view_layer.update()
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=a.samples;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=a.size;scene.render.resolution_y=a.size;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False
scene.world=bpy.data.worlds.new('Neutral studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.10,.12,.15,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def area(name,location,energy,color,size):
 bpy.ops.object.light_add(type='AREA',location=location);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.color=color;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,1))
area('Large warm key',(3,-4,5),650,(1,.88,.73),4);area('Soft cool fill',(-4,-2,3),450,(.7,.83,1),4);area('Back edge',(1,3,4),750,(1,.94,.8),3)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.006));floor=bpy.context.object;floor.name='Studio floor';mat=bpy.data.materials.new('Slate');mat.diffuse_color=(.035,.042,.055,1);mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.035,.042,.055,1);bsdf.inputs['Roughness'].default_value=.73;floor.data.materials.append(mat)
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=2.35;camera.data.lens=60
report={'renderer':bpy.app.version_string,'device':'CPU','samples':a.samples,'image_size':[a.size,a.size],'geometry_objects':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'triangles':sum(sum(len(poly.vertices)-2 for poly in o.data.polygons) for o in meshes),'material_count':len({m.name for o in meshes for m in o.data.materials if m}),'images':[{'name':im.name,'size':list(im.size)} for im in bpy.data.images if im.type=='IMAGE'],'views':[]}
original_materials={o.name:list(o.data.materials) for o in meshes}
clay=bpy.data.materials.new('Geometry inspection clay');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.45,.47,.5,1);clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8
# glTF +Z is front; Blender's import maps this to -Y. (degrees, camera height, target, ortho span)
VIEWS={'front':(0,1.5,(0,0,1.03),2.35),'three-quarter':(35,1.5,(0,0,1.03),2.35),'side':(90,1.5,(0,0,1.03),2.35),'back':(180,1.5,(0,0,1.03),2.35),'clay':(0,1.5,(0,0,1.03),2.35),
 'neck':(25,1.62,(0,0,1.55),.75),'torso':(0,1.25,(0,0,1.2),.8),'hands':(30,.95,(0,0,.98),1.0),'legs':(15,.45,(0,0,.4),.95),'back-detail':(160,1.25,(0,0,1.25),1.0),'clay-torso':(0,1.25,(0,0,1.2),.8),
 'back-upper':(180,1.45,(0,0,1.35),.62),'back-lower':(180,1.1,(0,0,1.05),.62),'skirt-front':(0,.95,(0,0,.82),.7),'skirt-back':(180,.95,(0,0,.82),.7),
 'hand-r-front':(0,.95,(-.39,.16,.88),.34),'hand-l-front':(0,.95,(.376,-.16,.89),.34),'hand-r-out':(-70,.95,(-.39,.16,.88),.34),'hand-l-out':(70,.95,(.376,-.16,.89),.34),
 'forearm-r':(-20,1.1,(-.37,.1,1.05),.5),'forearm-l':(20,1.1,(.36,-.1,1.05),.5),'knees':(0,.5,(0,0,.5),.7),'shins':(0,.3,(0,0,.3),.7),
 'seam-shin-l':(10,.3,(.24,-.16,.27),.18),'seam-forearm-l':(20,1.1,(.35,-.13,1.08),.2),
 'neck-front':(0,1.58,(0,0,1.52),.42),'neck-side':(90,1.58,(0,0,1.52),.42),'neck-left':(-90,1.58,(0,0,1.52),.42),'neck-back':(180,1.58,(0,0,1.52),.42),'neck-low':(20,1.35,(0,-.05,1.5),.4),
 'clay-neck-front':(0,1.58,(0,0,1.52),.42),'clay-neck-side':(90,1.58,(0,0,1.52),.42),'clay-neck-back':(180,1.58,(0,0,1.52),.42),
 'patch-r':(0,1.44,(-.17,0,1.43),.16),'patch-l':(0,1.44,(.10,0,1.44),.16),'clay-patch-r':(0,1.44,(-.17,0,1.43),.16),'clay-patch-l':(0,1.44,(.10,0,1.44),.16),
 'audit-shoulder-r':(-50,1.75,(-.22,0,1.42),.4),'audit-shoulder-l':(50,1.75,(.22,0,1.42),.4),'audit-armpit-r':(-90,1.25,(-.2,0,1.25),.4),'audit-armpit-l':(90,1.25,(.2,0,1.25),.4),
 'audit-waist':(0,1.1,(0,0,1.08),.4),'audit-skirt-r':(-90,.85,(-.15,0,.82),.5),'audit-skirt-l':(90,.85,(.15,0,.82),.5),'audit-boots':(15,.15,(0,0,.1),.6),'audit-boot-side':(90,.15,(.12,0,.1),.35),
 'audit-helmet-side':(90,1.75,(0,0,1.72),.45),'audit-helmet-back':(150,1.75,(0,0,1.72),.45),'audit-high':(35,2.6,(0,0,1.1),1.6),
 'knot-neck':(0,1.47,(-.006,-.08,1.455),.12),'knot-neck-side':(55,1.47,(-.006,-.08,1.455),.12),'knot-waist':(0,1.08,(-.07,-.15,1.07),.16),'knot-waist-side':(-50,1.08,(-.07,-.15,1.07),.16),'tassel-shoulder':(-20,1.42,(-.177,-.02,1.41),.13),
 'plate-chest':(0,1.3,(0,0,1.28),.42),'plate-sode-r':(-40,1.4,(-.25,0,1.38),.36),'plate-sode-l':(40,1.4,(.25,0,1.38),.36),'plate-skirt':(15,.85,(0,0,.85),.6),'plate-thigh':(10,.7,(0,0,.68),.55),'plate-shin':(10,.35,(0,0,.33),.55),
 'clay-plate-chest':(0,1.3,(0,0,1.28),.42),'clay-plate-sode-r':(-40,1.4,(-.25,0,1.38),.36),'clay-plate-skirt':(15,.85,(0,0,.85),.6),'clay-plate-shin':(10,.35,(0,0,.33),.55),
 'kusazuri-front':(0,.9,(0,0,.88),.62),'kusazuri-back':(180,.9,(0,0,.88),.62),'sode-l':(90,1.4,(.3,0,1.38),.42),'sode-r':(-90,1.4,(-.3,0,1.38),.42),
 'clay-kusazuri-front':(0,.9,(0,0,.88),.62),
 'clay-knees':(0,.5,(0,0,.5),.7),'clay-shins':(0,.3,(0,0,.3),.7),'clay-forearm-l':(20,1.1,(.36,-.1,1.05),.5),
 'clay-hand-r-front':(0,.95,(-.39,.16,.88),.34),'clay-hand-l-out':(70,.95,(.376,-.16,.89),.34),
 'clay-back-upper':(180,1.45,(0,0,1.35),.62),'clay-back-lower':(180,1.1,(0,0,1.05),.62),'clay-skirt-front':(0,.95,(0,0,.82),.7),'clay-skirt-back':(180,.95,(0,0,.82),.7)}
clay_views={'clay-knees','clay-shins','clay-forearm-l','clay-kusazuri-front','clay-plate-chest','clay-plate-sode-r','clay-plate-skirt','clay-plate-shin','clay-patch-r','clay-patch-l','clay-neck-front','clay-neck-side','clay-neck-back','clay-hand-r-front','clay-hand-l-out','clay','clay-torso','clay-back-upper','clay-back-lower','clay-skirt-front','clay-skirt-back'}
for name in a.views.split(','):
 degrees,height,target,span=VIEWS[name]
 for o in meshes:
  for i in range(len(o.data.materials)):o.data.materials[i]=clay if name in clay_views else original_materials[o.name][i]
 angle=math.radians(degrees);camera.location=(target[0]+math.sin(angle)*5,target[1]-math.cos(angle)*5,height);aim(camera,target);camera.data.ortho_scale=span;scene.render.filepath=str(out/f'{name}.png');started=time.monotonic();bpy.ops.render.render(write_still=True);report['views'].append({'name':name,'degrees':degrees,'target':target,'span':span,'seconds':round(time.monotonic()-started,2)})
(out/'render-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
