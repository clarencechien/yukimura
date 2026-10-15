import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {CombatState} from '../docs/routes/jigoku-2d/combat/combat-state.mjs';
import {enemyArm,closedGrip} from '../docs/routes/jigoku-2d/combat/enemy-arm.mjs';
import {enemyWeapon} from '../docs/routes/jigoku-2d/combat/enemy-weapon.mjs';
const read=name=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/combat/${name}.json`));
const rig=read('enemy-rig');
function setup(){const events=[];const s=new CombatState(read('spear-track'),e=>events.push(e),read('sweep-track'));s.startDuel();return {s,events};}
function advance(s,ms,step=10){while(ms>0){const dt=Math.min(ms,step);s.update(dt);ms-=dt;}}
test('practice stays passive; duel warns before one timed hit; no repeated strike damage',()=>{
 const {s,events}=setup();s.startDuel(false);advance(s,10000);assert.equal(s.duel.playerHP,3);assert.equal(events.length,0);
 s.startDuel();advance(s,1200);assert.equal(s.duel.stage,'windup');assert.equal(s.duel.playerHP,3);
 advance(s,849);assert.equal(s.duel.playerHP,3);advance(s,1);assert.equal(s.duel.playerHP,2);advance(s,180);assert.equal(s.duel.playerHP,2);assert.equal(events.filter(e=>e.type==='player-hit').length,1);
});
test('timely guard blocks; early guard expires; cooldown rejects spam and attacks during guard',()=>{
 const {s}=setup();advance(s,1700);assert.ok(s.defend());assert.equal(s.defend(),false);assert.equal(s.attack(),false);
 advance(s,350);assert.equal(s.duel.blocks,1);assert.equal(s.duel.playerHP,3);advance(s,230);assert.equal(s.duel.guard,0);assert.equal(s.defend(),false);assert.ok(s.attack());
 const early=setup().s;advance(early,1200);early.defend();advance(early,850);assert.equal(early.duel.playerHP,2);
});
test('cannot defend during attack; hit interrupts windup and leaves a counterattack opening',()=>{
 const {s,events}=setup();advance(s,1250);s.attack();assert.equal(s.defend(),false);advance(s,600);assert.equal(s.hp,2);assert.equal(s.duel.stage,'recovery');assert.ok(events.some(e=>e.type==='interrupt'));advance(s,700);assert.equal(s.duel.playerHP,3);
});
test('pause and hitstop freeze enemy and guard clocks; hidden tab catch-up is capped',()=>{
 const {s}=setup();advance(s,1700);s.defend();s.paused=true;const before=JSON.stringify(s.duel);s.update(10000);assert.equal(JSON.stringify(s.duel),before);s.paused=false;
 s.freeze=70;advance(s,70);assert.equal(JSON.stringify(s.duel),before);s.update(10000);assert.equal(s.duel.age,750);assert.equal(s.duel.guard,330);
});
test('duel timing is stable across fractional, coarse and fine render steps',()=>{
 const results=[];for(const step of [1,4,1000/30,100,250]){const {s,events}=setup();advance(s,1700,step);s.defend();advance(s,4200,step);results.push({hp:s.duel.playerHP,blocks:s.duel.blocks,stage:s.duel.stage,events:events.map(e=>e.type)});}
 for(const row of results)assert.deepEqual(row,results[0]);
});
test('far attacks miss; seal disables duel; reset clears damage, guard, result and queue',()=>{
 const {s,events}=setup();s.setRange('far');advance(s,2300);assert.equal(s.duel.playerHP,3);assert.ok(events.some(e=>e.type==='enemy-miss'));
 s.setTarget('seal');assert.equal(s.duel.enabled,false);assert.equal(s.startDuel(),false);s.setTarget('warrior');s.startDuel();advance(s,2050);s.reset();assert.equal(s.duel.playerHP,3);assert.equal(s.duel.stage,'waiting');assert.equal(s.duel.guard,0);assert.equal(s.queuedAttack,null);
});
test('defeat stops further damage and input; victory preserves enemy death sequence',()=>{
 const {s,events}=setup();advance(s,10000);assert.equal(s.duel.playerHP,0);assert.equal(s.duel.result,'defeat');assert.equal(s.attack(),false);assert.equal(s.defend(),false);assert.equal(events.filter(e=>e.type==='defeat').length,1);
 s.reset();for(let i=0;i<3;i++){s.attack();advance(s,1300);}assert.equal(s.hp,0);assert.equal(s.duel.result,'victory');advance(s,2500);assert.equal(s.enemy.phase,'gone');assert.equal(s.duel.playerHP,3);
});
test('windup and strike keep rigid arm lengths and the same hand/weapon grip',()=>{
 for(const stage of ['waiting','windup','strike','recovery'])for(let age=0;age<850;age+=10){
  const enemy={pose:0,alpha:1,intent:stage,intentAge:age};const arm=enemyArm(enemy,0,false,rig),weapon=enemyWeapon(enemy,0,false,rig);
  for(const [a,b,len] of [[arm.shoulder,arm.elbow,65],[arm.elbow,arm.wrist,75]])assert.ok(Math.abs(Math.hypot(a.x-b.x,a.y-b.y)-len)<1e-6);
  assert.deepEqual(weapon.grip,closedGrip(arm,rig).grip);assert.equal(weapon.held,true);
 }
});
