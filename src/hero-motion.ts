import {AnimationGroup} from '@babylonjs/core/Animations/animationGroup';

/** One skinned hero; crowd meshes remain GPU instances of shared geometry. */
export class HeroMotion {
 private clips=new Map<string,AnimationGroup>();
 private current='';
 private strike=0;
 constructor(groups:AnimationGroup[]){
  for(const name of ['idle','run','slash']){
   const clip=groups.find(g=>g.name===name||g.name.endsWith('|'+name));
   if(!clip)throw new Error(`Hero animation missing: ${name}`);
   clip.stop();
   for(const target of clip.targetedAnimations){target.animation.enableBlending=true;target.animation.blendingSpeed=.18;}
   this.clips.set(name,clip);
  }
  this.play('idle');
 }
 private play(name:string,restart=false){
  if(this.current===name&&!restart)return;
  for(const clip of this.clips.values())clip.stop();
  this.current=name;
  this.clips.get(name)!.start(name!=='slash',name==='slash'?1.15:1);
 }
 attack(){this.strike=.35;this.play('slash',true);}
 update(dt:number,moving:boolean,paused:boolean){
  if(!paused){this.strike=Math.max(0,this.strike-dt);if(this.strike===0)this.play(moving?'run':'idle');}
  const clip=this.clips.get(this.current)!;
  clip.speedRatio=paused?0:(this.current==='slash'?1.15:1);
 }
 reset(){this.strike=0;this.play('idle',true);}
 get state(){return this.current;}
 get names(){return [...this.clips.keys()];}
}
