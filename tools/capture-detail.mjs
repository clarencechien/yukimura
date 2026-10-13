import {chromium} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
const out='renders/detail-v16';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1000,height:1000}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));const results=[];
try{
 for(const kind of ['yukimura','ieyasu','ashigaru','tokugawa'])for(const rig of (['yukimura','ieyasu'].includes(kind)?['detail','physique']:['detail','detail-base'])){
  await page.goto(`http://127.0.0.1:5180/tools/model-preview.html?rig=${rig}&model=${kind}`);
  await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:60000});
  await page.evaluate(async()=>{const s=window.modelPreview.scene;await s.whenReadyAsync();s.render();s.getEngine().stopRenderLoop();});
  // Hide the version label only. Both versions use identical camera/light/frame.
  await page.locator('aside,nav').evaluateAll(nodes=>nodes.forEach(n=>n.style.display='none'));
  for(const clip of (['yukimura','ieyasu'].includes(kind)?['idle','thrust']:['idle']))for(const view of (['yukimura','ieyasu'].includes(kind)?['full','arms','armor']:['full','armor'])){
   const result=await page.evaluate(({clip,view})=>{
    const close=view!=='full';const p=window.modelPreview;p.play(clip);const g=p.loaded.animationGroups.find(g=>g.name===clip);
    g.pause();g.goToFrame(g.from+(g.to-g.from)*.35);p.scene.render();
    const m=p.loaded.meshes.find(m=>m.skeleton);m.skeleton.prepare(true);
    const wrist=m.skeleton.bones.find(b=>b.name==='hand.R').getAbsolutePosition(m);
    p.camera.target.copyFrom(close?wrist:wrist.set(0,1.35,0));
    p.camera.lowerRadiusLimit=.4;p.camera.radius=close?1.05:4.5;
    p.camera.alpha=1.25;p.camera.beta=1.35;if(view==='armor'){p.camera.target.set(0,1.65,0);p.camera.radius=1.6;p.camera.alpha=1.50;p.camera.beta=1.5;}p.scene.render();
    return {bones:m.skeleton.bones.length,triangles:p.loaded.meshes.reduce((s,m)=>s+m.getTotalIndices()/3,0)};
   },{clip,view});
   await page.waitForTimeout(100);
   const file=`${kind}-${rig}-${clip}-${view}.png`;
   await page.screenshot({path:`${out}/${file}`});
   results.push({kind,rig,clip,view,file,...result});
  }
 }
 if(errors.length)throw Error(errors.join('\n'));
 await writeFile(`${out}/capture.json`,JSON.stringify(results,null,2));
}finally{await browser.close()}
