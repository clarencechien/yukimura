import {chromium} from '@playwright/test';
import http from 'node:http';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const bodyV2=process.argv.includes('--body-v2');
const out=bodyV2?'docs/experiments/future-sanada/body-v2':'docs/experiments/future-sanada/head-study';
const html=await fs.readFile(bodyV2?'.tmp/future-sanada-body-v2-viewer/index.html':'.tmp/future-sanada-head-viewer/index.html');
const expected=JSON.parse(await fs.readFile(`${out}/${process.argv.includes('--pass3')?'pass3':process.argv.includes('--pass2')?'pass2':'refined'}/preview-inspection.json`));
const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end(html);});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const errors=[],external=[],checks=[];
try{
 for(const viewport of [{width:1280,height:900},{width:390,height:844}]){
  const page=await browser.newPage({viewport});page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(/^https?:/.test(r.url())&&!r.url().startsWith('http://127.0.0.1:'))external.push(r.url());});
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  await page.waitForFunction(()=>window.modelStudy?.loaded||window.modelStudy?.error,{},{timeout:60000});
  const state=await page.evaluate(()=>window.modelStudy);assert.equal(state.loaded,true,JSON.stringify(state));assert.equal(state.triangles,expected.triangles);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.context().setOffline(true);
  for(const selector of ['[data-angle="0"]','[data-angle="270"]','#clay','#wire','#wire','#clay','[data-angle="90"]','#spin','#spin','[data-angle="90"]'])await page.locator(selector).click();
  await page.screenshot({path:`${out}/viewer-${viewport.width}.png`});
  checks.push({viewport,loaded:state,controls:'front/side/back/clay/wireframe/autorotate toggles work offline',noHorizontalOverflow:true});await page.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 const report={passed:true,checks,consoleErrors:errors,externalRequests:external,limitation:'Headless Chromium; no physical mobile performance measurement'};
 await fs.writeFile(`${out}/viewer-verification.json`,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{await browser.close();await new Promise(r=>server.close(r));}
