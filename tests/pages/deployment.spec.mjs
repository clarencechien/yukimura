import {test,expect} from '@playwright/test';
test('v21 face and weapon-grip trials show candidates first with valid evidence',async({page,request})=>{
 const errors=[];page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 const root='http://127.0.0.1:4174/yukimura/review/';
 for(const [path,title,count] of [['menpo/trial/','赤冬 · 面具試作 v21',20],['technique/','赤冬 · 槍術與劍術握持試作',24]]){
  expect((await page.goto(root+path)).status()).toBe(200);
  await expect(page).toHaveTitle(title);await expect(page.locator('img')).toHaveCount(count);
  await expect(page.locator('figcaption').first()).toHaveText('v21 試作');
  await page.locator('img').evaluateAll(images=>Promise.all(images.map(i=>i.decode())));
  await expect(page.locator('.tag')).toContainText('v22');
  for(const width of [1280,390]){
   await page.setViewportSize({width,height:900});
   expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
  }
 }
 const response=await request.get(root+'technique/grip-check.json');expect(response.status()).toBe(200);
 const report=await response.json();
 for(const kind of ['yukimura','ieyasu']){
  expect(report[kind].after.maxGripErrorM).toBeLessThan(.0005);
  expect(report[kind].after.minAxisDot).toBeGreaterThan(.999);
 }
 expect(report.ieyasu.after.clips.thrust.maxWristAngle).toBeLessThan(10);
 expect(report.ieyasu.before.clips.thrust.maxWristAngle).toBeGreaterThan(40);
 await page.goto(root+'menpo/');await page.getByRole('link',{name:'查看較俐落的 v21 面具試作 ↗'}).click();
 await expect(page).toHaveTitle('赤冬 · 面具試作 v21');expect(errors).toEqual([]);
});
test('Menpo review loads all before/after images and motion evidence under Pages',async({page,request})=>{
 const errors=[];
 page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 const base='http://127.0.0.1:4174/yukimura/review/menpo/';
 expect((await page.goto(base)).status()).toBe(200);
 await expect(page).toHaveTitle('赤冬 · 立體面頬 v20');
 await expect(page.locator('img')).toHaveCount(20);
 await expect(page.locator('figcaption').first()).toContainText('新版 v20');
 await expect(page.locator('img').first()).toHaveAttribute('src','yukimura-sculpt-idle-face.png');
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
 await expect(page).toHaveTitle('赤冬 · 立體面頬 v20');
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


test('v22 wrist study links from the open trial and loads comparison images and motion',async({page,request})=>{
 const base='http://127.0.0.1:4174/yukimura/review/';
 const errors=[];page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 await page.goto(base+'menpo/trial/');
 await page.getByRole('link',{name:'最新 v22 手腕與握姿試作 ↗'}).click();
 await expect(page).toHaveTitle('赤冬 · 手腕與握姿試作 v22');
 await expect(page.locator('.tag')).toContainText('已套用至遊戲');
 await expect(page.locator('img')).toHaveCount(32);
 await page.locator('img').evaluateAll(images=>Promise.all(images.map(i=>{i.loading='eager';return i.decode()})));
 await expect(page.locator('figcaption').first()).toContainText('穿甲');
 await expect(page.locator('video')).toHaveCount(4);
 const motion=await page.locator('video').evaluateAll(videos=>Promise.all(videos.map(v=>new Promise((resolve,reject)=>{
  v.onloadedmetadata=()=>resolve({duration:v.duration,width:v.videoWidth,height:v.videoHeight});
  v.onerror=()=>reject(Error('Video failed to load'));v.preload='metadata';v.load();
 }))));
 for(const v of motion){expect(v.duration).toBeCloseTo(1,1);expect(v.width).toBe(720);expect(v.height).toBe(600)}
 const response=await request.get(base+'wrists/validation.json');expect(response.ok()).toBe(true);
 const report=await response.json();expect(report.passed).toBe(true);
 for(const model of Object.values(report.models)){
  expect(model.grip_check.maxGripErrorM).toBeLessThan(.0005);
  for(const digits of Object.values(model.exported.clips))for(const [name,digit] of Object.entries(digits)){
   expect(digit.max_compression_m).toBeLessThan(.002);
   if(name.endsWith('1'))expect(digit.max_q05_radius_m).toBeLessThan(.025);
  }
 }
 for(const width of [1280,390]){
  await page.setViewportSize({width,height:900});
  await page.locator('details').evaluateAll(nodes=>nodes.forEach(n=>n.open=true));
  expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
 }
 expect(errors).toEqual([]);
});
