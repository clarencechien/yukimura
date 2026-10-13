import {Scene} from '@babylonjs/core/scene';
import {Mesh} from '@babylonjs/core/Meshes/mesh';
import {InstancedMesh} from '@babylonjs/core/Meshes/instancedMesh';
import {TransformNode} from '@babylonjs/core/Meshes/transformNode';
import {Vector3,Vector4,Quaternion} from '@babylonjs/core/Maths/math.vector';
import {RawTexture} from '@babylonjs/core/Materials/Textures/rawTexture';
import {Texture} from '@babylonjs/core/Materials/Textures/texture';
import {BakedVertexAnimationManager} from '@babylonjs/core/BakedVertexAnimation/bakedVertexAnimationManager';
import {BoundingInfo} from '@babylonjs/core/Culling/boundingInfo';
import '@babylonjs/core/Meshes/instancedMesh';

export type CrowdClip='idle'|'run'|'thrust'|'hurt'|'fall'|'fall_back';
type Clip={start:number,end:number,duration:number};
type Palette={uri:string,bytes:number,width:number,height:number,joints:number,clips:Record<CrowdClip,Clip>};
export type CrowdManifest={fps:number,models:Record<string,Palette>};
const attribute='bakedVertexAnimationSettingsInstanced';

/** All soldiers share a palette and geometry; only one vec4 is updated per actor. */
export class CrowdModel {
 readonly manager:BakedVertexAnimationManager;
 constructor(readonly sources:Mesh[],readonly palette:Palette,texture:RawTexture,scene:Scene){
  this.manager=new BakedVertexAnimationManager(scene);this.manager.texture=texture;this.manager.time=0;
  for(const source of sources){
   source.bakedVertexAnimationManager=this.manager;source.registerInstancedBuffer(attribute,4);
   source.instancedBuffers[attribute]=new Vector4(0,0,0,0);
   // Shared bounds cover animated weapons and every material section.
   source.setBoundingInfo(new BoundingInfo(new Vector3(-4,-.5,-4),new Vector3(4,3.6,4)));
  }
 }
 create(root:TransformNode,scale:number,phase:number){
  const meshes=this.sources.map((source,index)=>{
   const mesh=source.createInstance(root.name+'-body-'+index);mesh.parent=root;
   const s=Vector3.One(),q=Quaternion.Identity(),p=Vector3.Zero();source.computeWorldMatrix(true).decompose(s,q,p);
   mesh.scaling.copyFrom(s.scale(scale));mesh.rotationQuaternion=q;mesh.position.copyFrom(p);
   mesh.instancedBuffers[attribute]=new Vector4(0,0,0,0);mesh.isPickable=false;mesh.receiveShadows=true;
   return mesh;
  });
  return new CrowdMotion(meshes,this.palette,phase);
 }
}
export async function loadPalettes(scene:Scene,manifest:CrowdManifest,base:string){
 const textures=new Map<string,RawTexture>();
 for(const p of Object.values(manifest.models)){
  if(textures.has(p.uri))continue;
  const response=await fetch(base+p.uri);if(!response.ok)throw Error('Crowd animation failed to load');
  const data=new Float32Array(await response.arrayBuffer());if(data.byteLength!==p.bytes||data.length!==p.width*p.height*4)throw Error('Invalid crowd palette dimensions');
  textures.set(p.uri,RawTexture.CreateRGBATexture(data,p.width,p.height,scene,false,false,Texture.NEAREST_SAMPLINGMODE,1));
 }
 return textures;
}
export class CrowdMotion {
 state:CrowdClip='idle';time=0;frame=0;private loopClock:number;
 get mesh(){return this.meshes[0];}
 constructor(readonly meshes:InstancedMesh[],private palette:Palette,phase:number){this.loopClock=phase;this.sample('idle',phase%1);}
 sample(clip:CrowdClip,progress:number){
  this.state=clip;const range=this.palette.clips[clip];
  this.frame=range.start+Math.round(Math.max(0,Math.min(1,progress))*(range.end-range.start));
  for(const mesh of this.meshes)(mesh.instancedBuffers[attribute] as Vector4).set(this.frame,this.frame,0,0);
 }
 loop(dt:number,moving:boolean,speed=1){
  this.loopClock+=dt*speed;const clip=moving?'run':'idle';const duration=this.palette.clips[clip].duration;
  this.sample(clip,(this.loopClock/duration)%1);
 }
}
