import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {CombatState} from '../docs/routes/jigoku-2d/combat/combat-state.mjs';
const read=n=>JSON.parse(fs.readFileSync(new URL('../docs/routes/jigoku-2d/combat/'+n,import.meta.url)));
const make=()=>new CombatState(read('shared-spear-track.json'),()=>{},read('sweep-track.json'));
function advance(s,ms,step=10){while(ms>0){const dt=Math.min(ms,step);s.update(dt);ms-=dt;}}
test('low sweep hits the near warrior once, misses far warrior and suspended seal',()=>{
 for(const [range,target,hits] of [['near','warrior',1],['far','warrior',0],['near','seal',0]]){
  const s=make();s.setRange(range);s.setTarget(target);assert.ok(s.attack('sweep'));advance(s,250);assert.equal(s.hits,0);advance(s,1500);assert.equal(s.hits,hits);assert.equal(s.phase,'idle');
 }
});
test('only thrust recovery accepts one queued sweep; combo recovers after two hits',()=>{
 const s=make();s.attack();assert.equal(s.attack('sweep'),false);advance(s,850);assert.ok(s.canQueueSweep);assert.ok(s.attack('sweep'));assert.equal(s.attack('sweep'),false);assert.equal(s.attack(),false);assert.equal(s.swings,1);advance(s,2000);assert.equal(s.swings,2);assert.equal(s.hits,2);assert.equal(s.phase,'idle');assert.equal(s.queuedAttack,null);
});
test('pause retains queue and reset cancels it; late input does not queue',()=>{
 const s=make();s.attack();advance(s,850);s.attack('sweep');s.paused=true;const frame=s.frame;advance(s,1200);assert.equal(s.frame,frame);assert.equal(s.swings,1);assert.equal(s.queuedAttack,'sweep');s.reset();s.paused=false;advance(s,1600);assert.equal(s.swings,0);assert.equal(s.queuedAttack,null);
 s.attack();advance(s,1150);assert.equal(s.canQueueSweep,false);assert.equal(s.attack('sweep'),false);
});
test('sweep hitstop and damage survive coarse and fine render timesteps',()=>{
 for(const step of [4,33,100,250]){const s=make();s.attack('sweep');advance(s,1800,step);assert.equal(s.hits,1);assert.equal(s.hp,2);assert.equal(s.swings,1);}
 const s=make();s.attack('sweep');while(!s.freeze)s.update(1);const f=s.frame;s.update(40);assert.equal(s.frame,f);assert.ok(s.freeze>0);
});
test('dead target rejects both attacks and has no combo window',()=>{
 const s=make();for(let i=0;i<3;i++){s.attack('sweep');advance(s,1500);}assert.equal(s.hp,0);assert.equal(s.canQueueSweep,false);assert.equal(s.attack('sweep'),false);assert.equal(s.attack(),false);
});

test('low hit has its own recovery sequence and resets cleanly',()=>{
 const s=make();s.attack('sweep');const seen=[];
 for(let t=0;t<1600;t+=10){s.update(10);if(seen.at(-1)!==s.enemy.phase)seen.push(s.enemy.phase);}
 assert.deepEqual(seen,['guard','leg-flinch','low-stagger','leg-rise','guard-settle','guard']);assert.equal(s.hp,2);
 s.reset();assert.equal(s.lastHitKind,null);s.attack();advance(s,550);assert.equal(s.enemy.phase,'flinch');assert.equal(s.lastHitKind,'thrust');
});
test('fatal low hit joins shared crouch and death sequence; no upper-body recoil',()=>{
 const s=make();s.hp=1;s.attack('sweep');const seen=[];
 for(let t=0;t<2300;t+=10){s.update(10);if(seen.at(-1)!==s.enemy.phase)seen.push(s.enemy.phase);}
 assert.deepEqual(seen,['guard','leg-flinch','low-stagger','crouch','kneel','brace','yield','sink','lower','settle','fallen','dissolve','gone']);assert.equal(s.hp,0);assert.equal(s.enemy.alpha,0);
});
test('low-hit reaction freezes during hitstop and pause, clears on target change',()=>{
 const s=make();s.attack('sweep');while(!s.freeze)s.update(1);const before=s.enemy;s.update(40);assert.deepEqual(s.enemy,before);assert.equal(s.enemyAge,0);
 s.paused=true;advance(s,500);assert.deepEqual(s.enemy,before);s.paused=false;advance(s,1600);s.setTarget('seal');assert.equal(s.lastHitKind,null);assert.equal(s.enemy.phase,'guard');
});

test('both recovery poses show at 30 Hz without extending recovery and freeze on pause',()=>{
 const s=make();s.enemyHit=true;s.lastHitKind='sweep';
 for(let offset=0;offset<34;offset++){
  const seen=new Set();for(let age=260+offset;age<420;age+=1000/30){s.enemyAge=age;seen.add(s.enemy.pose);}
  assert.ok(seen.has(14)&&seen.has(15));
 }
 s.enemyAge=300;s.paused=true;s.update(100);assert.equal(s.enemy.pose,14);assert.equal(s.enemyAge,300);
 s.paused=false;s.update(120);assert.equal(s.enemy.phase,'guard');
 s.hp=0;s.enemyAge=300;assert.equal(s.enemy.phase,'crouch');
 s.reset();assert.equal(s.enemy.phase,'guard');assert.equal(s.lastHitKind,null);
});
