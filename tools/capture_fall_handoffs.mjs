// Capture actual Canvas pixels, excluding labels, for reproducible art registration review.
import {chromium} from '@playwright/test';
import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';
const root=process.cwd(),out=process.argv[2]??'.tmp/fall-handoffs';await fs.mkdir(out,{recursive:true});
const server=http.createServer(async(req,res)=>{try{let file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+'/'))throw Error('path');if((await fs.stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',({'.html':'text/html','.mjs':'text/javascript','.json':'application/json','.webp':'image/webp'})[path.extname(file)]||'application/octet-stream');res.end(await fs.readFile(file));}catch{res.statusCode=404;res.end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
try{
 const page=await browser.newPage({viewport:{width:1280,height:1100}});await page.goto(`http://127.0.0.1:${server.address().port}/docs/routes/jigoku-2d/free-arm-settle/`);await page.waitForFunction(()=>window.freeArmSettle?.ready);
 await fs.writeFile(`${out}/registration.json`,JSON.stringify(await page.evaluate(()=>window.freeArmSettle.fall),null,2)+'\n');
 for(const time of [1220,1320,1440])for(const [suffix,delta] of [['before',-.001],['after',.001]]){
  await page.locator('#time').evaluate((el,t)=>{el.value=t;el.dispatchEvent(new Event('input'));},time+delta);
  const data=await page.evaluate(()=>{const c=document.createElement('canvas');c.width=600;c.height=550;c.getContext('2d').drawImage(document.querySelector('#view'),600,65,600,550,0,0,600,550);return c.toDataURL('image/png').split(',')[1];});
  await fs.writeFile(`${out}/${time}-${suffix}.png`,Buffer.from(data,'base64'));
  // A second render isolates body alpha; draw calls and transforms are unchanged.
  const mask=await page.evaluate(()=>{const c=document.querySelector('#view'),ctx=c.getContext('2d'),saved={};for(const key of ['fillRect','fill','fillText','drawImage'])saved[key]=ctx[key];const urls=new Set(window.freeArmSettle.bodies.filter(b=>b.panel===1).map(b=>b.url));
   ctx.clearRect(0,0,c.width,c.height);ctx.fillRect=ctx.fill=ctx.fillText=()=>{};ctx.drawImage=function(im,...args){if(urls.has(im.src.split('/').at(-1)))saved.drawImage.call(this,im,...args);};
   try{document.querySelector('#time').dispatchEvent(new Event('input'));const isolated=document.createElement('canvas');isolated.width=600;isolated.height=550;isolated.getContext('2d').drawImage(c,600,65,600,550,0,0,600,550);return isolated.toDataURL('image/png').split(',')[1];}finally{for(const key in saved)ctx[key]=saved[key];}
  });
  await fs.writeFile(`${out}/${time}-${suffix}-body.png`,Buffer.from(mask,'base64'));
 }
}finally{await browser.close();await new Promise(r=>server.close(r));}
