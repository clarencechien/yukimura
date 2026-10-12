import {Scene} from '@babylonjs/core/scene';
import {Mesh} from '@babylonjs/core/Meshes/mesh';
import {MeshBuilder} from '@babylonjs/core/Meshes/meshBuilder';
import {StandardMaterial} from '@babylonjs/core/Materials/standardMaterial';
import {Material} from '@babylonjs/core/Materials/material';
import {weatheredMaterial} from './environment-materials';
import {groundDressing} from './ground-dressing';
import {DynamicTexture} from '@babylonjs/core/Materials/Textures/dynamicTexture';
import {Vector3} from '@babylonjs/core/Maths/math.vector';
import {Color3} from '@babylonjs/core/Maths/math.color';
import {VertexBuffer} from '@babylonjs/core/Buffers/buffer';
import {VertexData} from '@babylonjs/core/Meshes/mesh.vertexData';
type Palette=Record<'snow'|'dirt'|'wood'|'dark'|'stone'|'crimson'|'gold',Material>;
export function battlefield(scene:Scene,m:Palette){
 let seed=1614;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 const box=(n:string,p:Vector3,s:Vector3,mat:Material)=>{const o=MeshBuilder.CreateBox(n,{size:1},scene);o.position=p;o.scaling=s;o.material=mat;return o;};
 function timber(a:Vector3,b:Vector3,r=.08){const d=b.subtract(a);const o=MeshBuilder.CreateCylinder('splintered timber',{height:d.length(),diameterBottom:r*2,diameterTop:r*1.4,tessellation:5},scene);o.position=a.add(b).scale(.5);const axis=Vector3.Cross(Vector3.Up(),d.normalize());const angle=Math.acos(Vector3.Dot(Vector3.Up(),d));if(axis.length()>.001)o.rotate(axis.normalize(),angle);o.material=m.wood;return o;}
 // Offline painted albedo + height normals + spatial roughness for wet tracks.
 const soil=weatheredMaterial(scene,'terrain','churned snow and mud');
 const ground=MeshBuilder.CreateGround('churned battlefield',{width:100,height:210,subdivisions:96,updatable:true},scene);ground.position.z=80;ground.material=soil;
 const pos=ground.getVerticesData(VertexBuffer.PositionKind)!;
 for(let i=0;i<pos.length;i+=3){const x=pos[i],z=pos[i+2]+80;const outside=Math.max(0,Math.abs(x)-19)/12;pos[i+1]=-.035+Math.min(2,outside)*(.6+Math.sin(z*.21+x*.14)*.4)+Math.sin(x*1.13+z*.84)*.009;}
 ground.updateVerticesData(VertexBuffer.PositionKind,pos);const normals:number[]=[];VertexData.ComputeNormals(pos,ground.getIndices()!,normals);ground.updateVerticesData(VertexBuffer.NormalKind,normals);
 const {soilFoot,snowLip}=groundDressing(scene,m.snow,m.stone);
 // Wind pushes rounded, dirty snow lips against the defensive line.
 for(const side of [-1,1])for(let i=0;i<14;i++){
  const cx=side*(13+random()*5),cz=i*12-7;snowLip(cx,cz,1.8+random(),.9+random()*.5,.18+random()*.2);
 }
 // Broken forward defenses: close silhouettes, irregular spacing, traversable central path.
 for(const side of [-1,1]){
  for(let section=0;section<13;section++){
   const z=section*13-8,x=side*(12+random()*5);
   soilFoot(x+side*1.6,z,3,.9);snowLip(x+side*1.4,z+.40,2.1,.6,.17);
   for(let j=0;j<9;j++){
    const px=x+side*j*.40,pz=z+random()*.28,h=1.2+random()*2.1;
    timber(new Vector3(px,0,pz),new Vector3(px+random()*.30-.15,h,pz+.12),.09+random()*.025);
   }
   timber(new Vector3(x-.2,.72,z-.13),new Vector3(x+side*3.6,.85,z-.12),.075);
   if(section%2===0){timber(new Vector3(x,0,z-1),new Vector3(x+side*1.2,1.4,z+1),.085);timber(new Vector3(x,1.4,z-1),new Vector3(x+side*1.2,0,z+1),.085);}
  }
  // Dense but cheap distant spear lines read as an army through the fog.
  for(let i=0;i<160;i++){
   const x=side*(24+random()*16),z=random()*185-8,h=1.4+random()*.25;
   box('distant armour',new Vector3(x,h*.61,z),new Vector3(.42,h*.33,.28),m.dark);
   for(const leg of [-1,1])box('distant greave',new Vector3(x+leg*.13,h*.20,z),new Vector3(.13,h*.4,.16),m.dark);
   const hat=MeshBuilder.CreateCylinder('distant jingasa',{diameterTop:.05,diameterBottom:.52,height:.17,tessellation:6},scene);hat.position.set(x,h,z);hat.material=m.dark;
   box('distant face',new Vector3(x,h-.18,z-.02),new Vector3(.19,.22,.18),m.gold);
   timber(new Vector3(x+.25,0,z),new Vector3(x+.25,2.4+random(),z),.025);
  }
  // Skeletal trees instead of cones that resemble model-kit pines.
  for(let i=0;i<8;i++){
   const x=side*(21+random()*11),z=i*22-9,h=4+random()*3;
   timber(new Vector3(x,0,z),new Vector3(x+.4,h,z),.20);
   for(let j=0;j<4;j++){const y=2+j*.8;timber(new Vector3(x+.2,y,z),new Vector3(x+(j%2?1:-1)*(1.3+random()),y+1.3,z+random()),.065);}
  }
 }
 // Destroyed cart wheels, abandoned shields, splintered spars and embedded spears.
 for(let i=0;i<65;i++){
  const z=random()*171-9,x=(i%2?1:-1)*(7+random()*13),angle=random()*6.28;
  soilFoot(x,z,.9,1.4);
  const beam=box('broken plank',new Vector3(x,.055,z),new Vector3(.16,.11,1+random()*2),m.wood);beam.rotation.y=angle;
  if(i%5===0){const wheel=MeshBuilder.CreateTorus('abandoned cart wheel',{diameter:1.25,thickness:.09,tessellation:12},scene);wheel.material=m.wood;wheel.position.set(x,.35,z);wheel.rotation.z=.75;for(let j=0;j<3;j++){const spoke=box('cart spoke',new Vector3(x,.35,z),new Vector3(1.12,.05,.05),m.wood);spoke.rotation.z=.75;spoke.rotation.y=j*Math.PI/3;}}
  if(i%3===0)timber(new Vector3(x,0,z),new Vector3(x+.35,1.7,z-.2),.026);
 }
 for(const z of [6,43,88,138])for(const x of [-8.6,8.6])soilFoot(x,z,1.8,1.5);
 for(const z of [43,88,137])for(const x of [-7.8,7.8]){soilFoot(x,z,1.6,1.4);snowLip(x+.4,z+.4,.8,.6,.14);}
 // Cloth silhouettes with actual torn hems, not rectangular signs.
 const flags:Mesh[]=[];
 for(let i=0;i<28;i++){
  const x=(i%2?1:-1)*(9.5+random()*9),z=i*6-7,h=3.5+random()*1.6;
  timber(new Vector3(x,0,z),new Vector3(x+.12,h,z),.05);
  const positions:number[]=[],indices:number[]=[];
  for(let row=0;row<8;row++)for(let col=0;col<4;col++)positions.push(col*.34, -row*.30+(row===7?(col%2)*.18:0),Math.sin(col*.9+row*.65)*.10);
  for(let r=0;r<7;r++)for(let c=0;c<3;c++){const n=r*4+c;indices.push(n,n+4,n+1,n+1,n+4,n+5);}
  const data=new VertexData();data.positions=positions;data.indices=indices;data.uvs=[];for(let row=0;row<8;row++)for(let col=0;col<4;col++)data.uvs.push(col/3,1-row/7);const ns:number[]=[];VertexData.ComputeNormals(positions,indices,ns);data.normals=ns;
  const flag=new Mesh('war torn sashimono',scene);data.applyToMesh(flag,true);flag.metadata={keepDynamic:i%3===0,rest:[...positions],phase:i*.73};flag.position.set(x,h-.12,z);flag.material=i<8?m.crimson:m.gold;flag.rotation.y=-.25;if(i%3===0)flags.push(flag);
 }
 m.crimson.backFaceCulling=false;m.gold.backFaceCulling=false;
 // Soft smoke with an irregular painted edge. No expensive fluid simulation.
 const smokeTex=new DynamicTexture('smoke wash',{width:128,height:128},scene,false);
 const sc=smokeTex.getContext();sc.clearRect(0,0,128,128);
 for(let i=0;i<22;i++){
  const x=36+random()*56,y=36+random()*56,r=18+random()*25;
  const grad=sc.createRadialGradient(x,y,0,x,y,r);grad.addColorStop(0,'rgba(98,111,118,.18)');grad.addColorStop(1,'rgba(98,111,118,0)');sc.fillStyle=grad;sc.fillRect(0,0,128,128);
 }smokeTex.hasAlpha=true;smokeTex.update();
 const smokeMat=new StandardMaterial('smoke pigment',scene);smokeMat.diffuseTexture=smokeTex;smokeMat.useAlphaFromDiffuseTexture=true;smokeMat.disableLighting=true;smokeMat.emissiveColor=new Color3(.6,.64,.64);smokeMat.alpha=.52;smokeMat.backFaceCulling=false;
 const smoke:Mesh[]=[];
 for(let i=0;i<20;i++){const plane=MeshBuilder.CreatePlane('drifting gunsmoke',{size:1},scene);plane.position.set((i%2?1:-1)*(10+random()*15),2+random()*5,i*9-5);plane.scaling.set(12+random()*10,8+random()*5,1);plane.billboardMode=Mesh.BILLBOARDMODE_ALL;plane.material=smokeMat;plane.metadata={keepDynamic:true,originX:plane.position.x,phase:random()*6.28};plane.isPickable=false;smoke.push(plane);}
 let lastCloth=0;
 return (t:number)=>{if(t-lastCloth>1/24){lastCloth=t;for(const flag of flags){const pos=flag.metadata.rest.slice();for(let i=0;i<pos.length;i+=3){const loose=pos[i]/1.02;pos[i+2]+=loose*(.15*Math.sin(t*3.4+pos[i]*2.5+pos[i+1]*1.8+flag.metadata.phase)+.05*Math.sin(t*7+pos[i+1]*3));}flag.updateVerticesData(VertexBuffer.PositionKind,pos);const n:number[]=[];VertexData.ComputeNormals(pos,flag.getIndices()!,n);flag.updateVerticesData(VertexBuffer.NormalKind,n);}}for(const cloud of smoke){cloud.position.x=cloud.metadata.originX+Math.sin(t*.08+cloud.metadata.phase)*1.7;cloud.visibility=.7+Math.sin(t*.15+cloud.metadata.phase)*.2;}};
}
