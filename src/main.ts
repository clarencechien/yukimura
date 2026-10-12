import './style.css';
import { HeroMotion } from './hero-motion';
import { illustrationPass } from './illustration';
import { battlefield } from './battlefield';
import { winterReflections } from './lighting';
import { ShadowGenerator } from '@babylonjs/core/Lights/Shadows/shadowGenerator';
import '@babylonjs/core/Lights/Shadows/shadowGeneratorSceneComponent';
import { PointLight } from '@babylonjs/core/Lights/pointLight';
import { DynamicTexture } from '@babylonjs/core/Materials/Textures/dynamicTexture';
import { Engine } from '@babylonjs/core/Engines/engine';
import { Scene } from '@babylonjs/core/scene';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { Color3, Color4 } from '@babylonjs/core/Maths/math.color';
import { FreeCamera } from '@babylonjs/core/Cameras/freeCamera';
import { HemisphericLight } from '@babylonjs/core/Lights/hemisphericLight';
import { DirectionalLight } from '@babylonjs/core/Lights/directionalLight';
import { MeshBuilder } from '@babylonjs/core/Meshes/meshBuilder';
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial';
import { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import { SceneLoader } from '@babylonjs/core/Loading/sceneLoader';
import { Mesh } from '@babylonjs/core/Meshes/mesh';
import { AbstractMesh } from '@babylonjs/core/Meshes/abstractMesh';
import '@babylonjs/core/Meshes/instancedMesh';
import '@babylonjs/loaders/glTF/glTFFileLoader';
import '@babylonjs/loaders/glTF/2.0/glTFLoader';
import { tuning, inRange, applyHit, nextCycle } from './rules.mjs';
const $ = <T extends HTMLElement = HTMLElement>(id:string) => document.getElementById(id) as T;
const canvas=$<HTMLCanvasElement>('battle');
const engine=new Engine(canvas,true,{stencil:true, preserveDrawingBuffer:true});
const softwareRenderer=/swiftshader|llvmpipe/i.test(engine.getGlInfo().renderer);
engine.setHardwareScalingLevel(softwareRenderer?1.35:(matchMedia('(pointer:coarse)').matches?1.4:1));
const scene=new Scene(engine);scene.clearColor=new Color4(.20,.28,.34,1);scene.fogMode=Scene.FOGMODE_EXP2;scene.fogDensity=.016;scene.fogColor=new Color3(.33,.38,.40);
const camera=new FreeCamera('battle-camera',new Vector3(16,27,-22),scene);camera.fov=.74;camera.minZ=.1;camera.maxZ=240;
illustrationPass(scene,camera);
const skyLight=new HemisphericLight('winter-sky',new Vector3(.3,1,-.2),scene);skyLight.intensity=.63;skyLight.diffuse=new Color3(.70,.82,.95);skyLight.groundColor=new Color3(.24,.29,.34);
const sun=new DirectionalLight('winter-sun',new Vector3(-.7,-1,.4),scene);sun.intensity=1.25;sun.diffuse=new Color3(1,.85,.67);
winterReflections(scene);
sun.shadowMinZ=1;sun.shadowMaxZ=95;sun.orthoLeft=-25;sun.orthoRight=25;sun.orthoTop=30;sun.orthoBottom=-30;sun.autoUpdateExtends=false;
const shadows=new ShadowGenerator(matchMedia('(pointer:coarse)').matches?512:1024,sun);shadows.usePoissonSampling=true;shadows.bias=.001;shadows.normalBias=.025;shadows.darkness=.23;
let shadowClock=0;
function material(name:string,hex:string,glow=false){const m=new StandardMaterial(name,scene);m.diffuseColor=Color3.FromHexString(hex);m.specularColor=Color3.Black();if(glow)m.emissiveColor=m.diffuseColor.scale(.65);return m;}
const snow=material('warm snow','#a8b6c0'), dirt=material('mud','#75695f'), wood=material('palisade','#443b37'), dark=material('roof','#243540'), stone=material('stone','#6c7e83'), paper=material('plaster','#d0c8ac'), crimson=material('crimson','#79242c'), gold=material('gold','#918166'), slashMat=material('slash','#ffd29b',true), redFx=material('musou','#fa4c4b',true);
function box(name:string,x:number,y:number,z:number,w:number,h:number,d:number,m:StandardMaterial){const o=MeshBuilder.CreateBox(name,{width:w,height:h,depth:d},scene);o.position.set(x,y,z);o.material=m;return o;}
function cylinder(name:string,x:number,y:number,z:number,r:number,h:number,m:StandardMaterial,top=r){const o=MeshBuilder.CreateCylinder(name,{diameter:r*2,diameterTop:top*2,height:h,tessellation:6},scene);o.position.set(x,y,z);o.material=m;return o;}
// Shared, generated surface grain: brushlike snow specks and dark timber fibers.
function surfaceGrain(name:string,base:string,mark:string,woodGrain=false){
 const tex=new DynamicTexture(name,{width:128,height:128},scene,false);const ctx=tex.getContext();ctx.fillStyle=base;ctx.fillRect(0,0,128,128);
 let seed=7;const rand=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
 for(let i=0;i<1000;i++){ctx.globalAlpha=.06+rand()*.14;ctx.fillStyle=mark;ctx.fillRect(rand()*128,rand()*128,woodGrain?1:1+rand()*5,woodGrain?4+rand()*28:1+rand()*2);}ctx.globalAlpha=1;tex.update();return tex;
}
const snowGrain=surfaceGrain('snow grain','#d6dce0','#5b6b78');snowGrain.uScale=26;snowGrain.vScale=40;snow.diffuseTexture=snowGrain;
wood.diffuseTexture=surfaceGrain('wood fibers','#8f8074','#151d25',true);const mudGrain=surfaceGrain('mud grain','#b2aba2','#303842');mudGrain.uScale=3;mudGrain.vScale=23;dirt.diffuseTexture=mudGrain;
const animateBattlefield=battlefield(scene,{snow,dirt,wood,dark,stone,crimson,gold});
// Fortified departure point, layered castle and distant mountains.
for(const x of [-1,1]){
 box('earthen rampart',x*22,1,-13,25,2.5,7,stone);
 for(let i=0;i<17;i++){const px=x*(10+i*1.35);cylinder('Sanada Maru palisade',px,2.65,-12,.16,3,wood,.06);}
 for(let i=0;i<10;i++){
  const z=i*16+4;const px=x*(18+(i%3)*3);
  box('timber barricade',px,1,z,5,.15,.25,wood);
  for(let j=0;j<5;j++)cylinder('pointed stakes',px-2+j,1,z,.12,2.5,wood,.015);
 }

}
for(let t=0;t<5;t++){
 const size=18-t*2.8,y=3+t*3.4;
 box('Osaka castle',-26,y,64,size,3,size*.8,paper);
 const roof=MeshBuilder.CreateCylinder('hip roof',{diameterTop:(size-4)*1.4,diameterBottom:(size+3)*1.4,height:1.7,tessellation:4},scene);roof.rotation.y=Math.PI/4;roof.position.set(-26,y+2,64);roof.material=dark;
 for(let q=-2;q<=2;q++)box('castle window',-26+q*size/6,y+.4,64-size*.4-.02,.5,.9,.03,dark);
}
for(let i=0;i<16;i++){const m=cylinder('mist mountain',-90+i*12,8+(i%4)*3,225+(i%2)*25,22,32+(i%4)*8,stone,0);m.rotation.y=i;}
// Command camp gates.
for(const z of [43,88,137]){
 for(const x of [-7.8,7.8])box('gate pillar',x,2.6,z,.65,5.2,.65,wood);
 box('gate crossbeam',0,5,z,17,.6,.8,wood);box('gate snow cap',0,5.35,z,18,.16,1,snow);
}
box('Ieyasu camp platform',0,.2,149,18,.4,12,wood);
box('command tent rear',0,3,155,17,6,.4,paper);
for(const x of [-8,8])box('command tent side',x,2.5,150,.4,5,10,paper);
box('black gold banner',0,3.5,154.7,4,4,.1,dark);
const crest=MeshBuilder.CreateDisc('Tokugawa crest',{radius:1.1,tessellation:24},scene);crest.position.set(0,3.6,154.6);crest.material=gold;
const flames:Mesh[]=[];
const ember=material('embers','#ff692c',true);const fireCore=material('fire core','#ffe1a3',true);
for(const z of [6,43,88,138])for(const x of [-8.6,8.6]){
 cylinder('brazier post',x,.8,z,.16,1.6,wood);cylinder('iron brazier',x,1.62,z,.38,.28,dark,.48);
 const flame=MeshBuilder.CreateSphere('fire',{diameter:1,segments:5},scene);flame.position.set(x,2.02,z);flame.scaling.set(.48,.83,.42);flame.material=ember;flames.push(flame);
 const core=MeshBuilder.CreateSphere('flame heart',{diameter:.3,segments:4},scene);core.position.set(x,1.89,z-.1);core.scaling.y=1.8;core.material=fireCore;
 // Four local lights rather than a point light per soldier.
 if(x<0){const glow=new PointLight('brazier glow',new Vector3(x,2.5,z),scene);glow.diffuse=new Color3(1,.3,.07);glow.intensity=2;glow.range=7;}
}
const snowflakes:AbstractMesh[]=[];
const snowSource=MeshBuilder.CreateSphere('snow template',{diameter:.07,segments:3},scene);snowSource.material=paper;snowSource.isVisible=false;
for(let i=0;i<100;i++){const s=snowSource.createInstance('snow');s.position.set(Math.random()*65-32,Math.random()*25,Math.random()*70-20);snowflakes.push(s);}
// Merge static scenery by material to reduce draw calls on mobile.
const groups=new Map<StandardMaterial,Mesh[]>();
for(const mesh of [...scene.meshes]){if(mesh instanceof Mesh&&mesh!==snowSource&&!snowflakes.includes(mesh)&&!flames.includes(mesh)&&!mesh.metadata?.keepDynamic&&mesh.material instanceof StandardMaterial){const list=groups.get(mesh.material)||[];list.push(mesh);groups.set(mesh.material,list);}}
for(const group of groups.values()){const merged=Mesh.MergeMeshes(group,true,true);if(merged){merged.freezeWorldMatrix();merged.isPickable=false;merged.receiveShadows=true;}}
// Ground silhouettes reinforce readable actor placement without costly dynamic shadows.
const shadowMat=material('contact shadow','#35444b');shadowMat.alpha=.28;
function shadow(parent:TransformNode,r=.5){const m=MeshBuilder.CreateDisc('contact',{radius:r,tessellation:12},scene);m.rotation.x=Math.PI/2;m.position.y=.035;m.material=shadowMat;m.parent=parent;return m;}
type Actor={root:TransformNode,hp:number,maxHp:number,cooldown:number,boss:boolean,dead:boolean,phase:number};
let hero:TransformNode;let heroMotion:HeroMotion;let heroMoving=false;const templates:Record<string,AbstractMesh>={};const allies:TransformNode[]=[];const foes:Actor[]=[];
let pendingVictory=false;
let state:'menu'|'playing'|'paused'|'won'|'lost'='menu';let cfg=tuning('normal',1);let hp=120,rage=35,kills=0,combo=0,comboTime=0,elapsed=0,spawnClock=0,attackCD=0,dashCD=0,dashTime=0,invuln=0,hitTimer=0,allyCD=0,formation='guard',bossSpawned=false,flash=0,shake=0;
let direction=new Vector3(0,0,1);let announceTime=0,lastStage=-1,unlocked=1;
try{unlocked=Math.max(1,Math.min(20,Number(localStorage.getItem('sanada-cycle'))||1));}catch{}
function fillCycles(){const select=$<HTMLSelectElement>('cycle');select.innerHTML='';for(let i=1;i<=Math.max(3,unlocked);i++){const o=document.createElement('option');o.value=String(i);o.textContent=`第 ${i} 周目${i===1?' · 初雪':''}`;select.append(o);}select.value=String(unlocked);}fillCycles();
const keys=new Set<string>();let joy={x:0,z:0},attackHeld=false;
function clearInput(){keys.clear();joy={x:0,z:0};attackHeld=false;$('stick').style.transform='';}
window.addEventListener('keydown',e=>{if(e.target instanceof HTMLSelectElement)return;const k=e.key.toLowerCase();if([' ','arrowup','arrowdown','arrowleft','arrowright'].includes(k))e.preventDefault();keys.add(k);if(e.repeat)return;if(k==='p'||k==='escape')pause();if(state!=='playing')return;if(k===' ')dash();if(k==='k')musou();if(k==='f')toggleFormation();});
window.addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));window.addEventListener('blur',()=>{clearInput();if(state==='playing')pause();});document.addEventListener('visibilitychange',()=>{if(document.hidden&&state==='playing')pause();});
function bind(id:string,fn:()=>void){$(id).addEventListener('click',fn);}
bind('readLore',()=>{$('lore').hidden=false;});bind('closeLore',()=>{$('lore').hidden=true;});
bind('start',start);bind('retry',()=>{if(state==='won'){$<HTMLSelectElement>('cycle').value=String(nextCycle(cfg.cycle));}start();});bind('back',menu);bind('returnMenu',menu);bind('pause',pause);bind('resume',pause);bind('dash',dash);bind('musou',musou);bind('formation',toggleFormation);
$('attack').addEventListener('pointerdown',e=>{e.preventDefault();attackHeld=true;$( 'attack').setPointerCapture(e.pointerId);attack();});for(const ev of ['pointerup','pointercancel','lostpointercapture'])$('attack').addEventListener(ev,()=>attackHeld=false);
const joystick=$('joystick');let joyId:number|null=null;
function moveJoy(e:PointerEvent){if(e.pointerId!==joyId)return;const r=joystick.getBoundingClientRect();let x=e.clientX-r.left-r.width/2,y=e.clientY-r.top-r.height/2;const len=Math.hypot(x,y);if(len>38){x*=38/len;y*=38/len;}joy={x:x/38,z:-y/38};$('stick').style.transform=`translate(${x}px,${y}px)`;}
joystick.addEventListener('pointerdown',e=>{joyId=e.pointerId;joystick.setPointerCapture(e.pointerId);moveJoy(e);});joystick.addEventListener('pointermove',moveJoy);for(const ev of ['pointerup','pointercancel','lostpointercapture'])joystick.addEventListener(ev,()=>{joyId=null;joy={x:0,z:0};$('stick').style.transform='';});
function announce(t:string){$('announcement').textContent=t;announceTime=2.6;}
function actor(kind:string,name:string,x:number,z:number,scale=1){const root=new TransformNode(name,scene);const model=templates[kind].instantiateHierarchy(root,{doNotInstantiate:false})!;model.name=name+'-model';model.setEnabled(true);model.scaling.scaleInPlace(scale);root.position.set(x,0,z);shadow(root,.48*scale);return root;}
function spawn(x:number,z:number,boss=false){const root=actor(boss?'ieyasu':'tokugawa',boss?'ieyasu':'enemy',x,z,boss?1.4:1);const life=boss?cfg.bossHealth:cfg.enemyHealth;const a={root,hp:life,maxHp:life,cooldown:Math.random(),boss,dead:false,phase:Math.random()*6.28};foes.push(a);if(boss){root.getChildMeshes().forEach(m=>{if(m.name.includes('contact'))return;m.outlineColor=new Color3(.7,.5,.2);});}}
function clearBattle(){for(const f of foes)f.root.dispose();foes.length=0;for(const a of allies)a.dispose();allies.length=0;for(const e of effects)e.mesh.dispose();effects.length=0;}
function start(){if(!hero)return;heroMotion.reset();heroMoving=false;clearInput();clearBattle();cfg=tuning($<HTMLSelectElement>('difficulty').value,Number($<HTMLSelectElement>('cycle').value));hp=cfg.health;rage=35;kills=0;combo=0;elapsed=0;spawnClock=0;attackCD=0;dashCD=0;dashTime=0;invuln=1;hitTimer=0;allyCD=0;bossSpawned=false;pendingVictory=false;formation='guard';lastStage=-1;hero.position.set(0,0,0);hero.rotation.y=0;direction.set(0,0,1);for(let i=0;i<10;i++)allies.push(actor('ashigaru','red-guard', (i%5-2)*1.35,-2-Math.floor(i/5)*1.8));for(let i=0;i<28;i++)spawn((Math.random()-.5)*30,7+Math.random()*28);state='playing';$('app').classList.add('playing');$('menu').hidden=true;$('result').hidden=true;$('pausePanel').hidden=true;$('hud').hidden=false;$('combat').hidden=false;$('loading').textContent='';announce('夏火已冷，冬雪重來。');updateHUD();}
function menu(){state='menu';$('bossHud').hidden=true;clearInput();$('app').classList.remove('playing');$('menu').hidden=false;$('result').hidden=true;$('pausePanel').hidden=true;$('hud').hidden=true;$('combat').hidden=true;$('announcement').textContent='';}
function pause(){if(state==='playing'){state='paused';clearInput();$('pausePanel').hidden=false;}else if(state==='paused'){state='playing';$('pausePanel').hidden=true;}}
function finish(won:boolean){state=won?'won':'lost';clearInput();$('combat').hidden=true;$('result').hidden=false;$('resultTitle').textContent=won?'本陣已破，此戰未終。':'此身暫歇，此志未滅。';$('resultText').textContent=won?`家康本陣突破。第 ${cfg.cycle} 周目・${kills} 擊破。修羅道記住了你的槍路。冬雪，將再度降臨。`:`此輪奮戰至此，共 ${kills} 擊破。雪還未停。整軍，再赴未竟之戰。`;$('retry').textContent=won?'再叩修羅 ↗':'重燃赤備 ↗';if(won){unlocked=Math.max(unlocked,nextCycle(cfg.cycle));try{localStorage.setItem('sanada-cycle',String(unlocked));}catch{}fillCycles();}}
const effects:{mesh:Mesh,life:number,max:number,velocity:Vector3}[]=[];
function ring(pos:Vector3,r:number,mat:StandardMaterial,duration=.3){const m=MeshBuilder.CreateTorus('slash wave',{diameter:r*2,thickness:.085,tessellation:40},scene);m.position.copyFrom(pos);m.position.y=.6;m.material=mat;effects.push({mesh:m,life:duration,max:duration,velocity:Vector3.Zero()});}
function sparks(pos:Vector3){for(let i=0;i<4;i++){const m=MeshBuilder.CreateBox('impact',{size:.11},scene);m.position.copyFrom(pos);m.position.y=.8;m.material=slashMat;effects.push({mesh:m,life:.35,max:.35,velocity:new Vector3((Math.random()-.5)*8,Math.random()*4,(Math.random()-.5)*8)});}}
function damageEnemy(f:Actor,dmg:number,push:number){if(f.dead)return;f.hp=applyHit(f.hp,dmg);const v=f.root.position.subtract(hero.position);v.y=0;v.normalize();f.root.position.addInPlace(v.scale(push));sparks(f.root.position);if(f.hp===0){f.dead=true;kills++;combo++;comboTime=3;rage=Math.min(100,rage+3);hp=Math.min(cfg.health,hp+(combo%8===0?4:0));f.root.dispose();if(f.boss)pendingVictory=true;}}
function attack(){if(state!=='playing'||attackCD>0)return;attackCD=.35;flash=.18;heroMotion.attack();hero.rotation.y=Math.atan2(direction.x,direction.z)+.35;ring(hero.position,2.7,slashMat);let hit=false;for(const f of foes){if(!f.dead&&inRange(hero.position,f.root.position,3.8)){damageEnemy(f,2,1.1);hit=true;}}if(hit)shake=.09;}
function dash(){if(state!=='playing'||dashCD>0)return;dashCD=1.35;dashTime=.25;invuln=.48;ring(hero.position,1.5,crimson,.25);}
function musou(){if(state!=='playing'||rage<100)return;rage=0;invuln=1.4;shake=.6;announce('奥義 · 六文赤蓮');for(let i=0;i<4;i++)ring(hero.position,3+i*2,redFx,.6+i*.1);for(const f of foes)if(!f.dead&&inRange(hero.position,f.root.position,12))damageEnemy(f,f.boss?24:100,4);}
function toggleFormation(){if(state!=='playing')return;formation=formation==='guard'?'charge':'guard';announce(formation==='guard'?'十勇士 · 結誓':'十勇士 · 破軍');}
function updateHUD(){const boss=foes.find(f=>f.boss&&!f.dead);$('bossHud').hidden=!boss||state==='menu';if(boss)$('bossHP').style.width=`${boss.hp/boss.maxHp*100}%`;$('hp').style.width=`${hp/cfg.health*100}%`;$('rage').style.width=`${rage}%`;$('kills').textContent=String(kills);$('combo').textContent=combo>1?`${combo} CHAIN`:'';$('progress').style.width=`${Math.min(100,hero.position.z/143*100)}%`;$('formationLabel').textContent=formation==='guard'?'十勇士・結誓':'十勇士・破軍';$('musou').classList.toggle('ready',rage>=100);$('dash').style.opacity=dashCD>0?'.45':'1';}
function update(dt:number){elapsed+=dt;attackCD-=dt;dashCD-=dt;dashTime-=dt;invuln-=dt;hitTimer-=dt;allyCD-=dt;flash-=dt;shake=Math.max(0,shake-dt);comboTime-=dt;if(comboTime<=0)combo=0;
 let x=joy.x+(keys.has('d')||keys.has('arrowright')?1:0)-(keys.has('a')||keys.has('arrowleft')?1:0),z=joy.z+(keys.has('w')||keys.has('arrowup')?1:0)-(keys.has('s')||keys.has('arrowdown')?1:0);
 let move=new Vector3(x,0,z);if(move.length()>1)move.normalize();
 // Screen-relative movement follows the fixed oblique camera.
 if(move.length()>.08){const mx=move.x,mz=move.z;move.set(mx*.894-mz*.447,0,mx*.447+mz*.894);direction.copyFrom(move).normalize();}
 if(dashTime>0)move=direction.scale(3.8);heroMoving=move.length()>.1;
 hero.position.addInPlace(move.scale(dt*6.4));hero.position.x=Math.max(-19,Math.min(19,hero.position.x));hero.position.z=Math.max(-5,Math.min(151,hero.position.z));hero.position.y=move.length()>.1?Math.sin(elapsed*15)*.018:0;if(flash<=0)hero.rotation.y=Math.atan2(direction.x,direction.z);
 if(keys.has('j')||attackHeld)attack();
 const stage=Math.min(3,Math.floor(hero.position.z/43));if(stage!==lastStage){lastStage=stage;$('stage').textContent=['壹 · 真田丸・回雪','貳 · 雪原・四面皆敵','參 · 柵門・未竟之路','終 · 本陣・再問天下'][stage];if(stage>0)announce(['','雪原 · 敵軍接近','柵門 · 突破重圍','德川家康 · 決戰'][stage]);}
 if(hero.position.z>123&&!bossSpawned){bossSpawned=true;spawn(0,146,true);announce('家康本陣 · 就在眼前');}
 spawnClock-=dt;if(spawnClock<=0){spawnClock=.8*cfg.spawn;const alive=foes.filter(f=>!f.dead&&!f.boss).length;if(alive<85){for(let i=0;i<4;i++){const a=Math.random()*Math.PI*2,r=14+Math.random()*9;spawn(Math.max(-24,Math.min(24,hero.position.x+Math.sin(a)*r)),Math.max(-5,Math.min(154,hero.position.z+Math.cos(a)*r)));}}}
 for(let i=foes.length-1;i>=0;i--){const f=foes[i];if(f.dead){foes.splice(i,1);continue;}const p=f.root.position;const delta=hero.position.subtract(p);delta.y=0;const distance=delta.length();f.cooldown-=dt;
  if(!f.boss&&distance>48){f.root.dispose();foes.splice(i,1);continue;}
  if(distance>1.25){delta.normalize();p.addInPlace(delta.scale(dt*(f.boss?2.4:2.1+Math.sin(f.phase)*.35)*cfg.speed));f.root.rotation.y=Math.atan2(delta.x,delta.z);p.y=Math.sin(elapsed*11+f.phase)*.015;}
  if(!f.boss){for(const other of foes){if(other===f||other.dead)continue;const dx=p.x-other.root.position.x,dz=p.z-other.root.position.z,dist2=dx*dx+dz*dz;if(dist2>.001&&dist2<.7){const strength=dt*1.6/Math.sqrt(dist2);p.x+=dx*strength;p.z+=dz*strength;}}}
  if(dashTime>0&&distance<2.7)damageEnemy(f,2,1.5);
  if(f.dead)continue;
  if(f.boss&&f.cooldown<=0){f.cooldown=2.5;ring(p,4.8,gold,.7);if(distance<4.8&&invuln<=0){hp=applyHit(hp,22*cfg.damage);invuln=.65;shake=.3;}}
  else if(!f.boss&&distance<1.65&&f.cooldown<=0&&invuln<=0&&hitTimer<=0){hp=applyHit(hp,(formation==='guard'?5:8)*cfg.damage);f.cooldown=1;hitTimer=.32;shake=.1;}
 }
 allies.forEach((a,i)=>{const target=new Vector3(hero.position.x+(i%5-2)*1.45,0,hero.position.z+(formation==='guard'?-2.4:3.2)-Math.floor(i/5)*1.8);const delta=target.subtract(a.position);a.position.addInPlace(delta.scale(Math.min(1,dt*5)));a.position.y=Math.sin(elapsed*12+i)*.012;a.rotation.y=hero.rotation.y;});
 if(allyCD<=0){allyCD=formation==='guard'?.95:.55;for(const a of allies){const f=foes.find(f=>!f.dead&&inRange(a.position,f.root.position,2.8));if(f)damageEnemy(f,1,.3);}}
 if(pendingVictory&&state==='playing')finish(true);else if(hp<=0&&state==='playing')finish(false);rage=Math.min(100,rage+dt*.8);updateHUD();
}
function visual(dt:number){
 shadowClock-=dt;
 if(hero){sun.position.copyFrom(hero.position.add(new Vector3(22,32,-20)));sun.direction.copyFrom(new Vector3(-22,-32,20).normalize());
 if(shadowClock<=0){shadowClock=.3;const casters=[hero,...allies,...foes.filter(f=>!f.dead&&inRange(hero.position,f.root.position,15)).slice(0,20).map(f=>f.root)];shadows.getShadowMap()!.renderList=casters.flatMap(root=>root.getChildMeshes()).filter(m=>!m.name.includes('contact'));}}
 const now=performance.now()*.001;animateBattlefield(now);for(let i=0;i<flames.length;i++)flames[i].scaling.y=.78+Math.sin(now*8+i)*.11;

 const target=state==='menu'?new Vector3(0,0,8):hero?.position||Vector3.Zero();const desired=target.add(new Vector3(9,13,-18));camera.position=Vector3.Lerp(camera.position,desired,Math.min(1,dt*4));camera.setTarget(target.add(new Vector3(state==='menu'?-7:0,0,6)));if(shake>0){camera.position.x+=(Math.random()-.5)*shake;camera.position.z+=(Math.random()-.5)*shake;}
 for(const s of snowflakes){s.position.y-=dt*(1+s.uniqueId%3*.2);s.position.x+=dt*.3;if(s.position.y<0){s.position.y=24;s.position.z=target.z+Math.random()*70-25;s.position.x=target.x+Math.random()*60-30;}}
 for(let i=effects.length-1;i>=0;i--){const e=effects[i];e.life-=dt;e.mesh.position.addInPlace(e.velocity.scale(dt));e.mesh.scaling.scaleInPlace(1+dt*2);e.mesh.visibility=Math.max(0,e.life/e.max);if(e.life<=0){e.mesh.dispose();effects.splice(i,1);}}
 if(announceTime>0){announceTime-=dt;$('announcement').style.opacity=String(Math.min(1,announceTime));}else $('announcement').style.opacity='0';
}
async function init(){try{for(const name of ['yukimura','ashigaru','tokugawa','ieyasu']){const loaded=await SceneLoader.ImportMeshAsync('', `${import.meta.env.BASE_URL}models/`,name+'.glb',scene);templates[name]=loaded.meshes[0];templates[name].setEnabled(false);
 if(name==='yukimura'){
  // Use the loaded skinned mesh directly so clips target the visible rig.
  hero=new TransformNode('yukimura',scene);templates[name].parent=hero;
  templates[name].scaling.scaleInPlace(1.15);templates[name].setEnabled(true);
  shadow(hero,.55);heroMotion=new HeroMotion(loaded.animationGroups);
 }
 }for(let i=0;i<10;i++)allies.push(actor('ashigaru','red-guard',(i%5-2)*1.5,-2-Math.floor(i/5)*2));for(let i=0;i<35;i++)spawn((Math.random()-.5)*29,11+Math.random()*34);$('start').textContent='再赴修羅　↗';$<HTMLButtonElement>('start').disabled=false;}catch(e){$('loading').textContent='模型載入失敗，請重新整理。';console.error(e);}}
engine.runRenderLoop(()=>{const dt=Math.min(engine.getDeltaTime()/1000,.05);if(state==='playing')update(dt);heroMotion?.update(dt,state==='playing'&&heroMoving,state==='paused');if(state!=='paused'){visual(dt);}scene.render();});window.addEventListener('resize',()=>engine.resize());init();
// Read-only diagnostics are useful for automated smoke tests and performance inspection.
Object.defineProperty(window,'__sanada',{get:()=>({state,hp,rage,kills,cycle:cfg.cycle,position:hero?{x:hero.position.x,z:hero.position.z}:null,enemies:foes.filter(f=>!f.dead).length,allies:allies.length,models:Object.keys(templates),fps:engine.getFps(),formation,heroAnimation:heroMotion?.state,animationClips:heroMotion?.names})});

if(import.meta.env.DEV && new URLSearchParams(location.search).has('test')){Object.defineProperty(window,'__sanadaTest',{value:{step:(seconds:number)=>{for(let t=0;t<seconds;t+=1/60){if(state==='playing')update(1/60);visual(1/60);}},snapshot:()=>({bossSpawned,bossHP:foes.find(f=>f.boss)?.hp,enemyCount:foes.length})}});}
