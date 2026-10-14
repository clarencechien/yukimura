import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const root=new URL('../public/models/',import.meta.url);
test('shared crowd palette has bounded, finite, genuinely animated bone matrices',()=>{
 const manifest=JSON.parse(readFileSync(new URL('crowd-animation.json',root)));assert.equal(manifest.fps,60);
 assert.deepEqual(Object.keys(manifest.models).sort(),['ashigaru','ieyasu','tokugawa']);
 const unique=new Set();
 for(const [kind,p] of Object.entries(manifest.models)){
  const bytes=readFileSync(new URL(p.uri,root));unique.add(p.uri);
  assert.equal(p.source_sha256,createHash('sha256').update(readFileSync(new URL(kind+'.glb',root))).digest('hex'),'palette was not rebuilt for the installed model');
  assert.equal(createHash('sha256').update(bytes).digest('hex').slice(0,16),p.uri.slice(7,23));
  assert.equal(bytes.length,p.width*p.height*16);assert.equal(p.width,(p.joints+1)*4);assert.equal(p.joints,kind==='ieyasu'?92:18);assert.ok(bytes.length<(kind==='ieyasu'?2700000:550000));
  const values=Array.from({length:bytes.length/4},(_,i)=>bytes.readFloatLE(i*4));assert.ok(values.every(Number.isFinite));
  assert.deepEqual(Object.keys(p.clips).sort(),['fall','fall_back','hurt','idle','run','thrust']);
  const stride=p.width*4;
  for(const [name,clip] of Object.entries(p.clips)){
   assert.ok(clip.start>=0&&clip.end<p.height&&clip.end>clip.start);assert.ok(clip.duration>0);
   const duration={idle:1.6,run:.8,thrust:1,hurt:.6,fall:1.4,fall_back:1.4}[name];
   assert.ok(Math.abs(clip.duration-duration)<1e-5,`${kind} ${name}: asset export changed combat timing`);
   const middle=clip.start+Math.floor((clip.end-clip.start)*.35);
   assert.ok(values.slice(clip.start*stride,(clip.start+1)*stride).some((v,i)=>Math.abs(v-values[middle*stride+i])>.003),name+' palette is frozen');
  }
 }
 assert.equal(manifest.models.ashigaru.uri,manifest.models.tokugawa.uri,'foot soldiers share one palette');assert.equal(unique.size,2,'commander uses a sword grip palette');
});

test('baked death poses lower the soldier to the ground and keep limbs above it',()=>{
 const manifest=JSON.parse(readFileSync(new URL('crowd-animation.json',root))),p=manifest.models.tokugawa;
 const glb=readFileSync(new URL('tokugawa.glb',root)),length=glb.readUInt32LE(12),g=JSON.parse(glb.toString('utf8',20,20+length)),bin=glb.subarray(28+length),attrs=g.meshes[0].primitives[0].attributes;
 function accessor(id){const a=g.accessors[id],v=g.bufferViews[a.bufferView],components={VEC3:3,VEC4:4}[a.type],bytes={5121:1,5123:2,5126:4}[a.componentType];return Array.from({length:a.count},(_,i)=>Array.from({length:components},(_,j)=>{const offset=(v.byteOffset||0)+(a.byteOffset||0)+i*(v.byteStride||components*bytes)+j*bytes;return bytes===4?bin.readFloatLE(offset):bytes===2?bin.readUInt16LE(offset):bin.readUInt8(offset);}));}
 const positions=accessor(attrs.POSITION),weights=accessor(attrs.WEIGHTS_0),joints=accessor(attrs.JOINTS_0),palette=readFileSync(new URL(p.uri,root));
 function bounds(frame){let min=Infinity,max=-Infinity,sum=0;for(let i=0;i<positions.length;i++){let y=0;for(let k=0;k<4;k++){const w=weights[i][k];if(!w)continue;const o=(frame*p.width*4+joints[i][k]*16)*4;const m=j=>palette.readFloatLE(o+j*4);y+=w*(positions[i][0]*m(1)+positions[i][1]*m(5)+positions[i][2]*m(9)+m(13));}min=Math.min(min,y);max=Math.max(max,y);sum+=y;}return {min,max,average:sum/positions.length};}
 const standing=bounds(p.clips.idle.start);
 for(const name of ['fall','fall_back']){const pose=bounds(p.clips[name].end);assert.ok(pose.min>-.035,`${name}: body penetrates ground ${pose.min}`);assert.ok(pose.max<1.5,`${name}: body remains upright ${pose.max}`);assert.ok(pose.average<standing.average-.45,`${name}: no meaningful body collapse`);}
});
