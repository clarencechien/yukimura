import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {CombatState} from '../docs/routes/jigoku-2d/combat/combat-state.mjs';
import {enemyBodyPose,ENEMY_LEGS} from '../docs/routes/jigoku-2d/combat/enemy-body.mjs';
import {enemyArm} from '../docs/routes/jigoku-2d/combat/enemy-arm.mjs';
import {enemyWeapon} from '../docs/routes/jigoku-2d/combat/enemy-weapon.mjs';
const read=n=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/combat/${n}.json`)),rig=read('enemy-rig');rig.duelBindings=read('duel-art').enemy.bindings;
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(dist(a,b)<1e-6),advance=(s,ms)=>{for(let i=0;i<ms;i++)s.update(1);};
function hit(kind,start=0,duel=true){const s=new CombatState(read('shared-spear-track'),()=>{},read('shared-sweep-track'));if(duel)s.startDuel();s.hp=1;advance(s,start);assert.ok(s.attack(kind));for(let i=0;i<700&&!s.freeze;i++)s.update(1);assert.equal(s.hp,0);assert.equal(s.enemyAge,0);return s;}
const pose=s=>({body:enemyBodyPose(s.enemy,rig),arm:enemyArm(s.enemy,s.enemyAge,true,rig),weapon:enemyWeapon(s.enemy,s.enemyAge,true,rig)});
test('fatal thrust and sweep preserve the interrupted torso, legs, wrist and blade at contact in every duel stage',()=>{
 for(const kind of ['thrust','sweep']){
  const stages=new Set();for(const start of [0,900,1250,1550,1700,1800,1900,2000,2100,2400]){
   const s=hit(kind,start),{from,fromAge}=s.enemy.bodyReaction;stages.add(from.intent);const p=pose(s),a=enemyArm(from,fromAge,false,rig),w=enemyWeapon(from,fromAge,false,rig);
   assert.deepEqual(p.body,enemyBodyPose(from,rig));for(const n of ['shoulder','elbow','wrist'])near(p.arm[n],a[n]);near(p.weapon.grip,w.grip);assert.ok(Math.abs(p.weapon.angle-w.angle)<1e-6);
  }assert.deepEqual([...stages].sort(),['recovery','strike','waiting','windup']);
 }
});
test('fatal loading retains limb lengths and sequential recovery steps, with continuous arm and blade through the 180 ms buckle handoff',()=>{
 for(const kind of ['thrust','sweep'])for(const start of [0,1700,1900]){
  const s=hit(kind,start),descriptor=s.enemy.bodyReaction;advance(s,70);let prev=pose(s);
  for(let age=0;age<=181;age++){
   const p=pose(s);for(const n of ['shoulder','elbow','wrist'])assert.ok(dist(p.arm[n],prev.arm[n])<2,`${kind} ${age} ${n}`);
   assert.ok(dist(p.weapon.grip,prev.weapon.grip)<2);assert.ok(Math.abs(dist(p.arm.shoulder,p.arm.elbow)-65)<1e-6);assert.ok(Math.abs(dist(p.arm.elbow,p.arm.wrist)-75)<1e-6);
   if(age<180){assert.ok(p.body);for(const [side,j] of Object.entries(ENEMY_LEGS)){const leg=p.body.legs[side];assert.ok(p.body.feet.left.lift===0||p.body.feet.right.lift===0);assert.ok(Math.abs(dist(leg.hip,leg.knee)-dist(j.hip,j.knee))<1e-6);assert.ok(Math.abs(dist(leg.knee,leg.ankle)-dist(j.knee,j.ankle))<1e-6);}}
   else{assert.equal(p.body,null);assert.equal(s.enemy.phase,'buckle');
    if(age===180){const endpoint={...s.enemy,bodyReaction:{...descriptor,age:180}},arm=enemyArm(endpoint,180,true,rig),weapon=enemyWeapon(endpoint,180,true,rig),authoredArm=enemyArm(s.enemy,180,true,rig),authoredWeapon=enemyWeapon(s.enemy,180,true,rig);for(const n of ['shoulder','elbow','wrist'])near(arm[n],authoredArm[n]);near(weapon.grip,authoredWeapon.grip);assert.ok(Math.abs(weapon.angle-authoredWeapon.angle)<1e-6);}
   }
   prev=p;s.update(1);
  }
 }
});
test('fatal bridge freezes for hitstop and pause, then reset clears captured death state',()=>{
 for(const kind of ['thrust','sweep']){const s=hit(kind),p=pose(s);advance(s,69);assert.deepEqual(pose(s),p);advance(s,100);s.paused=true;const held=pose(s);advance(s,500);assert.deepEqual(pose(s),held);s.paused=false;s.reset();assert.equal(s.enemyReactionFrom,null);assert.equal(s.hp,3);assert.equal(enemyBodyPose(s.enemy,rig).root.y,0);}
});
test('fatal bridge rejoins authored crouch and preserves hand relaxation, blade release, ground landing and fade',()=>{
 for(const kind of ['thrust','sweep']){const s=hit(kind,0,false);advance(s,70);let last;
  for(let age=0;age<=1701;age++){
   const p=pose(s);if(age===250)assert.equal(s.enemy.phase,'crouch');if(age===430)assert.equal(p.arm.handState,'relax');if(age===499)last=p.weapon;
   if(age===500){assert.equal(p.arm.handState,'open');assert.equal(p.weapon.held,false);assert.ok(dist(p.weapon.grip,last.grip)<.1);}
   if(age===780)assert.equal(p.weapon.landed,true);if(age===1700){assert.equal(s.enemy.phase,'gone');assert.equal(p.weapon.alpha,0);}s.update(1);
  }
 }
});
