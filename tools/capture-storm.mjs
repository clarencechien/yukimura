/** Record actual imported models and a controlled in-engine ultimate sequence. */
import {chromium} from '@playwright/test';
import {existsSync} from 'node:fs';
const base=process.argv[2]||'http://127.0.0.1:5180';
const browser=await chromium.launch({executablePath:existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
async function record(name,run){
 const context=await browser.newContext({viewport:{width:960,height:720},recordVideo:{dir:'/tmp/sanada-storm',size:{width:960,height:720}}});
 const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));const video=page.video();
 await run(page);await context.close();await video.saveAs(`docs/art/${name}.webm`);await video.delete();if(errors.length)throw Error(errors.join('\n'));
}
try{
 await record('soldier-falls',async page=>{
  await page.goto(base+'/tools/model-preview.html?model=ashigaru');await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:60000});
  await page.evaluate(()=>{const p=window.modelPreview;p.camera.radius=4.5;p.camera.target.y=.8;});
  for(const name of ['fall','fall_back']){
   await page.evaluate(name=>{const p=window.modelPreview;p.loaded.animationGroups.forEach(g=>g.stop());const g=p.loaded.animationGroups.find(g=>g.name===name);g.start(false,.65);},name);await page.waitForTimeout(3500);
  }
 });
 await record('winter-skills',async page=>{
  await page.goto(base+'/?test');await page.waitForFunction(()=>!document.querySelector('#start').disabled,{},{timeout:60000});await page.click('#start');await page.waitForTimeout(2000);
  await page.keyboard.down('j');await page.waitForTimeout(4000);await page.keyboard.up('j');
  await page.evaluate(()=>{window.__sanadaTest.setupCombat(30);window.stormTimer=setInterval(()=>window.__sanadaTest.step(1/30),33);});
  await page.keyboard.press('k');await page.waitForTimeout(4200);await page.evaluate(()=>clearInterval(window.stormTimer));
 });
 console.log('Saved soldier-falls.webm and winter-skills.webm from actual Babylon.js rendering.');
}finally{await browser.close();}
