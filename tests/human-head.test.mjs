import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const root=new URL('../public/models/',import.meta.url);
const normalMaps=[];
for(const kind of ['yukimura','ieyasu'])test(`${kind}: human head follows the battle skeleton with a blended neck and non-metal skin`,()=>{
 const bytes=readFileSync(new URL(kind+'.glb',root)),size=bytes.readUInt32LE(12);
 const g=JSON.parse(bytes.toString('utf8',20,20+size)),bin=bytes.subarray(28+size);
 const materialIndex=g.materials.findIndex(m=>m.name===`human skin / ${kind}`);assert.ok(materialIndex>=0);
 const mat=g.materials[materialIndex];assert.equal(mat.pbrMetallicRoughness.metallicFactor,0);
 assert.ok(mat.pbrMetallicRoughness.roughnessFactor>=.5);assert.ok(!mat.extensions?.KHR_materials_clearcoat);
 const normal=g.images[g.textures[mat.normalTexture.index].source].uri;normalMaps.push(normal);
 if(normalMaps.length===2)assert.equal(normalMaps[0],normalMaps[1],'the two commanders should reuse one skin normal map');
 const head=g.meshes.flatMap(m=>m.primitives).find(p=>p.material===materialIndex);assert.ok(head);
 assert.equal(g.skins.length,1);assert.equal(g.skins[0].joints.length,92);
 const names=g.skins[0].joints.map(j=>g.nodes[j].name);
 const read=index=>{
  const a=g.accessors[index],v=g.bufferViews[a.bufferView],n={VEC3:3,VEC4:4,SCALAR:1}[a.type];
  const step={5121:1,5123:2,5126:4}[a.componentType],method={5121:'readUInt8',5123:'readUInt16LE',5126:'readFloatLE'}[a.componentType];
  return Array.from({length:a.count},(_,r)=>Array.from({length:n},(_,c)=>bin[method]((v.byteOffset||0)+(a.byteOffset||0)+r*(v.byteStride||n*step)+c*step)));
 };
 const positions=read(head.attributes.POSITION),joints=read(head.attributes.JOINTS_0),weights=read(head.attributes.WEIGHTS_0);
 assert.ok(positions.length>1000&&positions.length<2500);
 let neckBlends=0,cranium=0;
 for(let i=0;i<positions.length;i++){
  assert.ok(positions[i].every(Number.isFinite));
  const used=joints[i].flatMap((j,k)=>weights[i][k]>.001?[names[j]]:[]);
  assert.ok(used.every(n=>['body.head','body.spine02'].includes(n)),'head attached to an unrelated limb');
  assert.ok(Math.abs(weights[i].reduce((a,b)=>a+b,0)-1)<.001);
  if(used.length===2)neckBlends++;
  // Jaw must remain rigid with the mask. The old blend reached the chin and
  // moved skin through the menpo during a strong slash/turn.
  if(positions[i][1]>1.74){assert.deepEqual(used,['body.head']);cranium++;}
 }
 assert.ok(neckBlends>4,'neck has no continuous transition into the torso');
 assert.ok(cranium>400,'cranium does not follow the helmet bone');
 assert.match(readFileSync(new URL('LICENSE-Rocketbox.txt',root),'utf8'),/Copyright \(c\) 2020 Microsoft/);
});
