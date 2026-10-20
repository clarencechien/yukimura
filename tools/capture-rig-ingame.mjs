/** Screenshot a candidate hero GLB in the real game: idle, running, then attacking.
 *  The candidate is served in place of public/models/yukimura.glb through a Playwright route, so the
 *  repository file is never touched. Start Vite first.
 *    node tools/capture-rig-ingame.mjs .tmp/rig8/open-8clips.glb out-prefix [http://127.0.0.1:5173]
 */
import {chromium} from '@playwright/test';
import {readFileSync,existsSync} from 'node:fs';
const [glb,prefix,base='http://127.0.0.1:5173']=process.argv.slice(2);
const body=readFileSync(glb);
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||(existsSync('/opt/pw-browsers/chromium')?'/opt/pw-browsers/chromium':undefined),args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const page=await browser.newPage({viewport:{width:1280,height:720}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.route(/models\/yukimura\.glb/,route=>route.fulfill({body,contentType:'model/gltf-binary'}));
 await page.goto(base+'/');await page.locator('#start').waitFor();
 await page.waitForFunction(()=>!document.querySelector('#start').disabled,{},{timeout:180000});
 await page.click('#start');await page.waitForTimeout(2500);await page.screenshot({path:`${prefix}-idle.png`});
 await page.keyboard.down('w');await page.waitForTimeout(900);await page.screenshot({path:`${prefix}-run.png`});await page.keyboard.up('w');
 await page.keyboard.down('j');await page.waitForTimeout(450);await page.screenshot({path:`${prefix}-attack.png`});await page.keyboard.up('j');
 console.log(JSON.stringify({glb,errors}));
}finally{await browser.close();}
