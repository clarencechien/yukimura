import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {settlePose,rotate} from '../docs/routes/jigoku-2d/free-arm-settle/rig.mjs';
import {yieldPose,yieldSword} from '../docs/routes/jigoku-2d/free-arm-settle/yield.mjs';
import {releasingSword} from '../docs/routes/jigoku-2d/free-arm-settle/release.mjs';
import {fallPose,fallSword} from '../docs/routes/jigoku-2d/free-arm-settle/fall.mjs';
import {SWORD_SOCKET_OFFSET} from '../docs/routes/jigoku-2d/free-arm-settle/sword.mjs';
const read=p=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/${p}`)),m=read('free-arm-settle/settle.json'),tr=read('free-arm-transition/transition.json'),k=read('free-arm-parts/parts.json'),s=read('free-arm-support/support.json'),rig=read('combat/enemy-rig.json'),rel=read('free-arm-settle/release.json'),meta=read('free-arm-settle/fall.json');
const base=t=>settlePose(t,m,tr,k,s),unload=t=>yieldPose(t,m,tr,k,s),pose=t=>fallPose(t,m,tr,k,s,meta),released=t=>releasingSword(t,base(t),m,rig,rel),weapon=t=>fallSword(t,pose(t),m,rig,released(t),unload(t),meta),d=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(Math.abs(a-b)<1e-6,`${a} vs ${b}`);
test('previous unloading remains exact, each authored side-fall pose is used and final state holds',()=>{
 for(let t=330;t<=1180;t+=.5){assert.deepEqual(pose(t),unload(t));assert.deepEqual(weapon(t),yieldSword(t,unload(t),m,rig,released(t)));}
 for(const [time,index] of [[1220,-1],[1220.001,0],[1260,0],[1320,0],[1320.001,1],[1380,1],[1440,1],[1440.001,2],[1500,2]])assert.equal(pose(time).fallFrame,index);
 assert.deepEqual(pose(1500),pose(1800));assert.deepEqual(weapon(1500),weapon(1800));assert.throws(()=>pose(NaN));
});
test('both shared arms remain reachable without clamping and shoulders stay continuous at image switches',()=>{
 for(let t=1180.1;t<=1800;t+=.25){const p=pose(t),w=weapon(t);near(d(p.shoulder,p.elbow),85);near(d(p.elbow,p.wrist),90);near(d(p.wrist,p.target),0);near(d(w.shoulder,w.elbow),65);near(d(w.elbow,w.wrist),75);near(d(w.wrist,w.target),0);
  if(p.fallFrame>=0){const f=meta.frames[p.fallFrame];near(f.shoulder[0]+p.fallOffset.x,p.shoulder.x);near(f.shoulder[1]+p.fallOffset.y,p.shoulder.y);}
  const delta=rotate(SWORD_SOCKET_OFFSET,unload(t).torso.angle);near(w.shoulder.x,p.shoulder.x+delta.x);near(w.shoulder.y,p.shoulder.y+delta.y);
 }
 for(const t of [1180,1220,1260,1320,1380,1440,1500])for(const fn of [pose,weapon])for(const key of ['shoulder','elbow','wrist'])assert.ok(d(fn(t-.001)[key],fn(t+.001)[key])<.01);
});
test('fallen blade stays world-fixed through the body drawings and backward scrubbing',()=>{
 const reference=weapon(1180);for(let t=1180;t<=1800;t+=.25)for(const key of ['grip','bladeAngle','grounded','bounds'])assert.deepEqual(weapon(t)[key],reference[key]);
 const a=pose(1390),b=weapon(1390);for(const t of [1800,330,1240,1500]){pose(t);weapon(t);}assert.deepEqual(pose(1390),a);assert.deepEqual(weapon(1390),b);
});
