import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const root=new URL(process.env.MODEL_TEST_ROOT||'../public/models/',import.meta.url);
for(const name of ['yukimura','ieyasu'])test(`${name}: continuous wrists use weighted forearm, wrist and articulated finger bones`,()=>{
 const raw=readFileSync(new URL(`${name}.glb`,root)),size=raw.readUInt32LE(12),g=JSON.parse(raw.toString('utf8',20,20+size)),bin=raw.subarray(28+size),skin=g.skins[0];
 const names=skin.joints.map(j=>g.nodes[j].name);
 assert.equal(names.length,92);assert.equal(new Set(names).size,92);
 for(const side of ['L','R'])for(const part of ['clavicle','shoulder01','upperarm01','upperarm02','lowerarm01','lowerarm02','wrist'])assert.ok(names.includes(`body.${part}.${side}`));
 const read=i=>{const a=g.accessors[i],v=g.bufferViews[a.bufferView],n={VEC3:3,VEC4:4,SCALAR:1}[a.type],bytes={5121:1,5123:2,5126:4}[a.componentType],method={5121:'readUInt8',5123:'readUInt16LE',5126:'readFloatLE'}[a.componentType];return Array.from({length:a.count},(_,r)=>Array.from({length:n},(_,c)=>bin[method]((v.byteOffset||0)+(a.byteOffset||0)+r*(v.byteStride||n*bytes)+c*bytes)))};
 const arms=g.meshes.flatMap(m=>m.primitives).find(p=>g.materials[p.material].name==='commander deerskin and cloth');assert.ok(arms,'anatomical arm section is missing');
 const ids=read(arms.attributes.JOINTS_0),weights=read(arms.attributes.WEIGHTS_0);const used=new Set(),bridges={L:0,R:0};
 for(let i=0;i<ids.length;i++){
  const influences=ids[i].flatMap((j,k)=>weights[i][k]>.015?[names[j]]:[]);influences.forEach(n=>used.add(n));
  assert.ok(weights[i].every(w=>w>=0&&w<=1));assert.ok(Math.abs(weights[i].reduce((a,b)=>a+b,0)-1)<.001);
  for(const side of ['L','R'])if(influences.some(n=>n.startsWith('body.lowerarm')&&n.endsWith(side))&&influences.includes('body.wrist.'+side))bridges[side]++;
 }
 for(const side of ['L','R']){
  assert.ok(bridges[side]>10,`${side}: wrist has no continuous weight transition`);
  for(let finger=1;finger<=5;finger++)for(let joint=1;joint<=3;joint++)assert.ok(used.has(`body.finger${finger}-${joint}.${side}`),'finger joint has no skinned vertices');
 }
 if(name==='ieyasu'){
  const fall=g.animations.find(a=>a.name==='fall');
  for(const side of ['L','R']){
   const j=g.nodes.findIndex(n=>n.name===`body.finger2-2.${side}`),channel=fall.channels.find(c=>c.target.node===j&&c.target.path==='rotation');assert.ok(channel);
   const data=read(fall.samplers[channel.sampler].output),first=data[0];assert.ok(data.some(q=>Math.abs(q.reduce((sum,v,i)=>sum+v*first[i],0))<.995),'fall does not loosen the fingers');
  }
 }
 console.log(name,{wristBlendVertices:bridges,weightedBones:used.size});
});
