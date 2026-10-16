import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {legEntryPose} from '../docs/routes/jigoku-2d/free-arm-settle/leg-entry.mjs';
const meta=JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/free-arm-settle/leg-entry.json'));
test('calf begins at its original registration and keeps all alpha cells above projected ground',()=>{
 const start=legEntryPose(1000,meta);assert.deepEqual(start.point,{x:meta.calf.pivot[0],y:meta.calf.pivot[1]});assert.equal(start.angle,0);
 let last=-Infinity;
 for(let t=1000;t<=1200;t+=.2){const p=legEntryPose(t,meta),r=p.angle*Math.PI/180;assert.ok(p.angle>=last);last=p.angle;
  const bottom=Math.max(...meta.calf.hull.map(([x,y])=>p.point.y+x*Math.sin(r)+y*Math.cos(r)));assert.ok(bottom<=meta.groundY);}
});
test('authored rotation settles smoothly at endpoints and reverse seeking is deterministic',()=>{
 assert.deepEqual(legEntryPose(900,meta),legEntryPose(1000,meta));assert.deepEqual(legEntryPose(1200,meta),legEntryPose(1300,meta));
 for(const t of [1000,1200]){const a=legEntryPose(t-.001,meta),b=legEntryPose(t+.001,meta);assert.ok(Math.hypot(a.point.x-b.point.x,a.point.y-b.point.y)<1e-6);assert.ok(Math.abs(a.angle-b.angle)<1e-6);}
 const p=legEntryPose(1100,meta);legEntryPose(1200,meta);assert.deepEqual(legEntryPose(1100,meta),p);assert.throws(()=>legEntryPose(NaN,meta));
});
