import {Scene} from '@babylonjs/core/scene';
import {Mesh} from '@babylonjs/core/Meshes/mesh';
import {MeshBuilder} from '@babylonjs/core/Meshes/meshBuilder';
import {VertexData} from '@babylonjs/core/Meshes/mesh.vertexData';
import {StandardMaterial} from '@babylonjs/core/Materials/standardMaterial';
import {Vector3} from '@babylonjs/core/Maths/math.vector';
import {Color3} from '@babylonjs/core/Maths/math.color';
import {Engine} from '@babylonjs/core/Engines/engine';

type Effect={mesh:Mesh,life:number,total:number,velocity:Vector3,grow:number,spin:number};
/** Bounded short-lived geometry, shared shaders, no full-screen bloom on mobile. */
export class CombatFX {
 private warming=false;private effects:Effect[]=[];private gold:StandardMaterial;private red:StandardMaterial;private dust:StandardMaterial;
 constructor(private scene:Scene,private reduced=false){
  const make=(name:string,hex:string,add=true)=>{const m=new StandardMaterial(name,scene);m.diffuseColor=Color3.FromHexString(hex);m.emissiveColor=m.diffuseColor.scale(add?1:.25);m.disableLighting=add;m.specularColor=Color3.Black();m.backFaceCulling=false;m.alpha=.85;if(add)m.alphaMode=Engine.ALPHA_ADD;return m;};
  this.gold=make('spear ivory','#ffd7a1');this.red=make('crimson wake','#df3645');this.dust=make('snow impact','#b8b9ab',false);
 }
 async warmup(){
  // Compile the exact arc/particle shader variants before the first strike.
  this.warming=true;const origin=new Vector3(0,-100,0);this.arc(origin,0,1,2);this.impact(origin);this.dustKick(origin,1);
  const meshes=this.effects.map(e=>e.mesh);for(const mesh of meshes)mesh.isVisible=false;
  try{await Promise.all(meshes.map(mesh=>(mesh.material as StandardMaterial).forceCompilationAsync(mesh)));}
  finally{this.clear();this.warming=false;}
 }
 private add(mesh:Mesh,life:number,velocity=Vector3.Zero(),grow=0,spin=0){
  const cap=this.reduced?40:96;
  if(this.effects.length>=cap)this.effects.shift()!.mesh.dispose();
  mesh.isPickable=false;this.effects.push({mesh,life,total:life,velocity,grow,spin});
 }
 arc(pos:Vector3,yaw:number,radius:number,span:number,reverse=false,ultimate=false){
  // Tapered two-tone blade wake. Vertices follow the same attack sector as damage.
  for(let layer=0;layer<2;layer++){
   const mesh=new Mesh('spear wake',this.scene),data=new VertexData();const positions:number[]=[],indices:number[]=[],colors:number[]=[];
   const segments=36;
   for(let i=0;i<=segments;i++){
    const t=i/segments,a=yaw+(t-.5)*span,r=radius*(layer?.91:1),width=(.12+.58*Math.sin(t*Math.PI))*(layer?.25:1);
    for(let edge=0;edge<2;edge++){
     const rr=r-(edge?width:0);positions.push(Math.sin(a)*rr,1.0+Math.sin(a-yaw)*.22,Math.cos(a)*rr);
     colors.push(1,1,1,Math.sin(t*Math.PI)*(edge?.15:.95));
    }
    if(i<segments){const k=i*2;indices.push(k,k+1,k+2,k+1,k+3,k+2);}
   }
   data.positions=positions;data.indices=indices;data.colors=colors;data.normals=[];VertexData.ComputeNormals(positions,indices,data.normals);data.applyToMesh(mesh);mesh.hasVertexAlpha=true;mesh.material=layer?this.gold:this.red;mesh.position.copyFrom(pos);
   this.add(mesh,ultimate?.42:.24,Vector3.Zero(),.25,(reverse?-1:1)*(ultimate?2:.65));
  }
 }
 thrust(pos:Vector3,yaw:number,length:number){
  const dir=new Vector3(Math.sin(yaw),0,Math.cos(yaw));
  for(let i=0;i<3;i++){const m=MeshBuilder.CreateBox('thrust streak',{width:i===0?.10:.04,height:.06,depth:length},this.scene);m.material=i===0?this.gold:this.red;m.rotation.y=yaw;m.position.copyFrom(pos.add(dir.scale(length*.55)));m.position.y=1.3+i*.18;this.add(m,.18,dir.scale(6));}
 }
 impact(pos:Vector3,heavy=false){
  for(let i=0;i<(this.reduced?3:6);i++){
   const a=i*Math.PI/3+.3,v=new Vector3(Math.sin(a)*(heavy?7:4),2+Math.random()*3,Math.cos(a)*(heavy?7:4));
   const m=MeshBuilder.CreateBox('impact shard',{width:.04,height:.04,depth:heavy?.65:.35},this.scene);m.material=this.gold;m.position.copyFrom(pos);m.position.y+=1;m.rotation.set(Math.random(),a,.6);this.add(m,.20+Math.random()*.12,v);
  }
 }
 burst(pos:Vector3,radius:number){this.arc(pos,0,radius,Math.PI*2,false,true);this.arc(pos,Math.PI*.4,radius*.7,Math.PI*2,true,true);this.dustKick(pos,12);}
 dustKick(pos:Vector3,count=5){
  for(let i=0;i<(this.reduced?3:count);i++){const a=Math.random()*Math.PI*2;const m=MeshBuilder.CreateSphere('snow spray',{diameter:.15+Math.random()*.2,segments:3},this.scene);m.material=this.dust;m.position.copyFrom(pos);m.position.y=.12;this.add(m,.32+Math.random()*.15,new Vector3(Math.sin(a)*3,Math.random()*2,Math.cos(a)*3),1);}
 }
 update(dt:number){if(this.warming)return;for(let i=this.effects.length-1;i>=0;i--){const e=this.effects[i];e.life-=dt;if(e.life<=0){e.mesh.dispose();this.effects.splice(i,1);continue;}e.mesh.position.addInPlace(e.velocity.scale(dt));e.velocity.y-=dt*8;e.mesh.scaling.scaleInPlace(1+e.grow*dt);e.mesh.rotation.y+=e.spin*dt;e.mesh.visibility=Math.max(0,e.life/e.total);}}
 clear(){for(const e of this.effects)e.mesh.dispose();this.effects.length=0;}
 get count(){return this.effects.length;}
}
