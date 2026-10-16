import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {settlePose,rotate} from '../docs/routes/jigoku-2d/free-arm-settle/rig.mjs';
import {settlingSword,SWORD_SOCKET_OFFSET} from '../docs/routes/jigoku-2d/free-arm-settle/sword.mjs';
const read=p=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/${p}`));
const m=read('free-arm-settle/settle.json'),tr=read('free-arm-transition/transition.json'),k=read('free-arm-parts/parts.json'),s=read('free-arm-support/support.json'),rig=read('combat/enemy-rig.json');
const body=t=>settlePose(t,m,tr,k,s),pose=t=>settlingSword(body(t),m,rig),d=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(Math.abs(a-b)<1e-6,`${a} vs ${b}`);
test('far wrist target stays reachable without solver clamping, fixed lengths and neutral projected wrist',()=>{
 for(let t=330;t<=540;t+=.1){const p=pose(t);near(d(p.shoulder,p.elbow),65);near(d(p.elbow,p.wrist),75);near(d(p.wrist,p.target),0);
  const v=rotate({x:Math.cos(rig.parts.grip.axisDegrees*Math.PI/180),y:Math.sin(rig.parts.grip.axisDegrees*Math.PI/180)},p.handAngle);
  near(v.x,(p.wrist.x-p.elbow.x)/75);near(v.y,(p.wrist.y-p.elbow.y)/75);
 }
});
test('far shoulder follows the torso hinge and remains continuous at body switches',()=>{
 for(let t=388.001;t<=540;t+=.1){const p=body(t),a=pose(t),h=p.torso,v=rotate({x:m.shoulder[0]+SWORD_SOCKET_OFFSET.x-h.pivot.x,y:m.shoulder[1]+SWORD_SOCKET_OFFSET.y-h.pivot.y},h.angle);near(a.shoulder.x,h.pivot.x+h.offset.x+v.x);near(a.shoulder.y,h.pivot.y+h.offset.y+v.y);}
 for(const t of [341,364,388,400,410,420,500])for(const key of ['shoulder','elbow','wrist','grip'])assert.ok(d(pose(t-1e-5)[key],pose(t+1e-5)[key])<.001);
});
test('held katana pivot stays inside the painted fist at every sample; scrubbing is deterministic',()=>{
 const h=rig.parts.grip;
 for(let t=330;t<=540;t+=.1){const p=pose(t),q=rotate({x:h.gripPoint[0]-h.pivot[0],y:h.gripPoint[1]-h.pivot[1]},p.handAngle);near(p.grip.x,p.wrist.x+q.x);near(p.grip.y,p.wrist.y+q.y);assert.equal(p.bladeAngle,p.handAngle);assert.equal(p.held,true);}
 const reference=pose(440);for(const t of [540,330,480,376,440])pose(t);assert.deepEqual(pose(440),reference);
});
