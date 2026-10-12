import {AnimationGroup} from '@babylonjs/core/Animations/animationGroup';
import {TransformNode} from '@babylonjs/core/Meshes/transformNode';
import {Quaternion,Vector3} from '@babylonjs/core/Maths/math.vector';

/** Combat clips are sampled from the damage clock, including hit-stop and pause. */
export class HeroMotion {
 private clips=new Map<string,AnimationGroup>();private current='';private clock=0;private blendTime=1;
 private targets:TransformNode[]=[];private previous:{q:Quaternion,p:Vector3}[]=[];
 constructor(groups:AnimationGroup[]){
  for(const name of ['idle','run','slash','reverse','thrust','spin','dash','hurt']){
   const clip=groups.find(g=>g.name===name||g.name.endsWith('|'+name));if(!clip)throw new Error(`Hero animation missing: ${name}`);clip.stop();this.clips.set(name,clip);
  }
  this.targets=[...new Set(groups.flatMap(g=>g.targetedAnimations.map(a=>a.target as TransformNode)).filter(t=>t instanceof TransformNode&&t.rotationQuaternion))];
  this.pose('idle',0,1);
 }
 pose(name:string,progress:number,dt=1/60){
  if(this.current!==name){
   this.previous=this.targets.map(t=>({q:t.rotationQuaternion!.clone(),p:t.position.clone()}));
   for(const clip of this.clips.values())clip.stop();this.current=name;this.blendTime=0;
   this.clips.get(name)!.start(true);this.clips.get(name)!.pause();
  }
  const clip=this.clips.get(name)!;clip.goToFrame(clip.from+(clip.to-clip.from)*Math.min(1,Math.max(0,progress)));
  this.blendTime+=dt;const t=Math.min(1,this.blendTime/(name==='idle'||name==='run'?.12:.045));
  if(t<1)this.targets.forEach((target,i)=>{Quaternion.SlerpToRef(this.previous[i].q,target.rotationQuaternion!,t,target.rotationQuaternion!);Vector3.LerpToRef(this.previous[i].p,target.position,t,target.position);});
 }
 update(dt:number,moving:boolean,paused:boolean){
  if(paused)return;this.clock+=dt*(moving?1.35:1);const name=moving?'run':'idle',clip=this.clips.get(name)!;
  const duration=(clip.to-clip.from)/clip.targetedAnimations[0].animation.framePerSecond;
  this.pose(name,(this.clock/duration)%1,dt);
 }
 reset(){this.current='';this.clock=0;this.pose('idle',0,1);}
 get state(){return this.current;}
 get names(){return [...this.clips.keys()];}
}
