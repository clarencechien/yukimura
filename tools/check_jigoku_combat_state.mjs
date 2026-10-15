import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {CombatState,segmentHitsCircle} from '../docs/routes/jigoku-2d/combat/combat-state.mjs';
const track=JSON.parse(fs.readFileSync(new URL('../docs/routes/jigoku-2d/combat/spear-track.json',import.meta.url)));
const finish=(s,step=16.67)=>{for(let elapsed=0;elapsed<1500;elapsed+=step)s.update(step);};
test('three distinct strikes break seal; spam cannot add damage',()=>{
 const events=[];const s=new CombatState(track,e=>events.push(e));
 for(let i=0;i<3;i++){assert.equal(s.attack(),true);assert.equal(s.attack(),false);finish(s);assert.equal(s.hp,2-i);}
 assert.equal(s.attack(),false);assert.equal(s.hits,3);assert.equal(events.filter(e=>e.type==='hit').length,3);
});
test('out-of-range thrust misses and cannot change range mid-attack',()=>{
 const s=new CombatState(track);assert.equal(s.setRange('far'),true);s.attack();assert.equal(s.setRange('near'),false);finish(s);
 assert.equal(s.hp,3);assert.equal(s.hits,0);assert.equal(s.swings,1);
});
test('contact only occurs in active frames, hitstop freezes pose',()=>{
 const s=new CombatState(track);s.attack();s.update(200);s.update(200);assert.equal(s.hp,3);s.update(67);assert.equal(s.hp,2);assert.equal(s.frame,14);
 s.update(40);assert.equal(s.frame,14);s.update(80);assert.ok(s.frame>14);assert.equal(s.hp,2);
});
test('coarse and fine render timesteps cannot skip or duplicate contact',()=>{
 for(const step of [4,1000/60,1000/30,100,250]){const s=new CombatState(track);s.attack();finish(s,step);assert.equal(s.hits,1);assert.equal(s.phase,'idle');}
});
test('pause stops attack and idle timers; reset clears combat',()=>{
 const s=new CombatState(track);s.attack();s.update(200);s.paused=true;const frame=s.frame;s.update(100);assert.equal(s.frame,frame);assert.equal(s.attack(),false);
 s.paused=false;finish(s);s.reset();assert.equal(s.hp,3);assert.equal(s.swings,0);assert.equal(s.freeze,0);
});
test('swept segment detects crossing, tangency and misses',()=>{
 assert.equal(segmentHitsCircle({x:0,y:0},{x:100,y:0},{x:50,y:0},2),true);
 assert.equal(segmentHitsCircle({x:0,y:0},{x:100,y:0},{x:50,y:2},2),true);
 assert.equal(segmentHitsCircle({x:0,y:0},{x:100,y:0},{x:50,y:3},2),false);
 assert.equal(segmentHitsCircle({x:0,y:0},{x:0,y:0},{x:0,y:0},2),true);
});
test('enemy hurt holds during hitstop and pause, then recovers',()=>{
 const s=new CombatState(track);s.attack();s.update(250);s.update(217);assert.equal(s.enemy.phase,'flinch');const age=s.enemyAge;s.update(40);assert.equal(s.enemyAge,age);
 s.paused=true;s.update(200);assert.equal(s.enemyAge,age);s.paused=false;finish(s);assert.equal(s.enemy.phase,'guard');
});
test('fatal hit orders all twelve silhouettes and dissolve; reset restores guard',()=>{
 const s=new CombatState(track);for(let i=0;i<2;i++){s.attack();finish(s);}
 s.attack();const seen=[];for(let i=0;i<170;i++){s.update(20);if(seen.at(-1)!==s.enemy.phase)seen.push(s.enemy.phase);}
 assert.deepEqual(seen,['guard','flinch','hurt','buckle','crouch','kneel','brace','yield','sink','lower','settle','fallen','dissolve','gone']);assert.equal(s.enemy.alpha,0);assert.equal(s.attack(),false);
 s.reset();assert.equal(s.enemy.phase,'guard');assert.equal(s.enemy.alpha,1);assert.equal(s.hp,3);
});
test('target switch resets reaction and is blocked during attack',()=>{
 const s=new CombatState(track);assert.equal(s.targetKind,'warrior');s.attack();assert.equal(s.setTarget('seal'),false);finish(s);assert.equal(s.setTarget('seal'),true);assert.equal(s.hp,3);assert.equal(s.enemy.phase,'guard');assert.equal(s.setTarget('unknown'),false);
});

test('nonfatal recoil eases through flinch and never enters a death pose',()=>{
 const s=new CombatState(track);s.attack();const seen=[];
 for(let i=0;i<100;i++){s.update(20);if(seen.at(-1)!==s.enemy.phase)seen.push(s.enemy.phase);assert.ok(s.enemy.pose<=2);}
 assert.deepEqual(seen,['guard','flinch','hurt','flinch','guard']);assert.equal(s.hp,2);
});
