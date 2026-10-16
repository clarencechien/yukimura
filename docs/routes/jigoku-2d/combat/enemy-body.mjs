import {DUEL_TIMING} from './duel-state.mjs';
// Source-space pivot at the belt, shared by the visible chest and shoulder socket.
export const ENEMY_WAIST={x:577,y:382};
export const ENEMY_BODY_BOXES={torso:[425,115,710,420],lower:[320,350,810,700]};
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
export function enemyBodyPose(enemy,rig){
 const shared=enemy.phase==='guard'||!!enemy.intent;
 if(!shared)return null;
 let angle=0;
 if(enemy.intent==='windup')angle=4*ease(enemy.intentAge/DUEL_TIMING.windup);
 if(enemy.intent==='strike')angle=4-14*ease(enemy.intentAge/DUEL_TIMING.strike);
 if(enemy.intent==='recovery'&&enemy.recoveryFrom==='attack')angle=-10*(1-ease(enemy.intentAge/520));
 const a=angle*Math.PI/180,[x,y]=rig.bindings[0].shoulder,dx=x-ENEMY_WAIST.x,dy=y-ENEMY_WAIST.y;
 return {angle,pivot:ENEMY_WAIST,shoulder:{x:ENEMY_WAIST.x+dx*Math.cos(a)-dy*Math.sin(a),y:ENEMY_WAIST.y+dx*Math.sin(a)+dy*Math.cos(a)}};
}
