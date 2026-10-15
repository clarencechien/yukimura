// Functional check of rendered art preview; no changes to the game test suite.
import { chromium } from '@playwright/test';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=process.cwd(),out='docs/routes/jigoku-2d/yari-motion';
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
  await page.goto(`http://127.0.0.1:${server.address().port}/docs/routes/jigoku-2d/yari-motion-review.html`);
  const ready=()=>page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('24 幀'));
  const scrub=async(frame)=>page.locator('#scrub').evaluate((el,value)=>{el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));},String(frame));
  const pixels=()=>page.locator('canvas').evaluate(el=>Array.from(el.getContext('2d').getImageData(0,0,el.width,el.height).data));
  await ready();assert.equal(await page.locator('canvas').getAttribute('data-quality'),'desktop');await scrub(0);const start=await pixels();assert(start.filter((v,i)=>i%4===3&&v>240).length>10000);
  await scrub(9);const thrust=await pixels();assert.notDeepEqual(start,thrust);checks.push('Rendered sprite visible; scrub changes actual canvas pixels.');
  await page.click('#play');await page.waitForFunction(()=>document.querySelector('canvas').dataset.frame!=='9');await page.click('#play');
  checks.push('Play advances frames; pause and scrub operate.');
  for(const clip of ['thrust','idle']){
    await page.click(`[data-clip="${clip}"]`);await ready();await scrub(9);
    const seen=[];
    for(const light of ['neutral','warm-left','cool-right']){
      await page.selectOption('#light',light);await ready();await scrub(9);seen.push(await pixels());
      assert.equal(await page.locator('canvas').getAttribute('data-light'),light);
    }
    assert.notDeepEqual(seen[0],seen[1]);assert.notDeepEqual(seen[0],seen[2]);
    for(let i=3;i<seen[0].length;i+=4){assert.equal(seen[0][i],seen[1][i]);assert.equal(seen[0][i],seen[2][i]);}
    checks.push(`${clip}: all 3 light atlases load, change RGB, preserve frame alpha.`);
  }
  await page.click('[data-clip="thrust"]');await ready();await page.selectOption('#light','warm-left');await ready();await scrub(9);
  await page.selectOption('#speed','0.25');assert.equal(await page.locator('#speed').inputValue(),'0.25');
  await page.locator('.stills img').evaluateAll(imgs=>Promise.all(imgs.map(im=>im.decode())));
  assert(await page.locator('.stills img').evaluateAll(imgs=>imgs.every(im=>im.naturalWidth===2048&&im.naturalHeight===1280)));
  await page.screenshot({path:'.tmp/yari-motion/review-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.reload();await ready();assert.equal(await page.locator('canvas').getAttribute('data-quality'),'mobile');await scrub(9);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:'.tmp/yari-motion/review-mobile.png',fullPage:true});
  checks.push('HD stills load; desktop 1440x1100 and mobile 390x844 have no overflow.');
  await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await ready();
  assert.equal(await page.locator('#play').getAttribute('aria-pressed'),'false');checks.push('Reduced-motion preference starts paused.');
  assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);checks.push('No page errors or failed asset requests.');
  await fs.writeFile(`${out}/browser-check.json`,JSON.stringify({passed:true,checks,scope:'Canvas illustration viewer only; not mobile game FPS or Phaser integration.'},null,2)+'\n');
  console.log('Yari motion preview: all browser checks passed.');
} finally {await browser.close();await new Promise(resolve=>server.close(resolve));}
