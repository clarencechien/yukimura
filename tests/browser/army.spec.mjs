import {test,expect} from '@playwright/test';

for(const kind of ['ashigaru','ieyasu'])test(`${kind}: baked GPU palette matches the imported glTF skeleton at three attack times`,async({page})=>{
 await page.goto('http://127.0.0.1:5175/tools/model-preview.html?model='+kind);
 await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:60000});
 const comparison=await page.evaluate(async(kind)=>{
  const p=window.modelPreview,manifest=await(await fetch('/models/crowd-animation.json')).json(),asset=manifest.models[kind];
  const data=new Float32Array(await(await fetch('/models/'+asset.uri)).arrayBuffer());
  p.loaded.animationGroups.forEach(g=>g.stop());const g=p.loaded.animationGroups.find(g=>g.name==='thrust');g.start(true);g.pause();
  const range=asset.clips.thrust,errors=[];
  const mesh=p.loaded.meshes.find(m=>m.skeleton),skeleton=mesh.skeleton;
  for(const sample of [7,24,41]){
   const frame=range.start+sample;g.goToFrame(g.from+(g.to-g.from)*sample/(range.end-range.start));p.scene.render();skeleton.prepare(true);
   const cpu=skeleton.getTransformMatrices(mesh),gpu=data.slice(frame*asset.width*4,(frame+1)*asset.width*4);
   errors.push(Math.max(...gpu.slice(0,asset.joints*16).map((v,i)=>Math.abs(v-cpu[i]))));
  }
  return {maxError:Math.max(...errors),joints:asset.joints};
 },kind);
 expect(comparison.joints).toBe(kind==='ieyasu'?92:18);expect(comparison.maxError).toBeLessThan(.002);
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

test('soldiers collapse through two articulated poses without rotating or shrinking the actor root',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:5175/?test');await expect(page.locator('#start')).toBeEnabled({timeout:60000});await page.click('#start');
 await page.evaluate(()=>window.__sanadaTest.setupFalls());await page.evaluate(()=>window.__sanadaTest.step(.38));
 const early=await page.evaluate(()=>({falls:window.__sanadaTest.snapshot().falls,states:window.__sanada.crowd.enemies}));
 expect(early.falls).toHaveLength(6);expect(new Set(early.states.map(a=>a.state))).toEqual(new Set(['fall','fall_back']));
 expect(new Set(early.falls.map(f=>f.duration)).size).toBeGreaterThan(3);
 for(const f of early.falls){expect(f.rootZ).toBe(0);expect(f.scale).toBe(1);}
 await page.screenshot({path:'test-results/fall-kneel.png'});
 await page.evaluate(()=>window.__sanadaTest.step(.93));
 const settled=await page.evaluate(()=>window.__sanadaTest.snapshot().falls);
 expect(settled).toHaveLength(6);expect(settled.every(f=>f.landed&&f.scale===1&&f.rootZ===0)).toBe(true);
 await page.screenshot({path:'test-results/fall-settled.png'});
 await page.keyboard.press('p');const before=await page.evaluate(()=>window.__sanadaTest.snapshot().falls);await page.evaluate(()=>window.__sanadaTest.step(.5));expect(await page.evaluate(()=>window.__sanadaTest.snapshot().falls)).toEqual(before);
 await page.click('#resume');await page.evaluate(()=>window.__sanadaTest.step(1));expect((await page.evaluate(()=>window.__sanada)).corpses).toBe(0);expect(errors).toEqual([]);
});

test('Ieyasu instances all four material sections on the same GPU animation frame',async({page})=>{
 await page.goto('http://127.0.0.1:5175/?test');await expect(page.locator('#start')).toBeEnabled({timeout:60000});await page.click('#start');
 await page.evaluate(()=>{window.__sanadaTest.inspectBoss(true);window.__sanadaTest.step(.3)});
 const parts=await page.evaluate(()=>window.__sanadaTest.snapshot().bossParts);
 expect(parts).toHaveLength(4);expect(new Set(parts.map(p=>p.frame)).size).toBe(1);expect(parts.every(p=>p.enabled&&p.vertices>0)).toBe(true);
 expect(parts.map(p=>p.material)).toEqual(expect.arrayContaining(['runtime/ieyasu high bake','commander deerskin and cloth','fitted black iron kote','samurai woven cords and fittings']));
});
