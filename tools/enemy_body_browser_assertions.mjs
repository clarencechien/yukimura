import {ENEMY_SOLES} from '../docs/routes/jigoku-2d/combat/enemy-footwork.mjs';
import assert from 'node:assert/strict';
import {ENEMY_BODY_BOXES,ENEMY_LEGS} from '../docs/routes/jigoku-2d/combat/enemy-body.mjs';
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-5,`${a} != ${b}`);
function mapped(p,box,point){
 const x=((point.x-box[0])/(box[2]-box[0])-p.originX)*p.width,y=((point.y-box[1])/(box[3]-box[1])-p.originY)*p.height,a=p.angle*Math.PI/180;
 return {x:p.x+x*Math.cos(a)-y*Math.sin(a),y:p.y+x*Math.sin(a)+y*Math.cos(a)};
}
const same=(a,b)=>{near(a.x,b.x);near(a.y,b.y);};
export function assertEnemyBody(row){
 const parts=row.enemyBodyParts,shared=!!row.enemyBodyPose,visible=row.targetKind==='warrior';
 assert.equal(row.legacyBodyVisible,visible&&!shared);
 for(const p of Object.values(parts))assert.equal(p.visible,visible&&shared);
 if(!shared)return;
 const torso=parts.torso,lower=parts.lower;
 near(torso.width,285*.6);near(torso.height,305*.6);
 near(lower.width,390*.6);near(lower.height,240*.6);near(lower.angle,0);
 // Independently map the painted socket through the ACTUAL Phaser transform.
 const x=((481-425)/285-torso.originX)*torso.width,y=((270-115)/305-torso.originY)*torso.height,a=torso.angle*Math.PI/180;
 near(torso.x+x*Math.cos(a)-y*Math.sin(a),row.renderedArm.shoulder.x);
 near(torso.y+x*Math.sin(a)+y*Math.cos(a),row.renderedArm.shoulder.y);
 near(torso.x,lower.x);near(torso.y,lower.y);
 for(const [side,j] of Object.entries(ENEMY_LEGS)){
  const thigh=parts[side+'Thigh'],shin=parts[side+'Shin'],foot=parts[side+'Foot'];
  const hip=mapped(thigh,ENEMY_BODY_BOXES[side+'Thigh'],j.hip),knee=mapped(thigh,ENEMY_BODY_BOXES[side+'Thigh'],j.knee),ankle=mapped(shin,ENEMY_BODY_BOXES[side+'Shin'],j.ankle);
  same(hip,{x:lower.x+(j.hip.x-577)*.6,y:lower.y+(j.hip.y-382)*.6});same(knee,mapped(shin,ENEMY_BODY_BOXES[side+'Shin'],j.knee));same(ankle,mapped(foot,ENEMY_BODY_BOXES[side+'Foot'],j.ankle));
  if(!row.enemy.bodyReaction?.fatal)same(ankle,{x:row.target.x+(j.ankle.x-576)*.6,y:574+(j.ankle.y-690)*.6});near(foot.angle,0);
  const sole=mapped(foot,ENEMY_BODY_BOXES[side+'Foot'],ENEMY_SOLES[side]),index=side==='left'?0:1,shadow=row.enemyFootShadows[index];
  near(sole.x,shadow.x);near(sole.y+row.enemyBodyPose.feet[side].lift*.6,shadow.y);
  near(shadow.alpha,.35*row.enemy.alpha*(1-.65*Math.min(1,row.enemyBodyPose.feet[side].lift/18)));
  if(row.enemy.bodyReaction?.fatal)assert.ok(row.enemyBodyPose.feet.left.lift===0||row.enemyBodyPose.feet.right.lift===0);
  for(const [name,p] of [[side+'Thigh',thigh],[side+'Shin',shin],[side+'Foot',foot]]){const box=ENEMY_BODY_BOXES[name];near(p.width,(box[2]-box[0])*.6);near(p.height,(box[3]-box[1])*.6);}
 }
 assert.ok(row.armOrder.upper<torso.order&&row.armOrder.upper>lower.order);
 assert.ok(row.armOrder.fore>torso.order&&row.armOrder.hand>row.armOrder.fore);
}
