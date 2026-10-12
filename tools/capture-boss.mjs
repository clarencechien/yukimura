/** Same in-engine camera, idle pose and escorts for commander readability. */
import {chromium} from '@playwright/test';
import {existsSync} from 'node:fs';
const base=process.argv[2]||'http://127.0.0.1:5180';
const suffix=process.argv[3]||'after';
if(!['before','after'].includes(suffix))throw Error('Expected before or after');
const browser=await chromium.launch({executablePath:existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 await page.goto(base+'/?test');await page.waitForFunction(()=>!document.querySelector('#start').disabled,{},{timeout:60000});await page.click('#start');await page.waitForTimeout(1000);
 for(const close of [false,true]){
  await page.evaluate(close=>window.__sanadaTest.inspectBoss(close),close);await page.waitForTimeout(700);
  await page.screenshot({path:`docs/screenshots/boss-${close?'close':'battle'}-${suffix}.png`});
 }
 if(suffix==='after'){
  await page.close();
  const phone=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1});
  const mobile=await phone.newPage();mobile.on('pageerror',e=>errors.push(e.message));mobile.on('console',m=>{if(m.type()==='error')errors.push(m.text())});mobile.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
  await mobile.goto(base+'/?test');await mobile.waitForFunction(()=>!document.querySelector('#start').disabled,{},{timeout:60000});await mobile.tap('#start');await mobile.waitForTimeout(1000);
  await mobile.evaluate(()=>window.__sanadaTest.inspectBoss(false));await mobile.waitForTimeout(700);
  await mobile.screenshot({path:'docs/screenshots/boss-mobile-after.png'});await phone.close();
 }
 if(errors.length)throw Error(errors.join('\n'));console.log('Saved commander battle and close views.');
}finally{await browser.close();}
