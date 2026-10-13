// Run against the Vite dev server, e.g. npm run dev -- --port 5180.
import {chromium} from '@playwright/test';
import {writeFile} from 'node:fs/promises';
const origin=process.env.CANDIDATE_ORIGIN||'http://127.0.0.1:5180';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const results=[];
try{
 const page=await browser.newPage({viewport:{width:1000,height:1200}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 for(const kind of ['rocketbox','cyber-samurai']){
  await page.goto(`${origin}/tools/character-candidate-preview.html?model=${kind}`);
  await page.waitForFunction(()=>window.candidatePreview?.ready,{},{timeout:120000});
  const result=await page.evaluate(()=>{
   const {scene,loaded}=window.candidatePreview;
   const meshes=loaded.meshes.filter(m=>m.getTotalVertices()>0);
   const missingTextures=scene.textures.filter(t=>!t.isReady()).map(t=>t.name);
   const nonFiniteMeshes=meshes.filter(m=>!Array.from(m.getWorldMatrix().m).every(Number.isFinite)).map(m=>m.name);
   const managers=[...new Set(meshes.map(m=>m.morphTargetManager).filter(Boolean))];
   // Exercise the actual exported expression targets and render once before restoring.
   for(const m of managers)for(let i=0;i<m.numTargets;i++)m.getTarget(i).influence=.35;
   scene.render();
   for(const m of managers)for(let i=0;i<m.numTargets;i++)m.getTarget(i).influence=0;
   scene.render();
   return {meshes:meshes.length,triangles:meshes.reduce((n,m)=>n+m.getTotalIndices()/3,0),
    skeletons:loaded.skeletons.length,bones:loaded.skeletons.map(s=>s.bones.length),
    morphTargets:managers.map(m=>m.numTargets),textures:scene.textures.length,missingTextures,nonFiniteMeshes};
  });
  if(result.missingTextures.length||result.nonFiniteMeshes.length||errors.length)throw Error(JSON.stringify({result,errors}));
  await page.screenshot({path:`public/review/candidates/${kind}-babylon.png`});
  results.push({kind,...result});
 }
 await page.goto(`${origin}/review/candidates/index.html`);
 for(const width of [1280,390]){
  await page.setViewportSize({width,height:900});
  const state=await page.evaluate(async()=>{
   await Promise.all([...document.images].map(i=>i.decode()));
   return {images:document.images.length,overflow:document.documentElement.scrollWidth>innerWidth};
  });
  if(state.images!==5||state.overflow)throw Error(JSON.stringify(state));
 }
 await writeFile('public/review/candidates/browser-check.json',JSON.stringify({renderer:'Chromium / SwiftShader (software; not a phone performance test)',results,errors,gallery:{images:5,widths:[1280,390],passed:true}},null,2)+'\n');
}finally{await browser.close()}
