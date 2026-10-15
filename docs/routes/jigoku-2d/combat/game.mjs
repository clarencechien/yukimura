import {CombatState} from './combat-state.mjs';
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
    this.load.image('arena','arena.webp');this.load.json('track','spear-track.json');
    this.hd=innerWidth>=900;
    this.load.spritesheet('warrior',`ghost-warrior${this.hd?'-hd':''}.webp`,{frameWidth:this.hd?1152:768,frameHeight:this.hd?768:512,endFrame:7});
    for(const clip of ['idle','thrust']){
      if(this.hd){
        this.load.spritesheet(clip,`../yari-rigid/${clip}-warm-left-hd.webp`,{frameWidth:1024,frameHeight:640,endFrame:23});
        this.load.spritesheet(clip+'-2',`../yari-rigid/${clip}-warm-left-hd-2.webp`,{frameWidth:1024,frameHeight:640,endFrame:11});
      }else this.load.spritesheet(clip,`../yari-rigid/${clip}-warm-left.webp`,{frameWidth:512,frameHeight:320,endFrame:35});
    }
    this.load.on('progress',p=>$('#loading').textContent=`正在載入赤甲與燼關… ${Math.round(p*100)}%`);
    this.load.on('loaderror',()=>{this.failed=true;$('#loading').textContent='素材載入失敗，請重新整理。';});
  }
  create(){
    if(this.failed)return;
    scene=this;this.track=this.cache.json.get('track');this.state=new CombatState(this.track,e=>this.onCombat(e));
    this.add.image(600,375,'arena').setDisplaySize(1200,750).setTint(0xb8b8bd);
    const shade=this.add.graphics();shade.fillStyle(0x080d14,.18);shade.fillRect(0,0,1200,750);
    // Fixed contact patches under actual planted feet, plus a softer body shadow.
    const shadow=this.add.graphics();for(let i=5;i>0;i--){shadow.fillStyle(0x060708,.035);shadow.fillEllipse(453,628,375+i*12,32+i*7);}
    shadow.fillStyle(0x050607,.5);shadow.fillEllipse(263,648,62,17);shadow.fillEllipse(661,606,91,18);
    this.hero=this.add.sprite(35,90,'idle',0).setOrigin(0).setDisplaySize(1024,640);
    this.pedestal=this.add.graphics();this.seal=this.add.container(970,334);this.sealArt=this.add.graphics();this.seal.add(this.sealArt);this.drawSeal();
    this.enemyShadow=this.add.graphics();
    this.enemySprite=this.add.sprite(970,574,'warrior',0).setOrigin(.5,690/768).setDisplaySize(1152*.6,768*.6);
    this.flash=this.add.circle(0,0,12,0xffd69b).setBlendMode(Phaser.BlendModes.ADD).setAlpha(0);
    const dot=this.make.graphics({x:0,y:0,add:false});dot.fillStyle(0xffffff);dot.fillCircle(4,4,4);dot.generateTexture('spark',8,8);dot.destroy();
    this.sparks=this.add.particles(0,0,'spark',{emitting:false,lifespan:{min:140,max:380},speed:{min:80,max:290},angle:{min:150,max:370},gravityY:340,scale:{start:.55,end:0},alpha:{start:1,end:0},tint:[0xffe5b3,0xf99e5b,0xbc3834],blendMode:'ADD',maxParticles:80});
    this.ash=this.add.particles(0,0,'spark',{emitting:!reduced,x:{min:0,max:1200},y:760,speedY:{min:-30,max:-90},speedX:{min:5,max:35},lifespan:4000,frequency:180,quantity:1,scale:{start:.2,end:0},alpha:{start:.25,end:0},tint:0xef9c69,blendMode:'ADD',maxParticles:30});
    this.trail=this.add.graphics();this.debug=this.add.graphics();
    this.input.keyboard.on('keydown-J',event=>{if(event.repeat||/INPUT|SELECT|BUTTON/.test(document.activeElement?.tagName))return;this.attack();});
    this.input.keyboard.on('keydown-SPACE',event=>{if(/INPUT|SELECT|BUTTON/.test(document.activeElement?.tagName))return;event.preventDefault();this.attack();});
    for(const id of ['attack','pause','reset','range','target'])$('#'+id).disabled=false;
    $('#loading').style.display='none';this.refreshUI();
    window.yariCombat={snapshot:()=>({ready:true,engine:Phaser.VERSION,phase:this.state.phase,frame:this.state.frame,hp:this.state.hp,hits:this.state.hits,swings:this.state.swings,paused:this.state.paused,freeze:this.state.freeze,range:this.state.range,targetKind:this.state.targetKind,flashAlpha:this.flash.alpha,enemyAge:this.state.enemyAge,enemy:this.state.enemy,enemyFrame:this.enemySprite.frame.name,enemyAlpha:this.enemySprite.alpha,enemyAngle:this.enemySprite.angle,hd:this.hd,texture:this.hero.texture.key,particles:this.sparks.getAliveParticleCount(),target:this.state.target,tip:this.track.frames[this.state.frame]})};
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
  attack(){if(this.state.attack()){tone(false);this.refreshUI();}}
  reset(){this.tweens.killTweensOf(this.seal);this.tweens.killTweensOf(this.flash);this.flash.setAlpha(0);this.state.reset();this.seal.setPosition(this.state.target.x,334).setScale(1).setAlpha(1);this.sparks.killAll();this.drawSeal();this.message(this.state.targetKind==='warrior'?'鬼武者現身 · 等待出槍':'封印重聚 · 等待出槍');this.refreshUI();}
  message(text){$('#message').textContent=text;}
  refreshUI(){
    $('#hp').textContent=Array.from({length:3},(_,i)=>i<this.state.hp?'●':'○').join(' ');
    $('#score').textContent=`命中 ${this.state.hits} ／ 出槍 ${this.state.swings}`;
    $('#attack').disabled=this.state.paused||this.state.phase==='attack'||this.state.hp===0;
    $('#range').disabled=this.state.phase==='attack';$('#target').disabled=this.state.phase==='attack';
    $('#target-name').textContent=this.state.targetKind==='warrior'?'燼關鬼武者':'怨火封印';
    $('#reset').textContent=this.state.targetKind==='warrior'?'再戰鬼武者':'重聚封印';
    $('#pause').textContent=this.state.paused?'繼續':'暫停';
  }
  setPaused(value){this.state.paused=value;if(value){this.tweens.pauseAll();this.sparks.pause();this.ash.pause();}else{this.tweens.resumeAll();this.sparks.resume();this.ash.resume();}this.refreshUI();}
  onCombat(event){
    if(event.type==='swing')this.message('蓄勢 · 赤槍將出');
    const warrior=this.state.targetKind==='warrior';
    if(event.type==='recover')this.message(this.state.hp===0?(warrior?'鬼武者倒下 · 六文不渡，赤槍開路':'封印已破 · 六文不渡，赤槍開路'):event.hit?'收槍 · 再進一擊':'刺空 · 一步之外，槍尖未及');
    if(event.type==='hit'){
      this.message(event.broken?(warrior?'破甲 · 鬼武者力竭':'破封 · 亡魂歸途已開'):(warrior?'命中 · 鬼武者失衡':'命中 · 怨火震裂'));tone(true);
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
  update(_time,delta){
    if(!this.state)return;
    this.state.update(delta);
    const clip=this.state.phase==='attack'?'thrust':'idle',page=this.hd&&this.state.frame>=24?'-2':'';
    this.hero.setTexture(clip+page,this.hd?this.state.frame%24:this.state.frame);
    const warrior=this.state.targetKind==='warrior',enemy=this.state.enemy;
    this.seal.setVisible(!warrior);this.pedestal.setVisible(!warrior);
    this.enemySprite.setVisible(warrior).setPosition(this.state.target.x,574).setFrame(enemy.pose).setAlpha(enemy.alpha);
    this.enemyShadow.clear();
    if(warrior){
      this.enemyShadow.fillStyle(0x06090b,.25*enemy.alpha);this.enemyShadow.fillEllipse(this.state.target.x,574,enemy.pose>=6?380:235,28);
      if(enemy.pose<3){this.enemyShadow.fillStyle(0x05070a,.35*enemy.alpha);this.enemyShadow.fillEllipse(this.state.target.x-115,572,55,14);this.enemyShadow.fillEllipse(this.state.target.x+105,565,62,14);}
    }
    this.trail.clear();this.debug.clear();
    const tip=this.track.frames[this.state.frame];
    if(this.state.phase==='attack'&&this.state.frame>=13&&this.state.frame<=17&&$('#feedback').checked){
      this.trail.lineStyle(8,0xd72f28,.16);this.trail.lineBetween(tip.x-88,tip.y+13,tip.x,tip.y);
      this.trail.lineStyle(2,0xffd5a0,.85);this.trail.lineBetween(tip.x-65,tip.y+10,tip.x,tip.y);
    }
    if($('#debug').checked){
      const target=this.state.target;this.debug.lineStyle(2,0x6edee2,.8);this.debug.strokeCircle(target.x,target.y,target.radius);
      if(this.state.phase==='attack'){this.debug.fillStyle(this.track.activeFrames.includes(this.state.frame)?0xffdd77:0xffffff);this.debug.fillCircle(tip.x,tip.y,5);}
    }
  }
}
const game=new Phaser.Game({type:Phaser.AUTO,parent:'stage',width:1200,height:750,backgroundColor:'#12171b',scene:Battle,render:{antialias:true,pixelArt:false},scale:{mode:Phaser.Scale.FIT,autoCenter:Phaser.Scale.CENTER_BOTH},audio:{noAudio:true},fps:{target:60},banner:false});
$('#attack').onclick=()=>scene?.attack();$('#pause').onclick=()=>scene?.setPaused(!scene.state.paused);$('#reset').onclick=()=>scene?.reset();
$('#range').onchange=e=>{if(scene?.state.setRange(e.target.value))scene.reset();};
$('#target').onchange=e=>{if(scene?.state.setTarget(e.target.value))scene.reset();};
$('#fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.querySelector('main').requestFullscreen();}catch{$('#message').textContent='此瀏覽器未提供全螢幕，請改用橫向畫面。';}};
document.addEventListener('visibilitychange',()=>{if(document.hidden)scene?.setPaused(true);});
window.addEventListener('pagehide',()=>{game.destroy(true);audioContext?.close();},{once:true});
