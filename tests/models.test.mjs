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
  assert.ok(g.buffers.every(b=>!b.uri));const commander=['yukimura','ieyasu'].includes(name);assert.equal(g.images.length,commander?5:3);assert.equal(g.materials.length,commander?4:1);
  const mat=g.materials[0];assert.ok(mat.pbrMetallicRoughness.baseColorTexture);assert.ok(mat.pbrMetallicRoughness.metallicRoughnessTexture);assert.ok(mat.normalTexture);
  for(const [imageIndex,image] of g.images.entries()){
   assert.match(image.uri,/^shared\/[a-f0-9]{16}\.png$/);
   const png=readFileSync(new URL(image.uri,root));assert.equal(png.toString('ascii',1,4),'PNG');
   assert.equal(createHash('sha256').update(png).digest('hex').slice(0,16),image.uri.slice(7,23),'texture content does not match its cache key');
   assert.ok((imageIndex>=3?[512]:name==='yukimura'?[2048]:[512,1024]).includes(png.readUInt32BE(16)));shared.add(image.uri);
  }
  for(const view of g.bufferViews)assert.ok((view.byteOffset||0)+view.byteLength<=g.buffers[0].byteLength,'repacked buffer view out of bounds');
  const primitives=g.meshes.flatMap(m=>m.primitives);assert.equal(primitives.length,commander?4:1);const p=primitives[0];assert.ok('COLOR_0' in p.attributes);assert.ok('TEXCOORD_0' in p.attributes);assert.ok(!('TEXCOORD_1' in p.attributes),'joined meshes split the painted atlas across UV sets');
  const color=g.accessors[p.attributes.COLOR_0],colorView=g.bufferViews[color.bufferView];
  assert.ok([5121,5123,5126].includes(color.componentType));const step=color.componentType===5126?4:color.componentType===5123?2:1;const offset=(colorView.byteOffset||0)+(color.byteOffset||0);const rgba=Array.from({length:color.count*4},(_,i)=>step===4?binary.readFloatLE(offset+i*4):step===2?binary.readUInt16LE(offset+i*2):binary.readUInt8(offset+i));
  if(!['yukimura','ieyasu'].includes(name))assert.ok(rgba.some((v,i)=>i%4===0&&v!==rgba[i+1]),'team palette was replaced by white');
  else assert.ok(rgba.some((v,i)=>i%4===0&&v<(step===4?1:step===2?65535:255)),'hero assembly occlusion multiplier is missing');
  const pos=g.accessors[p.attributes.POSITION];assert.ok(Math.abs(pos.min[1])<.025);assert.ok(pos.max[1]>1.8&&pos.max[1]<3.5);
  // One detailed hero; the crowd keeps its original per-instance budget.
  // Dedicated, non-overlapping hero UV islands split vertices at their seams;
  // Continuous anatomical hands and fitted plates keep each commander below
  // 80k triangles including surface-fitted cords; 6 MB per commander.
  const triangles=primitives.reduce((sum,p)=>sum+g.accessors[p.indices].count/3,0);assert.ok(triangles>1000&&triangles<=(['yukimura','ieyasu'].includes(name)?80000:3800));assert.ok(bytes.length<(['yukimura','ieyasu'].includes(name)?6000000:550000));
 });
}
test('commanders have dedicated bakes; foot soldiers reuse three atlas files',()=>{
 assert.equal(shared.size,11);
 const hero=new Set(readGLB('yukimura').gltf.images.slice(0,3).map(i=>i.uri));
 const army=new Set(['ashigaru','tokugawa'].flatMap(n=>readGLB(n).gltf.images.map(i=>i.uri)));
 const boss=new Set(readGLB('ieyasu').gltf.images.slice(0,3).map(i=>i.uri));assert.equal(boss.size,3);assert.ok([...boss].every(uri=>!hero.has(uri)&&!army.has(uri)));
 assert.deepEqual(readGLB('yukimura').gltf.images.slice(3).map(i=>i.uri),readGLB('ieyasu').gltf.images.slice(3).map(i=>i.uri),'commander fittings must reuse the same normal and ORM files');
 assert.equal(hero.size,3);assert.equal(army.size,3);assert.ok([...hero].every(uri=>!army.has(uri)));
 const report=JSON.parse(readFileSync(new URL('hero-bake.json',root)));
 assert.ok(report.high_triangles>report.low_triangles*8);assert.ok(report.high_triangles>200000);
 assert.equal(report.runtime_triangles??report.low_triangles,JSON.parse(readFileSync(new URL('manifest.json',root))).variants.yukimura.triangles);
 assert.deepEqual(report.passes,['diffuse_color','tangent_normal','roughness_metallic','ambient_occlusion']);
 assert.equal(report.resolution,2048);assert.ok(report.max_sculpt_relief_m>.002);
 const {gltf:g,binary}=readGLB('yukimura'),uv=g.accessors[g.meshes[0].primitives[0].attributes.TEXCOORD_0],view=g.bufferViews[uv.bufferView];
 for(let i=0;i<uv.count*2;i++){const v=binary.readFloatLE((view.byteOffset||0)+(uv.byteOffset||0)+i*4);assert.ok(v>=0&&v<=1,'hero bake UV lies outside its atlas');}
});
for(const name of ['yukimura','ashigaru','tokugawa','ieyasu'])test(`${name}: valid skin weights and authored animation clips`,()=>{
 const {gltf:g,binary}=readGLB(name);const p=g.meshes[0].primitives[0];assert.equal(g.skins.length,1);assert.equal(g.skins[0].joints.length,['yukimura','ieyasu'].includes(name)?92:18);assert.ok('JOINTS_0' in p.attributes);assert.ok('WEIGHTS_0' in p.attributes);
 function values(index){const a=g.accessors[index],v=g.bufferViews[a.bufferView];assert.equal(a.componentType,5126);const n={SCALAR:1,VEC3:3,VEC4:4}[a.type];const offset=(v.byteOffset||0)+(a.byteOffset||0);return Array.from({length:a.count*n},(_,i)=>binary.readFloatLE(offset+i*4));}
 const weights=g.meshes.flatMap(m=>m.primitives).flatMap(p=>values(p.attributes.WEIGHTS_0));for(let i=0;i<weights.length;i+=4){const sum=weights.slice(i,i+4).reduce((a,b)=>a+b,0);assert.ok(Math.abs(sum-1)<.001,'unbound vertex');}
 assert.deepEqual(g.animations.map(a=>a.name).sort(),name==='yukimura'?['dash','hurt','idle','reverse','run','slash','spin','thrust']:['fall','fall_back','hurt','idle','run','thrust']);
 for(const clip of g.animations){
  assert.ok(clip.channels.length>10);
  const changing=clip.samplers.some(s=>{const data=values(s.output),n={VEC3:3,VEC4:4}[g.accessors[s.output].type];return data.some((v,i)=>Math.abs(v-data[i%n])>.001)});
  assert.ok(changing,`${clip.name} is a frozen pose`);
 }
});

test('Ieyasu reuses hero armour with an independent commander bake',()=>{const m=JSON.parse(readFileSync(new URL('manifest.json',root))),b=JSON.parse(readFileSync(new URL('ieyasu-bake.json',root)));assert.equal(b.runtime_triangles??b.low_triangles,m.variants.ieyasu.triangles);assert.ok(b.high_triangles>b.low_triangles*8);assert.equal(b.resolution,1024);assert.ok(m.variants.ieyasu.source_parts>350);});
