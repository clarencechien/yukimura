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
