import {chromium} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
const out='renders/menpo-v21/grip';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const results=[],errors=[];
try{
 const page=await browser.newPage({viewport:{width:1100,height:900}});
 page.on('pageerror',e=>errors.push(e.message));
 for(const kind of ['yukimura','ieyasu'])for(const rig of ['trial-before','trial']){
  await page.goto(`http://127.0.0.1:5180/tools/model-preview.html?rig=${rig}&model=${kind}`);
  await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:120000});
  await page.evaluate(async()=>{const p=window.modelPreview;await p.scene.whenReadyAsync();p.scene.getEngine().stopRenderLoop()});
  await page.locator('aside,nav').evaluateAll(nodes=>nodes.forEach(n=>n.style.display='none'));
  for(const clip of ['idle','run','thrust'])for(const view of ['oblique','side']){
   const report=await page.evaluate(({clip,view})=>{
    const p=window.modelPreview;p.play(clip);
    const g=p.loaded.animationGroups.find(g=>g.name===clip);g.pause();g.goToFrame(g.from+(g.to-g.from)*.35);p.scene.render();
    const mesh=p.loaded.meshes.find(m=>m.skeleton);mesh.skeleton.prepare(true);
    const hands=['L','R'].map(s=>mesh.skeleton.bones.find(b=>b.name==='hand.'+s).getAbsolutePosition(mesh));
    p.camera.target.copyFrom(hands[0].add(hands[1]).scale(.5));
    p.camera.lowerRadiusLimit=.25;p.camera.radius=1.55;p.camera.alpha=view==='side'?.30:2.25;p.camera.beta=1.30;p.scene.render();
    return {hands:hands.map(h=>h.asArray()),bones:mesh.skeleton.bones.length};
   },{clip,view});
   const file=`${kind}-${rig}-${clip}-${view}.png`;await page.screenshot({path:`${out}/${file}`});
   results.push({kind,rig,clip,view,file,...report});
  }
 }
 if(errors.length)throw Error(errors.join('\n'));
 await writeFile(`${out}/capture.json`,JSON.stringify({results,errors},null,2)+'\n');
}finally{await browser.close()}
