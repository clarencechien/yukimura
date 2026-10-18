import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {MARKS,LENGTHS,assess,shoulderPlan,trajectory} from '../docs/routes/jigoku-2d/free-arm/reach.mjs';
const near=(a,b,tol=1e-6)=>assert.ok(Math.abs(a-b)<tol,`${a} != ${b}`),dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
test('existing kneel is unreachable with candidate fixed lengths; redraw is not silently accepted',()=>{
 assert.equal(assess(MARKS.buckle).reachable,true);assert.equal(assess(MARKS.crouch).reachable,true);
 assert.ok(assess(MARKS.kneel).overreach>30);assert.ok(assess(MARKS.candidate).overreach>9);
 for(const m of Object.values(MARKS)){const a=assess(m);near(dist(a.pose.shoulder,a.pose.elbow),85);near(dist(a.pose.elbow,a.pose.wrist),90);if(!a.reachable)assert.ok(a.miss>0);}
});
test('shoulder plan retains wrist and horizontal position, reaches with 5 px reserve and does not mutate marks',()=>{
 const original=JSON.stringify(MARKS);
 for(const m of Object.values(MARKS)){const p=shoulderPlan(m);assert.deepEqual(p.wrist,m.wrist);near(p.shoulder[0],m.shoulder[0]);assert.ok(p.lowering>=0);assert.ok(assess(p).distance<=170+1e-6);assert.equal(assess(p).reachable,true);}
 assert.equal(JSON.stringify(MARKS),original);assert.throws(()=>shoulderPlan({shoulder:[0,0],wrist:[200,10]}));
});
test('full planned reach keeps lengths, bend side and target with continuous key boundaries',()=>{
 for(const candidate of [false,true]){
  for(let age=180;age<=420;age+=.5){const p=trajectory(age,{planned:true,candidate});near(dist(p.shoulder,p.elbow),LENGTHS[0]);near(dist(p.elbow,p.wrist),LENGTHS[1]);near(p.miss,0);assert.ok(p.distance<=170+1e-6);const cross=(p.wrist.x-p.shoulder.x)*(p.elbow.y-p.shoulder.y)-(p.wrist.y-p.shoulder.y)*(p.elbow.x-p.shoulder.x);assert.ok(cross<0);}
  for(const age of [180,250,330,420]){const a=trajectory(age-.0001,{planned:true,candidate}),b=trajectory(age+.0001,{planned:true,candidate});for(const n of ['shoulder','elbow','wrist'])assert.ok(dist(a[n],b[n])<.001);}
 }
 assert.throws(()=>trajectory(NaN));assert.deepEqual(trajectory(-1),trajectory(180));assert.deepEqual(trajectory(500),trajectory(420));
});
const report={lengths:LENGTHS,marks:MARKS,measurements:Object.fromEntries(Object.entries(MARKS).map(([name,m])=>[name,{...assess(m),plannedShoulder:shoulderPlan(m).shoulder,lowering:shoulderPlan(m).lowering}])),scope:'Manual 2D reach diagnosis and authoring targets only; not installed in combat, no anatomical or force validation.'};
fs.writeFileSync('docs/routes/jigoku-2d/free-arm/reach-report.json',JSON.stringify(report,null,2)+'\n');
