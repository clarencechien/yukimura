import {Scene} from '@babylonjs/core/scene';
import {Mesh} from '@babylonjs/core/Meshes/mesh';
import {MeshBuilder} from '@babylonjs/core/Meshes/meshBuilder';
import {StandardMaterial} from '@babylonjs/core/Materials/standardMaterial';
import {DynamicTexture} from '@babylonjs/core/Materials/Textures/dynamicTexture';
import {Vector3} from '@babylonjs/core/Maths/math.vector';
import {Color3} from '@babylonjs/core/Maths/math.color';
import {VertexBuffer} from '@babylonjs/core/Buffers/buffer';
import {VertexData} from '@babylonjs/core/Meshes/mesh.vertexData';
type Palette=Record<'snow'|'dirt'|'wood'|'dark'|'stone'|'crimson'|'gold',StandardMaterial>;
export function battlefield(scene:Scene,m:Palette){
 let seed=1614;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 const box=(n:string,p:Vector3,s:Vector3,mat:StandardMaterial)=>{const o=MeshBuilder.CreateBox(n,{size:1},scene);o.position=p;o.scaling=s;o.material=mat;return o;};
 function timber(a:Vector3,b:Vector3,r=.08){const d=b.subtract(a);const o=MeshBuilder.CreateCylinder('splintered timber',{height:d.length(),diameterBottom:r*2,diameterTop:r*1.4,tessellation:5},scene);o.position=a.add(b).scale(.5);const axis=Vector3.Cross(Vector3.Up(),d.normalize());const angle=Math.acos(Vector3.Dot(Vector3.Up(),d));if(axis.length()>.001)o.rotate(axis.normalize(),angle);o.material=m.wood;return o;}
 // One shared painted ground map: broad snow washes, muddy scumbles and wheel scars.
 const tex=new DynamicTexture('painted battlefield',{width:1024,height:1024},scene,false);
 const ctx=tex.getContext() as CanvasRenderingContext2D;ctx.fillStyle='#7b8586';ctx.fillRect(0,0,1024,1024);
 for(let i=0;i<18000;i++){
  const x=random()*1024,y=random()*1024,center=512+Math.sin(y*.018)*24;
  const route=Math.exp(-(((x-center)/140)**2));
  ctx.globalAlpha=.045+random()*.20;ctx.fillStyle=random()<route*.83?'#403b37':random()<.48?'#b6bab0':'#56676d';
  ctx.fillRect(x,y,2+random()*11,1+random()*3);
 }
 for(let i=0;i<25;i++){
  const x=420+random()*184;ctx.globalAlpha=.05;ctx.strokeStyle='#1e292d';ctx.lineWidth=.8+random()*2;ctx.beginPath();ctx.moveTo(x,0);ctx.bezierCurveTo(x-14,330,x+12,700,x+5,1024);ctx.stroke();
 }
 ctx.globalAlpha=1;tex.update();tex.uScale=1;tex.vScale=2;
 const soil=new StandardMaterial('ink washed snow and earth',scene);soil.diffuseColor=new Color3(.77,.79,.77);soil.diffuseTexture=tex;soil.specularColor=Color3.Black();
 const ground=MeshBuilder.CreateGround('churned battlefield',{width:100,height:210,subdivisions:96,updatable:true},scene);ground.position.z=80;ground.material=soil;
 const pos=ground.getVerticesData(VertexBuffer.PositionKind)!;
 for(let i=0;i<pos.length;i+=3){const x=pos[i],z=pos[i+2]+80;const outside=Math.max(0,Math.abs(x)-19)/12;pos[i+1]=-.035+Math.min(2,outside)*(.6+Math.sin(z*.21+x*.14)*.4)+Math.sin(x*1.13+z*.84)*.023;}
 ground.updateVerticesData(VertexBuffer.PositionKind,pos);const normals:number[]=[];VertexData.ComputeNormals(pos,ground.getIndices()!,normals);ground.updateVerticesData(VertexBuffer.NormalKind,normals);
 // Broken forward defenses: close silhouettes, irregular spacing, traversable central path.
 for(const side of [-1,1]){
  for(let section=0;section<13;section++){
   const z=section*13-8,x=side*(12+random()*5);
   for(let j=0;j<9;j++){
    const px=x+side*j*.40,pz=z+random()*.28,h=1.2+random()*2.1;
    timber(new Vector3(px,0,pz),new Vector3(px+random()*.30-.15,h,pz+.12),.09+random()*.025);
   }
   timber(new Vector3(x-.2,.72,z-.13),new Vector3(x+side*3.6,.85,z-.12),.075);
   if(section%2===0){timber(new Vector3(x,0,z-1),new Vector3(x+side*1.2,1.4,z+1),.085);timber(new Vector3(x,1.4,z-1),new Vector3(x+side*1.2,0,z+1),.085);}
  }
  // Dense but cheap distant spear lines read as an army through the fog.
  for(let i=0;i<160;i++){
   const x=side*(24+random()*16),z=random()*185-8,h=1.3+random()*.9;
   box('distant soldier',new Vector3(x,h*.5,z),new Vector3(.30,h,.25),m.dark);
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
  const beam=box('broken plank',new Vector3(x,.055,z),new Vector3(.16,.11,1+random()*2),m.wood);beam.rotation.y=angle;
  if(i%5===0){const wheel=MeshBuilder.CreateTorus('abandoned cart wheel',{diameter:1.25,thickness:.09,tessellation:12},scene);wheel.material=m.wood;wheel.position.set(x,.35,z);wheel.rotation.z=.75;for(let j=0;j<3;j++){const spoke=box('cart spoke',new Vector3(x,.35,z),new Vector3(1.12,.05,.05),m.wood);spoke.rotation.z=.75;spoke.rotation.y=j*Math.PI/3;}}
  if(i%3===0)timber(new Vector3(x,0,z),new Vector3(x+.35,1.7,z-.2),.026);
 }
 // Cloth silhouettes with actual torn hems, not rectangular signs.
 const flags:Mesh[]=[];
 for(let i=0;i<28;i++){
  const x=(i%2?1:-1)*(9.5+random()*9),z=i*6-7,h=3.5+random()*1.6;
  timber(new Vector3(x,0,z),new Vector3(x+.12,h,z),.05);
  const positions:number[]=[],indices:number[]=[];
  for(let row=0;row<8;row++)for(let col=0;col<4;col++)positions.push(col*.34, -row*.30+(row===7?(col%2)*.18:0),Math.sin(col*.9+row*.65)*.10);
  for(let r=0;r<7;r++)for(let c=0;c<3;c++){const n=r*4+c;indices.push(n,n+4,n+1,n+1,n+4,n+5);}
  const data=new VertexData();data.positions=positions;data.indices=indices;data.uvs=[];for(let row=0;row<8;row++)for(let col=0;col<4;col++)data.uvs.push(col/3,1-row/7);const ns:number[]=[];VertexData.ComputeNormals(positions,indices,ns);data.normals=ns;
  const flag=new Mesh('war torn sashimono',scene);data.applyToMesh(flag);flag.position.set(x,h-.12,z);flag.material=i<8?m.crimson:m.gold;flag.rotation.y=-.25;flags.push(flag);
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
 return (t:number)=>{for(const cloud of smoke){cloud.position.x=cloud.metadata.originX+Math.sin(t*.08+cloud.metadata.phase)*1.7;cloud.visibility=.7+Math.sin(t*.15+cloud.metadata.phase)*.2;}};
}
