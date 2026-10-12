import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';

test('winter surface files match the manifest and keep the shared mobile texture budget',()=>{
 const root=new URL('../public/environment/',import.meta.url),manifest=JSON.parse(readFileSync(new URL('manifest.json',root)));
 let total=0;
 for(const [name,entry] of Object.entries(manifest.files)){
  const png=readFileSync(new URL(name,root));total+=png.length;
  assert.equal(png.toString('ascii',1,4),'PNG');assert.equal(png.length,entry.bytes);
  assert.equal(png.readUInt32BE(16),entry.width);assert.equal(png.readUInt32BE(20),entry.height);
  assert.equal(createHash('sha256').update(png).digest('hex'),entry.sha256,name);
  assert.ok(entry.width<=2048&&entry.height<=2048);
 }
 assert.equal(total,manifest.bytes);assert.ok(total<9_500_000);
 const detail=readFileSync(new URL('ground-detail.png',root));
 assert.equal(detail.readUInt32BE(16),512);assert.equal(detail.readUInt32BE(20),512);
 assert.equal(detail[25],6,'detail normal X lives in alpha: PNG must retain RGBA');
});

test('commander lacquer masks match their baked surface source and stay below 120 KB',()=>{
 const root=new URL('../public/look/',import.meta.url),manifest=JSON.parse(readFileSync(new URL('manifest.json',root)));
 let total=0;
 for(const [kind,entry] of Object.entries(manifest)){
  const png=readFileSync(new URL(entry.uri,root)),source=readFileSync(new URL(`../public/models/${entry.source}`,import.meta.url));
  assert.equal(createHash('sha256').update(source).digest('hex'),entry.source_sha256,`${kind}: regenerate coat mask after changing the bake`);
  assert.equal(createHash('sha256').update(png).digest('hex'),entry.sha256);
  assert.equal(png.length,entry.bytes);assert.equal(png.readUInt32BE(16),entry.size);assert.equal(png.readUInt32BE(20),entry.size);
  assert.ok(entry.size<=512);total+=png.length;
 }
 assert.deepEqual(Object.keys(manifest).sort(),['ieyasu','yukimura']);assert.ok(total<120_000);
});
