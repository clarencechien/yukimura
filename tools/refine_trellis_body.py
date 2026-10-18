"""First full-body pass: reusable armor, fitted CC0 hands and shared finishes.
Run with the repository's Blender bpy environment. The game is not modified.
"""
import argparse,json,math,hashlib
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
from trellis_body_parts import mesh,panel,stud,cord,material,baked_finish,uv_world,REGIONS
p=argparse.ArgumentParser();p.add_argument('--output',default='docs/experiments/future-sanada/body-study/refined');a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
source=Path('docs/experiments/future-sanada/head-study/fitting/static-fit.glb')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
for o in list(bpy.context.scene.objects):
 if o.type=='MESH':
  transform=o.matrix_world.copy();o.parent=None;o.matrix_world=Matrix.Identity(4);o.data.transform(transform)
 else:bpy.data.objects.remove(o,do_unlink=True)
body=bpy.data.objects['Body with old head region removed'];body.name='Body retained cloth and hardware'
bm=bmesh.new();bm.from_mesh(body.data);bvh=BVHTree.FromBMesh(bm);bm.free()
def sample(x,z,side=-1):
 hit=bvh.ray_cast(Vector((x,side*2,z)),Vector((0,-side,0)))[0]
 return hit.y if hit is not None else side*.15

def fit_surface(x0,x1,z0,z1,side):
 xs=np.linspace(x0,x1,17);zs=np.linspace(z0,z1,13);coords=np.array([(x,z) for z in zs for x in xs]);u=coords[:,0];v=coords[:,1]-(z0+z1)/2;d=np.stack([np.ones_like(u),u,v,u*u,u*v,v*v],axis=1);target=np.array([sample(x,z,side) for x,z in coords]);weights=np.ones(len(target))
 for _ in range(4):
  c=np.linalg.lstsq(d*weights[:,None],target*weights,rcond=None)[0];r=abs(target-d@c);scale=max(.004,float(np.median(r))*1.48);weights=np.minimum(1,1.5*scale/np.maximum(r,1e-8))
 return lambda x,z:float(np.array([1,x,z-(z0+z1)/2,x*x,x*(z-(z0+z1)/2),(z-(z0+z1)/2)**2])@c)+side*.008

red=baked_finish('Body oxblood lacquer',(.115,.0065,.004),.51,0,out)
gold=baked_finish('Body aged brass',(.28,.16,.052),.47,.72,out)
leather=baked_finish('Body glove leather',(.014,.018,.021),.79,0,out,True)
cloth=material('Body indigo cloth',(.012,.018,.024),.94);silk=material('Body burgundy lacing',(.075,.008,.006),.87)
# Separate source material response using its existing UV colors.
original=body.data.materials[0];tex=next(n.image for n in original.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.image.colorspace_settings.name=='sRGB');pixels=np.empty(len(tex.pixels),np.float32);tex.pixels.foreach_get(pixels);pixels=pixels.reshape(tex.size[1],tex.size[0],4)
uv=np.array([l.uv[:] for l in body.data.uv_layers.active.data]);starts=np.array([p.loop_start for p in body.data.polygons]);centers_uv=np.array([uv[p.loop_start:p.loop_start+p.loop_total].mean(0) for p in body.data.polygons]);rgb=pixels[np.clip((centers_uv[:,1]*tex.size[1]).astype(int),0,tex.size[1]-1),np.clip((centers_uv[:,0]*tex.size[0]).astype(int),0,tex.size[0]-1),:3]
roles=[]
for name,metal,rough,coat in [('Body source lacquer',0,.57,.12),('Body source brass',.68,.51,0),('Body source cloth',0,.91,0),('Body source cord',0,.83,0)]:
 m=original.copy();m.name=name;shader=m.node_tree.nodes.get('Principled BSDF')
 for key,value in [('Metallic',metal),('Roughness',rough),('Coat Weight',coat)]:
  for link in list(shader.inputs[key].links):m.node_tree.links.remove(link)
  shader.inputs[key].default_value=value
 body.data.materials.append(m);roles.append(len(body.data.materials)-1)
r,g,b=rgb.T;classes=np.full(len(rgb),roles[2],np.int32);classes[(r>g*1.45)&(r>b*1.55)&(r>.07)]=roles[0];classes[(r>g*1.02)&(g>b*1.25)&(g>.08)&(classes==roles[2])]=roles[1]
for poly in body.data.polygons:
 c=poly.center
 if 1.015<c.z<1.115 and abs(c.x)<.24 and abs(c.y)>.115 and classes[poly.index]==roles[0]:classes[poly.index]=roles[3]
body.data.polygons.foreach_set('material_index',classes)
for slot,mat in zip(roles,[red,gold,cloth,silk]):body.data.materials[slot]=mat
del pixels,rgb,uv,centers_uv
# Audit the regions removed before rebuilding the body core below.
bm=bmesh.new();bm.from_mesh(body.data);remove=[];counts={}
for f in bm.faces:
 c=f.calc_center_median();x=abs(c.x);armor=f.material_index in roles[:2];region=None
 if f.calc_area()<1e-11:region='degenerate cleanup'
 elif x>.32 and .75<c.z<.973:region='hands'
 elif c.z<.030:region='soles'
 else:
  if x<.177 and 1.105<c.z<1.505 and abs(c.y)>.030:region='torso'
  elif x>.225 and 1.30<c.z<1.57:region='shoulders'
  elif x>.315 and .973<c.z<1.30:region='forearms'
  elif x<.335 and .635<c.z<1.115:region='waist'
  elif x>.08 and .135<c.z<.685:region='legs'
  elif c.z<.135:region='feet'
 if region:remove.append(f);counts[region]=counts.get(region,0)+1
bmesh.ops.delete(bm,geom=remove,context='FACES')
# Discard detached remnants produced by region cuts, not intentional new parts.
remaining=set(bm.faces);small=[]
while remaining:
 seed=remaining.pop();component={seed};queue=[seed]
 while queue:
  for e in queue.pop().edges:
   for face in e.link_faces:
    if face in remaining:remaining.remove(face);component.add(face);queue.append(face)
 if len(component)<35:small.extend(component)
counts['detached remnants']=len(small);bmesh.ops.delete(bm,geom=small,context='FACES');bm.to_mesh(body.data);bm.free()

# Replace the remaining ragged generated body core with continuous clothing.
# The unmodified source GLB remains the provenance and shape reference.
counts['remaining body core replaced']=len(body.data.polygons)
bpy.data.objects.remove(body,do_unlink=True)
front_fit=fit_surface(-.175,.175,1.11,1.50,-1);back_fit=fit_surface(-.175,.175,1.11,1.50,1)
def torso_core(u,v):
 z=1.095+.410*v;t=.02+(math.tau-.04)*u;rx=.182+.022*math.sin(math.pi*v);x=rx*math.sin(t)
 yf=front_fit(x,z)+.020;yb=back_fit(x,z)-.020
 return(x,(yf+yb)/2-(yb-yf)/2*math.cos(t),z)
panel('Continuous torso cloth',torso_core,cloth,'torso',nu=65,nv=33)
panel('Neck cloth collar',lambda u,v:((.065+.010*(1-v))*math.sin(.02+(math.tau-.04)*u),.025-(.052+.008*(1-v))*math.cos(.02+(math.tau-.04)*u),1.49+.075*v),cloth,'torso',nu=49,nv=9)
for sign in [-1,1]:
 joint=stud('Shoulder cloth bridge '+str(sign),(0,0,0),cloth,'arms',1)
 for vertex in joint.data.vertices:
  vertex.co=Vector((sign*.214+vertex.co.x*.103,.050+vertex.co.y*.080,1.443+vertex.co.z*.105))
 joint.data.update();uv_world(joint)
 for side in [-1,1]:stud('Shoulder mount '+str(sign)+' '+str(side),(sign*.194,side*.139,1.487),gold,'shoulders',.010)
# Breast/back armor: separately formed lames with visible cloth gaps.
for side in [-1,1]:
 depth=fit_surface(-.175,.175,1.11,1.50,side)
 def torso_fn(u,v,z0=1.105,z1=1.51,w=.181):
  x=(2*u-1)*w;z=z0+(z1-z0)*v;return (x,depth(x,z)-side*.014,z)
 panel('Torso recessed lining '+str(side),torso_fn,cloth,'torso',thickness=.004)
 for row in range(6):
  z0=1.115+row*.061;z1=z0+.056;w=.157+.015*row/5
  def fn(u,v,z0=z0,z1=z1,w=w,side=side):
   # Small corner relief; no razor-thin collapsed grid corners.
   inset=.007*max(0,1-4*min(v,1-v));x=(2*u-1)*(w-inset);z=z0+(z1-z0)*v
   if side==1:x=-x
   return (x,depth(x,z),z)
  panel('Torso lame '+str(side)+' '+str(row),fn,red,'torso')
  cord('Torso lower rolled edge '+str(side)+' '+str(row),[fn(u,.06) for u in np.linspace(.04,.96,30)],gold,'torso',.0013)
  for u in [.07,.93]:
   pt=np.array(fn(u,.77));pt[1]+=side*.002;stud('Torso rivet '+str(side)+' '+str(row)+' '+str(u),pt,gold,'torso',.0028)
# Shoulder sode: four overlapping curved lames on each side, front-to-back wrap.
for sign in [-1,1]:
 for row in range(4):
  z0=1.322+row*.053;z1=z0+.057
  def shoulder(u,v,z0=z0,z1=z1,sign=sign):
   z=z0+(z1-z0)*v;t=(1.54-z)/.22;theta=-1.80+3.60*u;cx=.265+.24*(1.54-z);rx=.065+.020*t;ry=.118+.025*t
   return (sign*(cx+rx*math.cos(theta)),.025+ry*math.sin(theta),z-.035*math.cos(theta))
  panel('Shoulder sode '+str(sign)+' '+str(row),shoulder,red,'shoulders',nu=33)
  cord('Shoulder rolled hem '+str(sign)+' '+str(row),[shoulder(u,.025) for u in np.linspace(.02,.98,40)],gold,'shoulders',.0018)
  for u in [.12,.32,.68,.88]:
   pt=shoulder(u,.8);stud('Shoulder fastener '+str(sign)+' '+str(row)+' '+str(u),pt,gold,'shoulders',.003)
   cord('Shoulder lacing '+str(sign)+' '+str(row)+' '+str(u),[shoulder(u,v) for v in [.55,.9,1.]],silk,'shoulders',.0016)
 # Curved upper cap and underlying sleeve connect sode to the shoulder.
 def shoulder_cap(u,v,sign=sign):
  theta=-1.8+3.6*u;r=.12+.88*v
  return(sign*(.265+.070*r*math.cos(theta)),.025+.120*r*math.sin(theta),1.553-.04*r*r)
 panel('Shoulder crown '+str(sign),shoulder_cap,red,'shoulders',nu=33,nv=13)
 def sleeve(u,v,sign=sign):
  z=1.278+.192*v;theta=.02+(math.tau-.04)*u
  # Meet the forearm lining at the elbow, then narrow inside the sode.
  lower_t=(1.278-.970)/.290;blend=min(1,v/.23)
  cx=sign*((.405-.050*lower_t)*(1-v)+.277*v)
  cy=(-.020+.097*lower_t)*(1-blend)+.025*blend
  rx=(.039+.022*lower_t-.004)*(1-blend)+(.040+.003*v)*blend
  ry=(.043+.023*lower_t-.004)*(1-blend)+(.050+.008*v)*blend
  return(cx+rx*math.sin(theta),cy-ry*math.cos(theta),z)
 panel('Upper arm cloth '+str(sign),sleeve,cloth,'arms',nu=49,nv=13)
# Elbow/forearm: use the actual sloped forearm center, leaving wrist movement space.
for sign in [-1,1]:
 def arm(z):
  t=(z-.97)/.29;return sign*(.405-.050*t),-.020+.097*t,.039+.022*t,.043+.023*t
 def arm_lining(u,v):
  z=.970+.310*v;cx,cy,rx,ry=arm(z);t=.02+(math.tau-.04)*u
  return(cx+(rx-.004)*math.sin(t),cy-(ry-.004)*math.cos(t),z)
 panel('Forearm cloth '+str(sign),arm_lining,cloth,'arms',nu=49,nv=21)
 for col in range(5):
  start=-math.pi+col*math.tau/5+.035;end=start+math.tau/5-.07
  def bracer(u,v,start=start,end=end):
   z=.982+.235*v;cx,cy,rx,ry=arm(z);theta=start+(end-start)*u
   return (cx+rx*math.sin(theta),cy-ry*math.cos(theta),z)
  panel('Forearm splint '+str(sign)+' '+str(col),bracer,red,'arms',nv=21)
  cord('Forearm fine border '+str(sign)+' '+str(col),[bracer(.04,v) for v in np.linspace(.03,.97,18)],gold,'arms',.0011)
 for k,z in enumerate([.991,1.185]):
  def cuff(u,v,z=z):
   zz=z+(v-.5)*.016;cx,cy,rx,ry=arm(zz);t=.02+(math.tau-.04)*u;return(cx+(rx+.004)*math.sin(t),cy-(ry+.004)*math.cos(t),zz)
  panel('Forearm cuff '+str(sign)+' '+str(k),cuff,leather,'arms',nu=49,nv=3)
 # Separate elbow cap with smooth rounded volume, around the original joint.
 cx,cy,rx,ry=arm(1.245)
 panel('Elbow shield '+str(sign),lambda u,v,cx=cx,cy=cy:(cx+(.043-.014*abs(2*v-1)**4)*(2*u-1),cy-.086+.020*(2*u-1)**2-.003*(1-(2*v-1)**2),1.208+.070*v),red,'arms')
# Continuous hip lining, waist belt and authored knot replace the torn source belt.
panel('Hip indigo lining',lambda u,v:((.200+.055*(1-v))*math.sin(.02+(math.tau-.04)*u),-(.138+.045*(1-v))*math.cos(.02+(math.tau-.04)*u),.635+.475*v),cloth,'waist',nu=65,nv=25)
for k,z in enumerate([1.044,1.075]):
 cord('Waist braided cord '+str(k),[(.222*math.sin(t),-.166*math.cos(t),z+.003*math.sin(16*t)) for t in np.linspace(.025,math.tau-.025,160)],silk,'waist',.008)
for sign in [-1,1]:
 cord('Waist knot loop '+str(sign),[(0,-.179,1.060),(sign*.045,-.194,1.08),(sign*.074,-.185,1.06),(sign*.045,-.198,1.035),(0,-.188,1.06)],silk,'waist',.007)
 cord('Waist knot tail '+str(sign),[(sign*.008,-.190,1.05),(sign*.024,-.205,1.005),(sign*.020,-.216,.955)],silk,'waist',.007)
# Eight skirt sectors, each with four staggered lames and paired lacing.
for sector in range(8):
 angle=sector*math.tau/8
 for row in range(4):
  z0=.659+row*.084;z1=z0+.080
  def skirt(u,v,angle=angle,z0=z0,z1=z1):
   z=z0+(z1-z0)*v;t=(1.01-z)/.35;theta=angle+(u-.5)*.68
   return ((.210+.070*t)*math.sin(theta),-(.147+.058*t)*math.cos(theta),z)
  panel('Skirt sector '+str(sector)+' lame '+str(row),skirt,red,'waist')
  cord('Skirt hem '+str(sector)+' '+str(row),[skirt(u,.035) for u in np.linspace(.04,.96,22)],gold,'waist',.0013)
  for u in [.22,.78]:
   stud('Skirt stud '+str(sector)+' '+str(row)+' '+str(u),skirt(u,.82),gold,'waist',.0026)
   cord('Skirt silk '+str(sector)+' '+str(row)+' '+str(u),[skirt(u,v) for v in [.65,.88,1]],silk,'waist',.0015)
# Leg centers are not mirrored: keep the source's asymmetric standing pose.
for sign in [-1,1]:
 def leg(z,sign=sign):
  t=(z-.14)/.28
  bulge=math.sin(math.pi*max(0,min(1,t)))
  return ((-.237+.040*t) if sign==-1 else (.302-.070*t)),(.078-.012*t if sign==-1 else .002+.005*t),.047+.020*t+.006*bulge,.052+.034*t+.010*bulge
 def leg_lining(u,v):
  z=.130+.555*v;cx,cy,rx,ry=leg(z);t=.02+(math.tau-.04)*u
  wrinkle=.0014*math.sin(z*115+t*3)*math.sin(t)**2
  return(cx+(rx-.003+wrinkle)*math.sin(t),cy-(ry-.003+wrinkle)*math.cos(t),z)
 panel('Leg indigo lining '+str(sign),leg_lining,cloth,'legs',nu=49,nv=33)
 def knee(u,v):
  z=.425+.150*v;cx,cy,rx,ry=leg(z)
  w=min(.069,rx*.93)-.014*abs(2*v-1)**4;x=cx+(2*u-1)*w
  # Fit the reconstructed trouser volume, not the discarded neural surface.
  y=cy-(ry-.003)*math.sqrt(max(.01,1-((x-cx)/(rx-.003))**2))-.007
  return(x,y,z)
 panel('Knee shield '+str(sign),knee,red,'legs',nu=25,nv=19)
 cord('Knee lower rim '+str(sign),[knee(u,.035) for u in np.linspace(.06,.94,25)],gold,'legs',.002)
 for u in [.1,.9]:stud('Knee fastener '+str(sign)+' '+str(u),knee(u,.55),gold,'legs',.0035)
 for col in range(3):
  angle=(col-1)*.90
  def shin(u,v,angle=angle):
   z=.145+.267*v;cx,cy,rx,ry=leg(z);theta=angle+(u-.5)*.83
   return(cx+rx*math.sin(theta),cy-ry*math.cos(theta),z)
  panel('Shin splint '+str(sign)+' '+str(col),shin,red,'legs',nv=25)
  cord('Shin vertical edge '+str(sign)+' '+str(col),[shin(.04,v) for v in np.linspace(.03,.97,25)],gold,'legs',.0013)
 for k,z in enumerate([.182,.364]):
  def strap(u,v,z=z):
   zz=z+(v-.5)*.019;cx,cy,rx,ry=leg(zz);t=.02+(math.tau-.04)*u
   return(cx+(rx+.006)*math.sin(t),cy-(ry+.006)*math.cos(t),zz)
  panel('Calf strap '+str(sign)+' '+str(k),strap,leather,'legs',nu=49,nv=3)
  for u in [.09,.91]:stud('Calf buckle '+str(sign)+' '+str(k)+' '+str(u),strap(u,.5),gold,'legs',.0035)
# Boots: shaped rubber soles, instep plates, ankle cuff and sole tread blocks.
for sign in [-1,1]:
 cx=-.237 if sign==-1 else .302;cy=.078 if sign==-1 else .002;angle=sign*.42;c=math.cos(angle);s=math.sin(angle)
 def foot(x,y,z,cx=cx,cy=cy,c=c,s=s):return(cx+c*x-s*y,cy+s*x+c*y,z)
 outline=[(-.045,.065),(.045,.065),(.066,-.03),(.073,-.135),(.048,-.185),(-.048,-.185),(-.073,-.135),(-.066,-.03)]
 from trellis_lower_mask import boundary
 curve=boundary(outline,8);vs=[foot(x,y,z) for z in [.007,.032] for x,y in curve];n=len(curve);fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
 for i in range(n):fs.append((i,(i+1)%n,(i+1)%n+n,i+n))
 sole=mesh('Boot sole '+str(sign),vs,fs,leather,'feet');uv_world(sole)
 def boot_height(x,y):
  t=(y+.185)/.25
  return .060+.045*t+.018*(1-(x/.073)**2)
 def boot_upper(u,v):
  y=-.182+.245*v+.010*(2*u-1)**2*(1-2*v);w=.049+.021*math.sin(math.pi*v);x=(u-.5)*2*w
  return foot(x,y,boot_height(x,y))
 upper=panel('Boot leather upper '+str(sign),boot_upper,leather,'feet',nu=25,nv=33)
 # Extend the inner surface to the sole, producing a closed solid shoe volume.
 count=len(upper.data.vertices)//2
 for vertex in list(upper.data.vertices)[count:]:vertex.co.z=.029
 upper.data.update()
 for row in range(3):
  y0=-.170+row*.047;y1=y0+.044
  def toe(u,v,y0=y0,y1=y1):
   x=(u-.5)*.116;y=y0+(y1-y0)*v;z=boot_height(x,y)+.005
   return foot(x,y,z)
  panel('Boot instep lame '+str(sign)+' '+str(row),toe,red,'feet')
  cord('Boot instep edge '+str(sign)+' '+str(row),[toe(u,.04) for u in np.linspace(.05,.95,25)],gold,'feet',.0012)
 for row,y in enumerate([-.143,-.087,-.031,.025]):
  verts=[foot(x,yy,z) for z in [0,.009] for x,yy in [(-.047,y-.016),(.047,y-.016),(.047,y+.016),(-.047,y+.016)]];faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)];o=mesh('Boot tread '+str(sign)+' '+str(row),verts,faces,leather,'feet');uv_world(o)
 def ankle(u,v):
  t=.02+(math.tau-.04)*u;return foot(.048*math.sin(t),.049*math.cos(t),.111+.026*v)
 panel('Boot ankle collar '+str(sign),ankle,leather,'feet',nu=49,nv=5)
# CC0 anatomical hands from the existing pinned hand study, evaluated once.
hand_source=Path('assets/cinema/open-hand-study.blend');hand_sha=hashlib.sha256(hand_source.read_bytes()).hexdigest()
provenance=json.loads(Path('assets/vendor/mpfb/provenance.json').read_text())
for item in provenance['files']:assert hashlib.sha256((Path('assets/vendor/mpfb')/item['file']).read_bytes()).hexdigest()==item['sha256']
previous=set(bpy.data.objects)
with bpy.data.libraries.load(str(hand_source.resolve())) as (src,dst):dst.objects=[n for n in src.objects if n in ['MPFB right hand — CC0 anatomy base','Open hand rig']]
for o in dst.objects:
 if o and o.name not in bpy.context.scene.objects:bpy.context.collection.objects.link(o)
bpy.context.scene.frame_set(14);hand=bpy.data.objects['MPFB right hand — CC0 anatomy base'];hand.modifiers['anatomical surface smoothing'].levels=1;bpy.context.view_layer.update()
e=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());data=bpy.data.meshes.new_from_object(e);bm=bmesh.new();bm.from_mesh(data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,-.035,0),plane_no=(0,1,0),clear_inner=True)
boundary_edges=[e for e in bm.edges if e.is_boundary];bmesh.ops.holes_fill(bm,edges=boundary_edges,sides=0);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(data);bm.free()
hand_verts=[v.co.copy() for v in data.vertices];hand_faces=[tuple(p.vertices) for p in data.polygons]
bm=bmesh.new();bm.from_mesh(data);hand_bvh=BVHTree.FromBMesh(bm);bm.free()
rig=bpy.data.objects['Open hand rig'];finger_tips={str(i):list(rig.pose.bones[f'finger{i}-3.R'].tail) for i in range(1,6)}
hand_landmarks={}
for o in set(bpy.data.objects)-previous:bpy.data.objects.remove(o,do_unlink=True)
for sign in [-1,1]:
 basis=Matrix(((-sign,0,0),(0,-.15,-.988686),(0,-.988686,.15)));wrist=Vector((sign*.405,-.020,.966))
 hand_landmarks[str(sign)]={i:list(wrist+basis@Vector((v[0]*1.12,v[1],v[2]*1.10))*.85) for i,v in finger_tips.items()}
 verts=[wrist+basis@Vector((v.x*1.12,v.y,v.z*1.10))*.85 for v in hand_verts];o=mesh('CC0 anatomical glove '+str(sign),verts,hand_faces,leather,'hands');uv_world(o);o['source_license']='CC0-1.0';o['source_commit']=provenance['commit']
 # Wrist transition is a fitted cuff; back-of-hand armor follows the open hand.
 def tekko(u,v,sign=sign,basis=basis,wrist=wrist):
  x=(u-.5)*(.061-.012*abs(2*v-1)**4);y=.012+.062*v
  hit=hand_bvh.ray_cast(Vector((x,y,-1)),Vector((0,0,1)))[0];z=(hit.z if hit else -.014)-.003
  return wrist+basis@Vector((x*1.12,y,z*1.10))*.85
 panel('Hand back armor '+str(sign),tekko,red,'hands',nu=17,nv=13,thickness=.003)
 cord('Hand back edge '+str(sign),[tekko(u,.95) for u in np.linspace(.05,.95,20)],gold,'hands',.001)
# Remove unused imported source objects; export static meshes only, all textures packed.
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
 if o.type=='MESH':o.select_set(True)
for im in bpy.data.images:
 if im.type=='IMAGE' and im.size[0]>0 and not im.packed_file:im.pack()
bpy.context.scene.frame_set(1)
bpy.ops.export_scene.gltf(filepath=str((out/'body-refined.glb').resolve()),export_format='GLB',use_selection=True)
bpy.ops.wm.save_as_mainfile(filepath=str((out/'body-refined.blend').resolve()),compress=True)
# Batch shared material/region meshes in the inspection copy; retain editable
# individual plates in the saved Blender source, without reducing hand geometry.
preview_groups=[]
for region,names in REGIONS.items():
 groups={}
 for name in names:
  ob=bpy.data.objects[name];groups.setdefault(ob.data.materials[0].name,[]).append(ob)
 for matname,objects in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for ob in objects:ob.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='Preview '+region+' '+matname
  preview_groups.append({'name':ob.name,'region':region,'parts':len(objects)})
bpy.ops.object.select_all(action='SELECT')
for im in bpy.data.images:
 if im.type=='IMAGE' and max(im.size)>2048:im.scale(2048,2048);im.pack()
bpy.ops.export_scene.gltf(filepath=str((out/'body-preview.glb').resolve()),export_format='GLB',use_selection=True)
report={'iteration':9,'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'head_revision':'781952c / pass29 retained unchanged','device':'CPU','modal_calls':0,'removed_source_faces':counts,'regions':REGIONS,'preview_groups':preview_groups,'retained_source_body_geometry':False,'finger_tip_landmarks_blender':hand_landmarks,'hand_source':{'file':str(hand_source),'sha256':hand_sha,'asset_license':'CC0-1.0','upstream_commit':provenance['commit'],'pose_frame':14,'subdivision':1,'wrist_cut_canonical_y':-.035,'scale':.85},'shared_materials':[red.name,gold.name,leather.name],'limits':['First full-body static pass, not illustration-level final art','Overlapping independent armor and clothing shells; not welded into one body','No whole-character retopology, rig, skinning, collision or mobile FPS certification','Hands use a relaxed source pose, not a weapon-contact animation','Procedural finish tiles do not replace artist-authored wear maps','Live game unchanged']}
(out/'refinement-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'regions':{k:len(v) for k,v in REGIONS.items()},'removed':counts}))
