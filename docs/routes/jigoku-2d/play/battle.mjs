// Game rules are independent of Phaser rendering so combat can be replayed deterministically.
export const WORLD={width:1280,height:900,left:65,right:1215,top:350,bottom:810};
export const DIFFICULTY={story:{label:'初陣',hp:220,damage:.65,spawn:2.2,cap:38},normal:{label:'猛將',hp:170,damage:1,spawn:1.8,cap:48},hard:{label:'修羅',hp:150,damage:1.3,spawn:1.45,cap:58}};
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n)),dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
const norm=(x,y)=>{const d=Math.hypot(x,y)||1;return {x:x/d,y:y/d};};
export class BattleModel{
 constructor({difficulty='normal',cycle=1,seed=1615}={}){
  this.difficulty=DIFFICULTY[difficulty]?difficulty:'normal';this.cycle=clamp(Math.floor(cycle)||1,1,6);this.rules=DIFFICULTY[this.difficulty];this.seed=seed>>>0;this.time=0;this.stage=0;this.stageTime=0;this.result=null;this.paused=false;this.events=[];this.kills=0;this.combo=0;this.bestCombo=0;this.comboUntil=0;this.hitstop=0;this.nextId=1;this.spawnClock=1;this.spawnSide=0;this.attackIndex=0;this.formation='follow';
  this.hero={x:340,y:605,hp:this.rules.hp,maxHP:this.rules.hp,energy:45,face:{x:1,y:0},attack:null,attackCooldown:0,dash:0,dashCooldown:0,invulnerable:0,walk:0,moving:false};
  this.banner={x:250,y:520,hp:150,maxHP:150,progress:0};this.enemies=[];this.allies=Array.from({length:10},(_,i)=>({id:i,x:260+(i%5)*27,y:560+Math.floor(i/5)*45,attack:0,cooldown:i*.12,face:1,walk:i*.7}));this.pickups=[];this.hazards=[];this.boss=null;this.stats={damageTaken:0,musou:0,dashes:0,allyKills:0,spawnSides:[0,0,0,0]};
 }
 random(){this.seed=(Math.imul(this.seed,1664525)+1013904223)>>>0;return this.seed/4294967296;}
 emit(type,data={}){this.events.push({type,at:this.time,...data});}
 command(){if(this.result||this.paused)return;this.formation=this.formation==='follow'?'charge':'follow';this.emit('command',{mode:this.formation});}
 finish(result){if(this.result)return;this.result=result;this.hero.attack=null;this.hero.dash=0;this.hazards=[];this.emit(result,{kills:this.kills,time:this.time});}
 spawn(kind='soldier',side=this.spawnSide++%4){
  if(this.enemies.filter(e=>e.hp>0).length>=this.rules.cap)return null;
  const r=this.random(),p=side===0?{x:WORLD.left,y:WORLD.top+r*460}:side===1?{x:WORLD.right,y:WORLD.top+r*460}:side===2?{x:80+r*1120,y:WORLD.top}:{x:80+r*1120,y:WORLD.bottom};
  if(dist(p,this.hero)<180){p.x=this.hero.x<640?WORLD.right:WORLD.left;}
  const elite=kind==='elite',mult=1+(this.cycle-1)*.15,e={id:this.nextId++,kind,x:p.x,y:p.y,hp:(elite?115:34)*mult,maxHP:(elite?115:34)*mult,radius:elite?23:17,speed:(elite?52:60)+this.random()*17+(this.cycle-1)*3,cooldown:1+this.random(),windup:0,stun:0,dead:0,walk:this.random()*6,face:1,attackPoint:null,knock:{x:0,y:0}};
  this.stats.spawnSides[side]++;this.enemies.push(e);return e;
 }
 startBoss(){this.stage=2;this.stageTime=0;this.hero.hp=Math.min(this.hero.maxHP,this.hero.hp+45);this.hero.energy=100;const hp=2200*(1+(this.cycle-1)*.22)*(this.difficulty==='hard'?1.2:this.difficulty==='story'?.8:1);this.boss={id:this.nextId++,kind:'boss',x:1030,y:470,hp,maxHP:hp,radius:42,speed:45,cooldown:2.4,windup:0,stun:0,dead:0,walk:0,face:-1,knock:{x:0,y:0},phase:1,pattern:0};this.enemies.push(this.boss);this.emit('boss');}
 startAttack(kind='basic'){
  const h=this.hero;if(this.paused||this.result||h.attack||h.dash>0||h.attackCooldown>0)return false;
  if(kind==='musou'&&h.energy<100)return false;
  const nearby=this.enemies.filter(e=>e.hp>0&&dist(e,h)<260).sort((a,b)=>dist(a,h)-dist(b,h))[0];if(nearby)h.face=norm(nearby.x-h.x,nearby.y-h.y);
  const finisher=this.attackIndex++%3===2,musou=kind==='musou';h.attack={kind:musou?'musou':finisher?'sweep':'thrust',age:0,duration:musou?.95:finisher?.52:.42,hitAt:musou?.19:finisher?.20:.14,fired:false,face:{...h.face},finisher};h.attackCooldown=musou?1.05:finisher?.53:.43;
  if(musou){h.energy=0;h.invulnerable=1.25;this.stats.musou++;}this.emit('swing',{kind:h.attack.kind,x:h.x,y:h.y,face:h.face});return true;
 }
 dash(direction){const h=this.hero;if(this.result||this.paused||h.dashCooldown>0||h.attack?.kind==='musou')return false;h.attack=null;h.dash=.22;h.dashCooldown=1.25;h.invulnerable=Math.max(h.invulnerable,.36);h.dashFace=direction&&Math.hypot(direction.x,direction.y)>.1?norm(direction.x,direction.y):{...h.face};this.stats.dashes++;this.emit('dash',{x:h.x,y:h.y});return true;}
 damageEnemy(e,amount,source='hero',power=1){
  if(e.hp<=0||this.result)return false;e.hp=Math.max(0,e.hp-amount);const d=norm(e.x-this.hero.x,e.y-this.hero.y);e.knock={x:d.x*power*(e.kind==='boss'?20:125),y:d.y*power*(e.kind==='boss'?20:125)};e.stun=e.kind==='boss'?0:.24;e.windup=0;
  if(source==='hero'){this.combo++;this.comboUntil=this.time+3;this.bestCombo=Math.max(this.bestCombo,this.combo);this.hero.energy=Math.min(100,this.hero.energy+3);}
  this.emit('hit',{x:e.x,y:e.y,amount,source,boss:e.kind==='boss'});
  if(e.hp===0){e.dead=.001;this.kills++;if(source==='ally')this.stats.allyKills++;this.hero.energy=Math.min(100,this.hero.energy+5);this.emit('kill',{x:e.x,y:e.y,boss:e.kind==='boss'});if(e.kind!=='boss'&&this.kills%9===0)this.pickups.push({id:e.id,x:e.x,y:e.y,life:14});if(e.kind==='boss')this.finish('victory');}
  return true;
 }
 hurt(amount,target=this.hero){if(this.result||target===this.hero&&this.hero.invulnerable>0)return false;target.hp=Math.max(0,target.hp-amount);if(target===this.hero){target.invulnerable=.75;this.stats.damageTaken+=amount;this.combo=0;this.emit('hurt',{x:target.x,y:target.y});}else this.emit('banner-hit',{x:target.x,y:target.y});if(target.hp===0)this.finish('defeat');return true;}
 resolveAttack(a){
  const h=this.hero,musou=a.kind==='musou',radius=musou?310:a.finisher?195:178;let hits=0;
  for(const e of this.enemies){if(e.hp<=0)continue;const distance=dist(e,h),toward=norm(e.x-h.x,e.y-h.y),dot=toward.x*a.face.x+toward.y*a.face.y;if(distance<=radius+e.radius&&(musou||distance<45||dot>(a.finisher?-.15:.12))){this.damageEnemy(e,musou?155:a.finisher?48:28,'hero',musou?2:1);hits++;}}
  if(hits)this.hitstop=musou?.075:.045;this.emit('impact',{x:h.x,y:h.y,face:a.face,kind:a.kind,hits});
 }
 step(dt,input={}){
  if(this.paused||this.result||!Number.isFinite(dt)||dt<=0)return;dt=Math.min(dt,.05);if(this.hitstop>0){this.hitstop=Math.max(0,this.hitstop-dt);return;}
  this.time+=dt;this.stageTime+=dt;const h=this.hero;
  for(const key of ['attackCooldown','dashCooldown','invulnerable'])h[key]=Math.max(0,h[key]-dt);
  let move={x:Number(input.x)||0,y:Number(input.y)||0};if(Math.hypot(move.x,move.y)>1)move=norm(move.x,move.y);
  if(input.dash)this.dash(move);if(input.musou)this.startAttack('musou');else if(input.attack)this.startAttack();
  h.moving=Math.hypot(move.x,move.y)>.05;
  if(h.dash>0){h.dash=Math.max(0,h.dash-dt);move=h.dashFace;h.x+=move.x*710*dt;h.y+=move.y*710*dt;}
  else{const speed=h.attack?95:225;h.x+=move.x*speed*dt;h.y+=move.y*speed*dt;if(h.moving&&!h.attack)h.face=norm(move.x,move.y);}
  h.x=clamp(h.x,WORLD.left+20,WORLD.right-20);h.y=clamp(h.y,WORLD.top+20,WORLD.bottom-12);if(h.moving)h.walk+=dt*10;
  if(h.attack){const a=h.attack;a.age+=dt;if(!a.fired&&a.age>=a.hitAt){a.fired=true;this.resolveAttack(a);}if(a.age>=a.duration)h.attack=null;}
  if(this.result)return;if(this.time>this.comboUntil)this.combo=0;
  if(this.stage===0&&this.kills>=36&&this.stageTime>=45){this.stage=1;this.stageTime=0;h.hp=Math.min(h.maxHP,h.hp+30);this.emit('escort');}
  if(this.stage===1&&dist(h,this.banner)<230){const contested=this.enemies.some(e=>e.hp>0&&dist(e,this.banner)<95);this.banner.progress=Math.min(1,this.banner.progress+dt*(contested?.003:.009));this.banner.x=250+750*this.banner.progress;this.banner.y=520+Math.sin(this.banner.progress*Math.PI)*90;if(this.banner.progress>=1)this.startBoss();}
  this.spawnClock-=dt;if(this.spawnClock<=0){this.spawnClock=this.rules.spawn/(1+(this.cycle-1)*.08)*(this.stage===2?1.9:1);const n=this.stage===2?2:3;for(let i=0;i<n;i++)this.spawn(this.random()<(this.stage>0?.15:.06)?'elite':'soldier');}
  const alive=this.enemies.filter(e=>e.hp>0);
  for(const e of this.enemies){
   if(e.hp<=0){e.dead+=dt;e.x=clamp(e.x+e.knock.x*dt,WORLD.left,WORLD.right);e.y=clamp(e.y+e.knock.y*dt,WORLD.top,WORLD.bottom);e.knock.x*=Math.exp(-7*dt);e.knock.y*=Math.exp(-7*dt);continue;}e.cooldown-=dt;e.stun=Math.max(0,e.stun-dt);e.x+=e.knock.x*dt;e.y+=e.knock.y*dt;e.knock.x*=Math.exp(-9*dt);e.knock.y*=Math.exp(-9*dt);
   if(e.kind==='boss'){this.updateBoss(e,dt);continue;}
   const target=this.stage===1&&e.id%4===0?this.banner:h,d=dist(e,target);e.face=target.x>=e.x?1:-1;
   if(e.stun>0)continue;
   if(e.windup>0){e.windup-=dt;if(e.windup<=0){if(dist(e.attackPoint,target)<65&&dist(e,target)<100)this.hurt((e.kind==='elite'?16:9)*this.rules.damage*(1+(this.cycle-1)*.12),target);e.cooldown=1.6+this.random()*.5;}continue;}
   if(d<55&&e.cooldown<=0){e.windup=e.kind==='elite'?.75:.6;e.attackPoint={x:target.x,y:target.y};this.emit('warning',{x:e.x,y:e.y});}
   else if(d>43){const v=norm(target.x-e.x,target.y-e.y);e.x+=v.x*e.speed*dt;e.y+=v.y*e.speed*dt;e.walk+=dt*8;}
  }
  // Bounded crowd separation: at most 58 enemies plus the commander.
  for(let i=0;i<alive.length;i++)for(let j=i+1;j<alive.length;j++){const a=alive[i],b=alive[j],d=dist(a,b),r=(a.radius+b.radius)*.8;if(d<r&&d>.001){const k=(r-d)*.10/d;const dx=(a.x-b.x)*k,dy=(a.y-b.y)*k;a.x+=dx;a.y+=dy;b.x-=dx;b.y-=dy;}}
  for(const e of alive){e.x=clamp(e.x,WORLD.left,WORLD.right);e.y=clamp(e.y,WORLD.top,WORLD.bottom);}
  for(const a of this.allies){a.cooldown-=dt;a.attack=Math.max(0,a.attack-dt);const nearest=alive.filter(e=>e.hp>0).sort((x,y)=>dist(x,a)-dist(y,a))[0];const leader=this.stage===1?this.banner:h,angle=a.id*Math.PI*2/10,home={x:leader.x+Math.cos(angle)*145,y:leader.y+Math.sin(angle)*90};let target=home;
   if(nearest&&dist(nearest,a)<(this.formation==='charge'?240:100))target={x:nearest.x+Math.cos(angle)*65,y:nearest.y+Math.sin(angle)*48};const d=dist(target,a);if(d>25){const v=norm(target.x-a.x,target.y-a.y);a.x+=v.x*Math.min(155,d*3)*dt;a.y+=v.y*Math.min(155,d*3)*dt;a.walk+=dt*9;a.face=v.x>=0?1:-1;}
   if(nearest&&dist(nearest,a)<110&&a.cooldown<=0){a.attack=.32;a.cooldown=1.4+a.id*.04;a.face=nearest.x>=a.x?1:-1;this.damageEnemy(nearest,6,'ally',.2);this.emit('ally-strike',{x:a.x,y:a.y,to:{x:nearest.x,y:nearest.y}});}
   a.x=clamp(a.x,80,1200);a.y=clamp(a.y,360,810);
  }
  for(let i=0;i<this.allies.length;i++)for(let j=i+1;j<this.allies.length;j++){const a=this.allies[i],b=this.allies[j],d=dist(a,b);if(d>0&&d<40){const k=(40-d)*.08/d,dx=(a.x-b.x)*k,dy=(a.y-b.y)*k;a.x+=dx;a.y+=dy;b.x-=dx;b.y-=dy;}}
  for(const zone of this.hazards){zone.age+=dt;if(!zone.fired&&zone.age>=zone.delay){zone.fired=true;if(dist(h,zone)<zone.radius)this.hurt(zone.damage);this.emit('blast',{x:zone.x,y:zone.y,radius:zone.radius});}}
  this.hazards=this.hazards.filter(z=>z.age<z.delay+.4);
  for(const p of this.pickups){p.life-=dt;if(dist(p,h)<105){h.hp=Math.min(h.maxHP,h.hp+24);h.energy=Math.min(100,h.energy+8);p.life=0;this.emit('heal',{x:h.x,y:h.y});}}
  this.pickups=this.pickups.filter(p=>p.life>0);this.enemies=this.enemies.filter(e=>e.hp>0||e.dead<1.7);
 }
 updateBoss(e,dt){
  const h=this.hero;e.face=h.x>=e.x?1:-1;if(e.hp<e.maxHP*.5&&e.phase===1){e.phase=2;this.emit('rage');}
  if(e.windup>0){e.windup=Math.max(0,e.windup-dt);return;}
  const d=dist(e,h);if(d>125){const v=norm(h.x-e.x,h.y-e.y);e.x+=v.x*e.speed*dt;e.y+=v.y*e.speed*dt;e.walk+=dt*5;}
  if(e.cooldown<=0){const radius=e.pattern++%2===0?145:105,delay=e.phase===2?.8:1.05;e.windup=delay;e.cooldown=e.phase===2?2.4:3.2;this.hazards.push({x:h.x,y:h.y,radius,delay,age:0,fired:false,damage:28*this.rules.damage});if(e.phase===2)this.hazards.push({x:clamp(h.x+150,80,1200),y:clamp(h.y+65,360,810),radius:90,delay:delay+.35,age:0,fired:false,damage:25*this.rules.damage});this.emit('boss-warning');}
 }
 snapshot(){return {ready:true,time:this.time,stage:this.stage,result:this.result,paused:this.paused,kills:this.kills,combo:this.combo,bestCombo:this.bestCombo,formation:this.formation,difficulty:this.difficulty,cycle:this.cycle,hero:structuredClone(this.hero),banner:{...this.banner},boss:this.boss?{hp:this.boss.hp,maxHP:this.boss.maxHP,phase:this.boss.phase}:null,enemies:this.enemies.filter(e=>e.hp>0).length,allies:this.allies.length,stats:structuredClone(this.stats)};}
}
