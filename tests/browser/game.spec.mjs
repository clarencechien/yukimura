import {test,expect} from '@playwright/test';
const dev='http://127.0.0.1:5175/?test',prod='http://127.0.0.1:4173';
function errorsOn(page){const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});return errors;}
async function ready(page,url){await page.goto(url);await expect(page.locator('#start')).toBeEnabled({timeout:60000});}
test('production desktop: GLB, narrative, movement, combat, pause and formations',async({page})=>{
 const errors=errorsOn(page);await page.setViewportSize({width:1440,height:900});await ready(page,prod);
 await page.click('#readLore');await expect(page.locator('#lore')).toBeVisible();await expect(page.locator('#lore')).toContainText('猿飛佐助');await page.click('#closeLore');
 await expect(page.locator('#menuBackdrop')).toBeVisible();
 await page.screenshot({path:'test-results/desktop-menu.png'});await page.click('#start');
 await expect(page.locator('#menuBackdrop')).toBeHidden();
 expect((await page.evaluate(()=>window.__sanada)).allies).toBe(10);
 expect((await page.evaluate(()=>window.__sanada)).models).toHaveLength(4);
 expect((await page.evaluate(()=>window.__sanada)).animationClips).toEqual(['idle','run','slash']);
 await page.keyboard.down('w');await expect.poll(()=>page.evaluate(()=>window.__sanada.heroAnimation)).toBe('run');await page.keyboard.up('w');
 await expect.poll(()=>page.evaluate(()=>window.__sanada.heroAnimation)).toBe('idle');
 await page.keyboard.down('w');await page.keyboard.down('j');await expect.poll(()=>page.evaluate(()=>window.__sanada.heroAnimation)).toBe('slash');await page.waitForTimeout(2300);await page.keyboard.up('w');await page.keyboard.up('j');
 expect((await page.evaluate(()=>window.__sanada)).position.z).toBeGreaterThan(.5);
 await page.keyboard.press('f');expect((await page.evaluate(()=>window.__sanada)).formation).toBe('charge');await page.keyboard.press('p');expect((await page.evaluate(()=>window.__sanada)).state).toBe('paused');const before=await page.evaluate(()=>window.__sanada.position);await page.waitForTimeout(300);expect(await page.evaluate(()=>window.__sanada.position)).toEqual(before);await page.click('#resume');
 await page.screenshot({path:'test-results/desktop-battle.png'});expect(errors).toEqual([]);
 expect(await page.evaluate(()=>window.__sanadaTest)).toBeUndefined();
});
test('full combat loop wins, unlocks next cycle, and defeat restarts cleanly',async({page})=>{
 const errors=errorsOn(page);await ready(page,dev);await page.selectOption('#difficulty','story');await page.click('#start');await page.keyboard.down('j');
 for(let i=0;i<180;i++){
  const s=await page.evaluate(()=>window.__sanada);if(s.state!=='playing')break;
  if(s.position.z<145){await page.keyboard.down('w');if(s.position.x<0)await page.keyboard.down('d');else await page.keyboard.up('d');}else{await page.keyboard.up('w');await page.keyboard.up('d');}
  if(s.rage>=100)await page.keyboard.press('k');await page.evaluate(()=>window.__sanadaTest.step(.5));
 }
 await page.keyboard.up('j');expect((await page.evaluate(()=>window.__sanada)).state).toBe('won');expect((await page.evaluate(()=>window.__sanada)).kills).toBeGreaterThan(10);await expect(page.locator('#result')).toBeVisible();await page.screenshot({path:'test-results/victory.png'});
 await page.click('#retry');expect((await page.evaluate(()=>window.__sanada)).cycle).toBe(2);expect((await page.evaluate(()=>window.__sanada)).kills).toBe(0);
 await page.evaluate(()=>window.__sanadaTest.step(180));expect((await page.evaluate(()=>window.__sanada)).state).toBe('lost');await page.click('#retry');expect((await page.evaluate(()=>window.__sanada)).state).toBe('playing');expect((await page.evaluate(()=>window.__sanada)).hp).toBe(180);expect(errors).toEqual([]);
});
test('mobile portrait and landscape: touch joystick, skills, readable menu',async({browser})=>{
 const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1});const page=await context.newPage();const errors=errorsOn(page);await ready(page,prod);
 await page.screenshot({path:'test-results/mobile-menu.png'});await page.tap('#start');await expect(page.locator('#joystick')).toBeVisible();
 const r=await page.locator('#joystick').boundingBox();const client=await context.newCDPSession(page);const x=r.x+r.width/2,y=r.y+r.height/2;
 await client.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});await client.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y-35}]});await page.waitForTimeout(1300);await client.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});expect((await page.evaluate(()=>window.__sanada)).position.z).toBeGreaterThan(.2);
 await page.tap('#formation');expect((await page.evaluate(()=>window.__sanada)).formation).toBe('charge');await page.tap('#dash');await page.tap('#attack');await page.screenshot({path:'test-results/mobile-battle.png'});
 await page.tap('#pause');await page.tap('#returnMenu');await page.setViewportSize({width:844,height:390});await page.screenshot({path:'test-results/mobile-landscape.png'});const button=await page.locator('#start').boundingBox();expect(button.y+button.height).toBeLessThan(390);expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(844);expect(errors).toEqual([]);await context.close();
});
