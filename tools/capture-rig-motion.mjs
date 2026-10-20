/** Record a hero GLB in the real Babylon.js engine: every clip in the model preview, then a short battle
 *  (run, then attack). With a GLB path the candidate is served in place of models/yukimura.glb through a
 *  Playwright route, so the repository file is never touched; 'current' records the game's own hero.
 *  Software WebGL is far slower than real time, so after loading the page clock is faked and stepped one
 *  frame (1/24 s) per capture; the frames are assembled with ffmpeg.
 *  Start Vite first.
 *    node tools/capture-rig-motion.mjs .tmp/rig-lod1/yukimura-lod1.glb .tmp/motion/lod1 [http://127.0.0.1:5173]
 */
import {chromium} from '@playwright/test';
import {readFileSync,existsSync,mkdirSync,rmSync,writeFileSync} from 'node:fs';
import {dirname} from 'node:path';
import {execFileSync} from 'node:child_process';
const [glb,prefix,base='http://127.0.0.1:5173']=process.argv.slice(2);
mkdirSync(dirname(prefix),{recursive:true});
const body=glb==='current'?null:readFileSync(glb);
const FPS=24;
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||(existsSync('/opt/pw-browsers/chromium')?'/opt/pw-browsers/chromium':undefined),args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
async function record(name,run){
 const page=await browser.newPage({viewport:{width:960,height:720}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 if(body)await page.route(/models\/yukimura\.glb/,route=>route.fulfill({body,contentType:'model/gltf-binary'}));
 const dir=`${prefix}-${name}-frames`;rmSync(dir,{recursive:true,force:true});mkdirSync(dir,{recursive:true});let n=0;
 // after loading in real time, the page clock is faked and stepped one video frame per screenshot
 // The WebGL canvas is read directly (both pages keep their drawing buffer): screenshots wait for an
 // animation frame, which the fake clock holds back. HTML overlays such as the HUD are not in it.
 const shoot=async seconds=>{for(let i=0;i<Math.round(seconds*FPS);i++){await page.clock.runFor(1000/FPS);
  const data=await page.evaluate(()=>document.querySelector('canvas').toDataURL('image/jpeg',.92).split(',')[1]);
  writeFileSync(`${dir}/${String(n++).padStart(5,'0')}.jpg`,Buffer.from(data,'base64'));}};
 await run(page,shoot);await page.close();
 execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-framerate',String(FPS),'-i',`${dir}/%05d.jpg`,'-vf','scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p','-c:v','libx264','-crf','20',`${prefix}-${name}.mp4`]);
 rmSync(dir,{recursive:true,force:true});console.log(name,n,'frames');
 if(errors.length)throw Error(errors.join('\n'));
}
try{
 await record('preview',async (page,shoot)=>{
  await page.goto(base+'/tools/model-preview.html');await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:120000});
  await page.clock.install();await shoot(1);
  // clips are posed by time rather than played, so two recordings stay frame-for-frame in step
  for(const clip of ['run','slash','reverse','thrust','spin','dash','hurt','idle']){
   for(let k=0;k<1.5*FPS;k++){
    await page.evaluate(([name,t])=>{const groups=window.modelPreview.loaded.animationGroups,g=groups.find(x=>x.name===name);
     for(const o of groups)if(o!==g)o.stop();
     if(!g.isStarted){g.start(true);g.pause();}
     const fps=g.targetedAnimations[0].animation.framePerSecond,dur=(g.to-g.from)/fps;g.goToFrame(g.from+((t%dur)/dur)*(g.to-g.from));},[clip,k/FPS]);
    await shoot(1/FPS);
   }
  }
 });
 await record('battle',async (page,shoot)=>{
  await page.goto(base+'/');await page.locator('#start').waitFor();await page.waitForFunction(()=>!document.querySelector('#start').disabled,{},{timeout:180000});
  await page.click('#start');await page.waitForTimeout(500);await page.clock.install();await shoot(.5);
  await page.keyboard.down('w');await shoot(2);await page.keyboard.up('w');
  await page.keyboard.down('j');await shoot(4);await page.keyboard.up('j');await shoot(.5);
 });
 console.log('saved',prefix);
}finally{await browser.close();}
