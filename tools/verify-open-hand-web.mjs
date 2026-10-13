import {chromium} from 'playwright-core';
import {writeFile} from 'node:fs/promises';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const report={gallery:[],models:[]};
try{
 for(const width of [1280,390]){
  const page=await browser.newPage({viewport:{width,height:900},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  const dependencies=[];page.on('request',r=>{if(r.resourceType()!=='document'&&r.url().startsWith('http'))dependencies.push(r.url())});
  await page.goto('http://127.0.0.1:8767/renders/open-hand/index.html');
  await page.waitForFunction(()=>[...document.images].length===5&&[...document.images].every(i=>i.complete&&i.naturalWidth===2560));
  const gallery=await page.evaluate(()=>({images:[...document.images].map(i=>({width:i.naturalWidth,height:i.naturalHeight,embedded:i.src.startsWith('data:')})),overflow:document.documentElement.scrollWidth>innerWidth}));
  if(gallery.overflow)throw Error('Gallery overflow');report.gallery.push({width,...gallery});
  await page.goto('http://127.0.0.1:8767/renders/open-hand/game-model.html');
  await page.waitForFunction(()=>window.handPreview?.ready,{},{timeout:60000});
  await page.waitForTimeout(1500);
  for(const lod of [0,1]){
   await page.evaluate(async level=>{await window.handPreview.load(level)},lod);
   const model=await page.evaluate(()=>{const p=window.handPreview,s=p.scene;return {lod:p.lod,meshes:p.loaded.meshes.filter(m=>m.getTotalVertices()>0).map(m=>({vertices:m.getTotalVertices(),triangles:m.getTotalIndices()/3,skinned:!!m.skeleton})),skeletons:p.loaded.skeletons.map(s=>s.bones.length),materials:p.loaded.materials.length,textures:s.textures.filter(t=>t.name!=='local-winter-sky').map(t=>({ready:t.isReady(),size:t.getSize()})),overflow:document.documentElement.scrollWidth>innerWidth}});
   if(model.overflow||!model.meshes.every(m=>m.skinned)||!model.textures.every(t=>t.ready))throw Error(JSON.stringify(model));
   report.models.push({width,...model});
   if(width===1280){await page.screenshot({path:`renders/open-hand/game-lod${lod}.png`});await page.locator('canvas').screenshot({path:`renders/open-hand/game-canvas-lod${lod}.png`})}
  }
  if(errors.length)throw Error(errors.join('\n'));
  if(dependencies.length)throw Error('External dependency: '+dependencies.join(', '));
  if(width===390)await page.screenshot({path:'renders/open-hand/game-mobile.png'});
  await page.close();
 }
 await writeFile('renders/open-hand/web-check.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{await browser.close()}
