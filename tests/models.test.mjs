import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const root=new URL('../public/models/',import.meta.url);
function readGLB(name){const bytes=readFileSync(new URL(`${name}.glb`,root));assert.equal(bytes.toString('ascii',0,4),'glTF');assert.equal(bytes.readUInt32LE(4),2);assert.equal(bytes.readUInt32LE(8),bytes.length);const size=bytes.readUInt32LE(12);return {bytes,gltf:JSON.parse(bytes.toString('utf8',20,20+size)),binary:bytes.subarray(28+size)};}
const shared=new Set();
for(const name of ['yukimura','ashigaru','tokugawa','ieyasu']){
 test(`${name}: valid geometry, shared painted textures and mobile asset budget`,()=>{
  const {bytes,gltf:g,binary}=readGLB(name);
  assert.ok(g.buffers.every(b=>!b.uri));assert.equal(g.images.length,3);assert.equal(g.materials.length,1);
  const mat=g.materials[0];assert.ok(mat.pbrMetallicRoughness.baseColorTexture);assert.ok(mat.pbrMetallicRoughness.metallicRoughnessTexture);assert.ok(mat.normalTexture);
  for(const image of g.images){
   assert.match(image.uri,/^shared\/[a-f0-9]{16}\.png$/);
   const png=readFileSync(new URL(image.uri,root));assert.equal(png.toString('ascii',1,4),'PNG');
   assert.equal(createHash('sha256').update(png).digest('hex').slice(0,16),image.uri.slice(7,23),'texture content does not match its cache key');
   assert.ok([512,1024].includes(png.readUInt32BE(16)));shared.add(image.uri);
  }
  for(const view of g.bufferViews)assert.ok((view.byteOffset||0)+view.byteLength<=g.buffers[0].byteLength,'repacked buffer view out of bounds');
  const primitives=g.meshes.flatMap(m=>m.primitives);assert.equal(primitives.length,1);const p=primitives[0];assert.ok('COLOR_0' in p.attributes);assert.ok('TEXCOORD_0' in p.attributes);assert.ok(!('TEXCOORD_1' in p.attributes),'joined meshes split the painted atlas across UV sets');
  const color=g.accessors[p.attributes.COLOR_0],colorView=g.bufferViews[color.bufferView];
  assert.ok([5121,5123].includes(color.componentType));const step=color.componentType===5123?2:1;const offset=(colorView.byteOffset||0)+(color.byteOffset||0);const rgba=Array.from({length:color.count*4},(_,i)=>step===2?binary.readUInt16LE(offset+i*2):binary.readUInt8(offset+i));
  assert.ok(rgba.some((v,i)=>i%4===0&&v!==rgba[i+1]),'team palette was replaced by white');
  const pos=g.accessors[p.attributes.POSITION];assert.ok(Math.abs(pos.min[1])<.025);assert.ok(pos.max[1]>1.8&&pos.max[1]<3.5);
  const triangles=g.accessors[p.indices].count/3;assert.ok(triangles>1000&&triangles<=(name==='yukimura'?12000:name==='ieyasu'?10000:3200));assert.ok(bytes.length<(name==='yukimura'?1500000:name==='ieyasu'?900000:350000));
 });
}
test('all variants reuse exactly three atlas files',()=>assert.equal(shared.size,3));
test('hero skin has valid weights and six non-static bone animation clips',()=>{
 const {gltf:g,binary}=readGLB('yukimura');const p=g.meshes[0].primitives[0];assert.equal(g.skins.length,1);assert.equal(g.skins[0].joints.length,14);assert.ok('JOINTS_0' in p.attributes);assert.ok('WEIGHTS_0' in p.attributes);
 function values(index){const a=g.accessors[index],v=g.bufferViews[a.bufferView];assert.equal(a.componentType,5126);const n={SCALAR:1,VEC3:3,VEC4:4}[a.type];const offset=(v.byteOffset||0)+(a.byteOffset||0);return Array.from({length:a.count*n},(_,i)=>binary.readFloatLE(offset+i*4));}
 const weights=values(p.attributes.WEIGHTS_0);for(let i=0;i<weights.length;i+=4){const sum=weights.slice(i,i+4).reduce((a,b)=>a+b,0);assert.ok(Math.abs(sum-1)<.001,'unbound vertex');}
 assert.deepEqual(g.animations.map(a=>a.name).sort(),['idle','reverse','run','slash','spin','thrust']);
 for(const clip of g.animations){
  assert.ok(clip.channels.length>10);
  const changing=clip.samplers.some(s=>{const data=values(s.output),n={VEC3:3,VEC4:4}[g.accessors[s.output].type];return data.some((v,i)=>Math.abs(v-data[i%n])>.001)});
  assert.ok(changing,`${clip.name} is a frozen pose`);
 }
});
