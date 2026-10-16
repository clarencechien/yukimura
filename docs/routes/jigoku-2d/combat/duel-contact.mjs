import {enemyArm,closedGrip,solveArm} from './enemy-arm.mjs';
import {enemyWeapon,enemyPointToWorld} from './enemy-weapon.mjs';
import {sharedGuardPose} from './hero-rig.mjs';
import {DUEL_TIMING} from './duel-state.mjs';
const rad=Math.PI/180;
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
const rotate=(p,a)=>({x:p.x*Math.cos(a)-p.y*Math.sin(a),y:p.x*Math.sin(a)+p.y*Math.cos(a)});
// Manually marked points INSIDE the painted steel, in the 410 x 51 blade texture.
// The contact may slide along this polyline; no weapon scale or arm length changes.
export const BLADE_CONTACT_LINE=[[14,10],[40,18],[100,30],[170,34]];
function steelPoint(x){
 for(let i=1;i<BLADE_CONTACT_LINE.length;i++){
  const a=BLADE_CONTACT_LINE[i-1],b=BLADE_CONTACT_LINE[i];
  if(x<=b[0])return {x,y:a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0])};
 }
 return {x:170,y:34};
}
export function bladePointToWorld(point,weapon,targetX,rig){
 const p=rig.parts.katana.pivot,v=rotate({x:point.x-p[0],y:point.y-p[1]},weapon.angle*rad);
 return enemyPointToWorld({x:weapon.grip.x+v.x,y:weapon.grip.y+v.y},targetX,rig);
}
export function bladeContactArm(base,target,rig){
 const hand=rig.parts.grip,blade=rig.parts.katana,upper=rig.armLengths[0],fore=rig.armLengths[1];
 const vector=mark=>{
  const v=rotate({x:hand.gripPoint[0]-hand.pivot[0]+mark.x-blade.pivot[0],y:hand.gripPoint[1]-hand.pivot[1]+mark.y-blade.pivot[1]},(90-hand.axisDegrees)*rad);
  return {x:v.x,y:v.y+fore};
 };
 const distance=Math.hypot(target.x-base.shoulder.x,target.y-base.shoulder.y);
 // Choose a steel point with ample reach margin instead of clamping the target.
 let lo=14,hi=170;
 for(let i=0;i<28;i++){const mid=(lo+hi)/2,v=vector(steelPoint(mid));if(Math.hypot(v.x,v.y)>distance)lo=mid;else hi=mid;}
 const mark=steelPoint((lo+hi)/2),v=vector(mark),length=Math.hypot(v.x,v.y);
 if(distance>=upper+length||distance<=Math.abs(length-upper))throw Error('Blade contact outside fixed arm reach');
 const virtual=solveArm(base.shoulder,target,upper,length);
 const turn=Math.atan2(target.y-virtual.elbow.y,target.x-virtual.elbow.x)-Math.atan2(v.y,v.x);
 const offset=rotate({x:0,y:fore},turn),wrist={x:virtual.elbow.x+offset.x,y:virtual.elbow.y+offset.y};
 const solved=solveArm(base.shoulder,wrist,upper,fore);
 if(Math.hypot(solved.elbow.x-virtual.elbow.x,solved.elbow.y-virtual.elbow.y)>1e-5)throw Error('Blade contact would reverse elbow bend');
 return {wrist,mark};
}
export function duelContactPose(state,hero,guardRig,heroRig,rig){
 const enemy=state.enemy,dead=state.hp===0,base=enemyArm(enemy,state.enemyAge,dead,rig);
 const ordinary=()=>({arm:base,weapon:enemyWeapon(enemy,state.enemyAge,dead,rig),contact:null});
 const d=state.duel;
 if(!d.active||dead||state.range!=='near'||state.targetKind!=='warrior'||!enemy.intent)return ordinary();
 let weight=0,target=hero.weapon.contact;
 if(d.stage==='windup'&&d.guarding){
  const guardElapsed=DUEL_TIMING.guard-d.guard,start=Math.max(DUEL_TIMING.windup-240,d.age-guardElapsed);
  weight=ease((d.age-start)/(DUEL_TIMING.windup-start));
 }else if(d.blocked&&d.blockAge!==null&&d.blockAge<300){
  const hold=Math.min(65,d.guardAtBlock);
  weight=1-ease((d.blockAge-hold)/(300-hold));
  // Reconstruct this block's guard, even when the player has begun a counterattack.
  target=sharedGuardPose(DUEL_TIMING.guard-d.guardAtBlock+d.blockAge,d.blockAge,guardRig,heroRig).weapon.contact;
 }
 if(weight===0)return ordinary();
 const local={x:(target.x-state.target.x)/rig.worldScale+rig.bodyOrigin[0],y:(target.y-574)/rig.worldScale+rig.bodyOrigin[1]};
 const exact=bladeContactArm(base,local,rig),wrist={x:base.wrist.x+(exact.wrist.x-base.wrist.x)*weight,y:base.wrist.y+(exact.wrist.y-base.wrist.y)*weight};
 const solved=solveArm(base.shoulder,wrist,...rig.armLengths),handAngle=solved.foreAngle+90-rig.parts.grip.axisDegrees;
 const arm={...solved,handState:'grip',handAngle,alpha:enemy.alpha};
 const grip=closedGrip(arm,rig),weapon={held:true,landed:false,wrist:arm.wrist,...grip,alpha:enemy.alpha};
 const point=bladePointToWorld(exact.mark,weapon,state.target.x,rig);
 return {arm,weapon,contact:{weight,target,point,mark:exact.mark,gap:Math.hypot(point.x-target.x,point.y-target.y)}};
}
