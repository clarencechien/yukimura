import {chromium} from '@playwright/test';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const root=process.cwd(),out='docs/routes/jigoku-2d/play';
const server=http.createServer(async(req,res)=>{try{let file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+'/'))throw Error('path');if((await fs.stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',({'.html':'text/html','.mjs':'text/javascript','.json':'application/json','.webp':'image/webp','.css':'text/css','.js':'text/javascript'})[path.extname(file)]||'application/octet-stream');res.end(await fs.readFile(file));}catch{res.statusCode=404;res.end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']}),errors=[],failed=[];
const url=`http://127.0.0.1:${server.address().port}/${out}/?test=1`;
const watch=page=>{page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failed.push(r.url());});};
const ready=page=>page.waitForFunction(()=>window.sanadaBattle?.snapshot().ready);
const state=page=>page.evaluate(()=>window.sanadaBattle.snapshot());
const shown=(page,id)=>page.locator(id).waitFor({state:'visible'});
try{
 const page=await browser.newPage({viewport:{width:1366,height:900}});watch(page);await page.goto(url);await ready(page);await page.screenshot({path:`${out}/menu.jpg`});await page.locator('#start').click();
 await page.keyboard.down('d');await page.waitForFunction(()=>window.sanadaBattle.snapshot().hero.x>380);await page.keyboard.up('d');
 await page.keyboard.press('r');assert.equal((await state(page)).formation,'charge');
 await page.keyboard.down('Space');await page.waitForFunction(()=>window.sanadaBattle.snapshot().stats.dashes>0);await page.keyboard.up('Space');
 await page.keyboard.down('j');await page.waitForFunction(()=>!!window.sanadaBattle.snapshot().hero.attack);await page.keyboard.up('j');
 await page.locator('#pause').click();await shown(page,'#pause-menu');const frozen=await state(page);await page.waitForTimeout(200);assert.equal((await state(page)).time,frozen.time);await page.locator('#resume').click();
 await page.evaluate(()=>window.dispatchEvent(new Event('blur')));await shown(page,'#pause-menu');assert.equal((await state(page)).paused,true);await page.locator('#resume').click();
 await page.evaluate(()=>window.sanadaBattle.test.advance(16000,{attack:true}));await page.waitForTimeout(100);await page.screenshot({path:`${out}/battle-desktop.jpg`});assert.ok((await state(page)).enemies>0);
 // Seed stages to verify their browser presentation; full unmodified rules runs are tested separately.
 await page.evaluate(()=>{const t=window.sanadaBattle.test;t.model.stage=1;t.model.hero.x=t.model.banner.x;t.advance(1000,{attack:true});});assert.ok((await state(page)).banner.progress>0);
 await page.evaluate(()=>{const t=window.sanadaBattle.test;t.model.startBoss();t.model.boss.cooldown=0;t.advance(100);});await shown(page,'#boss-hud');await page.screenshot({path:`${out}/boss-desktop.jpg`});
 await page.keyboard.down('k');await page.waitForFunction(()=>window.sanadaBattle.snapshot().stats.musou>0);await page.keyboard.up('k');
 await page.evaluate(()=>{const t=window.sanadaBattle.test;t.model.damageEnemy(t.model.boss,99999);t.advance(1);});await shown(page,'#result');assert.equal((await state(page)).result,'victory');await page.screenshot({path:`${out}/victory.jpg`});await page.locator('#next-cycle').click();assert.equal((await state(page)).cycle,2);assert.equal((await state(page)).kills,0);
 await page.evaluate(()=>{const t=window.sanadaBattle.test;t.model.hero.invulnerable=0;t.model.hurt(99999);t.advance(1);});await shown(page,'#result');assert.equal((await state(page)).result,'defeat');await page.locator('#retry').click();assert.equal((await state(page)).result,null);assert.equal((await state(page)).hero.hp,(await state(page)).hero.maxHP);await page.close();
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1});watch(mobile);await mobile.goto(url);await ready(mobile);await mobile.locator('#start').tap();
 const cdp=await mobile.context().newCDPSession(mobile),stick=await mobile.locator('#stick').boundingBox(),attack=await mobile.locator('#attack').boundingBox();
 const center={x:stick.x+stick.width/2,y:stick.y+stick.height/2,id:1};const button={x:attack.x+attack.width/2,y:attack.y+attack.height/2,id:2};
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[center]});await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{...center,x:center.x+35}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{...center,x:center.x+35},button]});
 await mobile.waitForFunction(()=>{const s=window.sanadaBattle.snapshot();return s.hero.x>360&&!!s.hero.attack;});await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await mobile.waitForTimeout(150);assert.equal((await state(mobile)).hero.moving,false);
 await mobile.evaluate(()=>window.sanadaBattle.test.advance(14000,{attack:true}));await mobile.waitForTimeout(350);await mobile.screenshot({path:`${out}/battle-mobile.jpg`});assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await mobile.locator('#pause').tap();await shown(mobile,'#pause-menu');await mobile.locator('#resume').tap();await mobile.setViewportSize({width:844,height:390});await mobile.screenshot({path:`${out}/battle-mobile-landscape.jpg`});assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await mobile.close();
 const offline=await browser.newPage({viewport:{width:1280,height:800}});watch(offline);const external=[];let fileCheck='passed';
 try{await offline.goto(pathToFileURL(path.resolve('.tmp/jigoku-release/index.html')).href);}catch(error){
  if(!error.message.includes('ERR_BLOCKED_BY_ADMINISTRATOR'))throw error;
  fileCheck='Blocked by managed Chromium policy; verified the same standalone HTML over HTTP and then disconnected networking.';
  const documentURL=`http://127.0.0.1:${server.address().port}/.tmp/jigoku-release/index.html`;
  await offline.route(/^https?:/,route=>{if(route.request().url()===documentURL)return route.continue();external.push(route.request().url());return route.abort();});await offline.goto(documentURL);
 }
 await ready(offline);await offline.context().setOffline(true);await offline.locator('#start').click();await offline.keyboard.down('d');await offline.waitForFunction(()=>window.sanadaBattle.snapshot().hero.x>365);await offline.keyboard.up('d');assert.equal(await offline.evaluate(()=>window.sanadaBattle.engine),'3.90.0');assert.deepEqual(external,[]);await offline.close();
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 const report={passed:true,engine:'Phaser 3.90.0',checks:['desktop movement / attack / dash / command / musou','pause / blur / resume','escort and boss HUD (seeded stages)','victory / defeat / retry / next cycle (seeded outcomes)','simultaneous two-finger movement and attack','portrait and landscape layout','standalone HTML: embedded assets, movement after network disconnected'],viewports:['1366x900','390x844','844x390'],consoleErrors:errors,failedRequests:failed,fileSchemeCheck:fileCheck,limitation:'Chromium touch emulation, not physical-device performance or human difficulty validation'};
 await fs.writeFile(`${out}/verification.json`,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
}finally{await browser.close();await new Promise(r=>server.close(r));}
