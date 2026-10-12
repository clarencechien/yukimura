import {Scene} from '@babylonjs/core/scene';
import {Mesh} from '@babylonjs/core/Meshes/mesh';
import {MeshBuilder} from '@babylonjs/core/Meshes/meshBuilder';
import {VertexData} from '@babylonjs/core/Meshes/mesh.vertexData';
import {Material} from '@babylonjs/core/Materials/material';
import {PBRMaterial} from '@babylonjs/core/Materials/PBR/pbrMaterial';
import {Color3} from '@babylonjs/core/Maths/math.color';

/** Small shared surfaces, merged with static scenery. No per-prop textures or physics. */
export function groundDressing(scene:Scene,snow:Material,stone:Material){
 let seed=1620;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 const surface=(name:string,color:Color3,roughness:number)=>{const m=new PBRMaterial(name,scene);m.albedoColor=color;m.metallic=0;m.roughness=roughness;m.maxSimultaneousLights=4;return m;};
 const contact=surface('thawed earth at object feet',new Color3(.13,.10,.073),.94);contact.alpha=.38;
 const water=surface('dark meltwater in wheel ruts',new Color3(.075,.085,.085),.27);water.environmentIntensity=.75;water.alpha=.82;
 const ice=surface('broken dirty ice crust',new Color3(.25,.30,.32),.50);ice.environmentIntensity=.5;
 const grass=surface('winter straw',new Color3(.26,.20,.12),.98);grass.backFaceCulling=false;
 function patch(name:string,x:number,z:number,rx:number,rz:number,mat:Material,fade=false){
  const positions=[x,fade?.007:.014,z],colors=[1,1,1,1],indices:number[]=[],uvs=[.5,.5];
  const count=18,phase=random()*6.28;
  for(let i=0;i<=count;i++){
   const a=i/count*Math.PI*2,r=1+Math.sin(a*3+phase)*.14+Math.cos(a*7+phase)*.06;
   positions.push(x+Math.cos(a)*rx*r,fade?.007:.014,z+Math.sin(a)*rz*r);colors.push(1,1,1,fade?0:1);uvs.push(.5+Math.cos(a)*.5,.5+Math.sin(a)*.5);
   if(i<count)indices.push(0,i+1,i+2);
  }
  const data=new VertexData();data.positions=positions;data.indices=indices;data.uvs=uvs;data.colors=colors;data.normals=[];VertexData.ComputeNormals(positions,indices,data.normals);
  const mesh=new Mesh(name,scene);data.applyToMesh(mesh);mesh.material=mat;mesh.hasVertexAlpha=fade;return mesh;
 }
 const soilFoot=(x:number,z:number,rx=1.3,rz=.8)=>patch('embedded dirt and contact wash',x,z,rx,rz,contact,true);
 function snowLip(x:number,z:number,rx:number,rz:number,height:number){
  const p:number[]=[],uv:number[]=[],c:number[]=[],idx:number[]=[],count=20,phase=random()*6.28;
  // Three rounded rings with a dirty thin outer lip, rather than a pointed cone.
  for(let ring=0;ring<4;ring++)for(let i=0;i<=count;i++){
   const a=i/count*Math.PI*2,r=[.01,.40,.74,1][ring]*(1+.13*Math.sin(a*3+phase)+.05*Math.cos(a*7));
   p.push(x+Math.cos(a)*rx*r,[-.015+height,height*.78,height*.30,-.025][ring],z+Math.sin(a)*rz*r);
   uv.push((x+Math.cos(a)*rx*r)/4,(z+Math.sin(a)*rz*r)/4);
   const tint=[1,.99,.91,.72][ring];c.push(tint,tint,tint*.99,1);
   if(ring<3&&i<count){const a=ring*(count+1)+i,b=a+count+1;idx.push(a,b,b+1,a,b+1,a+1);}
  }
  const data=new VertexData();data.positions=p;data.indices=idx;data.uvs=uv;data.colors=c;data.normals=[];VertexData.ComputeNormals(p,idx,data.normals);
  const mesh=new Mesh('wind sculpted snow lip',scene);data.applyToMesh(mesh);mesh.material=snow;
 }
 for(let i=0;i<42;i++){
  const z=-12+i*4.6+random()*2,x=1.9*Math.sin(z*.08)+(i%2?1.25:-1.25),rx=.18+random()*.30,rz=.5+random()*1.25;
  soilFoot(x,z,rx*1.9,rz*1.2);patch('irregular thawed wheel rut',x,z,rx,rz,water,true).position.y=.004;
  // Cracked plates at the margin catch a different, duller reflection.
  for(let j=0;j<3;j++){
   const chip=MeshBuilder.CreateCylinder('broken ice plate',{diameter:.13+random()*.24,height:.016,tessellation:5},scene);
   chip.position.set(x+(j%2?1:-1)*rx*.8,.025,z+(random()-.5)*rz*1.5);chip.scaling.z=.6+random();chip.rotation.y=random()*6.28;chip.material=ice;
  }
 }
 for(let i=0;i<140;i++){
  const z=-12+random()*181,x=(i%2?1:-1)*(5+random()*13);
  const rock=MeshBuilder.CreateIcoSphere('half buried rubble',{radius:.13+random()*.18,subdivisions:1},scene);
  rock.position.set(x,.025,z);rock.scaling.set(1,.35+random()*.4,.6+random()*.7);rock.rotation.y=random()*6.28;rock.material=stone;
  if(i%3===0){soilFoot(x,z,.55,.5);snowLip(x-.1,z+.12,.5,.37,.08+random()*.05);}
 }
 // Bent, crossed straw blades, sparsely placed on the flanks; one merged draw.
 const p:number[]=[],idx:number[]=[],uv:number[]=[];
 for(let i=0;i<85;i++){
  const x=(i%2?1:-1)*(7+random()*12),z=-12+random()*181;
  for(let j=0;j<5;j++){
   const angle=random()*6.28,w=.024,h=.18+random()*.42,bend=.08+random()*.14,n=p.length/3;
   const bx=x+(random()-.5)*.3,bz=z+(random()-.5)*.3,dx=Math.cos(angle),dz=Math.sin(angle);
   p.push(bx-w*dx,0,bz-w*dz,bx+w*dx,0,bz+w*dz,bx+bend,h,bz+.05);uv.push(0,0,1,0,.5,1);idx.push(n,n+1,n+2);
  }
 }
 const data=new VertexData();data.positions=p;data.indices=idx;data.uvs=uv;data.normals=[];VertexData.ComputeNormals(p,idx,data.normals);
 const straw=new Mesh('bent winter grass',scene);data.applyToMesh(straw);straw.material=grass;
 return {soilFoot,snowLip};
}
