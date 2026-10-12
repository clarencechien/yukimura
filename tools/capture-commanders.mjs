import {chromium} from '@playwright/test';
import {existsSync} from 'node:fs';
const base=process.argv[2]||'http://127.0.0.1:5180';
const only=process.argv[3];
const browser=await chromium.launch({executablePath:existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const page=await browser.newPage({viewport:{width:1100,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 for(const kind of only?[only]:['ieyasu','ashigaru']){
  await page.goto(base+'/tools/model-preview.html?model='+kind);await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:60000});
  await page.evaluate(async()=>{const p=window.modelPreview;await p.scene.whenReadyAsync();});await page.waitForTimeout(1000);
  for(const [name,progress] of kind==='ieyasu'?[['idle',.3],['thrust',.4]]:[['fall',.43],['fall',1],['fall_back',1]]){
   const metrics=await page.evaluate(({name,progress})=>{
    const p=window.modelPreview;p.play(name);const g=p.loaded.animationGroups.find(g=>g.name===name);g.pause();g.goToFrame(g.from+(g.to-g.from)*progress);p.scene.render();
    p.camera.radius=4.5;p.camera.target.y=name.startsWith('fall')?.65:1.35;
    const mesh=p.loaded.meshes.find(m=>m.skeleton);mesh.skeleton.prepare(true);
    return mesh.skeleton.bones.filter(b=>['pelvis','head','hand.L','hand.R'].includes(b.name)).map(b=>({name:b.name,position:b.getAbsolutePosition(mesh).asArray()}));
   },{name,progress});
   await page.waitForTimeout(350);await page.screenshot({path:`docs/art/${kind}-${name}-${progress===1?'settled':'pose'}.png`});console.log(kind,name,progress,JSON.stringify(metrics));
  }
 }
 if(errors.length)throw Error(errors.join('\n'));
}finally{await browser.close();}
