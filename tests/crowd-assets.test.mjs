import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const root=new URL('../public/models/',import.meta.url);
test('shared crowd palette has bounded, finite, genuinely animated bone matrices',()=>{
 const manifest=JSON.parse(readFileSync(new URL('crowd-animation.json',root)));assert.equal(manifest.fps,60);
 assert.deepEqual(Object.keys(manifest.models).sort(),['ashigaru','ieyasu','tokugawa']);
 const unique=new Set();
 for(const p of Object.values(manifest.models)){
  const bytes=readFileSync(new URL(p.uri,root));unique.add(p.uri);
  assert.equal(createHash('sha256').update(bytes).digest('hex').slice(0,16),p.uri.slice(7,23));
  assert.equal(bytes.length,p.width*p.height*16);assert.equal(p.width,(p.joints+1)*4);assert.equal(p.joints,18);assert.ok(bytes.length<450000);
  const values=Array.from({length:bytes.length/4},(_,i)=>bytes.readFloatLE(i*4));assert.ok(values.every(Number.isFinite));
  assert.deepEqual(Object.keys(p.clips).sort(),['fall','hurt','idle','run','thrust']);
  const stride=p.width*4;
  for(const [name,clip] of Object.entries(p.clips)){
   assert.ok(clip.start>=0&&clip.end<p.height&&clip.end>clip.start);assert.ok(clip.duration>0);
   const middle=clip.start+Math.floor((clip.end-clip.start)*.35);
   assert.ok(values.slice(clip.start*stride,(clip.start+1)*stride).some((v,i)=>Math.abs(v-values[middle*stride+i])>.003),name+' palette is frozen');
  }
 }
 assert.equal(unique.size,1,'the army should share one animation texture');
});
