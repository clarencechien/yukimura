import {chromium} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
const menpo=process.argv.includes('--menpo');
const closeup=process.argv.includes('--closeup');
const out=closeup?'.tmp/menpo-v18/expressions':menpo?'renders/menpo-v18':'renders/face-v17';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const results=[],errors=[];
try{
 const page=await browser.newPage({viewport:{width:1000,height:1000}});
 page.on('pageerror',e=>errors.push(e.message));
 for(const kind of ['yukimura','ieyasu'])for(const rig of closeup?['menpo']:menpo?['menpo-before','menpo']:['face-before','face']){
  await page.goto(`http://127.0.0.1:5180/tools/model-preview.html?rig=${rig}&model=${kind}`);
  await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:120000});
  await page.evaluate(async()=>{const p=window.modelPreview;await p.scene.whenReadyAsync();p.scene.getEngine().stopRenderLoop()});
  await page.locator('aside,nav').evaluateAll(nodes=>nodes.forEach(n=>n.style.display='none'));
  for(const [clip,view] of closeup?[['idle','face']]:[['idle','face'],['idle','profile'],['idle','full'],['thrust','action'],['run','action']]){
   const report=await page.evaluate(({clip,view,kind})=>{
    const p=window.modelPreview;p.play(clip);const g=p.loaded.animationGroups.find(g=>g.name===clip);g.pause();g.goToFrame(g.from+(g.to-g.from)*.35);p.scene.render();
    p.camera.lowerRadiusLimit=.25;p.camera.alpha=view==='profile'?.28:kind==='ieyasu'?2.05:1.40;p.camera.beta=1.48;
    p.camera.target.set(0,view==='full'?1.45:view==='action'?1.75:1.94,view==='full'?0:.16);
    p.camera.radius=view==='full'?4.4:view==='action'?2.5:.85;p.scene.render();
    const skin=p.loaded.meshes.find(m=>m.material?.name.startsWith('human skin /'));
    return {triangles:p.loaded.meshes.reduce((n,m)=>n+m.getTotalIndices()/3,0),skin:skin?{vertices:skin.getTotalVertices(),material:skin.material.name,metallic:skin.material.metallic,detail:skin.material.detailMap.isEnabled,clearCoat:skin.material.clearCoat.isEnabled}:null};
   },{clip,view,kind});
   if((rig==='face'||menpo)&&(!report.skin||report.skin.metallic!==0||report.skin.detail||report.skin.clearCoat))throw Error('Skin inherited armor treatment');
   const file=`${kind}-${rig}-${clip}-${view}.png`;await page.screenshot({path:`${out}/${file}`});
   results.push({kind,rig,clip,view,file,...report});
  }
 }
 if(errors.length)throw Error(errors.join('\n'));
 await writeFile(`${out}/capture.json`,JSON.stringify({results,errors},null,2)+'\n');
}finally{await browser.close()}
