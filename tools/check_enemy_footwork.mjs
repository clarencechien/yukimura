import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {enemyBodyPose,ENEMY_LEGS} from '../docs/routes/jigoku-2d/combat/enemy-body.mjs';
import {ENEMY_SOLES,enemyFootstep} from '../docs/routes/jigoku-2d/combat/enemy-footwork.mjs';
const rig=JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/combat/enemy-rig.json'));
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(dist(a,b)<1e-6);
const pose=age=>enemyBodyPose({phase:'flinch',alpha:1,bodyReaction:{fatal:true,kind:'thrust',age,fromAge:0,from:{phase:'guard',alpha:1}}},rig);
test('recovery feet lift sequentially, have double support, and land at authored buckle sole landmarks',()=>{
 let leftPeak=0,rightPeak=0;
 for(let age=0;age<=180;age+=.25){const p=pose(age);assert.ok(p.feet.left.lift===0||p.feet.right.lift===0);leftPeak=Math.max(leftPeak,p.feet.left.lift);rightPeak=Math.max(rightPeak,p.feet.right.lift);for(const side of ['left','right'])assert.ok(p.feet[side].lift>=0);}
 assert.equal(leftPeak,18);assert.equal(rightPeak,10);
 for(const age of [0,5,75,80,85,175,180]){const p=pose(age);assert.equal(p.feet.left.lift,0);assert.equal(p.feet.right.lift,0);}
 for(const [i,side] of ['left','right'].entries()){
  near(pose(0).feet[side].sole,ENEMY_SOLES[side]);near(pose(180).feet[side].sole,{x:rig.bindings[3].footContacts[i][0],y:rig.bindings[3].footContacts[i][1]});
 }
});
test('fixed-length legs follow moving ankles without flips, extension, or step-boundary snaps',()=>{
 let last=pose(0);
 for(let age=.25;age<=180;age+=.25){const p=pose(age);
  for(const [side,j] of Object.entries(ENEMY_LEGS)){const leg=p.legs[side];assert.ok(Math.abs(dist(leg.hip,leg.knee)-dist(j.hip,j.knee))<1e-6);assert.ok(Math.abs(dist(leg.knee,leg.ankle)-dist(j.knee,j.ankle))<1e-6);assert.ok(dist(leg.ankle,last.legs[side].ankle)<1);assert.ok(dist(leg.knee,last.legs[side].knee)<1);
   const cross=(leg.ankle.x-leg.hip.x)*(leg.knee.y-leg.hip.y)-(leg.ankle.y-leg.hip.y)*(leg.knee.x-leg.hip.x);assert.equal(Math.sign(cross),j.bend);
  }last=p;
 }
 for(const [side,keys] of [['right',[10,75]],['left',[85,175]]])for(const age of keys){assert.ok(dist(enemyFootstep(side,age-.001,rig).sole,enemyFootstep(side,age+.001,rig).sole)<1e-5);}
});
test('planted foot does not drift during the other step; nonfatal and duel poses keep original soles',()=>{
 for(let age=10;age<=75;age++)near(pose(age).feet.left.sole,ENEMY_SOLES.left);
 const landed=pose(85).feet.right.sole;for(let age=85;age<=180;age++)near(pose(age).feet.right.sole,landed);
 for(const enemy of [{phase:'guard'},{phase:'guard',intent:'strike',intentAge:90},{phase:'leg-flinch',bodyReaction:{age:140,kind:'sweep',from:{phase:'guard'}}}]){
  const p=enemyBodyPose(enemy,rig);for(const side of ['left','right']){near(p.feet[side].sole,ENEMY_SOLES[side]);assert.equal(p.feet[side].lift,0);}
 }
});
