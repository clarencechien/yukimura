import {Scene} from '@babylonjs/core/scene';
import {Mesh} from '@babylonjs/core/Meshes/mesh';
import {MeshBuilder} from '@babylonjs/core/Meshes/meshBuilder';
import {VertexData} from '@babylonjs/core/Meshes/mesh.vertexData';
import {StandardMaterial} from '@babylonjs/core/Materials/standardMaterial';
import {Vector3} from '@babylonjs/core/Maths/math.vector';
import {Color3} from '@babylonjs/core/Maths/math.color';
import {DynamicTexture} from '@babylonjs/core/Materials/Textures/dynamicTexture';
import {PointLight} from '@babylonjs/core/Lights/pointLight';
import {Engine} from '@babylonjs/core/Engines/engine';

type Effect={mesh:Mesh,life:number,total:number,velocity:Vector3,grow:number,spin:number,gravity:number};
/** Bounded short-lived geometry, shared shaders, no full-screen bloom on mobile. */
export class CombatFX {
 private warming=false;private effects:Effect[]=[];private gold:StandardMaterial;private red:StandardMaterial;private dust:StandardMaterial;private ink:StandardMaterial;private flash:PointLight;
 constructor(private scene:Scene,private reduced=false){
  const make=(name:string,hex:string,add=true)=>{const m=new StandardMaterial(name,scene);m.diffuseColor=Color3.FromHexString(hex);m.emissiveColor=m.diffuseColor.scale(add?1:.25);m.disableLighting=add;m.specularColor=Color3.Black();m.backFaceCulling=false;m.alpha=.85;if(add)m.alphaMode=Engine.ALPHA_ADD;return m;};
  this.gold=make('spear ivory','#ffd7a1');this.red=make('crimson wake','#df3645');this.dust=make('snow impact','#b8c6cc',false);this.ink=make('ink crimson edge','#591a28',false);
  const tex=new DynamicTexture('soft snow impact',64,scene,false),ctx=tex.getContext(),g=ctx.createRadialGradient(32,32,2,32,32,31);
  g.addColorStop(0,'rgba(255,255,255,.65)');g.addColorStop(.4,'rgba(255,255,255,.35)');g.addColorStop(1,'rgba(255,255,255,0)');ctx.fillStyle=g;ctx.fillRect(0,0,64,64);tex.hasAlpha=true;tex.update();
  this.dust.diffuseTexture=tex;this.dust.useAlphaFromDiffuseTexture=true;
  this.flash=new PointLight('spear reflected light',Vector3.Zero(),scene);this.flash.diffuse=new Color3(1,.27,.08);this.flash.range=6;this.flash.intensity=0;this.flash.renderPriority=95; // Keep the light slot compiled; zero intensity between hits.
 }
 async warmup(){
  // Compile the exact arc/particle shader variants before the first strike.
  this.warming=true;const origin=new Vector3(0,-100,0);this.arc(origin,0,1,2);this.impact(origin);this.dustKick(origin,1);this.charge(origin);this.thrust(origin,0,2);
  const meshes=this.effects.map(e=>e.mesh);for(const mesh of meshes)mesh.isVisible=false;
  try{await Promise.all(meshes.map(mesh=>(mesh.material as StandardMaterial).forceCompilationAsync(mesh)));}
  finally{this.clear();this.warming=false;}
 }
 private add(mesh:Mesh,life:number,velocity=Vector3.Zero(),grow=0,spin=0,gravity=0){
  const cap=this.reduced?40:96;
  if(this.effects.length>=cap)this.effects.shift()!.mesh.dispose();
  mesh.isPickable=false;this.effects.push({mesh,life,total:life,velocity,grow,spin,gravity});
 }
 arc(pos:Vector3,yaw:number,radius:number,span:number,reverse=false,ultimate=false){
  // Tapered ink, crimson and ivory blade wake. Vertices follow the same attack sector as damage.
  for(let layer=0;layer<3;layer++){
   const mesh=new Mesh('spear wake',this.scene),data=new VertexData();const positions:number[]=[],indices:number[]=[],colors:number[]=[];
   const segments=40;
   for(let i=0;i<=segments;i++){
    const t=i/segments,a=yaw+(t-.5)*span,r=radius*(layer===0?1.025:layer===1?1:.99),width=(.06+.63*Math.sin(t*Math.PI)**.7)*(layer===2?.14:1);
    for(let edge=0;edge<2;edge++){
     const rr=r-(edge?width:0);positions.push(Math.sin(a)*rr,1.15+Math.sin(a-yaw)*.40+(ultimate?.18*Math.sin(t*Math.PI*6):0),Math.cos(a)*rr);
     colors.push(1,1,1,Math.sin(t*Math.PI)*(edge?0:.95));
    }
    if(i<segments){const k=i*2;indices.push(k,k+1,k+2,k+1,k+3,k+2);}
   }
   data.positions=positions;data.indices=indices;data.colors=colors;data.normals=[];VertexData.ComputeNormals(positions,indices,data.normals);data.applyToMesh(mesh);mesh.hasVertexAlpha=true;mesh.material=layer===0?this.ink:layer===1?this.red:this.gold;mesh.position.copyFrom(pos);
   this.add(mesh,ultimate?.40:.23,Vector3.Zero(),.20,(reverse?-1:1)*(ultimate?1.4:.7));
  }
  this.light(pos,ultimate?2.4:1.1);
 }
 thrust(pos:Vector3,yaw:number,length:number){
  const dir=new Vector3(Math.sin(yaw),0,Math.cos(yaw));
  for(let i=0;i<3;i++){const m=MeshBuilder.CreateBox('thrust streak',{width:i===0?.10:.04,height:.06,depth:length},this.scene);m.material=i===0?this.gold:this.red;m.rotation.y=yaw;m.position.copyFrom(pos.add(dir.scale(length*.55)));m.position.y=1.3+i*.18;this.add(m,.18,dir.scale(6));}
 }
 impact(pos:Vector3,heavy=false){
  this.light(pos,heavy?2.2:1.2);
  for(let i=0;i<(this.reduced?3:6);i++){
   const a=i*Math.PI/3+.3,v=new Vector3(Math.sin(a)*(heavy?7:4),2+Math.random()*3,Math.cos(a)*(heavy?7:4));
   const m=MeshBuilder.CreateBox('impact shard',{width:.04,height:.04,depth:heavy?.65:.35},this.scene);m.material=this.gold;m.position.copyFrom(pos);m.position.y+=1;m.rotation.set(Math.random(),a,.6);this.add(m,.20+Math.random()*.12,v,0,0,9);
  }
 }
 private light(pos:Vector3,strength:number){if(this.warming||this.reduced)return;this.flash.position.copyFrom(pos).addInPlaceFromFloats(0,1.2,0);this.flash.intensity=Math.max(this.flash.intensity,strength);}
 private ring(pos:Vector3,radius:number,width:number,life:number,grow:number,red=true){
  const mesh=new Mesh('snow pressure ring',this.scene),data=new VertexData(),positions:number[]=[],colors:number[]=[],indices:number[]=[];
  for(let i=0;i<=64;i++){const a=i*Math.PI/32;for(let edge=0;edge<2;edge++){const r=radius-(edge?width:0);positions.push(Math.sin(a)*r,.065,Math.cos(a)*r);colors.push(1,1,1,edge?0:.55);}if(i<64){const k=i*2;indices.push(k,k+1,k+2,k+1,k+3,k+2);}}
  data.positions=positions;data.colors=colors;data.indices=indices;data.normals=[];VertexData.ComputeNormals(positions,indices,data.normals);data.applyToMesh(mesh);mesh.hasVertexAlpha=true;mesh.material=red?this.red:this.gold;mesh.position.copyFrom(pos);this.add(mesh,life,Vector3.Zero(),grow);
 }
 windup(pos:Vector3,yaw:number){
  if(this.reduced)return;
  // A narrow gathering streak at the weapon side, not a full-screen flash.
  const m=MeshBuilder.CreateBox('gathering spear glint',{width:.025,height:.025,depth:.8},this.scene);m.material=this.gold;m.rotation.y=yaw;m.position.copyFrom(pos);m.position.y=1.4;this.add(m,.12,Vector3.Zero(),-.9);
 }
 charge(pos:Vector3){
  // Six embers gather inward before the existing first damage pulse.
  this.ring(pos,2.5,.10,.30,-1.8);
  for(let i=0;i<6;i++){const a=i*Math.PI/3,offset=new Vector3(Math.sin(a)*2.2,.02,Math.cos(a)*2.2);this.ring(pos.add(offset),.20,.075,.34,-.4,false);}
  this.dustKick(pos,6);this.light(pos,1.5);
 }
 burst(pos:Vector3,radius:number,final=false){
  this.arc(pos,0,radius,Math.PI*2,false,true);this.arc(pos,Math.PI*.4,radius*.7,Math.PI*2,true,true);
  this.ring(pos,radius*.65,.32,.42,1.15);this.dustKick(pos,final?14:8);
  if(final&&!this.reduced)for(let i=0;i<6;i++){
   const a=i*Math.PI/3,mesh=new Mesh('crimson lotus petal',this.scene),d=new VertexData();
   const positions:number[]=[],colors:number[]=[],indices:number[]=[],segments=18;
   // Curved tapered petals with transparent edges; broad solid triangles obscure soldiers.
   for(let j=0;j<=segments;j++){
    const t=j/segments,r=radius*.86*t,angle=a+Math.sin(t*Math.PI)*.25,width=.52*Math.sin(t*Math.PI)**1.4;
    for(let edge=-1;edge<=1;edge++){
     positions.push(Math.sin(angle)*r+Math.cos(angle)*width*edge,.13+Math.sin(t*Math.PI)*1.65+t*.5,Math.cos(angle)*r-Math.sin(angle)*width*edge);
     colors.push(1,1,1,edge===0?Math.sin(t*Math.PI)*.65:0);
    }
    if(j<segments)for(let k=0;k<2;k++){const n=j*3+k;indices.push(n,n+1,n+3,n+1,n+4,n+3);}
   }
   d.positions=positions;d.indices=indices;d.colors=colors;d.normals=[];VertexData.ComputeNormals(positions,indices,d.normals);d.applyToMesh(mesh);mesh.hasVertexAlpha=true;mesh.material=this.red;mesh.position.copyFrom(pos);this.add(mesh,.44,new Vector3(0,.7,0),.45,.3);
  }
 }
 dustKick(pos:Vector3,count=5){
  for(let i=0;i<(this.reduced?Math.min(3,count):count);i++){const a=Math.random()*Math.PI*2;const m=MeshBuilder.CreatePlane('snow impact plume',{size:.5+Math.random()*.5},this.scene);m.billboardMode=Mesh.BILLBOARDMODE_ALL;m.material=this.dust;m.position.copyFrom(pos);m.position.y=.12;this.add(m,.40+Math.random()*.15,new Vector3(Math.sin(a)*2.2,1+Math.random(),Math.cos(a)*2.2),2,0,5);}
 }
 update(dt:number){if(this.warming)return;this.flash.intensity*=Math.exp(-dt*12);for(let i=this.effects.length-1;i>=0;i--){const e=this.effects[i];e.life-=dt;if(e.life<=0){e.mesh.dispose();this.effects.splice(i,1);continue;}e.mesh.position.addInPlace(e.velocity.scale(dt));e.velocity.y-=dt*e.gravity;e.mesh.scaling.scaleInPlace(1+e.grow*dt);e.mesh.rotation.y+=e.spin*dt;e.mesh.visibility=Math.max(0,e.life/e.total);}}
 clear(){for(const e of this.effects)e.mesh.dispose();this.effects.length=0;this.flash.intensity=0;}
 get count(){return this.effects.length;}
}
