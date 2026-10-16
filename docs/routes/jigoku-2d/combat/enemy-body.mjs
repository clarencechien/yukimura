import {DUEL_TIMING} from './duel-state.mjs';
// Source-space pivot at the belt, shared by the visible chest and shoulder socket.
export const ENEMY_WAIST={x:577,y:382};
export const ENEMY_BODY_BOXES={torso:[425,115,710,420],lower:[320,350,810,700]};
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
// The hit starts at the interrupted pose, loads for 95 ms, then returns to
// ready by the existing 360 ms reaction boundary. Hitstop freezes this age.
export function recoilValue(from,peak,rest,age){
 return age<95?from+(peak-from)*ease(age/95):peak+(rest-peak)*ease((age-95)/265);
}
export function enemyBodyPose(enemy,rig){
 const shared=enemy.phase==='guard'||!!enemy.intent||!!enemy.bodyReaction;
 if(!shared)return null;
 let angle=0;
 if(enemy.intent==='windup')angle=4*ease(enemy.intentAge/DUEL_TIMING.windup);
 if(enemy.intent==='strike')angle=4-14*ease(enemy.intentAge/DUEL_TIMING.strike);
 if(enemy.intent==='recovery'&&enemy.recoveryFrom==='attack')angle=-10*(1-ease(enemy.intentAge/520));
 if(enemy.bodyReaction){
  const {from,age}=enemy.bodyReaction,start=enemyBodyPose(from,rig)?.angle??0;
  angle=recoilValue(start,Math.max(8,start+8),0,age);
 }
 const a=angle*Math.PI/180,[x,y]=rig.bindings[0].shoulder,dx=x-ENEMY_WAIST.x,dy=y-ENEMY_WAIST.y;
 return {angle,pivot:ENEMY_WAIST,shoulder:{x:ENEMY_WAIST.x+dx*Math.cos(a)-dy*Math.sin(a),y:ENEMY_WAIST.y+dx*Math.sin(a)+dy*Math.cos(a)}};
}
