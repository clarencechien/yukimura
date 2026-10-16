import {duelContactPose,bladePointToWorld} from './duel-contact.mjs';
import {sharedHeroPose} from './hero-rig.mjs';
import {enemyBinding,enemyTexture} from './duel-poses.mjs';
import {CombatState} from './combat-state.mjs';
import {enemyPointToWorld} from './enemy-weapon.mjs';
const $=s=>document.querySelector(s);
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
let scene,audioContext;
function tone(hit=false){
  if(!$('#sound').checked)return;
  audioContext??=new (window.AudioContext||window.webkitAudioContext)();
  audioContext.resume().catch(()=>{});
  const at=audioContext.currentTime,osc=audioContext.createOscillator(),gain=audioContext.createGain();
  osc.type=hit?'triangle':'sine';osc.frequency.setValueAtTime(hit?540:160,at);osc.frequency.exponentialRampToValueAtTime(hit?80:60,at+.12);
  gain.gain.setValueAtTime(.0001,at);gain.gain.exponentialRampToValueAtTime(hit?.13:.07,at+.006);gain.gain.exponentialRampToValueAtTime(.0001,at+.18);
  osc.connect(gain);gain.connect(audioContext.destination);osc.start(at);osc.stop(at+.2);osc.onended=()=>{osc.disconnect();gain.disconnect();};
}
class Battle extends Phaser.Scene {
  constructor(){super('battle');}
  preload(){
    for(const part of ['upper','fore','relax','open'])this.load.image('enemy-'+part,`enemy-${part}.webp`);
    this.load.json('enemyRig','enemy-rig.json');this.load.image('enemyKatana','enemy-katana.webp');this.load.image('enemyGrip','enemy-grip.webp');
    this.load.image('arena','arena.webp');this.load.json('track','shared-spear-track.json');
    this.hd=innerWidth>=900;
    this.load.json('duelArt','duel-art.json');
    this.load.spritesheet('enemyDuel',`enemy-duel${this.hd?'-hd':''}.webp`,{frameWidth:this.hd?1152:768,frameHeight:this.hd?768:512,endFrame:2});
    this.load.json('guardRig','guard-rig.json');
    this.load.json('thrustRig','thrust-rig.json');
    for(const part of ['rearFoot','frontFoot','rearShin','frontShin','rearThigh','frontThigh','lower','torso','rearUpper','rearFore','rearHand','frontUpper','frontFore','frontHand'])this.load.image('hero-'+part,`hero-${part}${this.hd?'-hd':''}.webp`);
    this.load.image('guardYari',`guard-yari${this.hd?'-hd':''}.webp`);
    this.load.json('sweepTrack','shared-sweep-track.json');
    this.load.spritesheet('enemyLow',`enemy-low${this.hd?'-hd':''}.webp`,{frameWidth:this.hd?1152:768,frameHeight:this.hd?768:512,endFrame:3});
    this.load.spritesheet('warrior',`ghost-warrior${this.hd?'-hd':''}.webp`,{frameWidth:this.hd?1152:768,frameHeight:this.hd?768:512,endFrame:11});
    this.load.on('progress',p=>$('#loading').textContent=`正在載入赤甲與燼關… ${Math.round(p*100)}%`);
    this.load.on('loaderror',()=>{this.failed=true;$('#loading').textContent='素材載入失敗，請重新整理。';});
  }
  create(){
    if(this.failed)return;
    scene=this;this.track=this.cache.json.get('track');this.state=new CombatState(this.track,e=>this.onCombat(e),this.cache.json.get('sweepTrack'));
    this.add.image(600,375,'arena').setDisplaySize(1200,750).setTint(0xb8b8bd);
    const shade=this.add.graphics();shade.fillStyle(0x080d14,.18);shade.fillRect(0,0,1200,750);
    // Fixed contact patches under actual planted feet, plus a softer body shadow.
    const shadow=this.add.graphics();for(let i=5;i>0;i--){shadow.fillStyle(0x060708,.035);shadow.fillEllipse(453,628,375+i*12,32+i*7);}
    shadow.fillStyle(0x050607,.5);shadow.fillEllipse(263,648,62,17);shadow.fillEllipse(661,606,91,18);
    this.hero=this.add.image(35,90,'hero-lower');
    this.guardRig=this.cache.json.get('guardRig');this.thrustRig=this.cache.json.get('thrustRig');
    this.heroParts={};
    for(const part of ['rearFoot','frontFoot','rearShin','frontShin','rearThigh','frontThigh'])this.heroParts[part]=this.add.image(0,0,'hero-'+part).setVisible(false);
    this.children.bringToTop(this.hero);
    this.heroParts.lower=this.hero;
    for(const part of ['rearUpper','frontUpper','torso','rearFore','frontFore'])this.heroParts[part]=this.add.image(0,0,'hero-'+part).setVisible(false);
    this.guardYari=this.add.image(0,0,'guardYari').setVisible(false);
    this.guardHands=[0,1].map(i=>this.add.image(0,0,'hero-'+(i===0?'rear':'front')+'Hand').setVisible(false));
    this.pedestal=this.add.graphics();this.seal=this.add.container(970,334);this.sealArt=this.add.graphics();this.seal.add(this.sealArt);this.drawSeal();
    this.enemyShadow=this.add.graphics();
    this.enemyRig=this.cache.json.get('enemyRig');this.enemyRig.duelBindings=this.cache.json.get('duelArt').enemy.bindings;
    const component=(key,part)=>this.add.image(0,0,key).setOrigin(part.pivot[0]/part.size[0],part.pivot[1]/part.size[1]).setDisplaySize(part.size[0]*.6,part.size[1]*.6);
    this.enemyKatana=component('enemyKatana',this.enemyRig.parts.katana);
    this.enemyUpper=component('enemy-upper',this.enemyRig.parts.upper);this.enemyFore=component('enemy-fore',this.enemyRig.parts.fore);
    this.enemySprite=this.add.sprite(970,574,'warrior',0).setOrigin(.5,690/768).setDisplaySize(1152*.6,768*.6);
    // The shared cuff must cover the painted socket opening on the body.
    this.enemyGrip=component('enemyGrip',this.enemyRig.parts.grip);
    this.flash=this.add.circle(0,0,12,0xffd69b).setBlendMode(Phaser.BlendModes.ADD).setAlpha(0);
    const dot=this.make.graphics({x:0,y:0,add:false});dot.fillStyle(0xffffff);dot.fillCircle(4,4,4);dot.generateTexture('spark',8,8);dot.destroy();
    this.sparks=this.add.particles(0,0,'spark',{emitting:false,lifespan:{min:140,max:380},speed:{min:80,max:290},angle:{min:150,max:370},gravityY:340,scale:{start:.55,end:0},alpha:{start:1,end:0},tint:[0xffe5b3,0xf99e5b,0xbc3834],blendMode:'ADD',maxParticles:80});
    this.ash=this.add.particles(0,0,'spark',{emitting:!reduced,x:{min:0,max:1200},y:760,speedY:{min:-30,max:-90},speedX:{min:5,max:35},lifespan:4000,frequency:180,quantity:1,scale:{start:.2,end:0},alpha:{start:.25,end:0},tint:0xef9c69,blendMode:'ADD',maxParticles:30});
    this.duelMarks=this.add.graphics();this.trail=this.add.graphics();this.debug=this.add.graphics();
    this.input.keyboard.on('keydown-J',event=>{if(event.repeat||/INPUT|SELECT|BUTTON/.test(document.activeElement?.tagName))return;this.attack();});
    this.input.keyboard.on('keydown-L',event=>{if(event.repeat||/INPUT|SELECT|BUTTON/.test(document.activeElement?.tagName))return;this.defend();});
    this.input.keyboard.on('keydown-K',event=>{if(event.repeat||/INPUT|SELECT|BUTTON/.test(document.activeElement?.tagName))return;this.attack('sweep');});
    this.input.keyboard.on('keydown-SPACE',event=>{if(/INPUT|SELECT|BUTTON/.test(document.activeElement?.tagName))return;event.preventDefault();this.attack();});
    for(const id of ['attack','sweep','guard','duel','pause','reset','range','target'])$('#'+id).disabled=false;
    $('#loading').style.display='none';this.refreshUI();
    window.yariCombat={snapshot:()=>({ready:true,contact:this.contactPose,lastClash:this.lastClash??null,heroArt:this.heroArt,heroParts:Object.fromEntries(Object.entries(this.heroParts).map(([n,p])=>[n,{x:p.x,y:p.y,width:p.displayWidth,height:p.displayHeight,angle:p.angle,originX:p.originX,originY:p.originY,visible:p.visible,texture:p.texture.key,order:this.children.getIndex(p)}])),heroWeapon:{visible:this.guardYari.visible,texture:this.guardYari.texture.key,width:this.guardYari.displayWidth,height:this.guardYari.displayHeight,x:this.guardYari.x,y:this.guardYari.y,angle:this.guardYari.angle,originX:this.guardYari.originX,originY:this.guardYari.originY,pose:this.guardWeaponPose,hands:this.guardHands.map(h=>({visible:h.visible,x:h.x,y:h.y,frame:h.frame.name,texture:h.texture.key,width:h.displayWidth,height:h.displayHeight,angle:h.angle,originX:h.originX,originY:h.originY,order:this.children.getIndex(h)})),order:this.children.getIndex(this.guardYari),bodyOrder:this.children.getIndex(this.hero)},armOrder:{body:this.children.getIndex(this.enemySprite),upper:this.children.getIndex(this.enemyUpper),fore:this.children.getIndex(this.enemyFore),hand:this.children.getIndex(this.enemyGrip)},duel:{enabled:this.state.duel.enabled,stage:this.state.duel.stage,age:this.state.duel.age,playerHP:this.state.duel.playerHP,guardPose:this.state.duel.guardPose,recoveryFrom:this.state.duel.recoveryFrom,guard:this.state.duel.guard,blockAge:this.state.duel.blockAge,guardAtBlock:this.state.duel.guardAtBlock,cooldown:this.state.duel.cooldown,blocks:this.state.duel.blocks,result:this.state.duel.result},engine:Phaser.VERSION,phase:this.state.phase,frame:this.state.frame,hp:this.state.hp,hits:this.state.hits,swings:this.state.swings,paused:this.state.paused,freeze:this.state.freeze,range:this.state.range,targetKind:this.state.targetKind,flashAlpha:this.flash.alpha,enemyAge:this.state.enemyAge,enemy:this.state.enemy,enemyFrame:this.enemySprite.frame.name,enemyTexture:this.enemySprite.texture.key,enemyAlpha:this.enemySprite.alpha,enemyAngle:this.enemySprite.angle,body:{x:this.enemySprite.x,y:this.enemySprite.y,width:this.enemySprite.displayWidth,height:this.enemySprite.displayHeight},renderedArm:{shoulder:{x:this.enemyUpper.x,y:this.enemyUpper.y},elbow:{x:this.enemyFore.x,y:this.enemyFore.y}},weapon:{held:this.weaponPose?.held,landed:this.weaponPose?.landed,x:this.enemyKatana.x,y:this.enemyKatana.y,angle:this.enemyKatana.angle,width:this.enemyKatana.displayWidth,height:this.enemyKatana.displayHeight,originX:this.enemyKatana.originX,originY:this.enemyKatana.originY,alpha:this.enemyKatana.alpha,visible:this.enemyKatana.visible},arm:this.armPose,hand:{x:this.enemyGrip.x,y:this.enemyGrip.y,angle:this.enemyGrip.angle,visible:this.enemyGrip.visible,state:this.armPose?.handState,texture:this.enemyGrip.texture.key},hd:this.hd,texture:this.hero.texture.key,particles:this.sparks.getAliveParticleCount(),target:this.state.target,collisionTip:(this.state.phase==='attack'?this.state.currentTrack:this.track).frames[this.state.frame],tip:this.heroArt?.weapon.tip??(this.state.phase==='attack'?this.state.currentTrack:this.track).frames[this.state.frame],attackKind:this.state.attackKind,queuedAttack:this.state.queuedAttack,canQueueSweep:this.state.canQueueSweep,heroFrame:this.hero.frame.name,sweepPose:this.state.phase==='attack'&&this.state.attackKind==='sweep'?this.state.currentTrack.poseFrames[this.state.frame]:null,hurtbox:this.state.hurtbox})};
  }
  drawSeal(){
    const g=this.sealArt;g.clear();
    for(let i=5;i>0;i--){g.lineStyle(6+i*3,0x53cfd4,.014*i);g.strokeCircle(0,0,46+i*3);}
    g.lineStyle(2,0x77dadd,.9);g.strokeCircle(0,0,54);g.lineStyle(1,0x9dc5bb,.65);g.strokeCircle(0,0,64);
    for(let i=0;i<12;i++){const a=i*Math.PI/6;g.lineBetween(Math.cos(a)*58,Math.sin(a)*58,Math.cos(a)*64,Math.sin(a)*64);}
    for(let i=0;i<6;i++){const x=(i%3-1)*23,y=(Math.floor(i/3)-.5)*24;g.fillStyle(0x102e35,.88);g.fillCircle(x,y,9);g.lineStyle(2,0xd4c397,.95);g.strokeCircle(x,y,9);g.strokeRect(x-2,y-2,4,4);}
    const p=this.pedestal,x=this.state.target.x;p.clear();
    p.fillStyle(0x06131a,.5);p.fillEllipse(x,578,150,30);
    for(let i=0;i<8;i++){p.lineStyle(1,0x61bec9,.12-i*.012);p.strokeEllipse(x,578-i*29,125-i*8,18);}
    p.lineStyle(1,0x75dbda,.2);p.lineBetween(x-19,385,x-50,571);p.lineBetween(x+19,385,x+50,571);
  }
  attack(kind='thrust'){if(this.state.attack(kind))this.refreshUI();}
  defend(){if(this.state.defend())this.refreshUI();}
  toggleDuel(){if(this.state.startDuel(!this.state.duel.enabled)){this.reset();this.message(this.state.duel.enabled?'交鋒開始 · 留意出刀預兆，按 L 格擋':'姿勢練習 · 鬼武者暫不出刀');}}
  reset(){this.lastClash=null;this.tweens.killTweensOf(this.seal);this.tweens.killTweensOf(this.flash);this.flash.setAlpha(0);this.state.reset();this.seal.setPosition(this.state.target.x,334).setScale(1).setAlpha(1);this.sparks.killAll();this.drawSeal();this.message(this.state.targetKind==='warrior'?'鬼武者現身 · 等待出槍':'封印重聚 · 等待出槍');this.refreshUI();}
  message(text){$('#message').textContent=text;}
  refreshUI(){
    const duel=this.state.duel;
    $('#player-hp').textContent=duel.enabled?'幸村 '+Array.from({length:3},(_,i)=>i<duel.playerHP?'●':'○').join(' '):'修羅道 · 三途燼關';
    $('#duel').textContent=duel.enabled?'結束交鋒':'開始交鋒';
    $('#duel').disabled=this.state.paused||this.state.phase==='attack'||this.state.targetKind!=='warrior';
    $('#guard').disabled=this.state.paused||this.state.phase==='attack'||!duel.active||duel.cooldown>0;
    $('#guard').innerHTML=(duel.guarding?'架槍格擋':duel.cooldown>0?'回氣中':'格擋')+' <kbd>L</kbd>';
    const cue=$('#enemy-cue');cue.hidden=!duel.enabled;
    cue.dataset.phase=duel.result||duel.stage;
    cue.textContent=duel.result==='victory'?'勝 · 燼關已破':duel.result==='defeat'?'敗 · 按「再戰鬼武者」':duel.stage==='windup'?'⚔ 鬼武者蓄刀 · 準備格擋':duel.stage==='strike'?'斬！':duel.stage==='recovery'?'收刀空隙 · 可以反擊':'交鋒 · 留意刀勢';
    $('#hp').textContent=Array.from({length:3},(_,i)=>i<this.state.hp?'●':'○').join(' ');
    $('#score').textContent=`命中 ${this.state.hits} ／ 出槍 ${this.state.swings}`;
    $('#attack').disabled=this.state.paused||this.state.phase==='attack'||this.state.hp===0||duel.guarding||!!duel.result;
    $('#sweep').disabled=this.state.paused||this.state.hp===0||duel.guarding||!!duel.result||(this.state.phase==='attack'&&!this.state.canQueueSweep);
    $('#sweep').classList.toggle('combo-ready',this.state.canQueueSweep);
    $('#sweep').innerHTML=(this.state.queuedAttack?'已接橫掃':this.state.canQueueSweep?'接橫掃':'橫掃')+' <kbd>K</kbd>';
    $('#range').disabled=this.state.phase==='attack';$('#target').disabled=this.state.phase==='attack';
    $('#target-name').textContent=this.state.targetKind==='warrior'?'燼關鬼武者':'怨火封印';
    $('#reset').textContent=this.state.targetKind==='warrior'?'再戰鬼武者':'重聚封印';
    $('#pause').textContent=this.state.paused?'繼續':'暫停';
  }
  setPaused(value){this.state.paused=value;if(value){this.tweens.pauseAll();this.sparks.pause();this.ash.pause();}else{this.tweens.resumeAll();this.sparks.resume();this.ash.resume();}this.refreshUI();}
  onCombat(event){
    const notices={guard:'架槍 · 守住此身',warning:'鬼武者蓄刀 · 待刀將至再格擋',block:'鏘！格擋成功 · 趁收刀反擊','player-hit':'中刀 · 下次留意蓄刀預兆',defeat:'力盡 · 再戰，莫忘回防',victory:'燼關已破 · 六文不渡，赤槍開路',interrupt:'斷招 · 鬼武者刀勢受阻','enemy-miss':'刀鋒未及 · 間合之外'};
    if(notices[event.type])this.message(notices[event.type]);
    if(event.type==='block'||event.type==='player-hit'){
      tone(true);
      const clash=event.type==='block'?duelContactPose(this.state,sharedHeroPose(this.state,this.guardRig,this.thrustRig),this.guardRig,this.thrustRig,this.enemyRig):null;
      if(clash)this.lastClash={...clash.contact,weapon:clash.weapon,arm:clash.arm};
      if($('#feedback').checked){const contact=clash?clash.contact.point:{x:650,y:420};this.sparks.explode(20,contact.x,contact.y);if(!reduced&&event.type==='player-hit')this.cameras.main.shake(75,.002);}
    }
    if(event.type==='swing'){tone(false);this.message(event.kind==='sweep'?'沉腰 · 赤槍低掃':'蓄勢 · 赤槍將出');}
    if(event.type==='queued')this.message('接招已記 · 收槍後橫掃');
    const warrior=this.state.targetKind==='warrior';
    if(event.type==='recover')this.message(this.state.hp===0?(warrior?'鬼武者倒下 · 六文不渡，赤槍開路':'封印已破 · 六文不渡，赤槍開路'):event.hit?'收槍 · 再進一擊':event.kind==='sweep'?'掃空 · 低槍未及':'刺空 · 一步之外，槍尖未及');
    if(event.type==='hit'){
      this.message(event.broken?(warrior?'破甲 · 鬼武者力竭':'破封 · 亡魂歸途已開'):(warrior?(event.kind==='sweep'?'掃中脛甲 · 鬼武者屈膝失衡':'命中 · 鬼武者失衡'):'命中 · 怨火震裂'));tone(true);
      if($('#feedback').checked){
        this.sparks.explode(event.broken?48:24,event.point.x,event.point.y);
        this.flash.setPosition(event.point.x,event.point.y).setScale(1).setAlpha(.8);
        this.tweens.add({targets:this.flash,alpha:0,scale:3,duration:150});
        if(!reduced)this.cameras.main.shake(75,.002);
        if(!warrior)this.tweens.add({targets:this.seal,x:this.state.target.x+12,duration:65,yoyo:true});
      }
      if(!warrior){
        if(event.broken)this.tweens.add({targets:this.seal,alpha:0,scale:1.15,duration:350});
        else this.seal.setAlpha(.45+this.state.hp*.18);
      }
    }
    this.refreshUI();
  }
  placeHeroPart(sprite,name,transform){
    const layer=this.thrustRig.layers[name],w=layer.size[0],h=layer.size[1];
    sprite.setTexture('hero-'+name).setOrigin((layer.pivot[0]-layer.box[0])/w,(layer.pivot[1]-layer.box[1])/h).setDisplaySize(w,h).setPosition(35+transform.point[0],90+transform.point[1]).setAngle(transform.angle);
  }
  update(_time,delta){
    if(!this.state)return;
    this.state.update(delta);
    this.heroArt=sharedHeroPose(this.state,this.guardRig,this.thrustRig);
    for(const [name,part] of Object.entries(this.heroParts)){
      part.setVisible(true);this.placeHeroPart(part,name,this.heroArt.transforms[name]);
    }
    this.guardWeaponPose=this.heroArt?.weapon??null;
    const guarded=this.guardWeaponPose;this.guardYari.setVisible(!!guarded);this.guardHands.forEach(h=>h.setVisible(!!guarded));
    if(guarded){
      this.guardYari.setOrigin(guarded.originX,guarded.originY).setDisplaySize(guarded.width,guarded.height).setPosition(guarded.rear.x,guarded.rear.y).setAngle(guarded.angle);
      this.guardHands.forEach((h,i)=>{
        const name=(i===0?'rear':'front')+'Hand';this.placeHeroPart(h,name,this.heroArt.transforms[name]);
      });
    }
    const uiKey=[this.state.phase,this.state.canQueueSweep,this.state.queuedAttack,this.state.duel.stage,this.state.duel.guarding,this.state.duel.cooldown>0,this.state.duel.result].join(':');
    if(uiKey!==this.uiKey){this.uiKey=uiKey;this.refreshUI();}
    const warrior=this.state.targetKind==='warrior',enemy=this.state.enemy;
    this.seal.setVisible(!warrior);this.pedestal.setVisible(!warrior);
    const bodyTexture=enemyTexture(enemy.pose);
    this.enemySprite.setVisible(warrior).setPosition(this.state.target.x,574).setTexture(bodyTexture.key,bodyTexture.frame).setAlpha(enemy.alpha);
    const actionArmFront=enemy.pose>=16;
    if(actionArmFront!==this.actionArmFront){
      if(actionArmFront){this.children.moveAbove(this.enemyUpper,this.enemySprite);this.children.moveAbove(this.enemyFore,this.enemyUpper);}
      else{this.children.moveBelow(this.enemyUpper,this.enemySprite);this.children.moveBelow(this.enemyFore,this.enemySprite);}
      this.actionArmFront=actionArmFront;
    }
    const encounter=duelContactPose(this.state,this.heroArt,this.guardRig,this.thrustRig,this.enemyRig);
    this.armPose=encounter.arm;this.weaponPose=encounter.weapon;this.contactPose=encounter.contact;
    const weapon=this.weaponPose,grip=enemyPointToWorld(weapon.grip,this.state.target.x,this.enemyRig),wrist=enemyPointToWorld(this.armPose.wrist,this.state.target.x,this.enemyRig);
    this.enemyKatana.setVisible(warrior).setPosition(grip.x,grip.y).setAngle(weapon.angle).setAlpha(weapon.alpha);
    const arm=this.armPose,hand=this.enemyRig.parts[arm.handState];
    const shoulder=enemyPointToWorld(arm.shoulder,this.state.target.x,this.enemyRig),elbow=enemyPointToWorld(arm.elbow,this.state.target.x,this.enemyRig);
    this.enemyUpper.setVisible(warrior).setPosition(shoulder.x,shoulder.y).setAngle(arm.upperAngle).setAlpha(enemy.alpha);
    this.enemyFore.setVisible(warrior).setPosition(elbow.x,elbow.y).setAngle(arm.foreAngle).setAlpha(enemy.alpha);
    this.enemyGrip.setTexture(arm.handState==='grip'?'enemyGrip':'enemy-'+arm.handState).setOrigin(hand.pivot[0]/hand.size[0],hand.pivot[1]/hand.size[1]).setDisplaySize(hand.size[0]*.6,hand.size[1]*.6);
    this.enemyGrip.setVisible(warrior).setPosition(wrist.x,wrist.y).setAngle(arm.handAngle).setAlpha(enemy.alpha);
    this.enemyShadow.clear();
    if(warrior&&!weapon.held){this.enemyShadow.fillStyle(0x05070a,.25*weapon.alpha);this.enemyShadow.fillEllipse(grip.x-65,574,230,9);}
    if(warrior){
      this.enemyShadow.fillStyle(0x06090b,.25*enemy.alpha);this.enemyShadow.fillEllipse(this.state.target.x,574,enemy.pose>=7&&enemy.pose<12?380:235,28);
      // Small painted support-hand contact, separate from the broad body shadow.
      const contact=enemyBinding(enemy.pose,this.enemyRig).supportContact;
      if(contact){const p=enemyPointToWorld({x:contact[0],y:contact[1]},this.state.target.x,this.enemyRig);this.enemyShadow.fillStyle(0x030609,.4*enemy.alpha);this.enemyShadow.fillEllipse(p.x,p.y-3,35,9);}
      const feet=enemyBinding(enemy.pose,this.enemyRig).footContacts;
      if(feet){for(const [x,y] of feet){const p=enemyPointToWorld({x,y},this.state.target.x,this.enemyRig);this.enemyShadow.fillStyle(0x05070a,.35*enemy.alpha);this.enemyShadow.fillEllipse(p.x,p.y,55,12);}}
      else if(enemy.pose<3){this.enemyShadow.fillStyle(0x05070a,.35*enemy.alpha);this.enemyShadow.fillEllipse(this.state.target.x-115,572,55,14);this.enemyShadow.fillEllipse(this.state.target.x+105,565,62,14);}
    }
    this.duelMarks.clear();
    const duel=this.state.duel,g=this.duelMarks;
    if(duel.active){
      if(duel.stage==='windup'){
        // Gameplay warning remains visible with effects off or reduced motion.
        const progress=Math.min(1,duel.age/850);
        g.lineStyle(2,0xf2bd7f,.9);g.strokeRect(this.state.target.x-85,242,130,9);
        g.fillStyle(0xf2bd7f,1);g.fillRect(this.state.target.x-83,244,126*progress,5);
        g.lineStyle(3,0xe5a173,.75);g.lineBetween(700,603,this.state.target.x-30,603);
        g.lineBetween(700,594,700,612);
      }
      if(duel.stage==='strike'&&$('#feedback').checked){
        // Highlight the actual painted blade, not an unrelated line to a fake contact.
        const tip=bladePointToWorld({x:14,y:10},weapon,this.state.target.x,this.enemyRig);
        const heel=bladePointToWorld({x:288,y:25},weapon,this.state.target.x,this.enemyRig);
        g.lineStyle(9,0xb94028,.22);g.lineBetween(heel.x,heel.y,tip.x,tip.y);
        g.lineStyle(2,0xffd9ac,.8);g.lineBetween(heel.x,heel.y,tip.x,tip.y);
      }
      if(duel.guarding&&guarded){g.lineStyle(4,0x8adddc,.9);g.beginPath();g.arc(guarded.contact.x-105,guarded.contact.y,105,-.8,.8);g.strokePath();}
    }
    this.trail.clear();this.debug.clear();
    const track=this.state.phase==='attack'?this.state.currentTrack:this.track,tip=track.frames[this.state.frame];
    if(this.state.phase==='attack'&&track.activeFrames.includes(this.state.frame)&&$('#feedback').checked){
      this.trail.lineStyle(8,0xd72f28,.16);this.trail.lineBetween(tip.x-88,tip.y+13,tip.x,tip.y);
      this.trail.lineStyle(2,0xffd5a0,.85);this.trail.lineBetween(tip.x-65,tip.y+10,tip.x,tip.y);
    }
    if($('#debug').checked){
      if(warrior){this.debug.lineStyle(1,0x59e7f0,.8);this.debug.lineBetween(shoulder.x,shoulder.y,elbow.x,elbow.y);this.debug.lineBetween(elbow.x,elbow.y,wrist.x,wrist.y);this.debug.fillStyle(0x59e7f0,1);this.debug.fillCircle(wrist.x,wrist.y,3);this.debug.fillStyle(0xffe08b,1);this.debug.fillCircle(grip.x,grip.y,3);}
      const target=this.state.hurtbox;this.debug.lineStyle(2,0x6edee2,.8);this.debug.strokeCircle(target.x,target.y,target.radius);
      if(this.state.phase==='attack'){this.debug.fillStyle(track.activeFrames.includes(this.state.frame)?0xffdd77:0xffffff);this.debug.fillCircle(tip.x,tip.y,5);}
    }
  }
}
const game=new Phaser.Game({type:Phaser.AUTO,parent:'stage',width:1200,height:750,backgroundColor:'#12171b',scene:Battle,render:{antialias:true,pixelArt:false},scale:{mode:Phaser.Scale.FIT,autoCenter:Phaser.Scale.CENTER_BOTH},audio:{noAudio:true},fps:{target:60},banner:false});
$('#guard').onclick=()=>scene?.defend();$('#duel').onclick=()=>scene?.toggleDuel();
$('#attack').onclick=()=>scene?.attack();$('#sweep').onclick=()=>scene?.attack('sweep');$('#pause').onclick=()=>scene?.setPaused(!scene.state.paused);$('#reset').onclick=()=>scene?.reset();
$('#range').onchange=e=>{if(scene?.state.setRange(e.target.value))scene.reset();};
$('#target').onchange=e=>{if(scene?.state.setTarget(e.target.value))scene.reset();};
$('#fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.querySelector('main').requestFullscreen();}catch{$('#message').textContent='此瀏覽器未提供全螢幕，請改用橫向畫面。';}};
document.addEventListener('visibilitychange',()=>{if(document.hidden)scene?.setPaused(true);});
window.addEventListener('pagehide',()=>{game.destroy(true);audioContext?.close();},{once:true});
