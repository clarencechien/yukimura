// Manually inspected sole centers in the existing guard illustration (HD pixels).
// These are registration landmarks, not measured three-dimensional contacts.
export const ENEMY_SOLES={left:{x:373,y:686},right:{x:775,y:674}};
const clamp=t=>Math.max(0,Math.min(1,t));
const smooth=t=>t*t*(3-2*t);
// Two short recovery steps: right foot lands before the left leaves the floor.
// The 10 ms double-support interval prevents an unintended hop.
const steps={right:{start:10,end:75,height:10,index:1},left:{start:85,end:175,height:18,index:0}};
export function enemyFootstep(side,age,rig){
 const base=ENEMY_SOLES[side],step=steps[side],t=clamp((age-step.start)/(step.end-step.start)),u=smooth(t),[x,y]=rig.bindings[3].footContacts[step.index];
 const lift=step.height*16*t*t*(1-t)*(1-t);
 const ground={x:base.x+(x-base.x)*u,y:base.y+(y-base.y)*u};
 return {sole:{x:ground.x,y:ground.y-lift},ground,lift};
}
export function restingEnemyFoot(side){const p=ENEMY_SOLES[side];return {sole:{...p},ground:{...p},lift:0};}
