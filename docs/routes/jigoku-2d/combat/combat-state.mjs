// Timing and hit rules are independent of rendering so dropped frames cannot skip a hit.
export const FRAME_MS=1000/30;
export function segmentHitsCircle(a,b,c,r){
  const dx=b.x-a.x,dy=b.y-a.y,d=dx*dx+dy*dy;
  const t=d?Math.max(0,Math.min(1,((c.x-a.x)*dx+(c.y-a.y)*dy)/d)):0;
  return Math.hypot(a.x+t*dx-c.x,a.y+t*dy-c.y)<=r;
}
export class CombatState {
  constructor(track,onEvent=()=>{}){this.track=track;this.onEvent=onEvent;this.range='near';this.targetKind='warrior';this.paused=false;this.reset();}
  reset(){this.hp=3;this.hits=0;this.swings=0;this.phase='idle';this.frame=0;this.elapsed=0;this.freeze=0;this.didHit=false;this.idleTime=0;this.enemyAge=0;this.enemyHit=false;}
  get target(){return {x:this.range==='near'?970:1060,y:334,radius:32};}
  get enemy(){
    if(!this.enemyHit)return {pose:0,phase:'guard',alpha:1};
    if(this.hp>0)return this.enemyAge<450?{pose:1,phase:'hurt',alpha:1}:{pose:0,phase:'guard',alpha:1};
    if(this.enemyAge<180)return {pose:1,phase:'hurt',alpha:1};
    if(this.enemyAge<480)return {pose:2,phase:'kneel',alpha:1};
    if(this.enemyAge<950)return {pose:3,phase:'fallen',alpha:1};
    return {pose:3,phase:this.enemyAge<1650?'dissolve':'gone',alpha:Math.max(0,1-(this.enemyAge-950)/700)};
  }
  setTarget(kind){if(this.phase==='attack'||!['warrior','seal'].includes(kind))return false;this.targetKind=kind;this.reset();return true;}
  setRange(range){if(this.phase==='attack'||!['near','far'].includes(range))return false;this.range=range;this.reset();return true;}
  attack(){if(this.paused||this.phase==='attack'||this.hp===0)return false;this.phase='attack';this.frame=0;this.elapsed=0;this.didHit=false;this.swings++;this.onEvent({type:'swing'});return true;}
  update(delta){
    if(this.paused)return;
    let remaining=Math.min(Math.max(delta,0),250); // Never catch up a hidden tab.
    while(remaining>1e-7){
      if(this.freeze>0){const t=Math.min(remaining,this.freeze);this.freeze-=t;remaining-=t;continue;}
      if(this.phase==='idle'){this.idleTime+=remaining;this.enemyAge+=remaining;this.frame=Math.floor(this.idleTime/FRAME_MS)%36;break;}
      const step=Math.min(remaining,FRAME_MS-this.elapsed);this.elapsed+=step;this.enemyAge+=step;remaining-=step;
      if(this.elapsed<FRAME_MS-1e-7)break;
      this.elapsed=0;this.frame++;
      if(this.frame>=36){this.phase='idle';this.frame=0;this.idleTime=0;this.onEvent({type:'recover',hit:this.didHit});continue;}
      if(this.track.activeFrames.includes(this.frame)&&!this.didHit&&this.hp>0){
        const a=this.track.frames[this.frame-1],b=this.track.frames[this.frame];
        if(segmentHitsCircle(a,b,this.target,this.target.radius)){
          this.didHit=true;this.hp--;this.hits++;this.freeze=70;this.enemyAge=0;this.enemyHit=true;
          this.onEvent({type:'hit',point:b,broken:this.hp===0});
        }
      }
    }
  }
}
