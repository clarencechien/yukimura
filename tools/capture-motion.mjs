/** Record actual Babylon.js motion. Start Vite before running this script. */
import {chromium} from '@playwright/test';
import {existsSync,mkdirSync} from 'node:fs';
const base=process.argv[2]||'http://127.0.0.1:5173';
mkdirSync('docs/art',{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||(existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
async function record(name,run){
 const context=await browser.newContext({viewport:{width:960,height:720},recordVideo:{dir:'/tmp/sanada-motion',size:{width:960,height:720}}});
 const page=await context.newPage(),video=page.video(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await run(page);await context.close();await video.saveAs(`docs/art/${name}.webm`);await video.delete();
 if(errors.length)throw Error(errors.join('\n'));
}
try{
 await record('hero-motion',async page=>{
  await page.goto(base+'/tools/model-preview.html');await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:60000});
  await page.waitForTimeout(1800);
  for(const clip of ['run','slash','reverse','thrust','spin','dash','hurt']){
   await page.evaluate(name=>window.modelPreview.play(name),clip);await page.waitForTimeout(1500);
  }
 });
 await record('army-motion',async page=>{
  await page.goto(base+'/');await page.locator('#start').waitFor();await page.waitForFunction(()=>!document.querySelector('#start').disabled,{},{timeout:60000});
  await page.click('#start');await page.keyboard.down('w');await page.waitForTimeout(2000);await page.keyboard.up('w');
  await page.keyboard.press('f');await page.keyboard.down('j');await page.waitForTimeout(6500);await page.keyboard.up('j');
 });
 console.log('Saved hero-motion.webm and army-motion.webm: actual engine recordings.');
}finally{await browser.close();}
