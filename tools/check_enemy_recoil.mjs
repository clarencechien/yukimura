import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {CombatState} from '../docs/routes/jigoku-2d/combat/combat-state.mjs';
import {enemyBodyPose} from '../docs/routes/jigoku-2d/combat/enemy-body.mjs';
import {enemyArm,closedGrip} from '../docs/routes/jigoku-2d/combat/enemy-arm.mjs';
import {enemyWeapon} from '../docs/routes/jigoku-2d/combat/enemy-weapon.mjs';
const read=n=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/combat/${n}.json`)),rig=read('enemy-rig');rig.duelBindings=read('duel-art').enemy.bindings;
const create=(duel=true)=>{const s=new CombatState(read('shared-spear-track'),()=>{},read('shared-sweep-track'));if(duel)s.startDuel();return s;};
const advance=(s,ms)=>{for(let i=0;i<ms;i++)s.update(1);};
const pose=s=>({body:enemyBodyPose(s.enemy,rig),arm:enemyArm(s.enemy,s.enemyAge,s.hp===0,rig),weapon:enemyWeapon(s.enemy,s.enemyAge,s.hp===0,rig)});
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(dist(a,b)<1e-6);
function hit(s,kind='thrust'){assert.ok(s.attack(kind));for(let i=0;i<700&&!s.freeze;i++)s.update(1);assert.ok(s.freeze>69&&s.freeze<=70);}
test('impact begins at the interrupted chest, elbow, wrist and weapon pose in every duel stage and practice',()=>{
 const stages=new Set();
 for(const start of [0,900,1250,1550,1700,2100,2400]){
  const s=create();advance(s,start);hit(s);const e=s.enemy,{from,fromAge}=e.bodyReaction;stages.add(from.intent);
  assert.equal(e.bodyReaction.age,0);const p=pose(s),a=enemyArm(from,fromAge,false,rig),w=enemyWeapon(from,fromAge,false,rig);
  assert.ok(Math.abs(p.body.angle-enemyBodyPose(from,rig).angle)<1e-8);near(p.body.shoulder,enemyBodyPose(from,rig).shoulder);for(const n of ['shoulder','elbow','wrist'])near(p.arm[n],a[n]);near(p.weapon.grip,w.grip);assert.ok(Math.abs(p.weapon.angle-w.angle)<1e-8);
 }
 assert.deepEqual([...stages].sort(),['recovery','strike','waiting','windup']);
 const s=create(false);hit(s);assert.equal(pose(s).body.angle,0);assert.equal(s.enemy.bodyReaction.from.intent,undefined);
});
test('recoil retains fixed arm lengths, grip and rigid torso; returns continuously to ready at 360 ms',()=>{
 for(const start of [0,1250,1550,1700]){
  const s=create();advance(s,start);hit(s);let prev=pose(s),peak=prev.body.angle;
  for(let i=0;i<435;i++){
   const p=pose(s);assert.ok(p.body);near(p.weapon.grip,closedGrip(p.arm,rig).grip);
   assert.ok(Math.abs(dist(p.arm.shoulder,p.arm.elbow)-65)<1e-6);assert.ok(Math.abs(dist(p.arm.elbow,p.arm.wrist)-75)<1e-6);
   assert.ok(Math.abs(dist(p.body.shoulder,p.body.pivot)-Math.hypot(96,112))<1e-6);
   for(const n of ['shoulder','elbow','wrist'])assert.ok(dist(p.arm[n],prev.arm[n])<2,`${n} jumps`);
   peak=Math.max(peak,p.body.angle);prev=p;s.update(1);
  }
  assert.ok(peak>=7.99);assert.equal(s.enemy.phase,'guard');assert.equal(pose(s).body.angle,0);
  assert.equal(s.duel.recoveryFrom,'hit');assert.equal(s.hp,2);
 }
});
test('70 ms hitstop and pause freeze the captured reaction; reset and target change discard it',()=>{
 const s=create();advance(s,1400);hit(s);const atHit=pose(s);advance(s,69);assert.deepEqual(pose(s),atHit);
 advance(s,60);s.paused=true;const paused=pose(s);advance(s,1000);assert.deepEqual(pose(s),paused);s.paused=false;
 s.reset();assert.equal(s.enemyReactionFrom,null);assert.equal(pose(s).body.angle,0);
 hit(s);advance(s,1300);s.setTarget('seal');assert.equal(s.enemyReactionFrom,null);assert.equal(s.enemy.bodyReaction,undefined);
});
test('low hit uses shared parts, fatal thrust captures the interrupted rig; next hit captures a fresh pose',()=>{
 const s=create(false);hit(s,'sweep');assert.equal(s.enemy.bodyReaction.kind,'sweep');assert.ok(enemyBodyPose(s.enemy,rig));advance(s,1400);
 hit(s);assert.equal(s.hp,1);assert.ok(s.enemy.bodyReaction);assert.equal(s.enemy.bodyReaction.from.phase,'guard');advance(s,1400);
 hit(s);assert.equal(s.hp,0);assert.equal(s.enemyReactionFrom.fatal,true);assert.ok(s.enemy.bodyReaction);assert.ok(enemyBodyPose(s.enemy,rig));
 advance(s,1500);assert.equal(s.enemy.phase,'dissolve');assert.equal(pose(s).weapon.landed,true);
});
