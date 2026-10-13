import {chromium} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
const out='renders/fullbody-v14';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1200,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));const results=[];
try{for(const kind of process.argv.slice(2).length?process.argv.slice(2):['yukimura','ieyasu']){
 await page.goto('http://127.0.0.1:5180/tools/model-preview.html?rig=fullbody&model='+kind);await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:60000});
 for(const clip of (kind==='yukimura'?['idle','slash','thrust','dash']:['idle','thrust']))for(const close of [false,true]){
  const result=await page.evaluate(({clip,close})=>{const p=window.modelPreview;p.play(clip);const g=p.loaded.animationGroups.find(g=>g.name===clip);g.pause();g.goToFrame(g.from+(g.to-g.from)*.35);p.scene.render();const m=p.loaded.meshes.find(m=>m.skeleton);m.skeleton.prepare(true);const wrist=m.skeleton.bones.find(b=>b.name==='hand.R').getAbsolutePosition(m);p.camera.target.copyFrom(close?wrist:wrist.set(0,1.35,0));p.camera.lowerRadiusLimit=.4;p.camera.radius=close?1.05:4.5;p.camera.alpha=1.25;p.camera.beta=1.35;p.scene.render();return {bones:m.skeleton.bones.length,triangles:p.loaded.meshes.reduce((s,m)=>s+m.getTotalIndices()/3,0),sections:p.loaded.meshes.filter(m=>m.getTotalVertices()>0).map(m=>({name:m.name,mat:m.material?.name,bones:m.skeleton?.bones.length}))};},{clip,close});
  await page.waitForTimeout(150);const file=`${kind}-${clip}-${close?'hands':'full'}.png`;await page.locator('canvas').screenshot({path:`${out}/${file}`});results.push({kind,clip,close,file,...result});
 }
}if(errors.length)throw Error(errors.join('\n'));await writeFile(out+'/capture.json',JSON.stringify(results,null,2));}finally{await browser.close()}
