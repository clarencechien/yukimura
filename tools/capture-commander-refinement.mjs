import {chromium} from '@playwright/test';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
const stage=process.argv[2]||'after',out='renders/commanders-v13';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const only=process.argv[3];
if(only&&!['yukimura','ieyasu'].includes(only))throw Error('Unknown commander');
const results=only?JSON.parse(await readFile(`${out}/${stage}.json`,'utf8')).filter(r=>!r.file.includes('-'+only+'-')):[];
try{
 const page=await browser.newPage({viewport:{width:1100,height:900}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 for(const kind of only?[only]:['yukimura','ieyasu']){
  await page.goto('http://127.0.0.1:5180/tools/model-preview.html?model='+kind);await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:60000});
  await page.evaluate(async()=>{await window.modelPreview.scene.whenReadyAsync()});
  for(const clip of (kind==='yukimura'?['idle','slash','thrust']:['idle','thrust'])){
   for(const close of [false,true]){
    const stats=await page.evaluate(({clip,close})=>{
     const p=window.modelPreview;p.play(clip);const g=p.loaded.animationGroups.find(g=>g.name===clip);g.pause();g.goToFrame(g.from+(g.to-g.from)*.35);p.scene.render();
     const m=p.loaded.meshes.find(m=>m.skeleton);m.skeleton.prepare(true);
     const wrist=m.skeleton.bones.find(b=>b.name==='hand.R').getAbsolutePosition(m);
     if(close)p.camera.target.copyFrom(wrist);else p.camera.target.set(0,1.35,0);p.camera.lowerRadiusLimit=.6;p.camera.radius=close?1.1:4.5;p.camera.alpha=1.25;p.camera.beta=1.35;p.scene.render();
     return {kind:m.name,clip,close,triangles:m.getTotalIndices()/3,bones:m.skeleton.bones.length};
    },{clip,close});
    await page.waitForTimeout(150);const file=`${stage}-${kind}-${clip}-${close?'hands':'full'}.png`;await page.locator('canvas').screenshot({path:`${out}/${file}`});results.push({...stats,file});
   }
  }
 }
 if(errors.length)throw Error(errors.join('\n'));await writeFile(`${out}/${stage}.json`,JSON.stringify(results,null,2));
}finally{await browser.close()}
