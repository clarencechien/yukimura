"""Blender local refinement: six coins, eye surfaces, material separation and baked finishes.
Uses inspected landmarks on the normalized head; does not claim anatomical retopology.
"""
from pathlib import Path
import argparse,json,math
import bpy,bmesh
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--model',default='docs/experiments/future-sanada/head-study/head-high.glb');p.add_argument('--output',default='docs/experiments/future-sanada/head-study/refined');a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
base=next(o for o in bpy.context.scene.objects if o.type=='MESH');world=base.matrix_world.copy();base.parent=None;base.matrix_world=Matrix.Identity(4);base.data.transform(world)
pts=[Vector(c) for c in base.bound_box];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);scale=2/(hi.z-lo.z);base.data.transform(Matrix.Scale(scale,4)@Matrix.Translation(Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))));base.name='Generated shell with local corrections'
mesh=base.data;vertices=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',vertices);vertices=vertices.reshape(-1,3)
bm=bmesh.new();bm.from_mesh(mesh);bvh=BVHTree.FromBMesh(bm);bm.free()
def surface(x,z):
 hit,normal,index,distance=bvh.ray_cast(Vector((x,-3,z)),Vector((0,1,0)))
 return hit.y if hit is not None else -.39

def mat(name,color,metal=0,rough=.45,coat=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*color,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough;n.inputs['Coat Weight'].default_value=coat;n.inputs['Coat Roughness'].default_value=.22;return m

def object_mesh(name,verts,faces,material):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(material)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
 for f in me.polygons:f.use_smooth=True
 return ob

def line(name,points,material,radius):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=12;c.bevel_depth=radius;c.bevel_resolution=3;s=c.splines.new('POLY');s.points.add(len(points)-1)
 for p,co in zip(s.points,points):p.co=(*co,1)
 ob=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(ob);c.materials.append(material);return ob

# Material assignments use original base-color UVs; colors are not repainted.
original=mesh.materials[0];image=next(n.image for n in original.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.image.colorspace_settings.name=='sRGB');pixels=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels);pixels=pixels.reshape(image.size[1],image.size[0],4)
uv=np.empty(len(mesh.loops)*2,dtype=np.float32);mesh.uv_layers.active.data.foreach_get('uv',uv);uv=uv.reshape(-1,3,2).mean(1);rgb=pixels[np.clip((uv[:,1]*image.size[1]).astype(int),0,image.size[1]-1),np.clip((uv[:,0]*image.size[0]).astype(int),0,image.size[0]-1),:3]
indices=np.empty(len(mesh.loops),dtype=np.int32);mesh.loops.foreach_get('vertex_index',indices);original_faces=indices.reshape(-1,3).copy();centers=vertices[original_faces].mean(1)
def material_copy(name,metal,rough,coat=0):
 m=original.copy();m.name=name;n=m.node_tree.nodes.get('Principled BSDF')
 for key,value in [('Metallic',metal),('Roughness',rough),('Coat Weight',coat)]:
  for link in list(n.inputs[key].links):m.node_tree.links.remove(link)
  n.inputs[key].default_value=value
 mesh.materials.append(m);return len(mesh.materials)-1
red=material_copy('Red lacquer / nonmetal coat',0,.38,.28);gold=material_copy('Worn gilding',.82,.34);cloth=material_copy('Dark cloth and cord',0,.82);skinidx=material_copy('Skin beneath helmet',0,.53)
classes=np.zeros(len(mesh.polygons),dtype=np.int32);r,g,b=rgb.T
classes[(r>g*1.6)&(r>b*1.8)&(r>.08)]=red
classes[(r>g*1.03)&(g>b*1.3)&(g>.12)&(classes==0)]=gold
classes[rgb.max(1)<.13]=cloth
skinroi=(centers[:,1]<-.15)&(centers[:,2]>.64)&(centers[:,2]<.83)&(abs(centers[:,0])<.29)&(abs(centers[:,0])>.07)&(g>.16)&(r>g)&(r<g*2.5)
classes[skinroi]=skinidx
underside=mat('Dark visor underside',(.018,.009,.006),0,.85);mesh.materials.append(underside);normals=np.empty(len(mesh.polygons)*3,dtype=np.float32);mesh.polygons.foreach_get('normal',normals)
under=(centers[:,1]<-.44)&(centers[:,2]>.77)&(centers[:,2]<.91)&(normals.reshape(-1,3)[:,2]<-.25);classes[under]=len(mesh.materials)-1
mesh.polygons.foreach_set('material_index',classes)
material_counts={mesh.materials[i].name:int((classes==i).sum()) for i in range(len(mesh.materials))}
del pixels,rgb,uv,centers

# Lift only the projecting front visor, not the helmet dome or face.
x,y,z=vertices.T
brim=(abs(x)<.39)&(y<-.46)&(z>.77)&(z<.94)
weight=np.clip((.94-z)/.10,0,1)*np.clip((.39-abs(x))/.08,0,1)*np.clip((z-.77)/.015,0,1)
vertices[brim,2]+=.060*weight[brim]
def plate_y(x,z):return -.570+.56*(z-1.0)+2.1*x*x
# Recess the four incorrect generated coins under a curved lacquer crest plate.
flatten=(abs(x)<.27)&(z>.865)&(z<1.245)&(y<-.20)
vertices[flatten,1]=np.maximum(vertices[flatten,1],plate_y(x[flatten],z[flatten])+.018)
# Clear the failed generated eye relief and give the replacement a smooth socket.
def eye_plane(x):return -.410+.50*(abs(x)-.160)
socket_count=0
for sign in [-1,1]:
 q=((x-sign*.160)/.080)**2+((z-.747-sign*.16*(x-sign*.160))/.031)**2
 socket=(q<1)&(y<-.20)&(y>-.48)
 target=eye_plane(x)+.012
 vertices[socket,1]=np.maximum(vertices[socket,1],target[socket]);socket_count+=int(socket.sum())
mesh.vertices.foreach_set('co',vertices.ravel());mesh.update()
base_before=len(mesh.polygons);bm=bmesh.new();bm.from_mesh(mesh);tiny=[f for f in bm.faces if f.calc_area()<1e-12];bmesh.ops.delete(bm,geom=tiny,context='FACES');bm.to_mesh(mesh);bm.free()

lacquer=mat('Crest oxblood lacquer',(.13,.012,.007),0,.48,.12);brass=mat('Crest aged brass',(.38,.23,.07),.78,.53);dark=mat('Lid edge and brow',(.026,.012,.007),0,.8)
skin=mat('Matte eyelid skin',(.16,.085,.05),0,.65)
white=mat('Warm sclera',(.09,.08,.065),0,.62);pupil=mat('Pupil',(.002,.0015,.001),0,.48)
# A rounded rectangular curved plate; all six coins share one reusable construction.
N=96;verts=[(0,plate_y(0,1.055),1.055)];faces=[]
for ring in range(1,9):
 for j in range(N):
  t=2*math.pi*j/N;c,s=math.cos(t),math.sin(t);x=.260*math.copysign(abs(c)**(1/3),c)*ring/8;z=1.055+.18*math.copysign(abs(s)**(1/3),s)*ring/8;verts.append((x,plate_y(x,z),z))
for j in range(N):faces.append((0,1+j,1+(j+1)%N))
for ring in range(7):
 for j in range(N):q=1+ring*N+j;n=1+ring*N+(j+1)%N;faces.append((q,n,n+N,q+N))
plate=object_mesh('Rebuilt crest backing',verts,faces,lacquer);solid=plate.modifiers.new('Crest thickness','SOLIDIFY');solid.thickness=.006
def planar_uv(ob):
 layer=ob.data.uv_layers.new(name='Local planar UV')
 xs=[v.co.x for v in ob.data.vertices];zs=[v.co.z for v in ob.data.vertices]
 for loop in ob.data.loops:
  v=ob.data.vertices[loop.vertex_index].co
  layer.data[loop.index].uv=(.04+.92*(v.x-min(xs))/(max(xs)-min(xs)),.04+.92*(v.z-min(zs))/(max(zs)-min(zs)))
planar_uv(plate)

coins=[]
for row,cz in enumerate([1.12,.98]):
 for col,cx in enumerate([-.144,0,.144]):
  vs=[];fs=[];radius=.060;half_hole=.016;depth=.009
  for level in [0,1]:
   for inner in [False,True]:
    for j in range(96):
     t=2*math.pi*j/96;c,s=math.cos(t),math.sin(t);rr=half_hole/max(abs(c),abs(s)) if inner else radius;dx,dz=rr*c,rr*s
     vs.append((cx+dx,plate_y(cx,cz)+4.2*cx*dx+.56*dz-.004-depth*level,cz+dz))
  for j in range(96):
   k=(j+1)%96
   fs.extend([(j,k,96+k,96+j),(192+j,288+j,288+k,192+k),(j,192+j,192+k,k),(96+j,96+k,288+k,288+j)])
  ob=object_mesh(f'Six coins / row {row+1} coin {col+1}',vs,fs,brass);coins.append(ob.name)
  planar_uv(ob)
  bevel=ob.modifiers.new('Coin edges','BEVEL');bevel.width=.0015;bevel.segments=2

# Independent convex eye surfaces with clipped irises and pupils. No emissive eyes.
landmarks=[]
for sign in [-1,1]:
 cx=.160*sign;cz=.747;w=.068;h=.016;slope=.16*sign
 def inside(x,z):return ((x-cx)/w)**2+((z-cz-slope*(x-cx))/h)**2<=1.00001
 def eye_y(x,z):
  q=((x-cx)/w)**2+((z-cz-slope*(x-cx))/h)**2
  return eye_plane(x)-.010+((x-cx)**2+(z-cz)**2)/.26
 # Skin annulus replaces the poorly resolved original eye rim without altering the mask.
 vs=[];fs=[]
 for ring in range(7):
  u=ring/6;ww=w+u*.008;hh=h+u*.010
  for j in range(96):
   t=2*math.pi*j/96;x=cx+ww*math.cos(t);z=cz+hh*math.sin(t)+slope*(x-cx)
   # Do not attach new eyelids to the forward-projecting visor in the original ray sample.
   depth=eye_plane(x)*(1-u)+surface(x,min(z,.762))*u;vs.append((x,depth-.003,z))
 for ring in range(6):
  for j in range(96):q=ring*96+j;n=ring*96+(j+1)%96;fs.append((q,n,n+96,q+96))
 object_mesh(f'Eyelid skin {sign}',vs,fs,skin)
 def eye_disc(name,radial,material,offset=0,palette=None):
  vs=[(cx,eye_y(cx,cz)+offset,cz)];fs=[];segments=128;rings=12
  for ring in range(1,rings+1):
   for j in range(segments):
    t=2*math.pi*j/segments
    if radial is None:dx=w*ring/rings*math.cos(t);dz=h*ring/rings*math.sin(t)+slope*dx
    else:
     hi=radial;lo=0
     for _ in range(12):
      mid=(hi+lo)/2
      if inside(cx+mid*math.cos(t),cz+mid*math.sin(t)):lo=mid
      else:hi=mid
     dx=lo*ring/rings*math.cos(t);dz=lo*ring/rings*math.sin(t)
    x,z=cx+dx,cz+dz;vs.append((x,eye_y(x,z)+offset,z))
  for j in range(segments):fs.append((0,1+j,1+(j+1)%segments))
  for ring in range(rings-1):
   for j in range(segments):q=1+ring*segments+j;n=1+ring*segments+(j+1)%segments;fs.append((q,n,n+segments,q+segments))
  ob=object_mesh(name,vs,fs,material)
  if palette:
   for m in palette:ob.data.materials.append(m)
   for f in ob.data.polygons:f.material_index=1+(f.index%segments*17%len(palette))
  return ob
 white.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.12
 pupil.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.02
 eye_disc(f'Eye sclera {sign}',None,white)
 iris=mat(f'Iris brown {sign}',(.055,.022,.007),0,.48);palette=[mat(f'Iris fiber {sign}/{i}',(.032+.005*i,.012+.002*i,.004+.0007*i),0,.48) for i in range(8)]

 for material in [iris]+palette:material.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.10
 eye_disc(f'Iris {sign}',.034,iris,-.001,palette);eye_disc(f'Pupil {sign}',.011,pupil,-.002)
 for upper in [True,False]:
  points=[]
  for j in range(49):
   t=(j/48*math.pi) if upper else (math.pi+j/48*math.pi);x=cx+w*math.cos(t);z=cz+h*math.sin(t)+slope*(x-cx);points.append((x,eye_y(x,z)-.002,z))
  line(f'Lid margin {sign}/{upper}',points,dark,.0018 if upper else .0009)
 # Sloping brow: inner ends descend toward the nose for a focused expression.
 points=[]
 for j in range(33):
  dx=-.085+.17*j/32;z=cz+.034+slope*dx+.004*math.sin(j/32*math.pi);x=cx+dx;points.append((x,surface(x,.758)-.008,z))
 line(f'Focused brow {sign}',points,dark,.004)
 landmarks.append({'side':sign,'center_x':cx,'center_z':cz,'half_width':w,'half_height':h,'iris_radius':.034,'pupil_radius':.011})
# Bake new worn finishes in Blender. UVs are local to each replacement part;
# no interpolation across unrelated source atlas islands.
def bake_finish(ob,material,name,colors,noise_scale):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.threads_mode='FIXED';scene.render.threads=4
 nodes=material.node_tree.nodes;links=material.node_tree.links;shader=nodes.get('Principled BSDF');output=nodes.get('Material Output')
 texcoord=nodes.new('ShaderNodeTexCoord');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=noise_scale;noise.inputs['Detail'].default_value=3
 ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.28;ramp.color_ramp.elements[0].color=(*colors[0],1);ramp.color_ramp.elements[1].position=.58;ramp.color_ramp.elements[1].color=(*colors[1],1)
 links.new(texcoord.outputs['UV'],noise.inputs['Vector']);links.new(noise.outputs['Fac'],ramp.inputs['Fac']);emit=nodes.new('ShaderNodeEmission');links.new(ramp.outputs['Color'],emit.inputs['Color']);links.new(emit.outputs[0],output.inputs['Surface'])
 image=bpy.data.images.new(name,512,512,alpha=False);image.colorspace_settings.name='sRGB';texture=nodes.new('ShaderNodeTexImage');texture.image=image;nodes.active=texture
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.bake(type='EMIT',margin=8)
 links.new(shader.outputs[0],output.inputs['Surface']);links.new(texture.outputs['Color'],shader.inputs['Base Color'])
 for node in [texcoord,noise,ramp,emit]:nodes.remove(node)
 image.filepath_raw=str((out/(name+'.png')).resolve());image.file_format='PNG';image.save();image.pack()
bake_finish(plate,lacquer,'crest-lacquer',[(.055,.004,.002),(.15,.013,.007)],36)
bake_finish(bpy.data.objects[coins[0]],brass,'crest-brass',[(.095,.044,.01),(.4,.25,.075)],75)
# Apply explicit geometry modifiers and export selected meshes only.
for ob in list(bpy.context.scene.objects):
 if ob.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
 if ob.type=='MESH':
  bpy.context.view_layer.objects.active=ob
  for modifier in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.scene.objects:
 if ob.type=='MESH':ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str((out/'head-refined.glb').resolve()),export_format='GLB',use_selection=True,export_yup=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=str((out/'head-refined.blend').resolve()),compress=True)
report={'iteration':5,'socket_vertices_recessed':socket_count,'source':a.model,'normalization_scale':scale,'generated_source_preserved':True,'material_face_counts':material_counts,'visor_vertices_adjusted':int(brim.sum()),'crest_vertices_recessed':int(flatten.sum()),'removed_near_zero_faces':len(tiny),'coin_objects':coins,'coin_count':len(coins),'eye_landmarks':landmarks,'changes':['Raised only front visor by up to 0.06 normalized units','Recessed incorrect four-coin relief and rebuilt six separate square-hole coins','Added independent sclera, clipped brown iris, pupil, eyelid and brow geometry','Separated lacquer, gold, cloth and skin material response','Baked independent crest lacquer and brass textures in Blender','Reduced iris and pupil specular reflection after close-up inspection'],'limitations':['Artist-directed procedural edits, not hand-sculpted anatomical retopology','Eye surfaces are convex caps, not complete anatomical eyeballs','Mask ventilation remains generated and is not certified as a separate hollow mask','No skeleton, weights or facial animation']}
(out/'refinement-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
