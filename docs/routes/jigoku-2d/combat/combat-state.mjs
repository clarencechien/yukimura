import {DuelState} from './duel-state.mjs';
// Timing and hit rules are independent of rendering so dropped frames cannot skip a hit.
export const FRAME_MS=1000/30;
export function segmentHitsCircle(a,b,c,r){
  const dx=b.x-a.x,dy=b.y-a.y,d=dx*dx+dy*dy;
  const t=d?Math.max(0,Math.min(1,((c.x-a.x)*dx+(c.y-a.y)*dy)/d)):0;
  return Math.hypot(a.x+t*dx-c.x,a.y+t*dy-c.y)<=r;
}
export class CombatState {
  constructor(track,onEvent=()=>{},sweepTrack=null){this.track=track;this.sweepTrack=sweepTrack;this.onEvent=onEvent;this.range='near';this.targetKind='warrior';this.paused=false;this.duel=new DuelState(onEvent);this.reset();}
  reset(){this.duel.reset();this.duelRemainder=0;this.hp=3;this.hits=0;this.swings=0;this.phase='idle';this.frame=0;this.elapsed=0;this.freeze=0;this.didHit=false;this.idleTime=0;this.enemyAge=0;this.enemyHit=false;this.attackKind='thrust';this.queuedAttack=null;this.lastHitKind=null;}
  startDuel(enabled=true){if(this.paused||this.phase==='attack'||this.targetKind!=='warrior')return false;this.duel.enabled=enabled;this.reset();return true;}
  defend(){return !this.paused&&this.phase==='idle'&&this.duel.defend();}
  get guardEnemy(){return {pose:0,phase:'guard',alpha:1,...(this.duel.active?{intent:this.duel.stage,intentAge:this.duel.age}: {})};}
  get target(){return {x:this.range==='near'?970:1060,y:334,radius:32};}
  get currentTrack(){return this.attackKind==='sweep'?this.sweepTrack:this.track;}
  get hurtbox(){return this.attackKind==='sweep'&&this.targetKind==='warrior'?{x:this.target.x-55,y:535,radius:42}:this.target;}
  get canQueueSweep(){return !!this.sweepTrack&&!this.paused&&this.hp>0&&!this.duel.guarding&&!this.duel.result&&this.phase==='attack'&&this.attackKind==='thrust'&&this.frame>=22&&this.frame<=30&&!this.queuedAttack;}
  get enemy(){
    if(!this.enemyHit)return this.guardEnemy;
    const age=this.enemyAge;
    if(this.lastHitKind==='sweep'){
      if(age<110)return {pose:12,phase:'leg-flinch',alpha:1,reaction:'sweep'};
      if(age<(this.hp>0?260:250))return {pose:13,phase:'low-stagger',alpha:1,reaction:'sweep'};
      if(this.hp>0){
        if(age<340)return {pose:14,phase:'leg-rise',alpha:1,reaction:'sweep'};
        if(age<420)return {pose:15,phase:'guard-settle',alpha:1,reaction:'sweep'};
        return this.guardEnemy;
      }
    }
    if(this.hp>0){
      if(age<90)return {pose:1,phase:'flinch',alpha:1};
      if(age<220)return {pose:2,phase:'hurt',alpha:1};
      if(age<360)return {pose:1,phase:'flinch',alpha:1};
      return this.guardEnemy;
    }
    // Authored silhouettes carry the weight shift; never rotate or stretch the whole body.
    const stages=[[90,1,'flinch'],[180,2,'hurt'],[250,3,'buckle'],[330,4,'crouch'],[420,5,'kneel'],[500,6,'brace'],[540,10,'yield'],[580,11,'sink'],[640,7,'lower'],[720,8,'settle'],[1000,9,'fallen']];
    for(const [end,pose,phase] of stages)if(age<end)return {pose,phase,alpha:1};
    return {pose:9,phase:age<1700?'dissolve':'gone',alpha:Math.max(0,1-(age-1000)/700)};
  }
  setTarget(kind){if(this.phase==='attack'||!['warrior','seal'].includes(kind))return false;this.targetKind=kind;if(kind==='seal')this.duel.enabled=false;this.reset();return true;}
  setRange(range){if(this.phase==='attack'||!['near','far'].includes(range))return false;this.range=range;this.reset();return true;}
  attack(kind='thrust'){
    if(!['thrust','sweep'].includes(kind)||kind==='sweep'&&!this.sweepTrack)return false;
    if(kind==='sweep'&&this.canQueueSweep){this.queuedAttack='sweep';this.onEvent({type:'queued',kind});return true;}
    if(this.paused||this.phase==='attack'||this.hp===0||this.duel.guarding||this.duel.result)return false;
    this.phase='attack';this.attackKind=kind;this.frame=0;this.elapsed=0;this.didHit=false;this.swings++;this.onEvent({type:'swing',kind});return true;
  }
  update(delta){
    if(this.paused)return;
    if(!this.duel.enabled){this.advance(delta);return;}
    // Shared 1 ms rule clock makes input windows independent of display frame rate.
    // Rendering still runs at the browser rate; this never creates extra draw calls.
    this.duelRemainder+=Math.min(Math.max(delta,0),250);
    while(this.duelRemainder>=1){
      this.duelRemainder--;
      const frozen=this.freeze>0;
      this.advance(1);
      if(!frozen)this.duel.update(1,this.range);
      if(this.duel.result==='defeat'){this.phase='idle';this.queuedAttack=null;this.frame=0;}
    }
  }
  advance(delta){
    if(this.paused)return;
    let remaining=Math.min(Math.max(delta,0),250); // Never catch up a hidden tab.
    while(remaining>1e-7){
      if(this.freeze>0){const t=Math.min(remaining,this.freeze);this.freeze-=t;remaining-=t;continue;}
      if(this.phase==='idle'){this.idleTime+=remaining;this.enemyAge+=remaining;this.frame=Math.floor(this.idleTime/FRAME_MS)%36;break;}
      const step=Math.min(remaining,FRAME_MS-this.elapsed);this.elapsed+=step;this.enemyAge+=step;remaining-=step;
      if(this.elapsed<FRAME_MS-1e-7)break;
      this.elapsed=0;this.frame++;
      if(this.frame>=this.currentTrack.frames.length){
        const next=this.queuedAttack;this.queuedAttack=null;this.phase='idle';this.frame=0;this.idleTime=0;this.onEvent({type:'recover',hit:this.didHit,kind:this.attackKind});
        if(next&&this.hp>0)this.attack(next);continue;
      }
      if(this.currentTrack.activeFrames.includes(this.frame)&&!this.didHit&&this.hp>0){
        const a=this.currentTrack.frames[this.frame-1],b=this.currentTrack.frames[this.frame];
        if(segmentHitsCircle(a,b,this.hurtbox,this.hurtbox.radius)){
          this.didHit=true;this.hp--;this.hits++;this.freeze=70;this.enemyAge=0;this.enemyHit=true;this.lastHitKind=this.attackKind;
          this.onEvent({type:'hit',point:b,broken:this.hp===0,kind:this.attackKind});
          this.duel.interrupt(this.hp===0);
        }
      }
    }
  }
}
