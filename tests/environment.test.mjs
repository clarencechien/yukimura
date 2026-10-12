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
