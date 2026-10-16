import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {CombatState} from '../docs/routes/jigoku-2d/combat/combat-state.mjs';
import {enemyBodyPose,ENEMY_LEGS} from '../docs/routes/jigoku-2d/combat/enemy-body.mjs';
import {enemyArm} from '../docs/routes/jigoku-2d/combat/enemy-arm.mjs';
const read=n=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/combat/${n}.json`)),rig=read('enemy-rig');rig.duelBindings=read('duel-art').enemy.bindings;
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(dist(a,b)<1e-6),advance=(s,ms)=>{for(let i=0;i<ms;i++)s.update(1);};
const create=()=>new CombatState(read('shared-spear-track'),()=>{},read('shared-sweep-track'));
function hit(s){assert.ok(s.attack('sweep'));for(let i=0;i<900&&!s.freeze;i++)s.update(1);assert.ok(s.freeze>69);}
test('low hit preserves impact pose then loads pelvis and bends fixed legs without moving either foot',()=>{
 const s=create();hit(s);const first=enemyBodyPose(s.enemy,rig);near(first.root,{x:0,y:0});let deepest=0,previous=first;
 for(let i=0;i<500;i++){
  const body=enemyBodyPose(s.enemy,rig);assert.ok(body);deepest=Math.max(deepest,body.root.y);
  for(const [side,j] of Object.entries(ENEMY_LEGS)){
   const p=body.legs[side];near(p.ankle,j.ankle);assert.ok(Math.abs(dist(p.hip,p.knee)-dist(j.hip,j.knee))<1e-6);assert.ok(Math.abs(dist(p.knee,p.ankle)-dist(j.knee,j.ankle))<1e-6);
   assert.ok(dist(p.knee,previous.legs[side].knee)<1);const cross=(p.ankle.x-p.hip.x)*(p.knee.y-p.hip.y)-(p.ankle.y-p.hip.y)*(p.knee.x-p.hip.x);assert.equal(Math.sign(cross),j.bend);
  }
  previous=body;s.update(1);
 }
 assert.ok(deepest>17.99);assert.deepEqual(previous.root,{x:0,y:0});assert.equal(s.enemy.phase,'guard');assert.equal(s.hp,2);
});
test('low impact captures every duel stage without shoulder, elbow or wrist discontinuity',()=>{
 const stages=new Set();
 for(const start of [0,900,1250,1550,1700,1800,1900,2000,2100]){
  const s=create();s.startDuel();advance(s,start);hit(s);const {from,fromAge}=s.enemy.bodyReaction;stages.add(from.intent);
  const body=enemyBodyPose(s.enemy,rig),prior=enemyBodyPose(from,rig);near(body.shoulder,prior.shoulder);assert.ok(Math.abs(body.angle-prior.angle)<1e-6);
  const a=enemyArm(s.enemy,s.enemyAge,false,rig),b=enemyArm(from,fromAge,false,rig);for(const n of ['shoulder','elbow','wrist'])near(a[n],b[n]);
  let prev=a;for(let i=0;i<500;i++){const arm=enemyArm(s.enemy,s.enemyAge,false,rig);for(const n of ['shoulder','elbow','wrist'])assert.ok(dist(arm[n],prev[n])<2);prev=arm;s.update(1);}
 }
 assert.ok(stages.has('windup')&&stages.has('strike')&&stages.has('recovery'));
});
test('low recoil clock holds during hitstop/pause; reset clears the loaded pelvis and all limbs',()=>{
 const s=create();hit(s);const frozen=enemyBodyPose(s.enemy,rig);advance(s,69);assert.deepEqual(enemyBodyPose(s.enemy,rig),frozen);advance(s,140);s.paused=true;const held=enemyBodyPose(s.enemy,rig);advance(s,1000);assert.deepEqual(enemyBodyPose(s.enemy,rig),held);s.paused=false;s.reset();assert.deepEqual(enemyBodyPose(s.enemy,rig).root,{x:0,y:0});
});
test('fatal low hit keeps authored knee-collapse/death/release; torso-only moves keep legs at rest',()=>{
 const s=create();for(let i=0;i<2;i++){hit(s);advance(s,1500);}hit(s);assert.equal(s.hp,0);assert.equal(enemyBodyPose(s.enemy,rig),null);advance(s,500);assert.equal(enemyBodyPose(s.enemy,rig),null);
 for(const intent of ['waiting','windup','strike','recovery'])for(const intentAge of [0,80,180,500]){
  const p=enemyBodyPose({phase:'guard',intent,intentAge,recoveryFrom:'attack'},rig);assert.deepEqual(p.root,{x:0,y:0});for(const [side,j] of Object.entries(ENEMY_LEGS))near(p.legs[side].knee,j.knee);
 }
});
