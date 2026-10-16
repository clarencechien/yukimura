import {chromium} from '@playwright/test';import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
const root=process.cwd(),out='docs/routes/jigoku-2d/free-arm-settle',tmp='.tmp/free-arm-settle-capture';await fs.mkdir(tmp,{recursive:true});
const server=http.createServer(async(req,res)=>{try{let file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+'/'))throw Error('path');if((await fs.stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',({'.html':'text/html','.mjs':'text/javascript','.json':'application/json','.webp':'image/webp'})[path.extname(file)]||'application/octet-stream');res.end(await fs.readFile(file));}catch{res.statusCode=404;res.end('not found');}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const errors=[],failed=[],url=`http://127.0.0.1:${server.address().port}/${out}/`;
const state=p=>p.evaluate(()=>window.freeArmSettle),map=(m,p)=>({x:m.a*p.x+m.c*p.y+m.e,y:m.b*p.x+m.d*p.y+m.f});
const near=(a,b)=>assert.ok(Math.hypot(a.x-b.x,a.y-b.y)<.001,JSON.stringify({a,b}));
function check(r){
 assert.equal(r.records.length,r.armVisible?6:0);
 for(let panel=0;panel<2;panel++){
  const p=panel?r.pose:r.old,f=r.meta.frames[p.index],torso=r.bodies.find(b=>b.name==='torso'&&b.panel===panel),lower=r.bodies.find(b=>b.name==='lower'&&b.panel===panel),base=r.bases[panel];
  const socket=panel&&p.late?r.settle.shoulder:f.shoulder;
  near(map(torso.transform,{x:socket[0],y:socket[1]}),map(base,p.shoulder));
  if(panel&&p.late){assert.equal(lower.mode,'fixed');assert.deepEqual(lower.transform,base);}else assert.deepEqual(lower.offset,{x:0,y:0});
  const cap=r.bodies.find(b=>b.name==='cap'&&b.panel===panel);assert.equal(!!cap,r.capVisible&&r.armVisible);if(cap)assert.deepEqual(cap.transform,torso.transform);
  if(!r.armVisible)continue;
  const [u,a,h]=r.records.filter(x=>x.panel===panel);
  near(map(u.transform,{x:0,y:0}),map(base,p.shoulder));near(map(u.transform,{x:u.end[0]-u.pivot[0],y:u.end[1]-u.pivot[1]}),map(a.transform,{x:0,y:0}));near(map(a.transform,{x:a.end[0]-a.pivot[0],y:a.end[1]-a.pivot[1]}),map(h.transform,{x:0,y:0}));
  const heel=map(h.transform,{x:h.end[0]-h.pivot[0],y:h.end[1]-h.pivot[1]});near(heel,map(base,p.heel));if(p.planted)near(heel,map(base,{x:470,y:668}));
 }
 assert.equal(r.swords.length,r.swordVisible?4:0);
 if(r.swordVisible){
  const [u,f,b,h]=r.swords,parts=r.swordRig.parts,base=r.bases[1],torso=r.bodies.find(x=>x.panel===1&&x.name==='torso');
  const socket=r.pose.late?r.settle.shoulder:r.meta.frames[r.pose.index].shoulder;
  near(map(u.transform,{x:0,y:0}),map(torso.transform,{x:socket[0]-95,y:socket[1]-28}));
  near(map(u.transform,{x:0,y:65}),map(f.transform,{x:0,y:0}));
  near(map(f.transform,{x:0,y:75}),map(h.transform,{x:0,y:0}));
  near(map(h.transform,{x:parts.grip.gripPoint[0]-h.pivot[0],y:parts.grip.gripPoint[1]-h.pivot[1]}),map(b.transform,{x:0,y:0}));
  near(map(b.transform,{x:0,y:0}),map(base,r.weapon.grip));
  // Full texture rectangles (stricter than opaque pixels) must fit each panel's clipping window.
  const origin={x:base.e+50,y:base.f+10};
  for(const part of r.swords){assert.equal(part.alpha,1);near({x:Math.hypot(part.transform.a,part.transform.b),y:Math.hypot(part.transform.c,part.transform.d)},{x:.8,y:.8});
   for(const x of [0,part.size[0]])for(const y of [0,part.size[1]]){const v=map(part.transform,{x:x-part.pivot[0],y:y-part.pivot[1]});assert.ok(v.x>=origin.x&&v.x<=origin.x+600&&v.y>=origin.y+65&&v.y<=origin.y+615,`clipped sword part ${part.name}`);}
  }
  const order=r.drawEvents.filter(e=>e.panel===1).map(e=>e.name);
  assert.ok(order.indexOf('sword:katana')<order.indexOf('sword:grip'));
  assert.ok(order.indexOf('sword:grip')<order.indexOf('torso'));
  if(r.armVisible)assert.ok(order.indexOf('torso')<order.indexOf('palm'));
 }

 assert.equal(r.legs.length,r.pose.late?2:0);
 if(r.pose.late){const [shin,shoe]=r.legs;assert.equal(shin.alpha,1);assert.equal(shoe.alpha,1);near(map(shin.transform,{x:0,y:0}),map(r.bases[1],r.pose.leg.knee));near(map(shin.transform,{x:shin.end[0]-shin.pivot[0],y:shin.end[1]-shin.pivot[1]}),map(shoe.transform,{x:0,y:0}));near(map(shoe.transform,{x:shoe.end[0]-shoe.pivot[0],y:shoe.end[1]-shoe.pivot[1]}),map(r.bases[1],r.pose.leg.toe));}
}
async function ready(p){p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.status()>=400)failed.push(r.url());});await p.goto(url);await p.waitForFunction(()=>window.freeArmSettle?.ready);}
async function seek(p,t){await p.locator('#time').evaluate((el,t)=>{el.value=t;el.dispatchEvent(new Event('input',{bubbles:true}));},t);}
try{
 const p=await browser.newPage({viewport:{width:1280,height:1100}});await p.clock.install();await ready(p);await p.clock.pauseAt(new Date(await p.evaluate(()=>Date.now())+2000));await p.clock.runFor(33);
 for(const age of [330,376,388,389,399,400,401,410,420,440,460,480,500]){await seek(p,age);check(await state(p));if([330,389,399,400,401,420,440,460,480,500].includes(age))await p.locator('#view').screenshot({path:`${out}/pose-${age}.png`});}
 // Compare the actual right-panel pixels just before/after the former full-lower-body swap.
 const boundary=[];for(const t of [399.999,400.001]){await seek(p,t);const r=await state(p);check(r);boundary.push({bodies:r.bodies.filter(b=>b.panel===1),pixels:await p.evaluate(()=>Array.from(document.querySelector('#view').getContext('2d').getImageData(600,0,600,720).data))});}
 assert.deepEqual(boundary[0].bodies.map(b=>b.url),boundary[1].bodies.map(b=>b.url));let boundaryChangedPixels=0;for(let i=0;i<boundary[0].pixels.length;i+=4)if(boundary[0].pixels.slice(i,i+4).some((v,j)=>v!==boundary[1].pixels[i+j]))boundaryChangedPixels++;const maxBoundaryChannelDelta=boundary[0].pixels.reduce((max,v,i)=>Math.max(max,Math.abs(v-boundary[1].pixels[i])),0);
 // Reject a color jump or broad pixel change at the former whole-body swap.
 assert.ok(maxBoundaryChannelDelta<=1&&boundaryChangedPixels<1000,`400ms discontinuity: ${boundaryChangedPixels} pixels, channel delta ${maxBoundaryChannelDelta}`);
 await seek(p,400);await p.locator('#patch').check();await p.locator('#arm').uncheck();await p.locator('#view').screenshot({path:`${out}/patch-region.png`});await p.locator('#patch').uncheck();await p.locator('#arm').check();await seek(p,500);
 const armed=await state(p),armedPixels=await p.locator('#view').screenshot();await p.locator('#sword').uncheck();check(await state(p));assert.deepEqual((await state(p)).records,armed.records);assert.deepEqual((await state(p)).legs,armed.legs);assert.notDeepEqual(await p.locator('#view').screenshot(),armedPixels);await p.locator('#sword').check();check(await state(p));assert.deepEqual((await state(p)).swords,armed.swords);
 const closed=await p.locator('#view').screenshot();const beforeLegs=(await state(p)).legs;await p.locator('#xray').check();check(await state(p));assert.deepEqual((await state(p)).legs,beforeLegs);const exposed=await p.locator('#view').screenshot();assert.notDeepEqual(closed,exposed);await p.locator('#arm').uncheck();check(await state(p));await p.locator('#view').screenshot({path:`${out}/exposed-foot.png`});await p.locator('#arm').check();await p.locator('#xray').uncheck();
 await p.locator('#joints').check();await p.locator('#view').screenshot({path:`${out}/joints.png`});await p.locator('#joints').uncheck();await p.locator('#arm').uncheck();check(await state(p));await p.locator('#arm').check();await p.locator('#cap').uncheck();check(await state(p));await p.locator('#cap').check();
 await seek(p,352);await p.locator('#next').click();assert.equal((await state(p)).age,376);await p.locator('#prev').click();assert.equal((await state(p)).age,352);
 await seek(p,330);await p.locator('#play').click();const capture=[];
 for(let i=0;i<30;i++){await p.clock.runFor(i%3===2?34:33);const r=await state(p);check(r);await p.locator('#view').screenshot({path:`${tmp}/${String(i).padStart(3,'0')}.png`});assert.equal((await state(p)).age,r.age);capture.push({sample:i,age:r.age,pose:r.pose,records:r.records,bases:r.bases,bodies:r.bodies,legs:r.legs,swords:r.swords,weapon:r.weapon,drawEvents:r.drawEvents});}
 assert.deepEqual([...new Set(capture.map(r=>r.pose.index))],[0,1,2,3,4]);assert.equal((await state(p)).age,540);assert.equal((await state(p)).playing,false);
 const planted=capture.filter(r=>r.pose.planted);for(const row of planted){assert.deepEqual(row.records.filter(r=>r.panel===1&&r.name==='palm'),planted[0].records.filter(r=>r.panel===1&&r.name==='palm'));assert.deepEqual(row.bodies.find(b=>b.panel===1&&b.name==='lower'),planted[0].bodies.find(b=>b.panel===1&&b.name==='lower'));}
 await p.locator('#play').click();await p.clock.runFor(50);assert.ok((await state(p)).age<420);await p.locator('#play').click();const held=await state(p);await p.clock.runFor(100);assert.deepEqual((await state(p)).records,held.records);
 await p.locator('#speed').selectOption('1');await seek(p,330);await p.locator('#play').click();await p.clock.runFor(270);assert.equal((await state(p)).age,540);assert.equal((await state(p)).playing,false);await seek(p,376);await p.screenshot({path:`${out}/desktop.jpg`,fullPage:true});
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});await ready(mobile);await mobile.locator('#next').tap();assert.equal((await state(mobile)).age,352);await seek(mobile,400);check(await state(mobile));assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await mobile.screenshot({path:`${out}/mobile.jpg`,fullPage:true});
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);await fs.writeFile(`${out}/capture.json`,JSON.stringify(capture,null,2)+'\n');await fs.writeFile(`${out}/browser-check.json`,JSON.stringify({passed:true,checks:['Far shoulder, elbow, wrist and actual fist-to-katana Canvas attachment; rigid texture scale, panel bounds, render order and independent visibility toggle','Actual Canvas arm, knee-to-ankle and ankle-to-shoe joints; hinged torso/cap shoulder alignment','Shared lower-body URLs persist across 400 ms; actual right-panel pixels checked at 399.999/400.001 ms; fixed planted hand','Whole sequence captured; controls and x-ray shows occluded leg with identical transforms and alpha 1','390 px touch key stepping and stacked layout without overflow'],boundaryChangedPixels,maxBoundaryChannelDelta,pageErrors:errors,failedRequests:failed,scope:'Independent two-arm held-katana settling review, not installed into combat; no physical phone FPS measurement.'},null,2)+'\n');console.log('Settle browser checks passed.');
}finally{await browser.close();await new Promise(r=>server.close(r));}
