import {BattleModel,WORLD} from './battle.mjs';
import {FILES,HERO_PARTS,ENEMY_PARTS,assetURL} from './assets.mjs';
import {thrustPose,sweepPose} from '../combat/hero-rig.mjs';
import {enemyArm,closedGrip} from '../combat/enemy-arm.mjs';
import {enemyWeapon} from '../combat/enemy-weapon.mjs';
import {enemyBodyPose,ENEMY_BODY_BOXES,ENEMY_LEGS} from '../combat/enemy-body.mjs';
const $=s=>document.querySelector(s),reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
let battle,scene,started=false,noticeUntil=0,audio;
const input={x:0,y:0,attack:false,musou:false,dash:false};let stickId=null,stickCenter;
const held=new Set(),uiPointers=new Map();
function clearInput(){scene?.input.keyboard.resetKeys();held.clear();uiPointers.clear();input.x=input.y=0;input.attack=input.musou=input.dash=false;stickId=null;$('#thumb').style.transform='';}
function sound(hit=false){if(!$('#sound').checked)return;try{audio??=new AudioContext();audio.resume().catch(()=>{});const o=audio.createOscillator(),g=audio.createGain(),t=audio.currentTime;o.type=hit?'triangle':'sawtooth';o.frequency.setValueAtTime(hit?190:95,t);o.frequency.exponentialRampToValueAtTime(40,t+.11);g.gain.setValueAtTime(.035,t);g.gain.exponentialRampToValueAtTime(.001,t+.15);o.connect(g);g.connect(audio.destination);o.start(t);o.stop(t+.16);o.onended=()=>{o.disconnect();g.disconnect();};}catch{}}
function notice(text,seconds=3){$('#notice').textContent=text;$('#notice').style.opacity=1;noticeUntil=(battle?.time??0)+seconds;}
function pause(value=true){if(!started||battle.result)return;battle.paused=value;clearInput();$('#pause-menu').hidden=!value;$('#pause').textContent=value?'已暫停':'暫停';if(value)$('#resume').focus();}
function menu(){started=false;clearInput();$('#hud').hidden=$('#controls').hidden=$('#hint').hidden=true;$('#boss-hud').hidden=true;$('#pause-menu').hidden=$('#result').hidden=true;$('#menu').hidden=false;$('#notice').textContent='';$('#combo').textContent='';}
function start(cycleOverride){battle=new BattleModel({difficulty:$('#difficulty').value,cycle:cycleOverride??Number($('#cycle').value)});started=true;clearInput();scene.resetActors();$('#menu').hidden=$('#pause-menu').hidden=$('#result').hidden=true;$('#hud').hidden=$('#controls').hidden=$('#hint').hidden=false;$('#pause').textContent='暫停';notice('六文已備，此戰未終。赤備，隨我破陣！',4);scene.accumulator=0;scene.cameras.main.stopFollow();scene.cameras.main.centerOn(battle.hero.x,battle.hero.y-70);refreshHUD();$('#stage canvas')?.focus();}
function end(){clearInput();$('#result').hidden=false;const win=battle.result==='victory';$('#result-kicker').textContent=win?'六文不渡 · 赤槍開路':'英魂未滅 · 再赴修羅';$('#result-title').textContent=win?'燼關已破':'此戰未終';$('#result-copy').textContent=win?'黑金之魂退散。赤備越過燼關，下一場決鬥仍在等候。':battle.hero.hp<=0?'幸村力盡。借疾風避開蓄刀，積滿無雙再殺出重圍。':'赤備軍旗失守。留在軍旗附近，清除圍攻的鬼軍。';$('#results').innerHTML=`<dt>用時</dt><dd>${clock(battle.time)}</dd><dt>擊破</dt><dd>${battle.kills} 斬</dd><dt>最高連擊</dt><dd>${battle.bestCombo}</dd><dt>赤備擊破</dt><dd>${battle.stats.allyKills}</dd><dt>無雙發動</dt><dd>${battle.stats.musou}</dd>`;$('#next-cycle').hidden=!win||battle.cycle>=6;$('#retry').focus();}
const clock=s=>`${String(Math.floor(s/60)).padStart(2,'0')}:${String(Math.floor(s)%60).padStart(2,'0')}`;
function refreshHUD(){if(!battle)return;const h=battle.hero;$('#hp').max=h.maxHP;$('#hp').value=h.hp;$('#hp-text').textContent=`${Math.ceil(h.hp)} / ${h.maxHP}`;$('#energy').value=h.energy;$('#kills').textContent=`${battle.kills} 斬`;$('#clock').textContent=clock(battle.time);$('#combo').textContent=battle.combo>1?`${battle.combo} 連擊`:'';$('#chapter').textContent=['一 · 燼關破陣','二 · 赤備推進','三 · 黑金決戰'][battle.stage];
 const escortNear=Math.hypot(h.x-battle.banner.x,h.y-battle.banner.y)<230;
 $('#objective').textContent=battle.stage===0?`擊破 ${Math.min(36,battle.kills)} / 36 · 守住 ${Math.min(45,Math.floor(battle.stageTime))} / 45 秒`:battle.stage===1?`${escortNear?'守住軍旗，向東推進':'返回軍旗附近，帶領赤備'} · 軍旗 ${Math.ceil(battle.banner.hp)}`:'擊倒家康 · 紅圈落斬前衝刺離開';
 $('#progress').value=battle.stage===0?Math.min(battle.kills/36,battle.stageTime/45):battle.stage===1?battle.banner.progress:1-(battle.boss?.hp/battle.boss?.maxHP||0);
 $('#boss-hud').hidden=battle.stage!==2||!!battle.result;$('#boss-hp').value=battle.boss?battle.boss.hp/battle.boss.maxHP:1;$('#boss-phase').textContent=battle.boss?.phase===2?'修羅化 · 二連落斬':'金甲壓陣 · 注意落斬';$('#musou').classList.toggle('ready',h.energy>=100);$('#musou-state').textContent=h.energy>=100?'已滿 · 破陣':`${Math.floor(h.energy)} / 100`;$('#musou').disabled=h.energy<100;$('#dash').style.opacity=h.dashCooldown>0?'.55':'1';$('#command').innerHTML=(battle.formation==='follow'?'集合':'突進')+' <kbd>R</kbd>';$('#notice').style.opacity=battle.time>noticeUntil?0:1;
}
const rotate=(x,y,degrees)=>{const a=degrees*Math.PI/180;return {x:x*Math.cos(a)-y*Math.sin(a),y:x*Math.sin(a)+y*Math.cos(a)};};
function gait(transforms,joints,phase,enemy=false){for(const [index,side] of Object.keys(joints).entries()){const j=joints[side],p=phase+index*Math.PI,s=Math.sin(p),angle=s*7,shinAngle=-Math.max(0,-s)*11,hip=enemy?j.hip:{x:j.hip[0],y:j.hip[1]},k=enemy?j.knee:{x:j.knee[0],y:j.knee[1]},a=enemy?j.ankle:{x:j.ankle[0],y:j.ankle[1]},v=rotate(k.x-hip.x,k.y-hip.y,angle),knee={x:hip.x+v.x,y:hip.y+v.y},w=rotate(a.x-k.x,a.y-k.y,shinAngle),ankle={x:knee.x+w.x,y:knee.y+w.y};for(const [suffix,point,turn] of [['Thigh',hip,angle],['Shin',knee,shinAngle],['Foot',ankle,-s*3]]){const t=transforms[side+suffix];t.point=enemy?point:[point.x,point.y];t.angle=turn;}}}
class BattleScene extends Phaser.Scene{
 constructor(){super('battle');this.views=new Map();this.effects=[];this.accumulator=0;}
 preload(){
  for(const file of FILES){if(file.endsWith('.json'))this.load.json(file,assetURL(file));else if(file==='ghost-warrior.webp')this.load.spritesheet(file,assetURL(file),{frameWidth:768,frameHeight:512,endFrame:11});else this.load.image(file,assetURL(file));}
  this.load.on('progress',p=>$('#loading').textContent=`集結赤備… ${Math.round(p*100)}%`);this.load.on('loaderror',f=>{this.failed=true;$('#loading').textContent='素材載入失敗，請重新開啟或重新整理。';});
 }
 create(){
  if(this.failed)return;scene=this;this.guard=this.cache.json.get('guard-rig.json');this.rig=this.cache.json.get('thrust-rig.json');this.enemyRig=this.cache.json.get('enemy-rig.json');
  this.add.image(640,450,'arena.webp').setDisplaySize(1280,900).setTint(0xb1aeb0).setDepth(-100);
  this.heroMark=this.add.text(0,0,'▼ 幸村',{fontFamily:'serif',fontSize:'12px',color:'#f2cf86',stroke:'#121515',strokeThickness:3}).setOrigin(.5).setVisible(false).setDepth(1500);
  const shade=this.add.graphics().setDepth(-99);shade.fillStyle(0x08101c,.12);shade.fillRect(0,0,1280,900);
  this.marks=this.add.graphics().setDepth(2);this.fx=this.add.graphics().setDepth(2000);this.shadows=this.add.graphics().setDepth(1);this.flag=this.add.graphics().setDepth(300);this.name=this.add.text(0,0,'家康',{fontFamily:'serif',fontSize:'18px',color:'#f8d68a',stroke:'#110e0a',strokeThickness:4}).setOrigin(.5).setVisible(false).setDepth(1500);
  this.cameras.main.setBounds(0,0,1280,900);this.scale.on('resize',()=>this.resizeCamera());this.resizeCamera();
  this.keys=this.input.keyboard.addKeys('W,A,S,D,UP,DOWN,LEFT,RIGHT,J,K,SPACE,R,ESC');this.input.keyboard.on('keydown-R',e=>{if(!e.repeat&&started&&!battle.paused)battle.command();});this.input.keyboard.on('keydown-ESC',e=>{if(!e.repeat&&started)pause(!battle.paused);});
  this.input.on('pointerdown',p=>{if(started&&!battle.paused&&!battle.result&&p.wasTouch===false)input.attack=true;});this.input.on('pointerup',()=>input.attack=false);this.input.on('gameout',()=>input.attack=false);
  $('#start').disabled=false;$('#start').textContent='再赴修羅 ↗';$('#loading').textContent='赤備已集結';
  window.sanadaBattle={snapshot:()=>battle?.snapshot()??{ready:true,menu:true},engine:Phaser.VERSION};
  if(new URLSearchParams(location.search).get('test')==='1')window.sanadaBattle.test={get model(){return battle;},advance:(ms,controls={})=>{for(let t=0;t<ms;t+=1000/60)battle.step(1/60,controls);this.handleBattleEvents();this.renderBattle();refreshHUD();}};
 }
 resizeCamera(){const {width:w,height:h}=this.scale;this.cameras.main.setZoom(w<h?.72:Math.max(w/1280,h/900));}
 resetActors(){for(const v of this.views.values())v.container.destroy();this.views.clear();this.effects=[];this.name.setVisible(false);this.heroMark.setVisible(false);}
 heroView(key,ally=false){let v=this.views.get(key);if(v)return v;const container=this.add.container(0,0),parts={};for(const name of HERO_PARTS){const l=this.rig.layers[name];parts[name]=this.add.image(0,0,`hero-${name}.webp`).setOrigin((l.pivot[0]-l.box[0])/l.size[0],(l.pivot[1]-l.box[1])/l.size[1]).setDisplaySize(...l.size);container.add(parts[name]);if(ally)parts[name].setTint(0x859f99);}
  const weapon=this.add.image(0,0,'guard-yari.webp');container.add(weapon);container.bringToTop(parts.rearHand);container.bringToTop(parts.frontHand);v={container,parts,weapon,kind:'hero',scale:ally?.16:.30};this.views.set(key,v);return v;
 }
 renderHero(a,key,ally=false){const v=this.heroView(key,ally),attack=ally?(a.attack>0?{kind:'thrust',age:.32-a.attack,duration:.32}:null):a.attack,frame=attack?Math.min(attack.kind==='sweep'?31:35,attack.age/attack.duration*(attack.kind==='sweep'?31:35)):0,p=attack?.kind==='sweep'?sweepPose(frame,this.guard,this.rig):thrustPose(frame,this.guard,this.rig);
  if((ally||a.moving)&&!attack)gait(p.transforms,this.rig.legs,a.walk);for(const [n,im] of Object.entries(v.parts)){const t=p.transforms[n];im.setPosition(t.point[0]-430,t.point[1]-520).setAngle(t.angle);}
  const w=p.weapon;v.weapon.setOrigin(w.originX,w.originY).setDisplaySize(w.width,w.height).setPosition(w.rear.x-35-430,w.rear.y-90-520).setAngle(w.angle);
  const face=ally?a.face:a.face.x>=0?1:-1;v.container.setPosition(a.x,a.y).setScale(v.scale*face,v.scale).setDepth(a.y+2).setAlpha(!ally&&a.invulnerable>0?.78+.22*Math.sin(battle.time*35):1);
  this.shadows.fillStyle(0x02090e,ally?.28:.55);this.shadows.fillEllipse(a.x,a.y+3,ally?55:95,ally?14:21);if(!ally){this.shadows.lineStyle(2,0xd9ad68,.7);this.shadows.strokeEllipse(a.x,a.y+4,85,23);}return v;
 }
 enemyView(e){let v=this.views.get(e.id);if(v)return v;const container=this.add.container(0,0),parts={};for(const name of ENEMY_PARTS){const [x,y,r,b]=ENEMY_BODY_BOXES[name];parts[name]=this.add.image(0,0,`enemy-body-${name}.webp`).setDisplaySize(r-x,b-y);container.add(parts[name]);}
  for(const n of ['upper','fore','katana','grip']){const p=this.enemyRig.parts[n];parts[n]=this.add.image(0,0,`enemy-${n}.webp`).setOrigin(p.pivot[0]/p.size[0],p.pivot[1]/p.size[1]).setDisplaySize(...p.size);container.add(parts[n]);}
  container.moveBelow(parts.upper,parts.torso);const corpse=this.add.sprite(0,0,'ghost-warrior.webp').setOrigin(.5,690/768).setDisplaySize(1152,768).setVisible(false);container.add(corpse);
  if(e.kind==='boss')for(const im of Object.values(parts))im.setTint(0xd6ae58);else if(e.kind==='elite')for(const im of Object.values(parts))im.setTint(0xccb1a6);v={container,parts,corpse,kind:'enemy',scale:e.kind==='boss'?.26:e.kind==='elite'?.17:.145};this.views.set(e.id,v);return v;
 }
 renderEnemy(e){const v=this.enemyView(e),dead=e.hp<=0;v.container.setPosition(e.x,e.y).setScale(v.scale*(e.face<0?1:-1),v.scale).setDepth(e.y).setAlpha(dead?Math.min(1,(1.7-e.dead)/.5):1);v.corpse.setVisible(dead);for(const im of Object.values(v.parts))im.setVisible(!dead);
  if(dead){const pose=e.dead<.15?1:e.dead<.25?2:e.dead<.34?3:e.dead<.44?4:e.dead<.56?5:e.dead<.68?6:e.dead<.82?7:e.dead<1?8:9;v.corpse.setFrame(pose);const arm=enemyArm({pose,alpha:1},e.dead*1000,true,this.enemyRig),w=enemyWeapon({pose,alpha:1},e.dead*1000,true,this.enemyRig);for(const [n,p,angle] of [['upper',arm.shoulder,arm.upperAngle],['fore',arm.elbow,arm.foreAngle],['katana',w.grip,w.angle]])v.parts[n].setVisible(true).setPosition(p.x-576,p.y-690).setAngle(angle);v.container.bringToTop(v.parts.fore);return;}
  const state={phase:'guard',pose:0,alpha:1,intent:e.windup>0?'windup':null,intentAge:(.75-e.windup)*1000},body=enemyBodyPose(state,this.enemyRig);if(e.windup<=0&&e.stun<=0)gait(body.transforms,ENEMY_LEGS,e.walk,true);
  for(const n of ENEMY_PARTS){const im=v.parts[n],[x,y,r,b]=ENEMY_BODY_BOXES[n],t=body.transforms[n];im.setOrigin((t.pivot.x-x)/(r-x),(t.pivot.y-y)/(b-y)).setPosition(t.point.x-576,t.point.y-690).setAngle(t.angle);}
  const arm=enemyArm(state,0,false,this.enemyRig),grip=closedGrip(arm,this.enemyRig);for(const [n,p,angle] of [['upper',arm.shoulder,arm.upperAngle],['fore',arm.elbow,arm.foreAngle],['grip',arm.wrist,arm.handAngle],['katana',grip.grip,grip.angle]])v.parts[n].setPosition(p.x-576,p.y-690).setAngle(angle);
  this.shadows.fillStyle(0x03080b,.42);this.shadows.fillEllipse(e.x,e.y+3,e.kind==='boss'?130:65,e.kind==='boss'?28:14);
  if(e.windup>0&&e.kind!=='boss'){this.marks.lineStyle(3,0xffcf71,.9);this.marks.strokeEllipse(e.x,e.y,75,32);}
  if(e.kind==='elite'){this.marks.lineStyle(2,0xf5a86b,.8);this.marks.strokeEllipse(e.x,e.y,58,20);}if(e.kind==='boss'){this.name.setVisible(true).setPosition(e.x,e.y-175);this.marks.lineStyle(3,0xeac467,.9);this.marks.strokeEllipse(e.x,e.y+4,120,40);}
 }
 handleBattleEvents(){for(const event of battle.events){
  const recent=battle.time-event.at<.15;
  if(!recent&&['hit','impact','swing','dash','blast','heal','ally-strike','hurt'].includes(event.type))continue;
  if(event.type==='hit'){this.effects.push({...event,life:.2,total:.2});}
  if(event.type==='impact'){this.effects.push({...event,life:event.kind==='musou'?.65:.22,total:event.kind==='musou'?.65:.22});if(event.hits){sound(true);if(!reduced)this.cameras.main.shake(event.kind==='musou'?140:50,event.kind==='musou'?.004:.0018);}}
  if(event.type==='swing')sound();if(['dash','blast','heal','ally-strike'].includes(event.type))this.effects.push({...event,life:event.type==='blast'?.35:.22,total:event.type==='blast'?.35:.22});
  if(event.type==='hurt'&&!reduced)this.cameras.main.flash(85,115,10,15,false);
  if(event.type==='escort')notice('赤備，推進！守住軍旗，殺向東側本陣。',4);
  if(event.type==='boss')notice('家康現身。六文無雙已滿！',4);
  if(event.type==='rage')notice('家康修羅化 · 留意二連落斬！',3);
  if(event.type==='command')notice(event.mode==='follow'?'赤備，歸陣護旗！':'赤備，向近敵突進！',1.5);
  if(event.type==='victory'||event.type==='defeat')end();
 }battle.events=[];}
 renderBattle(){if(!battle)return;this.shadows.clear();this.marks.clear();this.flag.clear();const used=new Set(['hero']);const heroView=this.renderHero(battle.hero,'hero');this.heroMark.setVisible(true).setPosition(battle.hero.x,battle.hero.y-135);
  if(this.following!==heroView.container){this.cameras.main.startFollow(heroView.container,false,.08,.08,0,65);this.following=heroView.container;}
  for(const a of battle.allies){used.add('ally'+a.id);this.renderHero(a,'ally'+a.id,true);}
  for(const e of battle.enemies){used.add(e.id);this.renderEnemy(e);}for(const [key,v] of this.views)if(!used.has(key)){v.container.destroy();this.views.delete(key);}
  if(battle.stage!==2||battle.boss?.hp<=0)this.name.setVisible(false);
  const flag=battle.banner,g=this.flag;g.setDepth(flag.y+1);if(battle.stage<=1){this.marks.lineStyle(2,0xb4d4ca,battle.stage===1?.35:.12);this.marks.strokeEllipse(flag.x,flag.y,210,80);g.lineStyle(4,0x9d8562,1);g.lineBetween(flag.x,flag.y,flag.x,flag.y-120);g.fillStyle(0x982e38,.96);g.fillTriangle(flag.x,flag.y-120,flag.x+55,flag.y-110,flag.x,flag.y-55);for(let i=0;i<6;i++){g.fillStyle(0xe5cf8b);g.fillCircle(flag.x+12+i%3*10,flag.y-105+Math.floor(i/3)*12,3);}g.fillStyle(0x282424);g.fillRect(flag.x-30,flag.y+15,60,4);g.fillStyle(0xa9c8a6);g.fillRect(flag.x-30,flag.y+15,60*flag.hp/flag.maxHP,4);}
  if(battle.stage===1){const off=Math.hypot(battle.hero.x-flag.x,battle.hero.y-flag.y)>220;if(off){const v={x:flag.x-battle.hero.x,y:flag.y-battle.hero.y},n=Math.hypot(v.x,v.y),x=battle.hero.x+v.x/n*115,y=battle.hero.y+v.y/n*115;this.marks.lineStyle(4,0xd5c081,.9);this.marks.lineBetween(x-v.x/n*20,y-v.y/n*20,x,y);this.marks.strokeCircle(x,y,8);}}
  for(const z of battle.hazards){const t=Math.min(1,z.age/z.delay);this.marks.fillStyle(z.fired?0xffb45d:0x9d2534,z.fired?.35:.10+t*.13);this.marks.fillCircle(z.x,z.y,z.radius);this.marks.lineStyle(3,z.fired?0xffde99:0xff6755,.95);this.marks.strokeCircle(z.x,z.y,z.radius);this.marks.lineStyle(2,0xffaf71,.8);this.marks.strokeCircle(z.x,z.y,z.radius*t);}
  for(const p of battle.pickups){this.marks.fillStyle(0x70e9cc,.15);this.marks.fillCircle(p.x,p.y-12,18);this.marks.fillStyle(0xa5f6d8,.9);this.marks.fillEllipse(p.x,p.y-12+Math.sin(battle.time*4+p.id)*3,10,20);}
 }
 drawEffects(dt){const g=this.fx;g.clear();if(!battle.paused&&!battle.result)for(const e of this.effects)e.life-=dt;this.effects=this.effects.filter(e=>e.life>0);for(const e of this.effects){const t=1-e.life/e.total,alpha=1-t;
   if(e.type==='hit'){g.lineStyle(2,e.source==='ally'?0xead5a1:0xffd89b,alpha);for(let i=0;i<5;i++){const a=i*1.4;g.lineBetween(e.x+Math.cos(a)*8,e.y-35+Math.sin(a)*8,e.x+Math.cos(a)*(12+30*t),e.y-35+Math.sin(a)*(12+30*t));}}
   if(e.type==='impact'){const musou=e.kind==='musou',r=musou?80+240*t:50+140*t;g.lineStyle(musou?8:5,musou?0xffb25e:0xf2c5a1,alpha);if(musou){g.strokeEllipse(e.x,e.y,r*2,r);g.lineStyle(2,0xf44838,alpha);g.strokeEllipse(e.x,e.y,r*2.2,r*1.2);for(let i=0;i<6;i++){const a=i*Math.PI/3+t*2;g.fillStyle(0xf5c87c,alpha);g.fillCircle(e.x+Math.cos(a)*r*.7,e.y+Math.sin(a)*r*.35-30,6);}}else{const a=Math.atan2(e.face.y*.6,e.face.x);g.beginPath();g.arc(e.x,e.y-32,r,a-.9+t*.2,a+.9+t*.2);g.strokePath();}}
   if(e.type==='ally-strike'){g.lineStyle(2,0xe9bf99,alpha*.65);g.lineBetween(e.x,e.y-30,e.to.x,e.to.y-30);}
   if(e.type==='dash'){g.lineStyle(3,0xb8e6df,alpha*.5);g.strokeEllipse(e.x,e.y,30+t*80,12+t*20);}
   if(e.type==='blast'){g.lineStyle(6,0xe7b377,alpha);g.strokeCircle(e.x,e.y,e.radius*(.5+t*.6));}
   if(e.type==='heal'){g.lineStyle(3,0x9ff4cd,alpha);g.strokeEllipse(e.x,e.y-20-t*40,45,15);}
  }
  if(!reduced){g.fillStyle(0xe6ac6b,.3);for(let i=0;i<18;i++){const x=(i*173+battle.time*12)%1280,y=(i*137-battle.time*24)%900;g.fillCircle(x,(y+900)%900,1.2);}}
 }
 update(_time,delta){if(!started||!battle)return;const dt=Math.min(delta/1000,.1);if(!battle.paused&&!battle.result){this.accumulator+=dt;while(this.accumulator>=1/60){const keys=this.keys,controls={x:input.x+(keys.D.isDown||keys.RIGHT.isDown?1:0)-(keys.A.isDown||keys.LEFT.isDown?1:0),y:input.y+(keys.S.isDown||keys.DOWN.isDown?1:0)-(keys.W.isDown||keys.UP.isDown?1:0),attack:input.attack||held.has('attack')||keys.J.isDown,musou:input.musou||held.has('musou')||keys.K.isDown,dash:input.dash||held.has('dash')||keys.SPACE.isDown};battle.step(1/60,controls);this.accumulator-=1/60;}this.handleBattleEvents();}else this.accumulator=0;this.renderBattle();this.drawEffects(dt);refreshHUD();}
}
$('#start').onclick=()=>start();$('#pause').onclick=()=>pause();$('#resume').onclick=()=>pause(false);$('#restart-pause').onclick=()=>start(battle.cycle);$('#quit').onclick=menu;$('#retry').onclick=()=>start(battle.cycle);$('#back').onclick=menu;$('#next-cycle').onclick=()=>start(battle.cycle+1);$('#command').onclick=()=>{if(started)battle.command();};
for(const id of ['attack','dash','musou']){const el=$('#'+id);el.addEventListener('pointerdown',e=>{e.preventDefault();el.setPointerCapture(e.pointerId);uiPointers.set(e.pointerId,id);held.add(id);});const release=e=>{uiPointers.delete(e.pointerId);if(![...uiPointers.values()].includes(id))held.delete(id);};for(const name of ['pointerup','pointercancel','lostpointercapture'])el.addEventListener(name,release);}
$('#stick').addEventListener('pointerdown',e=>{if(stickId!==null)return;e.preventDefault();stickId=e.pointerId;e.currentTarget.setPointerCapture(e.pointerId);const r=e.currentTarget.getBoundingClientRect();stickCenter={x:r.left+r.width/2,y:r.top+r.height/2};});
$('#stick').addEventListener('pointermove',e=>{if(e.pointerId!==stickId)return;const x=e.clientX-stickCenter.x,y=e.clientY-stickCenter.y,d=Math.max(30,Math.hypot(x,y));input.x=x/d;input.y=y/d;$('#thumb').style.transform=`translate(${input.x*28}px,${input.y*28}px)`;});
for(const name of ['pointerup','pointercancel','lostpointercapture'])$('#stick').addEventListener(name,e=>{if(e.pointerId!==stickId)return;stickId=null;input.x=input.y=0;$('#thumb').style.transform='';});
document.addEventListener('visibilitychange',()=>{if(document.hidden)pause(true);});window.addEventListener('blur',()=>pause(true));
new Phaser.Game({type:Phaser.AUTO,parent:'stage',backgroundColor:'#11191d',scale:{mode:Phaser.Scale.RESIZE,width:innerWidth,height:innerHeight},render:{antialias:true,roundPixels:false},input:{activePointers:4},scene:BattleScene,audio:{noAudio:true}});
