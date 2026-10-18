"""Blender local refinement: six coins, eye surfaces, material separation and baked finishes.
Uses inspected landmarks on the normalized head; does not claim anatomical retopology.
"""
from pathlib import Path
import argparse,json,math
from trellis_human_eyes import add_human_eyes
from trellis_mask_rim import trim_opening,add_rim,contour
from trellis_nasal_repair import remove_old_panels,add_panels
from trellis_lower_mask import remove_old_lower,add_lower_parts,finish_uv
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
red=material_copy('Red lacquer / nonmetal coat',0,.48,.20);gold=material_copy('Worn gilding',.82,.34);cloth=material_copy('Dark cloth and cord',0,.82);skinidx=material_copy('Skin beneath helmet',0,.53)
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

# Preserve the actual original UV surface for selected-to-active crest baking.
crest_source=base.copy();crest_source.data=base.data.copy();crest_source.name='Temporary crest bake source';bpy.context.collection.objects.link(crest_source)

# Lift only the projecting front visor, not the helmet dome or face.
x,y,z=vertices.T
brim=(abs(x)<.39)&(y<-.46)&(z>.77)&(z<.94)
weight=np.clip((.94-z)/.10,0,1)*np.clip((.39-abs(x))/.08,0,1)*np.clip((z-.77)/.015,0,1)
vertices[brim,2]+=.020*weight[brim]
def plate_y(x,z):return -.570+.56*(z-1.0)+2.1*x*x
# Recess the four incorrect generated coins under a curved lacquer crest plate.
flatten=(abs(x)<.27)&(z>.865)&(z<1.245)&(y<-.20)
vertices[flatten,1]=np.maximum(vertices[flatten,1],plate_y(x[flatten],z[flatten])+.018)
# Remove only generated skin / dark eye polygons, preserving the mask's gold rim.
socket_count=0
mesh.vertices.foreach_set('co',vertices.ravel());mesh.update()
base_before=len(mesh.polygons);bm=bmesh.new();bm.from_mesh(mesh)
tiny=[f for f in bm.faces if f.calc_area()<1e-12];bmesh.ops.delete(bm,geom=tiny,context='FACES')
# A spatial opening removes the old eyes as a whole. Color-only selection leaves
# islands over the new brows and can accidentally remove the gold visor.
mask_trim=trim_opening(bm,skinidx)
removed_skin_count=mask_trim['removed_faces'];removed_nasal_faces=remove_old_panels(bm);lower_removed=remove_old_lower(bm);bm.to_mesh(mesh);bm.free()
mask_rim=add_rim(surface,object_mesh,mat)
nasal_repair,nasal_material,nasal_shell,lip_shell=add_panels(object_mesh,mat)
nasal_repair['removed_source_faces']=removed_nasal_faces
lower_repair,lower_brass=add_lower_parts(object_mesh,mat,nasal_material,surface)
lower_repair['removed_source_faces']=lower_removed
# Keep all repaired lacquer pieces on the same finish; retain the eye-rim gold.
eye_rim=bpy.data.objects['Menpo continuous eye rim and return']
eye_rim.data.materials[0]=nasal_material;finish_uv(eye_rim)

lacquer=mat('Crest oxblood lacquer',(.13,.012,.007),0,.65,0);brass=mat('Crest aged brass',(.38,.23,.07),.82,.42);dark=mat('Lid edge and brow',(.026,.012,.007),0,.8)
skin=mat('Matte eyelid skin',(.16,.085,.05),0,.65)
white=mat('Warm sclera',(.09,.08,.065),0,.62);pupil=mat('Pupil',(.002,.0015,.001),0,.48)
# Flush curved repair surface: boundary sampled from the existing helmet.
# No thick raised rectangular badge or solidify rim.
N=128;verts=[(0,plate_y(0,1.055),1.055)];faces=[]
for ring in range(1,17):
 for j in range(N):
  t=2*math.pi*j/N;c,s=math.cos(t),math.sin(t);u=ring/16
  x=.285*math.copysign(abs(c)**.5,c)*u;z=1.055+.208*math.copysign(abs(s)**.5,s)*u
  blend=max(0,(u-.72)/.28);blend=blend*blend*(3-2*blend)
  y=plate_y(x,z)*(1-blend)+(surface(x,z)-.001)*blend
  verts.append((x,y,z))
for j in range(N):faces.append((0,1+j,1+(j+1)%N))
for ring in range(15):
 for j in range(N):q=1+ring*N+j;n=1+ring*N+(j+1)%N;faces.append((q,n,n+N,q+N))
plate=object_mesh('Flush lacquer crest repair',verts,faces,lacquer)
def planar_uv(ob):
 layer=ob.data.uv_layers.new(name='Local planar UV')
 xs=[v.co.x for v in ob.data.vertices];zs=[v.co.z for v in ob.data.vertices]
 for loop in ob.data.loops:
  v=ob.data.vertices[loop.vertex_index].co
  layer.data[loop.index].uv=(.04+.92*(v.x-min(xs))/(max(xs)-min(xs)),.04+.92*(v.z-min(zs))/(max(zs)-min(zs)))
planar_uv(plate)

coins=[]
# Front profile includes a thin raised outer rim, recessed coin face and hole lip.
rim=mat('Coin raised edge / aged gold',(.49,.30,.085),.82,.37)
for row,cz in enumerate([1.127,.975]):
 for col,cx in enumerate([-.151,0,.151]):
  vs=[];fs=[];radius=.070;half_hole=.014
  for layer in range(10):
   for j in range(128):
    t=2*math.pi*j/128;c,s=math.cos(t),math.sin(t);hole=half_hole/max(abs(c),abs(s))
    rr,depth=[(radius,0),(radius,-.008),(radius-.002,-.011),(radius-.005,-.011),(radius-.007,-.007),(hole+.003,-.007),(hole+.001,-.010),(hole,-.008),(hole,0),(radius,0)][layer]
    dx,dz=rr*c,rr*s
    vs.append((cx+dx,plate_y(cx+dx,cz+dz)-.002+depth,cz+dz))
  for layer in range(9):
   for j in range(128):k=(j+1)%128;fs.append((layer*128+j,layer*128+k,(layer+1)*128+k,(layer+1)*128+j))
  # Weld the closing ring to avoid duplicate vertices at the rear outer seam.
  fs=[tuple(i if i<9*128 else i-9*128 for i in face) for face in fs];vs=vs[:9*128]
  ob=object_mesh(f'Six coins / row {row+1} coin {col+1}',vs,fs,brass);coins.append(ob.name)
  ob.data.materials.append(rim)
  for f in ob.data.polygons:
   f.use_smooth=False
   if f.index//128 in [1,2,5,6]:f.material_index=1
  planar_uv(ob)
  floor=[]
  for dx,dz in [(-half_hole,-half_hole),(half_hole,-half_hole),(half_hole,half_hole),(-half_hole,half_hole)]:floor.append((cx+dx,plate_y(cx+dx,cz+dz)-.0035,cz+dz))
  object_mesh(f'Coin hole recessed dark seat {row}/{col}',floor,[(0,1,2,3)],dark)

human_eyes=add_human_eyes()
# A recessed dark lining closes the new face-to-mask stand-off when seen from
# the side. The eye opening remains unobstructed; this is not a welded face.
orbital=bpy.data.objects['Human eyes and orbital skin / Rocketbox']
orbital_bm=bmesh.new();orbital_bm.from_mesh(orbital.data);orbital_bvh=BVHTree.FromBMesh(orbital_bm);orbital_bm.free()
liner_verts=[];liner_faces=[]
for j in range(161):
 x=-.31+.62*j/160;z=contour(x)-.006
 hit=orbital_bvh.ray_cast(Vector((x,-2,z)),Vector((0,1,0)))[0]
 rear=(hit.y if hit else -.32)+.008;front=min(surface(x,z)+.003,rear-.012)
 liner_verts.extend([(x,front,z-.004),(x,rear,z-.004)])
 if j:liner_faces.append((2*j-2,2*j,2*j+1,2*j-1))
object_mesh('Recessed mask eye-opening lining',liner_verts,liner_faces,dark)
landmarks=[]
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
 if name=='crest-brass':
  bump=nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.00025;bump.inputs['Strength'].default_value=.32;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],shader.inputs['Normal'])
  normal_image=bpy.data.images.new('crest-brass-normal',512,512,alpha=False);normal_image.colorspace_settings.name='Non-Color';normal_tex=nodes.new('ShaderNodeTexImage');normal_tex.image=normal_image;nodes.active=normal_tex
  bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT',margin=8)
  nodes.remove(bump);normal_map=nodes.new('ShaderNodeNormalMap');links.new(normal_tex.outputs['Color'],normal_map.inputs['Color']);links.new(normal_map.outputs['Normal'],shader.inputs['Normal'])
  normal_image.filepath_raw=str((out/'crest-brass-normal.png').resolve());normal_image.file_format='PNG';normal_image.save();normal_image.pack()
 if name in ('menpo-lacquer','menpo-brass'):
  # Shared full-tile roughness, baked in linear data space and embedded in GLB.
  rough_image=bpy.data.images.new(name+'-roughness',512,512,alpha=False);rough_image.colorspace_settings.name='Non-Color'
  rough_texture=nodes.new('ShaderNodeTexImage');rough_texture.image=rough_image;nodes.active=rough_texture
  low,high=(.47,.53) if name=='menpo-lacquer' else (.40,.48)
  ramp.color_ramp.elements[0].color=(low,low,low,1);ramp.color_ramp.elements[1].color=(high,high,high,1)
  links.new(emit.outputs[0],output.inputs['Surface']);bpy.ops.object.bake(type='EMIT',margin=8)
  links.new(shader.outputs[0],output.inputs['Surface']);links.new(rough_texture.outputs['Color'],shader.inputs['Roughness'])
  rough_image.filepath_raw=str((out/(name+'-roughness.png')).resolve());rough_image.file_format='PNG';rough_image.save();rough_image.pack()
 for node in [texcoord,noise,ramp,emit]:nodes.remove(node)
 image.filepath_raw=str((out/(name+'.png')).resolve());image.file_format='PNG';image.save();image.pack()
# Bake a complete shared tile: the nose and lip occupy different UV regions.
# Baking only the nose leaves unpainted black texels on the lower lip.
swatch=object_mesh('Temporary shared finish swatch',[(0,0,0),(1,0,0),(1,1,0),(0,1,0)],[(0,1,2,3)],nasal_material)
layer=swatch.data.uv_layers.new(name='Full tile UV')
for loop in swatch.data.loops:layer.data[loop.index].uv=swatch.data.vertices[loop.vertex_index].co.xy
bake_finish(swatch,nasal_material,'menpo-lacquer',[(.115,.0066,.0038),(.130,.0077,.0043)],110)
swatch.data.materials[0]=lower_brass
bake_finish(swatch,lower_brass,'menpo-brass',[(.26,.14,.040),(.34,.20,.065)],100)
bpy.data.objects.remove(swatch,do_unlink=True)
bake_finish(plate,lacquer,'crest-lacquer',[(.055,.004,.002),(.11,.010,.006)],85)
bake_finish(bpy.data.objects[coins[0]],brass,'crest-brass',[(.14,.065,.015),(.52,.31,.09)],115)
# Project original lacquer / wear onto the repair. Only the four obsolete coin
# color footprints are replaced with lacquer before baking; surrounding wear is
# sampled from the original UV material through the actual 3D surface.
def bake_projected_crest():
 m=original.copy();m.name='Temporary coin removal projection'
 nodes=m.node_tree.nodes;links=m.node_tree.links
 color=nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_socket
 geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0])
 def op(kind,a,b=None):
  n=nodes.new('ShaderNodeMath');n.operation=kind
  for index,value in enumerate([a,b]):
   if value is None:continue
   if isinstance(value,(int,float)):n.inputs[index].default_value=value
   else:links.new(value,n.inputs[index])
  return n.outputs[0]
 dx=op('SUBTRACT',op('ABSOLUTE',sep.outputs['X']),.12)
 dz=op('MINIMUM',op('ABSOLUTE',op('SUBTRACT',sep.outputs['Z'],1.11)),op('ABSOLUTE',op('SUBTRACT',sep.outputs['Z'],.98)))
 dist=op('SQRT',op('ADD',op('MULTIPLY',dx,dx),op('MULTIPLY',dz,dz)))
 fade=nodes.new('ShaderNodeMapRange');fade.clamp=True;fade.interpolation_type='SMOOTHERSTEP';links.new(dist,fade.inputs['Value']);fade.inputs['From Min'].default_value=.110;fade.inputs['From Max'].default_value=.135;fade.inputs['To Min'].default_value=1;fade.inputs['To Max'].default_value=0
 noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;links.new(geo.outputs['Position'],noise.inputs['Vector'])
 ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.035,.002,.001,1);ramp.color_ramp.elements[1].color=(.095,.007,.003,1);links.new(noise.outputs['Fac'],ramp.inputs[0])
 mix=nodes.new('ShaderNodeMixRGB');links.new(fade.outputs[0],mix.inputs[0]);links.new(color,mix.inputs[1]);links.new(ramp.outputs[0],mix.inputs[2])
 emit=nodes.new('ShaderNodeEmission');links.new(mix.outputs[0],emit.inputs['Color']);links.new(emit.outputs[0],nodes.get('Material Output').inputs['Surface'])
 crest_source.data.materials.clear();crest_source.data.materials.append(m)
 for f in crest_source.data.polygons:f.material_index=0
 target=next(n for n in lacquer.node_tree.nodes if n.type=='TEX_IMAGE');lacquer.node_tree.nodes.active=target
 bpy.ops.object.select_all(action='DESELECT');crest_source.select_set(True);plate.select_set(True);bpy.context.view_layer.objects.active=plate
 bpy.ops.object.bake(type='EMIT',use_selected_to_active=True,cage_extrusion=.18,max_ray_distance=.35,margin=8)
 target.image.filepath_raw=str((out/'crest-lacquer.png').resolve());target.image.save();target.image.pack()
 shader=lacquer.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.45;shader.inputs['Coat Weight'].default_value=.18
 bpy.data.objects.remove(crest_source,do_unlink=True)
bake_projected_crest()
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
report={'iteration':26,'lower_repair':lower_repair,'nasal_repair':nasal_repair,'mask_trim':mask_trim,'mask_rim':mask_rim,'removed_generated_skin_faces':removed_skin_count,'human_eyes':human_eyes,'socket_vertices_recessed':socket_count,'source':a.model,'normalization_scale':scale,'generated_source_preserved':True,'material_face_counts':material_counts,'visor_vertices_adjusted':int(brim.sum()),'crest_vertices_recessed':int(flatten.sum()),'removed_near_zero_faces':len(tiny),'coin_objects':coins,'coin_count':len(coins),'eye_landmarks':landmarks,'changes':['Rebuilt both cheek vent frames and central chin shield; shared baked lacquer/brass color and roughness','Rebuilt nasal shell with two through-cut nostrils and recessed backing; replaced broken upper-lip band','Clipped eye-opening triangles at a continuous contour with UV interpolation; rebuilt rolled menpo rim and return','Raised only front visor by up to 0.02 normalized units','Recessed incorrect four-coin relief and rebuilt six separate square-hole coins','Replaced procedural eye caps with licensed Rocketbox orbital skin and eye geometry','Separated lacquer, gold, cloth and skin material response','Baked independent crest lacquer and brass textures in Blender','Rebuilt thin six coins with raised outer rims, recessed faces and square-hole lips; flush helmet backing','Projected original helmet lacquer onto repair and baked coin micro-normal texture'],'limitations':['Artist-directed procedural edits, not hand-sculpted anatomical retopology','Eye appearance and anatomy inherited from Rocketbox; no independent gaze controls','Outer side jaw and helmet retain generated defects; repair parts are not welded into the full mask','No skeleton, weights or facial animation']}
(out/'refinement-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
