import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {fallPose,fallSword} from '../docs/routes/jigoku-2d/free-arm-settle/fall.mjs';
import {settlePose} from '../docs/routes/jigoku-2d/free-arm-settle/rig.mjs';
import {yieldPose} from '../docs/routes/jigoku-2d/free-arm-settle/yield.mjs';
import {releasingSword} from '../docs/routes/jigoku-2d/free-arm-settle/release.mjs';
const read=p=>JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/'+p)),m=read('free-arm-settle/settle.json'),tr=read('free-arm-transition/transition.json'),k=read('free-arm-parts/parts.json'),s=read('free-arm-support/support.json'),rig=read('combat/enemy-rig.json'),rel=read('free-arm-settle/release.json'),base=read('free-arm-settle/fall.json'),bridge=read('free-arm-settle/bridge.json');
const pose=(t,meta=bridge)=>fallPose(t,m,tr,k,s,meta),weapon=(t,meta=bridge)=>fallSword(t,pose(t,meta),m,rig,releasingSword(t,settlePose(t,m,tr,k,s),m,rig,rel),yieldPose(t,m,tr,k,s),meta),d=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
test('bridge reuses existing candidate; original later keys and completed poses remain exact',()=>{
 assert.deepEqual(bridge.frames.slice(1),base.frames);assert.match(bridge.frames[0].source,/side-fall-bowed-head\.png$/);
 for(let t=330;t<=1180;t+=.5){assert.deepEqual(pose(t),pose(t,base));assert.deepEqual(weapon(t),weapon(t,base));}
 for(let t=1260;t<=1800;t+=.5){const a=pose(t),b=pose(t,base);a.fallFrame--;assert.deepEqual(a,b);assert.deepEqual(weapon(t),weapon(t,base));}
});
test('new bridge appears only between 1200 and 1240 ms; shoulder and both fixed arms stay connected',()=>{
 for(const [t,i] of [[1200,-1],[1200.001,0],[1220,0],[1240,0],[1240.001,1],[1320,1],[1320.001,2],[1440,2],[1440.001,3]])assert.equal(pose(t).fallFrame,i);
 for(let t=1180.001;t<1260;t+=.1){const p=pose(t),w=weapon(t);for(const [a,b,n] of [[p.shoulder,p.elbow,85],[p.elbow,p.wrist,90],[w.shoulder,w.elbow,65],[w.elbow,w.wrist,75]])assert.ok(Math.abs(d(a,b)-n)<1e-6);assert.ok(d(p.wrist,p.target)<1e-6);assert.ok(d(w.wrist,w.target)<1e-6);}
 for(const t of [1180,1200,1220,1240,1260])for(const fn of [pose,weapon])for(const key of ['shoulder','elbow','wrist'])assert.ok(d(fn(t-.001)[key],fn(t+.001)[key])<.01);
});
test('bridge does not move the fallen blade; reverse scrubbing gives identical state',()=>{
 const still=weapon(1180);for(let t=1180;t<1260;t+=.1)for(const key of ['grip','bladeAngle','grounded','bounds'])assert.deepEqual(weapon(t)[key],still[key]);
 const p=pose(1225),w=weapon(1225);for(const t of [1800,1190,330,1400]){pose(t);weapon(t);}assert.deepEqual(pose(1225),p);assert.deepEqual(weapon(1225),w);
});
