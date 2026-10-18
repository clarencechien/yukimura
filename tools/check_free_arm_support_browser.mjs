import {chromium} from '@playwright/test';import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
const root=process.cwd(),out='docs/routes/jigoku-2d/free-arm-support',tmp='.tmp/free-arm-support-capture';await fs.mkdir(tmp,{recursive:true});
const server=http.createServer(async(req,res)=>{try{let file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+'/'))throw Error('path');if((await fs.stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',({'.html':'text/html','.mjs':'text/javascript','.json':'application/json','.webp':'image/webp'})[path.extname(file)]||'application/octet-stream');res.end(await fs.readFile(file));}catch{res.statusCode=404;res.end('not found');}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const errors=[],failed=[],url=`http://127.0.0.1:${server.address().port}/${out}/`;
const state=p=>p.evaluate(()=>window.freeArmSupport);
const map=(m,p)=>({x:m.a*p.x+m.c*p.y+m.e,y:m.b*p.x+m.d*p.y+m.f});
// Canvas transforms have float32 rounding (~0.000012 px observed); retain a subpixel 0.001 px tolerance.
const near=(a,b)=>assert.ok(Math.hypot(a.x-b.x,a.y-b.y)<.001,JSON.stringify({a,b,error:Math.hypot(a.x-b.x,a.y-b.y)}));
function check(r){
 assert.equal(r.records.length,r.armVisible?6:0);const torso=r.bodies.find(b=>b.name==='torso'),lower=r.bodies.find(b=>b.name==='lower');assert.equal(lower.dy,0);
 near(map(torso.transform,{x:r.meta.body.shoulder[0],y:r.meta.body.shoulder[1]}),map(r.bases[0],r.pose.shoulder));
 if(!r.armVisible)return;
 for(let i=0;i<2;i++){const [u,f,h]=r.records.filter(x=>x.panel===i);assert.deepEqual([u.name,f.name,h.name],['upper','fore','palm']);
  for(const [rec,point] of [[u,r.pose.shoulder],[f,r.pose.elbow],[h,r.pose.wrist]])near(map(rec.transform,{x:0,y:0}),map(r.bases[i],point));
  near(map(u.transform,{x:u.end[0]-u.pivot[0],y:u.end[1]-u.pivot[1]}),map(f.transform,{x:0,y:0}));near(map(f.transform,{x:f.end[0]-f.pivot[0],y:f.end[1]-f.pivot[1]}),map(h.transform,{x:0,y:0}));
  const heel=map(h.transform,{x:h.end[0]-h.pivot[0],y:h.end[1]-h.pivot[1]});near(heel,map(r.bases[i],r.pose.heel));if(r.pose.planted)near(heel,map(r.bases[i],{x:470,y:668}));
  const shadow=r.shadows[i];near(map(shadow.transform,{x:shadow.x,y:shadow.y}),map(r.bases[i],{x:470,y:680}));
 }
}
async function ready(p){p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.status()>=400)failed.push(r.url());});await p.goto(url);await p.waitForFunction(()=>window.freeArmSupport?.ready);}
async function seek(p,t){await p.locator('#time').evaluate((el,t)=>{el.value=t;el.dispatchEvent(new Event('input',{bubbles:true}));},t);}
try{
 const p=await browser.newPage({viewport:{width:1280,height:1050}});await p.clock.install();await ready(p);await p.clock.pauseAt(new Date(await p.evaluate(()=>Date.now())+2000));await p.clock.runFor(33);
 for(const age of [330,420,500]){await seek(p,age);check(await state(p));await p.locator('#view').screenshot({path:`${out}/support-${age}.png`});}
 await p.locator('#joints').check();await p.locator('#view').screenshot({path:`${out}/joints.png`});await p.locator('#joints').uncheck();
 await p.locator('#arm').uncheck();check(await state(p));await p.locator('#view').screenshot({path:`${out}/clean-body.png`});await p.locator('#arm').check();await p.locator('#cap').uncheck();assert.equal((await state(p)).capVisible,false);check(await state(p));await p.locator('#cap').check();
 await seek(p,330);await p.locator('#play').click();const capture=[];
 for(let i=0;i<30;i++){await p.clock.runFor(i%3===2?34:33);const r=await state(p);check(r);await p.locator('#view').screenshot({path:`${tmp}/${String(i).padStart(3,'0')}.png`});assert.equal((await state(p)).age,r.age);capture.push({sample:i,age:r.age,pose:r.pose,records:r.records,bases:r.bases,bodies:r.bodies,shadows:r.shadows});}
 assert.ok(capture.some(r=>r.pose.planted));assert.ok(capture.some(r=>!r.pose.planted));const plants=capture.filter(r=>r.pose.planted);for(const row of plants){assert.deepEqual(row.records.filter(r=>r.name==='palm'),plants[0].records.filter(r=>r.name==='palm'));assert.deepEqual(row.bodies.find(b=>b.name==='lower'),plants[0].bodies.find(b=>b.name==='lower'));}await p.locator('#play').click();const held=await state(p);await p.clock.runFor(500);assert.deepEqual((await state(p)).records,held.records);await seek(p,500);await p.screenshot({path:`${out}/desktop.jpg`,fullPage:true});
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});await ready(mobile);await seek(mobile,500);check(await state(mobile));assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await mobile.screenshot({path:`${out}/mobile.jpg`,fullPage:true});
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);await fs.writeFile(`${out}/capture.json`,JSON.stringify(capture,null,2)+'\n');await fs.writeFile(`${out}/browser-check.json`,JSON.stringify({passed:true,checks:['Actual Canvas draw matrices attach upper endpoint to fore pivot and fore endpoint to hand pivot in both panels','Painted heel contact stays fixed after 420 ms while torso and shoulder descend; lower body stays fixed','Torso/cap shoulder transforms, contact shadow, playback/seek/pause/toggles; thirty screenshots','390 px touch viewport stacks panels without horizontal overflow'],pageErrors:errors,failedRequests:failed,scope:'Independent fitting page, not installed into combat; no physical phone FPS claim.'},null,2)+'\n');console.log('Support contact browser checks passed.');
}finally{await browser.close();await new Promise(r=>server.close(r));}
