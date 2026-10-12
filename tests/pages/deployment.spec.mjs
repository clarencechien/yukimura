import {test,expect} from '@playwright/test';
test('Pages subpath loads background, four models and shared textures, and starts combat',async({page})=>{
 const errors=[],assets=new Set();
 page.on('pageerror',e=>errors.push(e.message));
 page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);assets.add(new URL(r.url()).pathname)});
 await page.goto('http://127.0.0.1:4174/yukimura/');
 await expect(page.locator('#start')).toBeEnabled({timeout:60000});
 expect(assets.has('/yukimura/art/concept.png')).toBe(true);
 for(const name of ['yukimura','ashigaru','tokugawa','ieyasu'])expect(assets.has(`/yukimura/models/${name}.glb`)).toBe(true);
 expect([...assets].filter(p=>p.startsWith('/yukimura/models/shared/')&&p.endsWith('.png'))).toHaveLength(3);
 expect(assets.has('/yukimura/models/crowd-animation.json')).toBe(true);
 expect([...assets].filter(p=>p.startsWith('/yukimura/models/shared/')&&p.endsWith('.bin'))).toHaveLength(1);
 await page.click('#start');await page.keyboard.down('w');await page.waitForTimeout(1500);await page.keyboard.up('w');
 const status=await page.evaluate(()=>window.__sanada);
 expect(status.state).toBe('playing');expect(status.position.z).toBeGreaterThan(.2);expect(status.allies).toBe(10);
 expect(status.crowd.instances).toBeGreaterThanOrEqual(50);expect(status.crowd.allies).toHaveLength(10);expect(errors).toEqual([]);
});
