import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const url=process.argv[2]||'https://clarencechien.github.io/yukimura/jigoku/';
const source='44d6f935102fc9361146504a06467841fd25a663';
const version=await fetch(new URL('version.txt',url));assert.equal(version.status,200);assert.equal((await version.text()).trim(),source);
const response=await fetch(url);assert.equal(response.status,200);const html=await response.text();assert.ok(html.includes('燼關突圍'));assert.ok(html.includes('window.SANADA_ASSETS='));
const local=await fs.readFile('.tmp/jigoku-release/index.html','utf8');assert.equal(createHash('sha256').update(html).digest('hex'),createHash('sha256').update(local).digest('hex'));
const license=await fetch(new URL('PHASER-LICENSE.md',url));assert.equal(license.status,200);assert.match(await license.text(),/MIT/);
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']}),errors=[],failed=[];
try{
 for(const mobile of [false,true]){
  const page=await browser.newPage({viewport:mobile?{width:390,height:844}:{width:1366,height:900},hasTouch:mobile,isMobile:mobile,ignoreHTTPSErrors:process.env.PLAYWRIGHT_PROXY_CA_BYPASS==='1'});page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failed.push(r.url());});
  await page.goto(url);await page.waitForFunction(()=>window.sanadaBattle?.snapshot().ready);await page.locator('#start').click();
  if(!mobile){await page.keyboard.down('d');await page.waitForFunction(()=>window.sanadaBattle.snapshot().hero.x>370);await page.keyboard.up('d');await page.keyboard.down('Space');await page.waitForFunction(()=>window.sanadaBattle.snapshot().stats.dashes>0);await page.keyboard.up('Space');}
  else{await page.locator('#command').tap();assert.equal(await page.evaluate(()=>window.sanadaBattle.snapshot().formation),'charge');}
  await page.locator('#pause').click();assert.equal(await page.evaluate(()=>window.sanadaBattle.snapshot().paused),true);await page.locator('#resume').click();assert.equal(await page.evaluate(()=>window.sanadaBattle.snapshot().paused),false);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await page.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 const report={url,source,checkedAt:new Date().toISOString(),passed:true,checks:['HTTP 200: game, version and Phaser license','Published HTML matches the locally tested build','Desktop start, movement, dash, pause and resume','Mobile viewport start, touch command, pause and resume'],errors,failedRequests:failed,proxyCertificateBypass:process.env.PLAYWRIGHT_PROXY_CA_BYPASS==='1'};
 await fs.writeFile('docs/routes/jigoku-2d/play/pages-verification.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
}finally{await browser.close();}
