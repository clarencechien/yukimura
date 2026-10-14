import {chromium} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
const out='renders/wrist-v22';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const results=[],errors=[];
try{
 const page=await browser.newPage({viewport:{width:1000,height:850}});
 page.on('pageerror',e=>errors.push(e.message));
 for(const kind of ['yukimura','ieyasu'])for(const version of ['trial','wrist']){
  await page.goto(`http://127.0.0.1:5180/tools/model-preview.html?rig=${version}&model=${kind}`);
  await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:120000});
  await page.evaluate(async()=>{const p=window.modelPreview;await p.scene.whenReadyAsync();p.scene.getEngine().stopRenderLoop()});
  await page.locator('aside,nav').evaluateAll(nodes=>nodes.forEach(n=>n.style.display='none'));
  for(const look of ['armor','bare']){
   if(look==='bare')await page.evaluate(()=>{
    const p=window.modelPreview;
    for(const m of p.loaded.meshes){
     if(!m.getTotalVertices())continue;
     if(m.material?.name.includes('deerskin')){
      const bones=m.getVerticesData('matricesIndices'),weights=m.getVerticesData('matricesWeights');
      const arms=new Set(m.skeleton.bones.flatMap((b,i)=>/^body\.(upperarm|lowerarm|wrist|finger|metacarpal)/.test(b.name)?[i]:[]));
      const ids=m.getIndices(),filtered=[];const isArm=v=>{let sum=0;for(let j=0;j<4;j++)if(arms.has(bones[v*4+j]))sum+=weights[v*4+j];return sum>.7};
      for(let i=0;i<ids.length;i+=3)if([ids[i],ids[i+1],ids[i+2]].every(isArm))filtered.push(ids[i],ids[i+1],ids[i+2]);m.setIndices(filtered);
      const mat=m.material;mat.albedoTexture=null;mat.bumpTexture=null;mat.metallicTexture=null;mat.detailMap.isEnabled=false;mat.albedoColor.set(.53,.40,.29);mat.metallic=0;mat.roughness=.8;
     }else{
      const bones=m.getVerticesData('matricesIndices'),weights=m.getVerticesData('matricesWeights');
      const weapon=m.skeleton?.bones.findIndex(b=>b.name==='weapon');
      if(!bones||weapon==null){m.setEnabled(false);continue}
      const ids=m.getIndices(),filtered=[];
      const belongs=v=>{let sum=0;for(let i=0;i<4;i++)if(bones[v*4+i]===weapon)sum+=weights[v*4+i];return sum>.95};
      for(let i=0;i<ids.length;i+=3)if([ids[i],ids[i+1],ids[i+2]].every(belongs))filtered.push(ids[i],ids[i+1],ids[i+2]);
      if(filtered.length)m.setIndices(filtered);else m.setEnabled(false);
     }
    }
   });
   for(const clip of ['idle','thrust'])for(const view of version==='trial'?['oblique']:['oblique','side','top']){
    const report=await page.evaluate(({clip,view})=>{
     const p=window.modelPreview;p.play(clip);
     const g=p.loaded.animationGroups.find(g=>g.name===clip);g.pause();g.goToFrame(g.from+(g.to-g.from)*.45);p.scene.render();
     const m=p.loaded.meshes.find(m=>m.skeleton);m.skeleton.prepare(true);
     const hands=['L','R'].map(s=>m.skeleton.bones.find(b=>b.name==='hand.'+s).getAbsolutePosition(m));
     p.camera.target.copyFrom(hands[0].add(hands[1]).scale(.5));p.camera.target.y+=.03;
     p.camera.lowerRadiusLimit=.25;p.camera.radius=1.45;p.camera.alpha=view==='side'?.08:view==='top'?Math.PI/2:2.05;p.camera.beta=view==='top'?.20:1.26;p.scene.render();
     return {hands:hands.map(h=>h.asArray()),bones:m.skeleton.bones.length};
    },{clip,view});
    const file=`${kind}-${version}-${clip}-${look}-${view}.png`;await page.screenshot({path:`${out}/${file}`});results.push({kind,version,clip,look,view,file,...report});
   }
   if(version==='wrist'){
    const frames=`.tmp/wrist-v22/frames/${kind}-${look}`;await mkdir(frames,{recursive:true});
    await page.setViewportSize({width:720,height:600});
    for(let i=0;i<30;i++){
     await page.evaluate(i=>{
      const p=window.modelPreview;p.play('thrust');const g=p.loaded.animationGroups.find(g=>g.name==='thrust');g.pause();g.goToFrame(g.from+(g.to-g.from)*i/30);
      p.camera.radius=1.7;p.camera.alpha=2.05;p.camera.beta=1.26;p.scene.render();
     },i);
     await page.screenshot({path:`${frames}/${String(i).padStart(3,'0')}.png`});
    }
    await page.setViewportSize({width:1000,height:850});
   }
  }
 }
 if(errors.length)throw Error(errors.join('\n'));
 await writeFile(`${out}/capture.json`,JSON.stringify({results,errors},null,2)+'\n');
}finally{await browser.close()}
