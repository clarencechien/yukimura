import {chromium} from '@playwright/test';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=process.cwd(),out='docs/routes/jigoku-2d/free-arm',tmp='.tmp/free-arm-capture';await fs.mkdir(tmp,{recursive:true});
const server=http.createServer(async(req,res)=>{try{let file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+'/'))throw Error('path');if((await fs.stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',({'.html':'text/html','.mjs':'text/javascript','.json':'application/json','.webp':'image/webp'})[path.extname(file)]||'application/octet-stream');res.end(await fs.readFile(file));}catch{res.statusCode=404;res.end('not found');}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
const errors=[],failed=[],url=`http://127.0.0.1:${server.address().port}/${out}/`,get=p=>p.evaluate(()=>window.freeArmReview);
async function ready(p){p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.status()>=400)failed.push(r.url());});await p.goto(url);await p.waitForFunction(()=>window.freeArmReview?.ready);}
async function seek(p,time){await p.locator('#time').evaluate((el,t)=>{el.value=t;el.dispatchEvent(new Event('input',{bubbles:true}));},time);}
function check(r){for(const p of [r.pose,r.plan]){assert.ok(Math.abs(Math.hypot(p.elbow.x-p.shoulder.x,p.elbow.y-p.shoulder.y)-85)<1e-6);assert.ok(Math.abs(Math.hypot(p.wrist.x-p.elbow.x,p.wrist.y-p.elbow.y)-90)<1e-6);}assert.ok(r.plan.miss<1e-6);assert.ok(r.plan.distance<=170+1e-6);}
try{
 const p=await browser.newPage({viewport:{width:1380,height:1200}});await p.clock.install();await ready(p);await p.clock.pauseAt(new Date(await p.evaluate(()=>Date.now())+2000));await p.clock.runFor(33);
 let r=await get(p);check(r);assert.equal(r.age,330);assert.ok(r.pose.miss>30);
 for(const age of [180,250,330]){await seek(p,age);r=await get(p);check(r);await p.locator('#view').screenshot({path:`${out}/reach-${age}.png`});}
 await p.locator('#source').selectOption('candidate');r=await get(p);check(r);assert.equal(r.candidate,true);assert.ok(r.pose.miss>9);assert.ok(r.pose.miss<15);await p.locator('#view').screenshot({path:`${out}/candidate-reach.png`});await p.screenshot({path:`${out}/desktop.jpg`,fullPage:true});
 await p.locator('#source').selectOption('original');await seek(p,180);await p.locator('#play').click();const frames=[];
 for(let i=0;i<30;i++){await p.clock.runFor(i%3===2?34:33);r=await get(p);check(r);const before=r.age;await p.locator('#view').screenshot({path:`${tmp}/${String(i).padStart(3,'0')}.png`});assert.equal((await get(p)).age,before);frames.push({sample:i,age:r.age,pose:r.pose,plan:r.plan});}
 await p.locator('#play').click();r=await get(p);assert.equal(r.playing,false);await p.clock.runFor(500);assert.deepEqual((await get(p)).pose,r.pose);
 await seek(p,250);assert.equal((await get(p)).age,250);
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});await ready(mobile);assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await mobile.locator('#source').selectOption('candidate');await seek(mobile,330);check(await get(mobile));await mobile.screenshot({path:`${out}/mobile.jpg`,fullPage:true});
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);await fs.writeFile(`${out}/capture.json`,JSON.stringify(frames,null,2)+'\n');await fs.writeFile(`${out}/browser-check.json`,JSON.stringify({passed:true,checks:['Original/candidate unreachable targets are reported, not silently stretched','Actual review state preserves both segment lengths and solved target','Slider, source selection, playback, pause and 30 actual canvas screenshots','390 px mobile controls and no horizontal overflow'],pageErrors:errors,failedRequests:failed,scope:'Diagnostic page only; production combat is unchanged. Desktop/mobile emulation is not hardware performance measurement.'},null,2)+'\n');console.log('Free arm diagnostic browser checks passed.');
}finally{await browser.close();await new Promise(r=>server.close(r));}
