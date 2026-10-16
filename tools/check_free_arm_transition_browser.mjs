import {chromium} from '@playwright/test';import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
const root=process.cwd(),out='docs/routes/jigoku-2d/free-arm-transition',tmp='.tmp/free-arm-transition-capture';await fs.mkdir(tmp,{recursive:true});
const server=http.createServer(async(req,res)=>{try{let file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+'/'))throw Error('path');if((await fs.stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',({'.html':'text/html','.mjs':'text/javascript','.json':'application/json','.webp':'image/webp'})[path.extname(file)]||'application/octet-stream');res.end(await fs.readFile(file));}catch{res.statusCode=404;res.end('not found');}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const errors=[],failed=[],url=`http://127.0.0.1:${server.address().port}/${out}/`;
const state=p=>p.evaluate(()=>window.freeArmTransition),map=(m,p)=>({x:m.a*p.x+m.c*p.y+m.e,y:m.b*p.x+m.d*p.y+m.f});
const near=(a,b)=>assert.ok(Math.hypot(a.x-b.x,a.y-b.y)<.001,JSON.stringify({a,b}));
function check(r){
 assert.equal(r.records.length,r.armVisible?6:0);
 for(let panel=0;panel<2;panel++){
  const p=panel?r.pose:r.old,f=r.meta.frames[p.index],torso=r.bodies.find(b=>b.name==='torso'&&b.panel===panel),lower=r.bodies.find(b=>b.name==='lower'&&b.panel===panel),base=r.bases[panel];
  assert.deepEqual(lower.offset,{x:0,y:0});near(map(torso.transform,{x:f.shoulder[0],y:f.shoulder[1]}),map(base,p.shoulder));
  const cap=r.bodies.find(b=>b.name==='cap'&&b.panel===panel);assert.equal(!!cap,r.capVisible&&r.armVisible);if(cap)assert.deepEqual(cap.transform,torso.transform);
  if(!r.armVisible)continue;
  const [u,a,h]=r.records.filter(x=>x.panel===panel);assert.deepEqual([u.name,a.name,h.name],['upper','fore','palm']);
  near(map(u.transform,{x:0,y:0}),map(base,p.shoulder));
  near(map(u.transform,{x:u.end[0]-u.pivot[0],y:u.end[1]-u.pivot[1]}),map(a.transform,{x:0,y:0}));
  near(map(a.transform,{x:a.end[0]-a.pivot[0],y:a.end[1]-a.pivot[1]}),map(h.transform,{x:0,y:0}));
  const heel=map(h.transform,{x:h.end[0]-h.pivot[0],y:h.end[1]-h.pivot[1]});near(heel,map(base,p.heel));if(p.planted)near(heel,map(base,{x:470,y:668}));
 }
}
async function ready(p){p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.status()>=400)failed.push(r.url());});await p.goto(url);await p.waitForFunction(()=>window.freeArmTransition?.ready);}
async function seek(p,t){await p.locator('#time').evaluate((el,t)=>{el.value=t;el.dispatchEvent(new Event('input',{bubbles:true}));},t);}
try{
 const p=await browser.newPage({viewport:{width:1280,height:1100}});await p.clock.install();await ready(p);await p.clock.pauseAt(new Date(await p.evaluate(()=>Date.now())+2000));await p.clock.runFor(33);
 for(const age of [330,341,352,364,376,388,400,410,420,500]){await seek(p,age);check(await state(p));if([330,352,376,400,420,500].includes(age))await p.locator('#view').screenshot({path:`${out}/pose-${age}.png`});}
 await p.locator('#joints').check();await p.locator('#view').screenshot({path:`${out}/joints.png`});await p.locator('#joints').uncheck();await p.locator('#arm').uncheck();check(await state(p));await p.locator('#arm').check();await p.locator('#cap').uncheck();check(await state(p));await p.locator('#cap').check();
 await seek(p,352);await p.locator('#next').click();assert.equal((await state(p)).age,376);await p.locator('#prev').click();assert.equal((await state(p)).age,352);
 await seek(p,330);await p.locator('#play').click();const capture=[];
 for(let i=0;i<30;i++){await p.clock.runFor(i%3===2?34:33);const r=await state(p);check(r);await p.locator('#view').screenshot({path:`${tmp}/${String(i).padStart(3,'0')}.png`});assert.equal((await state(p)).age,r.age);capture.push({sample:i,age:r.age,pose:r.pose,records:r.records,bases:r.bases,bodies:r.bodies});}
 assert.deepEqual([...new Set(capture.map(r=>r.pose.index))],[0,1,2,3,4]);assert.equal((await state(p)).age,540);assert.equal((await state(p)).playing,false);
 const planted=capture.filter(r=>r.pose.planted);for(const row of planted){assert.deepEqual(row.records.filter(r=>r.panel===1&&r.name==='palm'),planted[0].records.filter(r=>r.panel===1&&r.name==='palm'));assert.deepEqual(row.bodies.find(b=>b.panel===1&&b.name==='lower'),planted[0].bodies.find(b=>b.panel===1&&b.name==='lower'));}
 await p.locator('#play').click();await p.clock.runFor(50);assert.ok((await state(p)).age<420);await p.locator('#play').click();const held=await state(p);await p.clock.runFor(100);assert.deepEqual((await state(p)).records,held.records);
 await p.locator('#speed').selectOption('1');await seek(p,330);await p.locator('#play').click();await p.clock.runFor(270);assert.equal((await state(p)).age,540);assert.equal((await state(p)).playing,false);await seek(p,376);await p.screenshot({path:`${out}/desktop.jpg`,fullPage:true});
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});await ready(mobile);await mobile.locator('#next').tap();assert.equal((await state(mobile)).age,352);await seek(mobile,400);check(await state(mobile));assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await mobile.screenshot({path:`${out}/mobile.jpg`,fullPage:true});
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);await fs.writeFile(`${out}/capture.json`,JSON.stringify(capture,null,2)+'\n');await fs.writeFile(`${out}/browser-check.json`,JSON.stringify({passed:true,checks:['Actual Canvas arm endpoints and torso/cap shoulder alignment across all five poses','Planted hand and lower-body draw matrices stay fixed after contact','All five poses captured; play, pause, restart, auto-stop, speeds, key stepping, seeking and toggles','390 px touch key stepping and stacked layout without overflow'],pageErrors:errors,failedRequests:failed,scope:'Independent five-pose review, not installed into combat; no physical phone FPS measurement.'},null,2)+'\n');console.log('Transition browser checks passed.');
}finally{await browser.close();await new Promise(r=>server.close(r));}
