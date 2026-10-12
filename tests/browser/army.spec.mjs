import {test,expect} from '@playwright/test';

test('baked GPU palette matches the imported glTF skeleton at an attack frame',async({page})=>{
 await page.goto('http://127.0.0.1:5175/tools/model-preview.html?model=ashigaru');
 await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:60000});
 const comparison=await page.evaluate(async()=>{
  const p=window.modelPreview,manifest=await(await fetch('/models/crowd-animation.json')).json(),asset=manifest.models.ashigaru;
  const data=new Float32Array(await(await fetch('/models/'+asset.uri)).arrayBuffer());
  p.loaded.animationGroups.forEach(g=>g.stop());const g=p.loaded.animationGroups.find(g=>g.name==='thrust');g.start(true);g.pause();
  const range=asset.clips.thrust,frame=range.start+24;g.goToFrame(g.from+(g.to-g.from)*24/(range.end-range.start));p.scene.render();
  const mesh=p.loaded.meshes.find(m=>m.skeleton),skeleton=mesh.skeleton;skeleton.prepare(true);
  const cpu=skeleton.getTransformMatrices(mesh),gpu=data.slice(frame*asset.width*4,(frame+1)*asset.width*4);
  return {maxError:Math.max(...gpu.slice(0,asset.joints*16).map((v,i)=>Math.abs(v-cpu[i]))),joints:asset.joints};
 });
 expect(comparison.joints).toBe(18);expect(comparison.maxError).toBeLessThan(.002);
});

test('100 enemies and ten allies animate independently, pause and clear on restart',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.goto('http://127.0.0.1:5175/?test');await expect(page.locator('#start')).toBeEnabled({timeout:60000});await page.click('#start');
 await page.evaluate(()=>{window.__sanadaTest.setupArmy();window.__sanadaTest.step(.22)});
 const initial=await page.evaluate(()=>window.__sanada.crowd);
 expect(initial.actors).toBe(110);expect(initial.instances).toBe(110);expect(initial.allies).toHaveLength(10);
 expect(initial.allies.filter(a=>a.state==='run').length).toBeGreaterThan(4);
 expect(initial.enemies.filter(a=>a.state==='run').length).toBe(100);
 expect(new Set(initial.enemies.map(a=>a.frame)).size).toBeGreaterThan(10);
 await page.keyboard.press('p');await page.evaluate(()=>window.__sanadaTest.step(1));expect(await page.evaluate(()=>window.__sanada.crowd)).toEqual(initial);
 await page.click('#resume');await page.evaluate(()=>window.__sanadaTest.step(.24));
 expect(await page.evaluate(()=>window.__sanada.crowd.enemies)).not.toEqual(initial.enemies);
 await page.evaluate(()=>window.__sanadaTest.step(3));
 const fighting=await page.evaluate(()=>window.__sanada.crowd);
 expect(fighting.enemies.some(a=>a.state==='thrust'||a.state==='hurt')).toBe(true);
 expect(fighting.allies.some(a=>a.state==='thrust')).toBe(true);
 await page.screenshot({path:'test-results/animated-army.png'});
 await page.keyboard.press('p');await page.click('#returnMenu');await page.click('#start');
 expect((await page.evaluate(()=>window.__sanada.crowd)).actors).toBe(50);expect(errors).toEqual([]);
});
