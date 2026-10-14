import {test,expect} from '@playwright/test';
test('Menpo review loads all before/after images and motion evidence under Pages',async({page,request})=>{
 const errors=[];
 page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 const base='http://127.0.0.1:4174/yukimura/review/menpo/';
 expect((await page.goto(base)).status()).toBe(200);
 await expect(page).toHaveTitle('赤冬 · 武士面頬 v19');
 await expect(page.locator('img')).toHaveCount(20);
 await page.locator('img').evaluateAll(images=>Promise.all(images.map(i=>i.decode())));
 for(const width of [1280,390]){
  await page.setViewportSize({width,height:900});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
 }
 const motion=await request.get(base+'motion-check.json');expect(motion.status()).toBe(200);
 const report=await motion.json();expect(report.passed).toBe(true);expect(report.results).toHaveLength(14);
 for(const clip of report.results){expect(clip.minimum_skin_clearance_m).toBeGreaterThan(.0001);expect(clip.mask_vertices).toBeGreaterThan(0);}
 expect((await request.get(base+'LICENSE-Rocketbox.txt')).status()).toBe(200);
 await page.goto('http://127.0.0.1:4174/yukimura/review/faces/');
 await page.getByRole('link',{name:'查看真人頭部加上面罩的新版比較 ↗'}).click();
 await expect(page).toHaveTitle('赤冬 · 武士面頬 v19');
 expect(errors).toEqual([]);
});
test('Human head review displays all twenty before/after images under Pages',async({page,request})=>{
 const errors=[];
 page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 const base='http://127.0.0.1:4174/yukimura/review/faces/';
 const response=await page.goto(base);expect(response.status()).toBe(200);
 await expect(page).toHaveTitle('赤冬 · 武將頭臉精修 v17');
 await expect(page.locator('img')).toHaveCount(20);
 await page.locator('img').evaluateAll(images=>Promise.all(images.map(i=>i.decode())));
 for(const width of [1280,390]){
  await page.setViewportSize({width,height:900});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
 }
 const motion=await request.get(base+'motion-check.json');expect(motion.status()).toBe(200);
 expect((await motion.json()).results).toHaveLength(14);
 expect((await request.get(base+'LICENSE-Rocketbox.txt')).status()).toBe(200);
 expect(errors).toEqual([]);
});
test('Candidate study resolves images, licensed models and provenance under Pages subpath',async({page,request})=>{
 const errors=[];
 page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 const base='http://127.0.0.1:4174/yukimura/review/candidates/';
 const response=await page.goto(base);
 expect(response.status()).toBe(200);
 await expect(page).toHaveTitle('赤冬 · 寫實人物素材試載');
 await expect(page.locator('img')).toHaveCount(5);
 await page.locator('img').evaluateAll(images=>Promise.all(images.map(i=>i.decode())));
 for(const width of [1280,390]){
  await page.setViewportSize({width,height:900});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
 }
 for(const file of ['rocketbox-LICENSE.txt','cyber-samurai-LICENSE.txt','sources.json','validation.json','browser-check.json']){
  expect((await request.get(base+file)).status()).toBe(200);
 }
 for(const name of ['rocketbox','cyber-samurai']){
  const model=await request.get(base+name+'.glb');expect(model.status()).toBe(200);
  expect((await model.body()).subarray(0,4).toString()).toBe('glTF');
 }
 expect(errors).toEqual([]);
});
test('Pages subpath loads background, four models and shared textures, and starts combat',async({page})=>{
 const errors=[],assets=new Set();
 page.on('pageerror',e=>errors.push(e.message));
 page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);assets.add(new URL(r.url()).pathname)});
 await page.goto('http://127.0.0.1:4174/yukimura/');
 await expect(page.locator('#start')).toBeEnabled({timeout:60000});
 expect(assets.has('/yukimura/art/concept.png')).toBe(true);
 for(const kind of ['terrain','wood','stone','plaster','roof','snow'])for(const map of ['color','normal','surface'])expect(assets.has(`/yukimura/environment/${kind}-${map}.png`)).toBe(true);
 expect(assets.has('/yukimura/environment/ground-detail.png')).toBe(true);
 for(const role of ['yukimura','ieyasu'])expect(assets.has(`/yukimura/look/${role}-coat.png`)).toBe(true);
 for(const surface of ['forged','woven'])expect(assets.has(`/yukimura/look/${surface}-detail.png`)).toBe(true);
 for(const name of ['yukimura','ashigaru','tokugawa','ieyasu'])expect(assets.has(`/yukimura/models/${name}.glb`)).toBe(true);
 expect([...assets].filter(p=>p.startsWith('/yukimura/models/shared/')&&p.endsWith('.png'))).toHaveLength(14);
 expect(assets.has('/yukimura/models/crowd-animation.json')).toBe(true);
 expect([...assets].filter(p=>p.startsWith('/yukimura/models/shared/')&&p.endsWith('.bin'))).toHaveLength(2);
 await page.click('#start');await page.keyboard.down('w');await page.waitForTimeout(1500);await page.keyboard.up('w');
 const status=await page.evaluate(()=>window.__sanada);
 expect(status.state).toBe('playing');expect(status.position.z).toBeGreaterThan(.2);expect(status.allies).toBe(10);
 expect(status.crowd.instances).toBeGreaterThanOrEqual(50);expect(status.crowd.allies).toHaveLength(10);expect(errors).toEqual([]);
});

test('Pages review opens with all twenty embedded comparison images without JavaScript',async({browser})=>{
 const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:1280,height:900}});
 try{
  const page=await context.newPage(),errors=[];
  page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
  const response=await page.goto('http://127.0.0.1:4174/yukimura/review/');
  expect(response.status()).toBe(200);await expect(page).toHaveTitle('共用甲冑套件 · v16');
  await expect(page.locator('img')).toHaveCount(20);
  await expect.poll(()=>page.locator('img').evaluateAll(images=>images.filter(i=>i.complete&&i.naturalWidth>0&&i.src.startsWith('data:image/png;base64,')).length)).toBe(20);
  for(const width of [1280,390]){
   await page.setViewportSize({width,height:900});
   expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
  }
  expect(errors).toEqual([]);
 }finally{await context.close()}
});
