import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {settlePose,rotate} from '../docs/routes/jigoku-2d/free-arm-settle/rig.mjs';import {transitionPose} from '../docs/routes/jigoku-2d/free-arm-transition/rig.mjs';
const read=p=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/${p}`)),m=read('free-arm-settle/settle.json'),tr=read('free-arm-transition/transition.json'),k=read('free-arm-parts/parts.json'),s=read('free-arm-support/support.json'),pose=t=>settlePose(t,m,tr,k,s),d=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(Math.abs(a-b)<1e-6,`${a} vs ${b}`);
test('shin and shoe remain rigid, ankle joins and projected toe does not sink below its start',()=>{
 for(let t=388;t<=540;t+=.1){const p=pose(t),l=p.leg;near(d(l.knee,l.ankle),m.shinLength);near(d(l.ankle,l.toe),m.footLength);assert.ok(Math.abs(l.ankleDeflection)<=30);assert.ok(l.toe.y<=m.toe[1]+1e-6);}
});
test('foot stays still until palm contact and arm motion exactly reuses previous transition',()=>{
 const start=pose(400).leg;for(let t=330;t<=540;t+=.25){const p=pose(t),old=transitionPose(t,tr,k,s);for(const n of ['shoulder','elbow','wrist','heel'])assert.deepEqual(p[n],old[n]);if(t<=420)assert.deepEqual(p.leg,start);else near(d(p.heel,p.contact),0);}
});
test('hip hinge maps the original shoulder exactly and keeps waist translation below four pixels',()=>{
 for(let t=400;t<=540;t+=.1){const p=pose(t),h=p.torso,q=rotate({x:m.shoulder[0]-h.pivot.x,y:m.shoulder[1]-h.pivot.y},h.angle);near(q.x+h.pivot.x+h.offset.x,p.shoulder.x);near(q.y+h.pivot.y+h.offset.y,p.shoulder.y);assert.ok(Math.hypot(h.offset.x,h.offset.y)<4);}
});
test('foot rotation starts smoothly, ends smoothly and seeking stays deterministic',()=>{
 for(const t of [420,448,500]){const a=pose(t-1e-5).leg,b=pose(t+1e-5).leg;assert.ok(d(a.ankle,b.ankle)<.001);assert.ok(d(a.toe,b.toe)<.001);}
 assert.deepEqual(pose(470),pose(470));assert.throws(()=>pose(NaN));
});

test('shared lower body starts with the touch pose and stays active across 400 ms',()=>{
 assert.equal(pose(388).late,false);assert.equal(pose(388.001).late,true);
 for(let t=388.001;t<=540;t+=.1)assert.equal(pose(t).late,true);
 for(const t of [388.001,390,395,399.999,400,400.001,410,420]){const p=pose(t),h=p.torso,q=rotate({x:m.shoulder[0]-h.pivot.x,y:m.shoulder[1]-h.pivot.y},h.angle);near(q.x+h.pivot.x+h.offset.x,p.shoulder.x);near(q.y+h.pivot.y+h.offset.y,p.shoulder.y);}
 const a=pose(399.999).torso,b=pose(400.001).torso;assert.ok(d(a.offset,b.offset)<.001);assert.ok(Math.abs(a.angle-b.angle)<.001);
});
