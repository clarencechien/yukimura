import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {CombatState} from '../docs/routes/jigoku-2d/combat/combat-state.mjs';
import {enemyBodyPose} from '../docs/routes/jigoku-2d/combat/enemy-body.mjs';
import {enemyArm} from '../docs/routes/jigoku-2d/combat/enemy-arm.mjs';
const read=n=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/combat/${n}.json`)),rig=read('enemy-rig');
const create=()=>{const s=new CombatState(read('shared-spear-track'),()=>{},read('shared-sweep-track'));s.startDuel();return s;};
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
test('one shoulder socket moves continuously through waiting, windup, strike and recovery',()=>{
 const s=create();let prev=null,max=0;
 for(let i=0;i<3500;i++){
  const e=s.enemy,p=enemyBodyPose(e,rig),arm=enemyArm(e,s.enemyAge,false,rig);
  assert.ok(p);assert.deepEqual(arm.shoulder,p.shoulder);assert.ok(p.angle>=-10&&p.angle<=4);
  if(prev){max=Math.max(max,dist(p.shoulder,prev.shoulder));assert.ok(dist(arm.wrist,prev.wrist)<1.5,'No wrist jump at pose/stage boundaries');}
  prev={...p,wrist:arm.wrist};s.update(1);
 }
 assert.ok(max<.31);assert.ok(Math.abs(enemyBodyPose(s.enemy,rig).angle)<1e-8);
});
test('rigid chest preserves socket-to-waist distance; waiting and hit recovery do not replay a slash',()=>{
 for(const stage of ['windup','strike','recovery'])for(let age=0;age<1500;age++){
  const p=enemyBodyPose({phase:'guard',intent:stage,intentAge:age,recoveryFrom:'attack'},rig);
  assert.ok(Math.abs(dist(p.shoulder,p.pivot)-Math.hypot(481-577,270-382))<1e-6);
 }
 for(const intent of ['waiting','recovery'])assert.equal(enemyBodyPose({phase:'guard',intent,intentAge:80,recoveryFrom:'hit'},rig).angle,0);
 for(const phase of ['flinch','hurt','leg-flinch','fallen','gone'])assert.equal(enemyBodyPose({phase,pose:1},rig),null);
});
test('pause freezes torso; reset restores neutral; interrupted attacks retain authored hit and death poses',()=>{
 const s=create();for(let i=0;i<1800;i++)s.update(1);const before=enemyBodyPose(s.enemy,rig);
 s.paused=true;s.update(1000);assert.deepEqual(enemyBodyPose(s.enemy,rig),before);s.paused=false;s.reset();assert.ok(Math.abs(enemyBodyPose(s.enemy,rig).angle)<1e-8);
 s.attack();for(let i=0;i<600;i++)s.update(1);assert.equal(s.hp,2);assert.equal(enemyBodyPose(s.enemy,rig),null);
 for(let i=0;i<600;i++)s.update(1);assert.ok(Math.abs(enemyBodyPose(s.enemy,rig).angle)<1e-8);
});
