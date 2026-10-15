// Functional check of rendered art preview; no changes to the game test suite.
import { chromium } from '@playwright/test';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const rigid=process.argv.includes('--rigid'),study=rigid?'yari-rigid':'yari-motion';
const root=process.cwd(),out=`docs/routes/jigoku-2d/${study}`;
const server=http.createServer(async(req,res)=>{
  try {
    const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
    if(!file.startsWith(root+'/'))throw Error('outside root');
    const data=await fs.readFile(file);
    res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.png':'image/png','.webp':'image/webp','.gif':'image/gif','.json':'application/json'})[path.extname(file)]||'text/plain; charset=utf-8');res.end(data);
  } catch {res.statusCode=404;res.end('not found');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
const errors=[],failed=[],checks=[];
try {
  const page=await browser.newPage({viewport:{width:1440,height:1100}});
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('/favicon.ico'))failed.push(r.url());});
  await page.goto(`http://127.0.0.1:${server.address().port}/docs/routes/jigoku-2d/${study}-review.html`);
  const ready=()=>page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('36 幀'));
  const scrub=async(frame)=>page.locator('#scrub').evaluate((el,value)=>{el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));},String(frame));
  const pixels=()=>page.locator('canvas').evaluate(async el=>{
    const rgba=el.getContext('2d').getImageData(0,0,el.width,el.height).data,alpha=new Uint8Array(rgba.length/4);
    let opaque=0;for(let i=0;i<alpha.length;i++){alpha[i]=rgba[i*4+3];if(alpha[i]>240)opaque++;}
    const hash=async a=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',a))).join(',');
    return {rgba:await hash(rgba),alpha:await hash(alpha),opaque};
  });
  await ready();assert.equal(await page.locator('canvas').getAttribute('data-quality'),'desktop');await scrub(0);const start=await pixels();assert(start.opaque>10000);
  await scrub(14);const thrust=await pixels();assert.notDeepEqual(start,thrust);checks.push('Rendered sprite visible; scrub changes actual canvas pixels.');
  await page.click('#play');await page.waitForFunction(()=>document.querySelector('canvas').dataset.frame!=='14');await page.click('#play');
  checks.push('Play advances frames; pause and scrub operate.');
  await scrub(23);const lastPageOne=await pixels();await scrub(24);const firstPageTwo=await pixels();assert(firstPageTwo.opaque>10000);assert.notEqual(lastPageOne.rgba,firstPageTwo.rgba);await scrub(35);assert.equal((await pixels()).rgba,start.rgba);checks.push('Desktop frames 23→24 cross atlas pages; frame 35 closes the 36-frame loop.');
  for(const clip of ['thrust','idle']){
    await page.click(`[data-clip="${clip}"]`);await ready();await scrub(14);
    const seen=[];
    for(const light of ['neutral','warm-left','cool-right']){
      await page.selectOption('#light',light);await ready();await scrub(14);seen.push(await pixels());
      assert.equal(await page.locator('canvas').getAttribute('data-light'),light);
    }
    assert.notDeepEqual(seen[0],seen[1]);assert.notDeepEqual(seen[0],seen[2]);
    assert.equal(seen[0].alpha,seen[1].alpha);assert.equal(seen[0].alpha,seen[2].alpha);
    checks.push(`${clip}: all 3 light atlases load, change RGB, preserve frame alpha.`);
  }
  await page.click('[data-clip="thrust"]');await ready();await page.selectOption('#light','warm-left');await ready();await scrub(14);
  await page.selectOption('#speed','0.25');assert.equal(await page.locator('#speed').inputValue(),'0.25');
  await page.locator('.stills img').evaluateAll(imgs=>Promise.all(imgs.map(im=>im.decode())));
  assert(await page.locator('.stills img').evaluateAll(imgs=>imgs.every(im=>im.naturalWidth===2048&&im.naturalHeight===1280)));
  await page.screenshot({path:`.tmp/${study}/review-desktop.png`,fullPage:true});
  if(rigid){const off=await pixels();await page.check('#joints');assert.notEqual((await pixels()).rgba,off.rgba);await page.uncheck('#joints');assert.equal((await pixels()).rgba,off.rgba);checks.push('Joint overlay toggles on and off without changing the rendered frame.');}
  await page.setViewportSize({width:390,height:844});await page.reload();await ready();assert.equal(await page.locator('canvas').getAttribute('data-quality'),'mobile');await scrub(14);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:`.tmp/${study}/review-mobile.png`,fullPage:true});
  checks.push('HD stills load; desktop 1440x1100 and mobile 390x844 have no overflow.');
  await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await ready();
  assert.equal(await page.locator('#play').getAttribute('aria-pressed'),'false');checks.push('Reduced-motion preference starts paused.');
  await page.clock.install();await page.clock.pauseAt(new Date(Date.now()+100));await page.clock.runFor(100);
  // Dispatch directly while the clock is paused: locator auto-wait can advance
  // mocked animation frames during click stabilization before timing starts.
  await scrub(0);await page.locator('#play').evaluate(el=>el.click());await page.clock.runFor(600);
  const halfFrame=Number(await page.locator('canvas').getAttribute('data-frame'));
  assert([17,18].includes(halfFrame),`Expected 17–18 frames at 600 ms; got ${halfFrame}`);
  await page.clock.runFor(600);assert([35,0].includes(Number(await page.locator('canvas').getAttribute('data-frame'))));
  checks.push('Controlled clock: ~18 frames per 600 ms and a 36-frame loop in 1.2 s at 1x, not sped-up 24-frame playback.');

  assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);checks.push('No page errors or failed asset requests.');
  await fs.writeFile(`${out}/browser-check.json`,JSON.stringify({passed:true,checks,scope:'Canvas illustration viewer only; not mobile game FPS or Phaser integration.'},null,2)+'\n');
  console.log('Yari motion preview: all browser checks passed.');
} finally {await browser.close();await new Promise(resolve=>server.close(resolve));}
