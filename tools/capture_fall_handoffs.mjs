// Capture actual Canvas pixels, excluding labels, for reproducible art registration review.
import {chromium} from '@playwright/test';
import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';
const root=process.cwd(),out=process.argv[2]??'.tmp/fall-handoffs';await fs.mkdir(out,{recursive:true});
const mode=process.argv[3]??'bridge';if(!['baseline','bridge','helmet'].includes(mode))throw Error('mode must be baseline, bridge or helmet');
const server=http.createServer(async(req,res)=>{try{let file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+'/'))throw Error('path');if((await fs.stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',({'.html':'text/html','.mjs':'text/javascript','.json':'application/json','.webp':'image/webp'})[path.extname(file)]||'application/octet-stream');res.end(await fs.readFile(file));}catch{res.statusCode=404;res.end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
try{
 const page=await browser.newPage({viewport:{width:1280,height:1100}});await page.goto(`http://127.0.0.1:${server.address().port}/docs/routes/jigoku-2d/free-arm-settle/${mode==='baseline'?'?motion=baseline':mode==='helmet'?'?helmet=shared':'?helmet=baked'}`);await page.waitForFunction(()=>window.freeArmSettle?.ready);
 await fs.writeFile(`${out}/registration.json`,JSON.stringify(await page.evaluate(()=>window.freeArmSettle.fall),null,2)+'\n');
 const meta=await page.evaluate(()=>window.freeArmSettle.fall),keys=[meta.start,...meta.frames.map(f=>f.time)],times=keys.slice(1).map((t,i)=>(t+keys[i])/2);
 if(mode==='helmet'){times.unshift(1180);times.push(1500);await fs.writeFile(`${out}/head-registration.json`,JSON.stringify(await page.evaluate(()=>window.freeArmSettle.headMeta),null,2)+'\n');}
 const drawStates=[];
 for(const time of times)for(const [suffix,delta] of [['before',-.001],['after',.001]]){
  await page.locator('#time').evaluate((el,t)=>{el.value=t;el.dispatchEvent(new Event('input'));},time+delta);
  const data=await page.evaluate(()=>{const c=document.createElement('canvas');c.width=600;c.height=550;c.getContext('2d').drawImage(document.querySelector('#view'),600,65,600,550,0,0,600,550);return c.toDataURL('image/png').split(',')[1];});
  await fs.writeFile(`${out}/${time}-${suffix}.png`,Buffer.from(data,'base64'));
  drawStates.push(await page.evaluate(()=>({age:window.freeArmSettle.age,helmet:window.freeArmSettle.helmet})));
  // Isolate body alpha, then the shared helmet; retain actual drawing matrices.
  for(const kind of (mode==='helmet'?['body','head']:['body'])){
  const mask=await page.evaluate(kind=>{const c=document.querySelector('#view'),ctx=c.getContext('2d'),saved={};for(const key of ['fillRect','fill','fillText','drawImage'])saved[key]=ctx[key];const urls=new Set(window.freeArmSettle.bodies.filter(b=>b.panel===1&&(kind==='body'||b.name==='helmet')).map(b=>b.url));
   ctx.clearRect(0,0,c.width,c.height);ctx.fillRect=ctx.fill=ctx.fillText=()=>{};ctx.drawImage=function(im,...args){if(urls.has(im.src.split('/').at(-1)))saved.drawImage.call(this,im,...args);};
   try{document.querySelector('#time').dispatchEvent(new Event('input'));const isolated=document.createElement('canvas');isolated.width=600;isolated.height=550;isolated.getContext('2d').drawImage(c,600,65,600,550,0,0,600,550);return isolated.toDataURL('image/png').split(',')[1];}finally{for(const key in saved)ctx[key]=saved[key];}
  },kind);
  await fs.writeFile(`${out}/${time}-${suffix}-${kind}.png`,Buffer.from(mask,'base64'));
  }
 }
 await fs.writeFile(`${out}/draw-states.json`,JSON.stringify(drawStates,null,2)+'\n');
}finally{await browser.close();await new Promise(r=>server.close(r));}
