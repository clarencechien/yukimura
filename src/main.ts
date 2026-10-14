import './style.css';
import { HeroMotion } from './hero-motion';
import {CrowdModel,CrowdMotion,loadPalettes,type CrowdManifest} from './crowd-motion';
import { ComboChain, STRIKES, MUSOU_PULSES, MUSOU_DURATION, strikeContains } from './combat.mjs';
import { CombatFX } from './combat-fx';
import { BattleAudio } from './battle-audio';
import { illustrationPass } from './illustration';
import { battlefield } from './battlefield';
import { winterReflections } from './lighting';
import {finishMaterials} from './material-finish';
import {winterWeather} from './winter-weather';
import {battleFires} from './battle-fires';
import {weatheredMaterials} from './environment-materials';
import {PBRMaterial} from '@babylonjs/core/Materials/PBR/pbrMaterial';
import {Material} from '@babylonjs/core/Materials/material';
import { ShadowGenerator } from '@babylonjs/core/Lights/Shadows/shadowGenerator';
import '@babylonjs/core/Lights/Shadows/shadowGeneratorSceneComponent';
import { PointLight } from '@babylonjs/core/Lights/pointLight';
import { Engine } from '@babylonjs/core/Engines/engine';
import { Scene } from '@babylonjs/core/scene';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { Color3, Color4 } from '@babylonjs/core/Maths/math.color';
import { FreeCamera } from '@babylonjs/core/Cameras/freeCamera';
import { HemisphericLight } from '@babylonjs/core/Lights/hemisphericLight';
import { DirectionalLight } from '@babylonjs/core/Lights/directionalLight';
import { MeshBuilder } from '@babylonjs/core/Meshes/meshBuilder';
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial';
import { DynamicTexture } from '@babylonjs/core/Materials/Textures/dynamicTexture';
import { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import { SceneLoader } from '@babylonjs/core/Loading/sceneLoader';
import { Mesh } from '@babylonjs/core/Meshes/mesh';
import { AbstractMesh } from '@babylonjs/core/Meshes/abstractMesh';
import {VertexBuffer} from '@babylonjs/core/Buffers/buffer';
import '@babylonjs/core/Meshes/instancedMesh';
import '@babylonjs/loaders/glTF/glTFFileLoader';
import '@babylonjs/loaders/glTF/2.0/glTFLoader';
import { tuning, inRange, applyHit, nextCycle } from './rules.mjs';
const $ = <T extends HTMLElement = HTMLElement>(id:string) => document.getElementById(id) as T;
const canvas=$<HTMLCanvasElement>('battle');
const engine=new Engine(canvas,true,{stencil:true, preserveDrawingBuffer:true});
const softwareRenderer=/swiftshader|llvmpipe/i.test(engine.getGlInfo().renderer);
engine.setHardwareScalingLevel(softwareRenderer?1.35:(matchMedia('(pointer:coarse)').matches?1.4:1));
const scene=new Scene(engine);scene.clearColor=new Color4(.20,.28,.34,1);scene.fogMode=Scene.FOGMODE_EXP2;scene.fogDensity=.011;scene.fogColor=new Color3(.33,.38,.40);
const camera=new FreeCamera('battle-camera',new Vector3(16,27,-22),scene);camera.fov=.74;camera.minZ=.1;camera.maxZ=240;
illustrationPass(scene,camera);
const skyLight=new HemisphericLight('winter-sky',new Vector3(.3,1,-.2),scene);skyLight.intensity=.38;skyLight.diffuse=new Color3(.64,.77,.94);skyLight.groundColor=new Color3(.17,.22,.29);
const sun=new DirectionalLight('winter-sun',new Vector3(-.7,-1,.4),scene);sun.intensity=1.75;sun.diffuse=new Color3(1,.83,.62);
scene.requireLightSorting=true;sun.renderPriority=100;skyLight.renderPriority=90;
winterReflections(scene);
sun.shadowMinZ=1;sun.shadowMaxZ=95;sun.orthoLeft=-25;sun.orthoRight=25;sun.orthoTop=30;sun.orthoBottom=-30;sun.autoUpdateExtends=false;
const shadows=new ShadowGenerator(matchMedia('(pointer:coarse)').matches?512:1024,sun);shadows.usePoissonSampling=true;shadows.bias=.001;shadows.normalBias=.025;shadows.darkness=.23;
let shadowClock=0;
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const combatFX=new CombatFX(scene,reducedMotion);const audio=new BattleAudio();
const chain=new ComboChain();const strikeFacing=new Vector3(0,0,1);
let hitStop=0,musouTime=-1,musouPulse=0,hitReadoutTime=0,hurtFlash=0,impactZoom=0,dashSerial=0;
let totalHits=0,lastStrike=-1,lastStrikeHits=0;
const attackHistory:number[]=[];
function material(name:string,hex:string,glow=false){const m=new StandardMaterial(name,scene);m.diffuseColor=Color3.FromHexString(hex);m.specularColor=Color3.Black();if(glow)m.emissiveColor=m.diffuseColor.scale(.65);return m;}
const {snow,wood,dark:roofMaterial,stone,paper}=weatheredMaterials(scene);
const dark=material('charcoal iron and banners','#243540'), dirt=material('mud','#75695f'), crimson=material('crimson','#79242c'), gold=material('gold','#918166'), slashMat=material('slash','#ffd29b',true), redFx=material('musou','#fa4c4b',true);
function box(name:string,x:number,y:number,z:number,w:number,h:number,d:number,m:Material){const o=MeshBuilder.CreateBox(name,{width:w,height:h,depth:d},scene);o.position.set(x,y,z);o.material=m;return o;}
function cylinder(name:string,x:number,y:number,z:number,r:number,h:number,m:Material,top=r){const o=MeshBuilder.CreateCylinder(name,{diameter:r*2,diameterTop:top*2,height:h,tessellation:6},scene);o.position.set(x,y,z);o.material=m;return o;}
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
box('castle stone plinth',-26,1.1,64,21,3.2,17,stone);
for(let t=0;t<5;t++){
 const size=18-t*2.8,y=3+t*3.4;
 box('Osaka castle',-26,y,64,size,3,size*.8,paper);
 for(const side of [-1,1]){box('weathered castle corner',-26+side*(size*.5-.1),y,64-size*.4-.06,.16,3,.14,wood);}
 box('castle lower timber',-26,y-1.4,64-size*.4-.06,size,.18,.15,wood);
 const roof=MeshBuilder.CreateCylinder('hip roof',{diameterTop:(size-4)*1.4,diameterBottom:(size+3)*1.4,height:1.7,tessellation:4},scene);roof.rotation.y=Math.PI/4;roof.position.set(-26,y+2,64);roof.material=roofMaterial;
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
const fireLights:PointLight[]=[];
const firePositions=[6,43,88,138].flatMap(z=>[-8.6,8.6].map(x=>new Vector3(x,2.2,z)));
for(const z of [6,43,88,138])for(const x of [-8.6,8.6]){
 cylinder('brazier post',x,.8,z,.16,1.6,wood);cylinder('iron brazier',x,1.62,z,.38,.28,dark,.48);
 // Four local lights rather than a point light per soldier.
 if(x<0){const glow=new PointLight('brazier glow',new Vector3(x,2.2,z),scene);glow.diffuse=new Color3(1,.43,.14);glow.intensity=4.5;glow.range=8;fireLights.push(glow);}
}
// Merge static scenery by material to reduce draw calls on mobile.
const groups=new Map<Material,Mesh[]>();const staticCasters:AbstractMesh[]=[];
for(const mesh of [...scene.meshes]){if(mesh instanceof Mesh&&!mesh.metadata?.keepDynamic&&mesh.material instanceof Material){const list=groups.get(mesh.material)||[];list.push(mesh);groups.set(mesh.material,list);}}
for(const [mat,group] of groups){
 // Tinted snow lips share their material with untinted architecture. Babylon
 // requires identical vertex attributes when merging; white preserves both.
 if(group.some(mesh=>mesh.isVerticesDataPresent(VertexBuffer.ColorKind)))for(const mesh of group)if(!mesh.isVerticesDataPresent(VertexBuffer.ColorKind))mesh.setVerticesData(VertexBuffer.ColorKind,new Float32Array(mesh.getTotalVertices()*4).fill(1));
 const vertexAlpha=group.some(mesh=>mesh.hasVertexAlpha);
 const merged=Mesh.MergeMeshes(group,true,true);if(merged){merged.hasVertexAlpha=vertexAlpha;merged.freezeWorldMatrix();merged.isPickable=false;merged.receiveShadows=true;if([wood,stone,paper,dark,roofMaterial,snow,crimson,gold].includes(mat as typeof wood))staticCasters.push(merged);}
}
const weather=winterWeather(scene,sun,reducedMotion);
const fires=battleFires(scene,reducedMotion);
// Ground silhouettes reinforce readable actor placement without costly dynamic shadows.
const shadowMat=material('contact shadow','#202b2e');shadowMat.alpha=.42;
const contactTexture=new DynamicTexture('soft foot contact',64,scene,false),contactContext=contactTexture.getContext();
const contactGradient=contactContext.createRadialGradient(32,32,3,32,32,31);contactGradient.addColorStop(0,'rgba(255,255,255,.8)');contactGradient.addColorStop(.5,'rgba(255,255,255,.45)');contactGradient.addColorStop(1,'rgba(255,255,255,0)');contactContext.fillStyle=contactGradient;contactContext.fillRect(0,0,64,64);contactTexture.hasAlpha=true;contactTexture.update();shadowMat.diffuseTexture=contactTexture;shadowMat.useAlphaFromDiffuseTexture=true;
function shadow(parent:TransformNode,r=.5){const m=MeshBuilder.CreateDisc('contact',{radius:r,tessellation:12},scene);m.rotation.x=Math.PI/2;m.position.y=.035;m.material=shadowMat;m.parent=parent;return m;}
type Actor={root:TransformNode,hp:number,maxHp:number,cooldown:number,boss:boolean,dead:boolean,phase:number,velocity:Vector3,stun:number,deathTime:number,dashHit:number,windup:number,warning:Mesh|null,attackTime:number,hitAge:number,deathAge:number,deathDuration:number,deathClip:'fall'|'fall_back',landed:boolean,moving:number};
let hero:TransformNode;let heroMotion:HeroMotion;let heroMoving=false;const templates:Record<string,AbstractMesh>={};const allies:TransformNode[]=[];const foes:Actor[]=[];
const crowdModels:Record<string,CrowdModel>={};const crowdMotions=new Map<TransformNode,CrowdMotion>();
const support=new Map<TransformNode,{cooldown:number,attack:number,target:Actor|null,hit:boolean}>();
function disposeActor(root:TransformNode){crowdMotions.delete(root);support.delete(root);root.dispose();}
function turn(root:TransformNode,yaw:number,dt:number){const delta=Math.atan2(Math.sin(yaw-root.rotation.y),Math.cos(yaw-root.rotation.y));root.rotation.y+=delta*Math.min(1,dt*12);}
let pendingVictory=false;let manualTestClock=false;
let state:'menu'|'playing'|'paused'|'won'|'lost'='menu';let cfg=tuning('normal',1);let hp=120,rage=35,kills=0,combo=0,comboTime=0,elapsed=0,spawnClock=0,dashCD=0,dashTime=0,invuln=0,hitTimer=0,allyCD=0,formation='guard',bossSpawned=false,flash=0,shake=0;
let direction=new Vector3(0,0,1);let announceTime=0,lastStage=-1,unlocked=1;
try{unlocked=Math.max(1,Math.min(20,Number(localStorage.getItem('sanada-cycle'))||1));}catch{}
function fillCycles(){const select=$<HTMLSelectElement>('cycle');select.innerHTML='';for(let i=1;i<=Math.max(3,unlocked);i++){const o=document.createElement('option');o.value=String(i);o.textContent=`第 ${i} 周目${i===1?' · 初雪':''}`;select.append(o);}select.value=String(unlocked);}fillCycles();
const keys=new Set<string>();let joy={x:0,z:0},attackHeld=false;
function clearInput(){keys.clear();joy={x:0,z:0};attackHeld=false;$('stick').style.transform='';}
window.addEventListener('keydown',e=>{if(e.target instanceof HTMLSelectElement)return;const k=e.key.toLowerCase();if([' ','arrowup','arrowdown','arrowleft','arrowright'].includes(k))e.preventDefault();keys.add(k);if(e.repeat)return;if(k==='p'||k==='escape')pause();if(state!=='playing')return;if(k==='j')attack();if(k===' ')dash();if(k==='k')musou();if(k==='f')toggleFormation();});
window.addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));window.addEventListener('blur',()=>{clearInput();if(state==='playing')pause();});document.addEventListener('visibilitychange',()=>{if(document.hidden&&state==='playing')pause();});
function bind(id:string,fn:()=>void){$(id).addEventListener('click',fn);}
bind('readLore',()=>{$('lore').hidden=false;});bind('closeLore',()=>{$('lore').hidden=true;});
bind('sound',()=>{audio.unlock();audio.toggle();syncSound();});
function syncSound(){$('sound').textContent=audio.muted?'音效 關':'音效 開';$('sound').setAttribute('aria-pressed',String(!audio.muted));}syncSound();
bind('start',start);bind('retry',()=>{if(state==='won'){$<HTMLSelectElement>('cycle').value=String(nextCycle(cfg.cycle));}start();});bind('back',menu);bind('returnMenu',menu);bind('pause',pause);bind('resume',pause);bind('dash',dash);bind('musou',musou);bind('formation',toggleFormation);
$('attack').addEventListener('pointerdown',e=>{e.preventDefault();attackHeld=true;$( 'attack').setPointerCapture(e.pointerId);attack();});for(const ev of ['pointerup','pointercancel','lostpointercapture'])$('attack').addEventListener(ev,()=>attackHeld=false);
const joystick=$('joystick');let joyId:number|null=null;
function moveJoy(e:PointerEvent){if(e.pointerId!==joyId)return;const r=joystick.getBoundingClientRect();let x=e.clientX-r.left-r.width/2,y=e.clientY-r.top-r.height/2;const len=Math.hypot(x,y);if(len>38){x*=38/len;y*=38/len;}joy={x:x/38,z:-y/38};$('stick').style.transform=`translate(${x}px,${y}px)`;}
joystick.addEventListener('pointerdown',e=>{joyId=e.pointerId;joystick.setPointerCapture(e.pointerId);moveJoy(e);});joystick.addEventListener('pointermove',moveJoy);for(const ev of ['pointerup','pointercancel','lostpointercapture'])joystick.addEventListener(ev,()=>{joyId=null;joy={x:0,z:0};$('stick').style.transform='';});
function announce(t:string){$('announcement').textContent=t;announceTime=2.6;}
function actor(kind:string,name:string,x:number,z:number,scale=1){const root=new TransformNode(name,scene);const motion=crowdModels[kind].create(root,scale,crowdMotions.size*.618);crowdMotions.set(root,motion);root.position.set(x,0,z);shadow(root,.48*scale);if(kind==='ashigaru')support.set(root,{cooldown:.2+support.size*.073,attack:-1,target:null,hit:false});return root;}
// Scale the instanced body, keeping the world-space attack/warning radius intact.
function spawn(x:number,z:number,boss=false){const root=actor(boss?'ieyasu':'tokugawa',boss?'ieyasu':'enemy',x,z,boss?1.65:1);const life=boss?cfg.bossHealth:cfg.enemyHealth;const a={root,hp:life,maxHp:life,cooldown:Math.random(),boss,dead:false,phase:Math.random()*6.28,velocity:Vector3.Zero(),stun:0,deathTime:0,dashHit:-1,windup:0,warning:null,attackTime:-1,hitAge:0,deathAge:0,deathDuration:1,deathClip:'fall' as const,landed:false,moving:0};foes.push(a);if(boss){root.getChildMeshes().forEach(m=>{if(m.name.includes('contact'))return;m.outlineColor=new Color3(.7,.5,.2);});}}
function clearBattle(){combatFX.clear();chain.reset();musouTime=-1;musouPulse=0;hitStop=0;hurtFlash=0;impactZoom=0;hitReadoutTime=0;totalHits=0;lastStrike=-1;lastStrikeHits=0;attackHistory.length=0;$('strikeReadout').textContent='';$('app').classList.remove('musou-active');for(const f of foes)disposeActor(f.root);foes.length=0;for(const a of allies)disposeActor(a);allies.length=0;}
function start(){if(!hero)return;audio.unlock();audio.pause(false);heroMotion.reset();heroMoving=false;clearInput();clearBattle();cfg=tuning($<HTMLSelectElement>('difficulty').value,Number($<HTMLSelectElement>('cycle').value));hp=cfg.health;rage=35;kills=0;combo=0;elapsed=0;spawnClock=0;dashCD=0;dashTime=0;invuln=1;hitTimer=0;allyCD=0;bossSpawned=false;pendingVictory=false;formation='guard';lastStage=-1;hero.position.set(0,0,0);hero.rotation.y=0;direction.set(0,0,1);for(let i=0;i<10;i++)allies.push(actor('ashigaru','red-guard', (i%5-2)*1.35,-2-Math.floor(i/5)*1.8));for(let i=0;i<40;i++){const a=(i%10)/10*Math.PI*2,r=6+Math.floor(i/10)*3;spawn(Math.sin(a)*r,5+Math.cos(a)*r);}state='playing';$('app').classList.add('playing');$('menu').hidden=true;$('result').hidden=true;$('pausePanel').hidden=true;$('hud').hidden=false;$('combat').hidden=false;$('loading').textContent='';announce('夏火已冷，冬雪重來。');updateHUD();}
function menu(){state='menu';audio.pause(false);chain.reset();musouTime=-1;$('app').classList.remove('musou-active');$('bossHud').hidden=true;clearInput();$('app').classList.remove('playing');$('menu').hidden=false;$('result').hidden=true;$('pausePanel').hidden=true;$('hud').hidden=true;$('combat').hidden=true;$('announcement').textContent='';}
function pause(){if(state==='playing'){state='paused';audio.pause(true);clearInput();$('pausePanel').hidden=false;}else if(state==='paused'){state='playing';audio.pause(false);$('pausePanel').hidden=true;}}
function finish(won:boolean){chain.reset();musouTime=-1;$('app').classList.remove('musou-active');state=won?'won':'lost';clearInput();$('combat').hidden=true;$('result').hidden=false;$('resultTitle').textContent=won?'本陣已破，此戰未終。':'此身暫歇，此志未滅。';$('resultText').textContent=won?`家康本陣突破。第 ${cfg.cycle} 周目・${kills} 擊破。修羅道記住了你的槍路。冬雪，將再度降臨。`:`此輪奮戰至此，共 ${kills} 擊破。雪還未停。整軍，再赴未竟之戰。`;$('retry').textContent=won?'再叩修羅 ↗':'重燃赤備 ↗';if(won){unlocked=Math.max(unlocked,nextCycle(cfg.cycle));try{localStorage.setItem('sanada-cycle',String(unlocked));}catch{}fillCycles();}}
function warningRing(root:TransformNode){const m=MeshBuilder.CreateTorus('boss warning',{diameter:9.6,thickness:.10,tessellation:48},scene);m.parent=root;m.position.y=.06;m.material=redFx;m.isPickable=false;return m;}
function damageEnemy(f:Actor,dmg:number,push:number,lift=0,player=false){
 if(f.dead)return;
 f.hitAge=0;f.hp=applyHit(f.hp,dmg);const v=f.root.position.subtract(hero.position);v.y=0;if(v.length()<.01)v.copyFrom(strikeFacing);v.normalize();
 const resistance=f.boss?.18:1;f.velocity.x=v.x*push*resistance;f.velocity.z=v.z*push*resistance;
 f.velocity.y=Math.max(f.velocity.y,lift*resistance);f.stun=f.boss?.12:.24+lift*.055;if(!f.boss||push>=12){f.attackTime=-1;f.windup=0;f.warning?.dispose();f.warning=null;}
 if(player){totalHits++;combo++;comboTime=3.5;rage=Math.min(100,rage+1.5);}
 if(f.hp===0){f.warning?.dispose();f.warning=null;f.dead=true;f.deathDuration=1.08+(f.phase/6.28)*.20;f.deathTime=f.deathDuration+.45;f.deathClip=Math.sin(f.phase)>0?'fall':'fall_back';f.root.rotation.z=0;f.root.rotation.x=0;kills++;rage=Math.min(100,rage+3);hp=Math.min(cfg.health,hp+(kills%8===0?4:0));if(f.boss)pendingVictory=true;}
}
function attack(){if(state!=='playing'||musouTime>=0||dashTime>0)return;chain.press();}
function aimStrike(){
 strikeFacing.copyFrom(direction);let target:Actor|undefined;let best=Infinity;
 for(const f of foes){if(f.dead)continue;const d=f.root.position.subtract(hero.position);d.y=0;const distance=d.length();if(distance>6.5)continue;const dot=distance>0?Vector3.Dot(d.scale(1/distance),direction):1;const score=distance+(1-dot)*2.5;if(score<best){best=score;target=f;}}
 if(target){strikeFacing.copyFrom(target.root.position.subtract(hero.position));strikeFacing.y=0;strikeFacing.normalize();}
 direction.copyFrom(strikeFacing);hero.rotation.y=Math.atan2(strikeFacing.x,strikeFacing.z);
}
function impactStrike(index:number){
 const strike=STRIKES[index],yaw=Math.atan2(strikeFacing.x,strikeFacing.z);let count=0;
 if(index===2)combatFX.thrust(hero.position,yaw,strike.range);else combatFX.arc(hero.position,yaw,strike.range,strike.arc,index===1);
 audio.swing(index);
 for(const f of foes){if(f.dead||!strikeContains(hero.position,f.root.position,strikeFacing,strike))continue;damageEnemy(f,strike.damage,strike.push,strike.lift,true);if(count<5)combatFX.impact(f.root.position,index===3);count++;}
 lastStrikeHits=count;
 if(count){hitStop=Math.max(hitStop,strike.hitstop);shake=index===3?.32:.10;impactZoom=index===3?.085:.025;audio.hit(index===3);$('strikeReadout').textContent=`${strike.name}　${count} 人貫破`;hitReadoutTime=.8;}
 if(index===3)combatFX.dustKick(hero.position,10);
}
function dash(){if(state!=='playing'||dashCD>0||musouTime>=0)return;chain.reset();dashSerial++;dashCD=1.15;dashTime=.26;invuln=.42;audio.dash();combatFX.thrust(hero.position,Math.atan2(direction.x,direction.z),3.5);combatFX.dustKick(hero.position);}
function musou(){if(state!=='playing'||rage<100||musouTime>=0)return;chain.reset();dashTime=0;rage=0;musouTime=0;musouPulse=0;invuln=MUSOU_DURATION+.3;audio.ultimate();announce('奥義 · 六文赤蓮');$('app').classList.add('musou-active');combatFX.charge(hero.position);}
function updateMusou(dt:number){
 if(musouTime<0)return;musouTime+=dt;
 while(musouPulse<MUSOU_PULSES.length&&musouTime>=MUSOU_PULSES[musouPulse]){
  const final=musouPulse===MUSOU_PULSES.length-1;const radius=final?12:8+musouPulse*.5;let count=0;
  combatFX.burst(hero.position,radius,final);audio.ultimate(final);shake=final?.45:.16;impactZoom=final?.13:.045;hitStop=final?.09:.025;
  for(const f of foes){if(!f.dead&&inRange(hero.position,f.root.position,radius)){damageEnemy(f,final?12:4,final?17:7,final?8:3,true);if(count<5)combatFX.impact(f.root.position,true);count++;}}
  lastStrikeHits=count;musouPulse++;
 }
 if(musouTime>=MUSOU_DURATION){musouTime=-1;$('app').classList.remove('musou-active');}
}
function hurt(damage:number){hp=applyHit(hp,damage);hitTimer=.35;hurtFlash=.35;shake=.15;audio.hurt();}
function toggleFormation(){if(state!=='playing')return;formation=formation==='guard'?'charge':'guard';announce(formation==='guard'?'十勇士 · 結誓':'十勇士 · 破軍');}
function updateHUD(){const boss=foes.find(f=>f.boss&&!f.dead);$('bossHud').hidden=!boss||state==='menu';if(boss)$('bossHP').style.width=`${boss.hp/boss.maxHp*100}%`;$('hp').style.width=`${hp/cfg.health*100}%`;$('rage').style.width=`${rage}%`;$('kills').textContent=String(kills);$('combo').textContent=combo>1?`${combo} HITS`:'';$('progress').style.width=`${Math.min(100,hero.position.z/143*100)}%`;$('formationLabel').textContent=formation==='guard'?'十勇士・結誓':'十勇士・破軍';$('musou').classList.toggle('ready',rage>=100);$('dash').style.opacity=dashCD>0?'.45':'1';}
function update(dt:number){elapsed+=dt;dashCD-=dt;dashTime-=dt;invuln-=dt;hitTimer-=dt;allyCD-=dt;flash-=dt;hurtFlash=Math.max(0,hurtFlash-dt);hitReadoutTime=Math.max(0,hitReadoutTime-dt);shake=Math.max(0,shake-dt);comboTime-=dt;if(comboTime<=0)combo=0;
 let x=joy.x+(keys.has('d')||keys.has('arrowright')?1:0)-(keys.has('a')||keys.has('arrowleft')?1:0),z=joy.z+(keys.has('w')||keys.has('arrowup')?1:0)-(keys.has('s')||keys.has('arrowdown')?1:0);
 let move=new Vector3(x,0,z);if(move.length()>1)move.normalize();
 // Screen-relative movement follows the fixed oblique camera.
 if(move.length()>.08){const mx=move.x,mz=move.z;move.set(mx*.894-mz*.447,0,mx*.447+mz*.894);if(!chain.active&&musouTime<0)direction.copyFrom(move).normalize();}
 if(dashTime>0)move=direction.scale(3.8);else if(chain.active)move.scaleInPlace(.6);else if(musouTime>=0)move.scaleInPlace(.25);heroMoving=move.length()>.1;
 hero.position.addInPlace(move.scale(dt*6.4));hero.position.x=Math.max(-19,Math.min(19,hero.position.x));hero.position.z=Math.max(-5,Math.min(151,hero.position.z));hero.position.y=move.length()>.1?Math.sin(elapsed*15)*.018:0;if(!chain.active&&musouTime<0)hero.rotation.y=Math.atan2(direction.x,direction.z);
 if(musouTime<0&&dashTime<=0){
  for(const event of chain.step(dt,keys.has('j')||attackHeld)){
   if(event.type==='begin'){aimStrike();combatFX.windup(hero.position,Math.atan2(strikeFacing.x,strikeFacing.z));lastStrike=event.index;attackHistory.push(event.index);if(attackHistory.length>16)attackHistory.shift();$('strikeReadout').textContent=STRIKES[event.index].name;hitReadoutTime=.8;}
   else impactStrike(event.index);
  }
  if(chain.active){const strike=STRIKES[chain.active.index],t=chain.active.time;
   if(t<strike.impact)hero.position.addInPlace(strikeFacing.scale(dt*strike.lunge/strike.impact));
   const spinProgress=Math.max(0,Math.min(1,(t/strike.duration-.12)/.76));const spin=chain.active.index===3?spinProgress*spinProgress*(3-2*spinProgress)*Math.PI*2:0;
   hero.rotation.y=Math.atan2(strikeFacing.x,strikeFacing.z)+spin;
  }
 }
 hero.position.x=Math.max(-19,Math.min(19,hero.position.x));hero.position.z=Math.max(-5,Math.min(151,hero.position.z));
 updateMusou(dt);
 const stage=Math.min(3,Math.floor(hero.position.z/43));if(stage!==lastStage){lastStage=stage;$('stage').textContent=['壹 · 真田丸・回雪','貳 · 雪原・四面皆敵','參 · 柵門・未竟之路','終 · 本陣・再問天下'][stage];if(stage>0)announce(['','雪原 · 敵軍接近','柵門 · 突破重圍','德川家康 · 決戰'][stage]);}
 if(hero.position.z>123&&!bossSpawned){bossSpawned=true;spawn(0,146,true);announce('家康本陣 · 就在眼前');}
 spawnClock-=dt;if(spawnClock<=0){spawnClock=.68*cfg.spawn;const alive=foes.filter(f=>!f.dead&&!f.boss).length;if(alive<92){for(let i=0;i<6;i++){const a=Math.random()*Math.PI*2,r=13+Math.random()*6;spawn(Math.max(-24,Math.min(24,hero.position.x+Math.sin(a)*r)),Math.max(-5,Math.min(154,hero.position.z+Math.cos(a)*r)));}}}
 for(let i=foes.length-1;i>=0;i--){
  const f=foes[i],p=f.root.position;f.moving=0;f.hitAge+=dt;if(f.attackTime>=0){f.attackTime+=dt;if(f.attackTime>(f.boss?1.97:.79))f.attackTime=-1;}
  if(f.dead){
   f.deathAge+=dt;f.deathTime-=dt;p.addInPlace(f.velocity.scale(dt));f.velocity.y-=dt*16;
   const grounded=p.y<=0;if(grounded){p.y=0;f.velocity.y=0;}
   f.velocity.x*=Math.exp(-dt*(grounded?8:2));f.velocity.z*=Math.exp(-dt*(grounded?8:2));
   if(grounded&&!f.landed&&f.deathAge>f.deathDuration*.68){f.landed=true;combatFX.dustKick(p,4);}
   if(f.deathTime<.18)p.y-=.18-f.deathTime;
   if(f.deathTime<=0){disposeActor(f.root);foes.splice(i,1);}continue;
  }
  f.cooldown-=dt;f.stun=Math.max(0,f.stun-dt);
  if(f.stun>0||p.y>.03){p.addInPlace(f.velocity.scale(dt));f.velocity.y-=dt*18;f.velocity.x*=Math.exp(-dt*4);f.velocity.z*=Math.exp(-dt*4);if(p.y<=0){p.y=0;f.velocity.y=0;}f.root.rotation.z=Math.sin(f.phase)*Math.min(.6,f.stun);}
  else{p.y=0;f.root.rotation.z*=Math.exp(-dt*14);}
  const delta=hero.position.subtract(p);delta.y=0;const distance=delta.length();
  if(!f.boss&&distance>48){disposeActor(f.root);foes.splice(i,1);continue;}
  if(dashTime>0&&distance<2.7&&f.dashHit!==dashSerial){f.dashHit=dashSerial;damageEnemy(f,2,11,3,true);combatFX.impact(p);audio.hit();}
  if(f.dead||f.stun>0||p.y>.15)continue;
  if(f.windup>0){
   f.windup-=dt;if(f.warning)f.warning.visibility=.5+.5*(1-f.windup/.75);
   if(f.windup<=0){f.warning?.dispose();f.warning=null;f.cooldown=f.boss?2.4:1.1;if(distance<(f.boss?4.8:1.9)&&invuln<=0&&hitTimer<=0){hurt((f.boss?22:formation==='guard'?5:8)*cfg.damage);if(f.boss)invuln=.65;}if(f.boss)combatFX.burst(p,4.8);}
   continue;
  }
  if(f.attackTime>=0)continue;
  if(distance>(f.boss?3.2:1.5)){delta.normalize();f.moving=(f.boss?2.5:3.1+Math.sin(f.phase)*.45)*cfg.speed;p.addInPlace(delta.scale(dt*f.moving));turn(f.root,Math.atan2(delta.x,delta.z),dt);}
  if(!f.boss){for(const other of foes){if(other===f||other.dead)continue;const dx=p.x-other.root.position.x,dz=p.z-other.root.position.z,dist2=dx*dx+dz*dz;if(dist2>.001&&dist2<.65){const strength=dt*1.4/Math.sqrt(dist2);p.x+=dx*strength;p.z+=dz*strength;}}}
  if(f.cooldown<=0&&distance<(f.boss?6:2.0)){f.windup=f.boss?.75:.3;f.attackTime=0;turn(f.root,Math.atan2(delta.x,delta.z),1);if(f.boss){f.warning=warningRing(f.root);announce('家康 · 重斬將至');}}
 }
 // Keep defeated silhouettes bounded even during a large musou burst.
 const corpses=foes.filter(f=>f.dead);for(const f of corpses.slice(0,Math.max(0,corpses.length-28))){f.deathTime=0;}
 for(const f of foes){const motion=crowdMotions.get(f.root)!;if(f.dead)motion.sample(f.deathClip,Math.min(f.root.position.y>.1?.70:1,f.deathAge/f.deathDuration));else if(f.stun>0||f.root.position.y>.1)motion.sample('hurt',Math.min(.65,f.hitAge/.4));else if(f.attackTime>=0)motion.sample('thrust',f.boss?Math.min(1,f.attackTime/1.97):f.attackTime/.79);else motion.loop(dt,f.moving>.1,Math.max(.8,f.moving/3.8));}
 allies.forEach((a,i)=>{
  const data=support.get(a)!,motion=crowdMotions.get(a)!;data.cooldown-=dt;
  if(data.attack>=0){
   data.attack+=dt;const f=data.target;
   if(f&&!f.dead){const d=f.root.position.subtract(a.position);turn(a,Math.atan2(d.x,d.z),dt);if(data.attack>=.30&&!data.hit){data.hit=true;if(inRange(a.position,f.root.position,3.2))damageEnemy(f,formation==='charge'?2:1,2.2);}}
   motion.sample('thrust',data.attack/.79);
   if(data.attack>=.79){data.attack=-1;data.cooldown=(formation==='guard'?.45:.12)+(i%3)*.08;data.target=null;}
   return;
  }
  let nearest:Actor|null=null,best=formation==='charge'?5.5:3.0;
  for(const f of foes){if(f.dead)continue;const d=Vector3.Distance(a.position,f.root.position);if(d<best){best=d;nearest=f;}}
  if(nearest&&best<2.7&&data.cooldown<=0){data.attack=0;data.hit=false;data.target=nearest;motion.sample('thrust',0);return;}
  const target=nearest&&formation==='charge'&&inRange(a.position,hero.position,9)?nearest.root.position:new Vector3(hero.position.x+(i%5-2)*1.45,0,hero.position.z+(formation==='guard'?-3.2:4.2)-Math.floor(i/5)*1.8);
  const delta=target.subtract(a.position);delta.y=0;const distance=delta.length(),speed=distance>.25?Math.min(7.2,distance*3):0;
  if(speed>0){delta.normalize();a.position.addInPlace(delta.scale(Math.min(distance,dt*speed)));turn(a,Math.atan2(delta.x,delta.z),dt);}else turn(a,hero.rotation.y,dt);
  motion.loop(dt,speed>.1,Math.max(.75,Math.min(1.65,speed/4.5)));
 });
 if(pendingVictory&&state==='playing')finish(true);else if(hp<=0&&state==='playing')finish(false);rage=Math.min(100,rage+dt*.8);updateHUD();
}
function visual(dt:number){
 combatFX.update(dt);$('strikeReadout').style.opacity=String(Math.min(1,hitReadoutTime*3));$('hitVignette').style.opacity=String(hurtFlash*1.7);
 impactZoom=Math.max(0,impactZoom-dt*.2);
 shadowClock-=dt;
 if(hero){sun.position.copyFrom(hero.position.add(new Vector3(22,32,-20)));sun.direction.copyFrom(new Vector3(-22,-32,20).normalize());
 if(shadowClock<=0){shadowClock=.3;const nearestFires=[...firePositions].sort((a,b)=>Vector3.DistanceSquared(a,hero.position)-Vector3.DistanceSquared(b,hero.position));fireLights.forEach((light,i)=>{light.position.copyFrom(nearestFires[i]);light.renderPriority=10-i;});const casters=[hero,...allies,...foes.filter(f=>!f.dead&&inRange(hero.position,f.root.position,15)).slice(0,20).map(f=>f.root)];shadows.getShadowMap()!.renderList=[...staticCasters,...casters.flatMap(root=>root.getChildMeshes()).filter(m=>!m.name.includes('contact')&&!m.name.includes('warning'))];}}
 const now=performance.now()*.001;animateBattlefield(now);fires.update(now);for(let i=0;i<fireLights.length;i++)fireLights[i].intensity=4.2+Math.sin(now*5.3+i)*.35+Math.sin(now*11.1+i)*.18;

 const target=state==='menu'?new Vector3(0,0,8):hero?.position||Vector3.Zero();const zoom=musouTime>=0&&!reducedMotion?(musouTime<.3?.82:.93):1;const desired=target.add(new Vector3(8*zoom,11*zoom,-16*zoom));camera.fov+=(.76-(reducedMotion?0:impactZoom)-camera.fov)*Math.min(1,dt*9);camera.position=Vector3.Lerp(camera.position,desired,Math.min(1,dt*4));camera.setTarget(target.add(new Vector3(state==='menu'?-7:0,0,6)));if(shake>0&&!reducedMotion){camera.position.x+=(Math.random()-.5)*shake;camera.position.z+=(Math.random()-.5)*shake;}
 weather.update(dt,target);
 if(announceTime>0){announceTime-=dt;$('announcement').style.opacity=String(Math.min(1,announceTime));}else $('announcement').style.opacity='0';
}
async function init(){try{const response=await fetch(`${import.meta.env.BASE_URL}models/crowd-animation.json?rev=commander-19`);if(!response.ok)throw Error('Crowd manifest unavailable');const crowdManifest: CrowdManifest=await response.json();const palettes=await loadPalettes(scene,crowdManifest,`${import.meta.env.BASE_URL}models/`);for(const name of ['yukimura','ashigaru','tokugawa','ieyasu']){const loaded=await SceneLoader.ImportMeshAsync('', `${import.meta.env.BASE_URL}models/`,name+'.glb?rev=commander-19',scene);finishMaterials(scene,loaded.meshes,name);loaded.meshes.forEach(mesh=>mesh.receiveShadows=true);templates[name]=loaded.meshes[0];templates[name].setEnabled(false);
 if(name==='yukimura'){
  // Use the loaded skinned mesh directly so clips target the visible rig.
  hero=new TransformNode('yukimura',scene);templates[name].parent=hero;
  templates[name].scaling.scaleInPlace(1.15);templates[name].setEnabled(true);
  shadow(hero,.55);heroMotion=new HeroMotion(loaded.animationGroups);
 }else{loaded.animationGroups.forEach(g=>g.stop());const meshes=loaded.meshes.filter((m):m is Mesh=>m instanceof Mesh&&m.getTotalVertices()>0);const palette=crowdManifest.models[name];crowdModels[name]=new CrowdModel(meshes,palette,palettes.get(palette.uri)!,scene);}
 }await combatFX.warmup();for(let i=0;i<10;i++)allies.push(actor('ashigaru','red-guard',(i%5-2)*1.5,-2-Math.floor(i/5)*2));for(let i=0;i<35;i++)spawn((Math.random()-.5)*29,11+Math.random()*34);$('start').textContent='再赴修羅　↗';$<HTMLButtonElement>('start').disabled=false;}catch(e){$('loading').textContent='模型載入失敗，請重新整理。';console.error(e);}}
function tick(realDt:number){
 let dt=realDt;
 if(state==='playing'&&hitStop>0){hitStop=Math.max(0,hitStop-realDt);dt=0;}
 if(state==='playing'&&dt>0)update(dt);
 if(heroMotion&&state!=='paused'){
  if(chain.active){const strike=STRIKES[chain.active.index];heroMotion.pose(strike.clip,chain.active.time/strike.duration,dt);}
  else if(musouTime>=0){heroMotion.pose('spin',Math.min(1,(musouTime%.48)/.48),dt);hero.rotation.y=Math.atan2(direction.x,direction.z)+musouTime*9;}
  else if(state==='playing'&&dashTime>0)heroMotion.pose('dash',1-dashTime/.26,dt);
  else if(state==='playing'&&hitTimer>0)heroMotion.pose('hurt',1-hitTimer/.35,dt);
  else heroMotion.update(dt,state==='playing'&&heroMoving,dt===0);
 }
 if(state!=='paused')visual(realDt);
}
engine.runRenderLoop(()=>{weather.pause(state==='paused'||manualTestClock);fires.pause(state==='paused'||manualTestClock);if(!manualTestClock)tick(Math.min(engine.getDeltaTime()/1000,.05));scene.render();});window.addEventListener('resize',()=>engine.resize());init();
// Read-only diagnostics are useful for automated smoke tests and performance inspection.
Object.defineProperty(window,'__sanada',{get:()=>({state,hp,rage,kills,cycle:cfg.cycle,position:hero?{x:hero.position.x,z:hero.position.z}:null,enemies:foes.filter(f=>!f.dead).length,allies:allies.length,models:Object.keys(templates),fps:engine.getFps(),formation,heroAnimation:heroMotion?.state,animationClips:heroMotion?.names,look:{toneMapping:scene.imageProcessingConfiguration.toneMappingEnabled,reflectionSize:scene.environmentTexture?.getSize().width,renderWidth:engine.getRenderWidth(),renderHeight:engine.getRenderHeight(),passes:camera._postProcesses.flatMap(p=>p?[{name:p.name,width:p.width,height:p.height,type:p.inputTexture?.texture?.type}]:[]),coats:scene.materials.filter(m=>m instanceof PBRMaterial&&m.clearCoat.isEnabled).map(m=>m.name)},environment:{terrain:scene.getMaterialByName('churned snow and mud')?.getClassName(),staticCasters:staticCasters.length,weatherCapacity:weather.capacity,weatherActive:weather.active,terrainDetail:(scene.getMaterialByName('churned snow and mud') as PBRMaterial)?.detailMap.isEnabled,fireCapacity:fires.capacity,fireActive:fires.active},crowd:{actors:crowdMotions.size,instances:[...crowdMotions.values()].filter(m=>m.mesh.getClassName()==='InstancedMesh').length,allies:allies.map(a=>({state:crowdMotions.get(a)?.state,frame:crowdMotions.get(a)?.frame})),enemies:foes.map(f=>({state:crowdMotions.get(f.root)?.state,frame:crowdMotions.get(f.root)?.frame})),palettes:Object.keys(crowdModels).length},attackIndex:chain.active?.index??-1,attackHistory:[...attackHistory],totalHits,lastStrikeHits,hitStop,musouActive:musouTime>=0,musouPulse,airborne:foes.filter(f=>!f.dead&&f.root.position.y>.2).length,corpses:foes.filter(f=>f.dead).length,effects:combatFX.count,muted:audio.muted})});

if(import.meta.env.DEV && new URLSearchParams(location.search).has('test')){Object.defineProperty(window,'__sanadaTest',{value:{step:(seconds:number)=>{for(let t=0;t<seconds;t+=1/60){tick(1/60);}},setupCombat:(health=30)=>{manualTestClock=true;clearBattle();heroMotion.reset();dashCD=0;dashTime=0;invuln=0;hp=cfg.health;rage=100;hero.position.set(0,0,0);direction.set(0,0,1);spawnClock=60;allyCD=60;for(let i=0;i<12;i++){const a=(i-5.5)*.22;spawn(Math.sin(a)*3,Math.cos(a)*3);}for(const f of foes){f.hp=health;f.maxHp=health;f.cooldown=30;}},setupArmy:()=>{manualTestClock=true;clearBattle();heroMotion.reset();hero.position.set(0,0,0);spawnClock=60;invuln=999;for(let i=0;i<10;i++)allies.push(actor('ashigaru','red-guard',(i%5-2)*1.5,-5-Math.floor(i/5)*2));for(let i=0;i<100;i++){const a=i*Math.PI*2/25,r=8+Math.floor(i/25)*2;spawn(Math.sin(a)*r,Math.cos(a)*r);}updateHUD();},setupFalls:()=>{manualTestClock=true;clearBattle();heroMotion.reset();hero.position.set(0,0,0);spawnClock=60;invuln=999;for(let i=0;i<6;i++){spawn((i%3-1)*3,4+Math.floor(i/3)*3);const f=foes[foes.length-1];f.phase=.4+i;damageEnemy(f,999,2,i%2?2:0);}},inspectBoss:(close=false)=>{manualTestClock=true;clearBattle();heroMotion.reset();hero.position.set(-2.5,0,126);hero.rotation.y=Math.PI;spawnClock=60;invuln=999;bossSpawned=true;spawn(1,132,true);spawn(-3,132);spawn(5,132);for(const f of foes){f.root.rotation.y=Math.PI;f.cooldown=60;crowdMotions.get(f.root)!.sample('idle',0);}announceTime=0;updateHUD();shadowClock=0;visual(0);camera.position.set(close?9:5.5,close?5:11,close?123:110);camera.setTarget(new Vector3(1,close?1.6:0,132));},inspectEnvironment:(z=0,close=false)=>{manualTestClock=true;clearBattle();heroMotion.reset();hero.position.set(0,0,z);shadowClock=0;visual(0);camera.position.set(close?10:17,close?7:14,z+(close?-8:-18));camera.setTarget(new Vector3(close?3:0,0,z+5));return scene.meshes.filter(m=>['dark meltwater in wheel ruts','thawed earth at object feet'].includes(m.material?.name??'')).map(m=>({name:m.material!.name,vertexAlpha:m.hasVertexAlpha,upward:m.getVerticesData(VertexBuffer.NormalKind)!.filter((_,i)=>i%3===1).every(y=>y>.99),vertices:m.getTotalVertices()}));},snapshot:()=>({bossParts:foes.filter(f=>f.boss).flatMap(f=>(crowdMotions.get(f.root)?.meshes??[]).map(m=>({vertices:m.getTotalVertices(),material:m.material?.name,frame:m.instancedBuffers.bakedVertexAnimationSettingsInstanced.x,enabled:m.isEnabled()}))),falls:foes.filter(f=>f.dead).map(f=>({clip:f.deathClip,age:f.deathAge,duration:f.deathDuration,rootZ:f.root.rotation.z,scale:f.root.scaling.x,landed:f.landed})),bossSpawned,bossHP:foes.find(f=>f.boss)?.hp,enemyCount:foes.length,enemyHP:foes.map(f=>f.hp),heights:foes.map(f=>f.root.position.y),musouTime,attackTime:chain.active?.time??null})}});}
