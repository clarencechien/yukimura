import {AnimationGroup} from '@babylonjs/core/Animations/animationGroup';

/** Combat clips are sampled from the damage clock, including hit-stop and pause. */
export class HeroMotion {
 private clips=new Map<string,AnimationGroup>();private current='';private posed=false;
 constructor(groups:AnimationGroup[]){
  for(const name of ['idle','run','slash','reverse','thrust','spin']){
   const clip=groups.find(g=>g.name===name||g.name.endsWith('|'+name));if(!clip)throw new Error(`Hero animation missing: ${name}`);clip.stop();this.clips.set(name,clip);
  }
  this.play('idle');
 }
 private play(name:string){if(this.current===name)return;for(const clip of this.clips.values())clip.stop();this.current=name;this.clips.get(name)!.start(name==='idle'||name==='run');}
 pose(name:string,progress:number){this.play(name);const clip=this.clips.get(name)!;clip.pause();clip.goToFrame(clip.from+(clip.to-clip.from)*Math.min(1,Math.max(0,progress)));this.posed=true;}
 update(_dt:number,moving:boolean,paused:boolean){
  if(paused){this.clips.get(this.current)!.speedRatio=0;return;}
  if(this.posed){this.current='';this.posed=false;}this.play(moving?'run':'idle');this.clips.get(this.current)!.speedRatio=paused?0:1;
 }
 reset(){this.current='';this.posed=false;this.play('idle');}
 get state(){return this.current;}
 get names(){return [...this.clips.keys()];}
}
