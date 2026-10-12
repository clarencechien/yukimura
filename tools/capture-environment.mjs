/** Actual game geometry/materials; development-only inspection camera, no concept overlay. */
import {chromium} from '@playwright/test';
import {existsSync} from 'node:fs';
const base=process.argv[2]||'http://127.0.0.1:5180';
const browser=await chromium.launch({executablePath:existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 await page.goto(base+'/?test');await page.waitForFunction(()=>!document.querySelector('#start').disabled,{},{timeout:60000});await page.click('#start');await page.waitForTimeout(1800);
 await page.addStyleTag({content:'#app{visibility:hidden!important}'});
 for(const [name,z,close] of [['winter-ground',0,true],['winter-gate',36,false],['winter-camp',138,false]]){
  await page.evaluate(({z,close})=>window.__sanadaTest.inspectEnvironment(z,close),{z,close});await page.waitForTimeout(800);
  await page.screenshot({path:`docs/screenshots/${name}.png`});
 }
 if(errors.length)throw Error(errors.join('\n'));console.log('Saved three actual battlefield inspection views.');
}finally{await browser.close();}
