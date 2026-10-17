import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {sequenceBodyPose} from '../docs/routes/jigoku-2d/free-arm-settle/body-sequence.mjs';
import {fallPose} from '../docs/routes/jigoku-2d/free-arm-settle/fall.mjs';
const root='docs/routes/jigoku-2d/',read=p=>JSON.parse(fs.readFileSync(root+p)),m=read('free-arm-settle/body-sequence.json'),settle=read('free-arm-settle/settle.json'),transition=read('free-arm-transition/transition.json'),kit=read('free-arm-parts/parts.json'),support=read('free-arm-support/support.json'),fall=read('free-arm-settle/bridge.json');
test('three rigid body poses keep the actual moving shoulder and visible-cell support on ground',()=>{
 const seen=new Set();let maxAngle=0;
 for(let i=0;i<2400;i++){
  const age=1200+(i+1)/10,p=fallPose(age,settle,transition,kit,support,fall),f=m.frames[p.fallFrame],q=sequenceBodyPose(p.shoulder,f,m);seen.add(f.id);assert.deepEqual(q.point,p.shoulder);assert.ok(Math.abs(q.bounds.bottom-m.groundY)<1e-6);assert.ok(Math.abs(q.angle)<m.rotationLimit);maxAngle=Math.max(maxAngle,Math.abs(q.angle));
  const a=q.angle*Math.PI/180,c=Math.cos(a),s=Math.sin(a);assert.ok(Math.abs(c*c+s*s-1)<1e-12);
  for(const [x,y] of f.supportHull){const dx=x-f.pivot[0],dy=y-f.pivot[1],rx=dx*c-dy*s,ry=dx*s+dy*c;assert.ok(Math.abs(Math.hypot(dx,dy)-Math.hypot(rx,ry))<1e-9);assert.ok(q.point.y+ry<=m.groundY+1e-6);}
 }
 assert.equal(seen.size,3);assert.ok(maxAngle<5);
});
test('contact support is monotonic across the allowed rotation interval for all three authored silhouettes',()=>{
 for(const f of m.frames){let previous=-Infinity;for(let i=0;i<=480;i++){const a=(-12+i*.05)*Math.PI/180,value=Math.max(...f.supportHull.map(([x,y])=>(x-f.pivot[0])*Math.sin(a)+(y-f.pivot[1])*Math.cos(a)));assert.ok(value>previous);previous=value;}}
});
test('contact pose is deterministic when scrubbing backwards and rejects unreachable or nonfinite inputs',()=>{
 const f=m.frames[1],p={x:494,y:541},a=sequenceBodyPose(p,f,m);sequenceBodyPose({x:480,y:550},f,m);assert.deepEqual(sequenceBodyPose(p,f,m),a);
 assert.throws(()=>sequenceBodyPose({x:NaN,y:541},f,m),/finite/);assert.throws(()=>sequenceBodyPose({x:494,y:100},f,m),/outside rotation/);
});
