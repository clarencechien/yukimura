import test from 'node:test';
import assert from 'node:assert/strict';
import {BattleModel,WORLD} from '../docs/routes/jigoku-2d/play/battle.mjs';
const quiet=(options={})=>{const b=new BattleModel(options);b.allies=[];b.spawnClock=10000;return b;};
const advance=(b,seconds,input={})=>{for(let i=0;i<Math.ceil(seconds*60);i++)b.step(1/60,input);};
const foe=(b,x,y)=>{const e=b.spawn('elite');Object.assign(e,{x,y,hp:200,maxHP:200,speed:0,cooldown:999});return e;};
test('a thrust hits multiple enemies in front once and misses the rear',()=>{const b=quiet(),h=b.hero,a=foe(b,h.x+90,h.y),c=foe(b,h.x+100,h.y+30),rear=foe(b,h.x-120,h.y);b.startAttack();advance(b,.6);assert.equal(a.hp,172);assert.equal(c.hp,172);assert.equal(rear.hp,200);assert.equal(b.combo,2);});
test('musou consumes full energy and reaches enemies behind the hero',()=>{const b=quiet(),h=b.hero;assert.equal(b.startAttack('musou'),false);h.energy=100;const e=foe(b,h.x-190,h.y);assert.equal(b.startAttack('musou'),true);assert.equal(h.energy,0);advance(b,.4);assert.equal(e.hp,45);assert.equal(b.stats.musou,1);});
test('movement is normalized, bounded; dash grants brief immunity and has a cooldown',()=>{const a=quiet(),b=quiet();advance(a,.3,{x:1});advance(b,.3,{x:1,y:1});assert.ok(Math.abs(Math.hypot(b.hero.x-340,b.hero.y-605)-(a.hero.x-340))<1e-7);assert.equal(a.dash({x:1,y:0}),true);assert.equal(a.dash({x:1,y:0}),false);assert.equal(a.hurt(50),false);advance(a,.5);assert.equal(a.hurt(50),true);advance(a,10,{x:1,y:1});assert.ok(a.hero.x<=WORLD.right-20&&a.hero.y<=WORLD.bottom-12);});
test('pause freezes time, attacks, spawning and position; completed rounds stay completed',()=>{const b=quiet();b.startAttack();b.paused=true;const state=JSON.stringify(b.snapshot());advance(b,2,{x:1,attack:true,dash:true});assert.equal(JSON.stringify(b.snapshot()),state);assert.equal(b.startAttack(),false);b.paused=false;b.hurt(999);const ended=JSON.stringify(b.snapshot());advance(b,2,{attack:true});b.finish('victory');assert.equal(JSON.stringify(b.snapshot()),ended);assert.equal(new BattleModel().result,null);});
test('enemies arrive from all four sides, respect the cap, and scale with difficulty/cycle',()=>{const b=quiet();for(let i=0;i<100;i++)b.spawn();assert.equal(b.enemies.length,b.rules.cap);assert.ok(b.stats.spawnSides.every(n=>n>0));const hard=quiet({difficulty:'hard',cycle:3}),normal=quiet();assert.ok(hard.spawn().hp>normal.spawn().hp);assert.ok(hard.rules.damage>normal.rules.damage);hard.startBoss();normal.startBoss();assert.ok(hard.boss.hp>normal.boss.hp);});
test('escort requires both opening objectives and proximity; losing the banner ends the run',()=>{const b=quiet();b.kills=36;advance(b,1);assert.equal(b.stage,0);b.stageTime=44.99;b.step(1/60);assert.equal(b.stage,1);Object.assign(b.hero,{x:1100,y:780});const p=b.banner.progress;advance(b,1);assert.equal(b.banner.progress,p);Object.assign(b.hero,{x:b.banner.x,y:b.banner.y});advance(b,1);assert.ok(b.banner.progress>p);b.hurt(999,b.banner);assert.equal(b.result,'defeat');});
test('boss warning gives time to escape, rage adds another zone, and killing him wins',()=>{const b=quiet();b.startBoss();b.boss.cooldown=0;b.step(1/60);assert.equal(b.hazards.length,1);assert.equal(b.hero.hp,b.hero.maxHP);const hp=b.hero.hp;advance(b,1.2);assert.ok(b.hero.hp<hp);const dodge=quiet();dodge.startBoss();dodge.boss.cooldown=0;dodge.step(1/60);dodge.hero.x=80;dodge.hero.y=790;advance(dodge,1.2);assert.equal(dodge.hero.hp,dodge.hero.maxHP);dodge.boss.hp=dodge.boss.maxHP*.4;dodge.boss.cooldown=0;dodge.step(1/60);assert.equal(dodge.boss.phase,2);assert.equal(dodge.hazards.filter(z=>!z.fired).length,2);dodge.damageEnemy(dodge.boss,99999);assert.equal(dodge.result,'victory');});
// Drives production rules only: no forced stage, health, damage or victory changes.
for(const difficulty of ['story','normal','hard'])test(`${difficulty}: full three-stage run is completable`,()=>{
 const b=new BattleModel({difficulty}),stages=new Set();
 for(let i=0;i<60*380&&!b.result;i++){
  const h=b.hero,alive=b.enemies.filter(e=>e.hp>0).sort((a,c)=>Math.hypot(a.x-h.x,a.y-h.y)-Math.hypot(c.x-h.x,c.y-h.y));
  const target=b.stage===1?b.banner:alive[0]??{x:640,y:550};let x=target.x-h.x,y=target.y-h.y,d=Math.hypot(x,y)||1;
  if(b.stage!==1&&d<125){x=-y/d;y=(target.x-h.x)/d;}else{x/=d;y/=d;}if(b.stage===1&&d<45){x=0;y=0;}
  const danger=b.hazards.find(z=>!z.fired&&Math.hypot(z.x-h.x,z.y-h.y)<z.radius+15&&z.age>.25);
  if(danger){x=h.x-danger.x||1;y=h.y-danger.y||.3;const n=Math.hypot(x,y);x/=n;y/=n;}
  b.step(1/60,{x,y,attack:true,musou:h.energy>=100&&(alive.length>8||b.stage===2),dash:!!danger||alive.some(e=>e.windup>0&&Math.hypot(e.x-h.x,e.y-h.y)<55)&&h.hp<h.maxHP*.5});b.events=[];stages.add(b.stage);
 }
 assert.equal(b.result,'victory');assert.deepEqual([...stages],[0,1,2]);assert.ok(b.time>=120&&b.time<300);assert.ok(b.stats.spawnSides.every(n=>n>0));assert.equal(b.allies.length,10);
 console.log(`${difficulty}: ${b.time.toFixed(1)}s, ${b.kills} kills`);
});
