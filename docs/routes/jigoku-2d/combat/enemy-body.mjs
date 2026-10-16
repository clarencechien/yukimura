import {ENEMY_SOLES,enemyFootstep,restingEnemyFoot} from './enemy-footwork.mjs';
import {DUEL_TIMING} from './duel-state.mjs';
// Source-space pivot at the belt, shared by the visible chest and shoulder socket.
export const ENEMY_WAIST={x:577,y:382};
export const ENEMY_BODY_BOXES={leftFoot:[315,610,445,700],rightFoot:[685,615,815,700],leftShin:[345,510,495,660],rightShin:[650,525,785,675],leftThigh:[375,440,555,580],rightThigh:[610,435,755,585],lower:[420,350,810,590],torso:[425,115,710,420]};
export const ENEMY_LEGS={left:{hip:{x:535,y:422},knee:{x:442,y:535},ankle:{x:395,y:637},bend:1},right:{hip:{x:601,y:415},knee:{x:699,y:536},ankle:{x:736,y:635},bend:-1}};
const distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
const direction=(a,b)=>Math.atan2(b.y-a.y,b.x-a.x);
function leg(j,root,ankle){
 const hip={x:j.hip.x+root.x,y:j.hip.y+root.y},thigh=distance(j.hip,j.knee),shin=distance(j.knee,j.ankle),d=distance(hip,ankle);
 if(d>=thigh+shin||d<=Math.abs(thigh-shin))throw Error('Unreachable fixed enemy leg target');
 const dx=(ankle.x-hip.x)/d,dy=(ankle.y-hip.y)/d,along=(thigh*thigh-shin*shin+d*d)/(2*d),off=Math.sqrt(Math.max(0,thigh*thigh-along*along))*j.bend;
 const knee={x:hip.x+dx*along-dy*off,y:hip.y+dy*along+dx*off};
 return {hip,knee,ankle,thigh,shin,thighAngle:(direction(hip,knee)-direction(j.hip,j.knee))*180/Math.PI,shinAngle:(direction(knee,ankle)-direction(j.knee,j.ankle))*180/Math.PI};
}
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
// The hit starts at the interrupted pose, loads for 95 ms, then returns to
// ready by the existing 360 ms reaction boundary. Hitstop freezes this age.
export function recoilValue(from,peak,rest,age){
 return age<95?from+(peak-from)*ease(age/95):peak+(rest-peak)*ease((age-95)/265);
}
export function lowRecoilValue(from,peak,rest,age){
 return age<140?from+(peak-from)*ease(age/140):peak+(rest-peak)*ease((age-140)/280);
}
// A bounded bridge to the authored buckle socket. Texture silhouettes/feet at
// the handoff still differ; this does not claim a continuous full-body fall.
export const FATAL_BRIDGE_MS=180;
export function fatalBlend(age){return ease(age/FATAL_BRIDGE_MS);}
export function fatalBodyTarget(rig){
 const angle=-14,a=angle*Math.PI/180,dx=rig.bindings[0].shoulder[0]-ENEMY_WAIST.x,dy=rig.bindings[0].shoulder[1]-ENEMY_WAIST.y;
 const [x,y]=rig.bindings[3].shoulder;
 return {angle,root:{x:x-ENEMY_WAIST.x-dx*Math.cos(a)+dy*Math.sin(a),y:y-ENEMY_WAIST.y-dx*Math.sin(a)-dy*Math.cos(a)}};
}
export function enemyBodyPose(enemy,rig){
 const shared=enemy.phase==='guard'||!!enemy.intent||!!enemy.bodyReaction;
 if(!shared)return null;
 let angle=0;const root={x:0,y:0};
 if(enemy.intent==='windup')angle=4*ease(enemy.intentAge/DUEL_TIMING.windup);
 if(enemy.intent==='strike')angle=4-14*ease(enemy.intentAge/DUEL_TIMING.strike);
 if(enemy.intent==='recovery'&&enemy.recoveryFrom==='attack')angle=-10*(1-ease(enemy.intentAge/520));
 if(enemy.bodyReaction){
  const {from,age}=enemy.bodyReaction,start=enemyBodyPose(from,rig)?.angle??0;
  if(enemy.bodyReaction.fatal){
   const target=fatalBodyTarget(rig),t=fatalBlend(age),prior=enemyBodyPose(from,rig);
   angle=start+(target.angle-start)*t;
   root.x=(prior?.root.x??0)*(1-t)+target.root.x*t;
   root.y=(prior?.root.y??0)*(1-t)+target.root.y*t;
  }else if(enemy.bodyReaction.kind==='sweep'){
   const weight=lowRecoilValue(0,1,0,age);root.x=-5*weight;root.y=18*weight;
   angle=lowRecoilValue(start,-7,0,age);
  }else angle=recoilValue(start,Math.max(8,start+8),0,age);
 }
 const a=angle*Math.PI/180,[x,y]=rig.bindings[0].shoulder,dx=x-ENEMY_WAIST.x,dy=y-ENEMY_WAIST.y;
 const pivot={x:ENEMY_WAIST.x+root.x,y:ENEMY_WAIST.y+root.y},transforms={lower:{pivot:ENEMY_WAIST,point:pivot,angle:0},torso:{pivot:ENEMY_WAIST,point:pivot,angle}},legs={},feet={};
 for(const [side,j] of Object.entries(ENEMY_LEGS)){
  const foot=feet[side]=enemy.bodyReaction?.fatal?enemyFootstep(side,enemy.bodyReaction.age,rig):restingEnemyFoot(side);
  const ankle={x:j.ankle.x+foot.sole.x-ENEMY_SOLES[side].x,y:j.ankle.y+foot.sole.y-ENEMY_SOLES[side].y};
  const p=legs[side]=leg(j,root,ankle);
  transforms[side+'Thigh']={pivot:j.hip,point:p.hip,angle:p.thighAngle};
  transforms[side+'Shin']={pivot:j.knee,point:p.knee,angle:p.shinAngle};
  transforms[side+'Foot']={pivot:j.ankle,point:p.ankle,angle:0};
 }
 return {angle,pivot,root,transforms,legs,feet,shoulder:{x:pivot.x+dx*Math.cos(a)-dy*Math.sin(a),y:pivot.y+dx*Math.sin(a)+dy*Math.cos(a)}};
}
