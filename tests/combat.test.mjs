import {test} from 'node:test';
import assert from 'node:assert/strict';
import {ComboChain,STRIKES,strikeContains} from '../src/combat.mjs';
test('held input progresses four distinct attacks and each strikes once',()=>{
 const chain=new ComboChain(),begins=[],hits=[];
 for(let i=0;i<110;i++)for(const e of chain.step(1/60,true))(e.type==='begin'?begins:hits).push(e.index);
 assert.deepEqual(begins.slice(0,4),[0,1,2,3]);assert.deepEqual(hits.slice(0,4),[0,1,2,3]);assert.equal(hits.length,4);
});
test('windup does no damage, buffered tap survives recovery, idle resets chain',()=>{
 const chain=new ComboChain();chain.press();assert.deepEqual(chain.step(.05).map(e=>e.type),['begin']);
 chain.press();const events=chain.step(.07);assert.equal(events.filter(e=>e.type==='impact').length,1);
 assert.equal(chain.step(.12).length,0);chain.step(.15);assert.deepEqual(chain.step(.01).map(e=>[e.type,e.index]),[['begin',1]]);
 chain.step(.5);chain.step(.8);chain.press();assert.equal(chain.step(.01)[0].index,0);
});
test('sweep and thrust respect facing, range and finisher covers rear',()=>{
 const o={x:0,z:0},f={x:0,z:1};
 assert.equal(strikeContains(o,{x:0,z:4},f,STRIKES[0]),true);
 assert.equal(strikeContains(o,{x:0,z:-3},f,STRIKES[0]),false);
 assert.equal(strikeContains(o,{x:4,z:0},f,STRIKES[2]),false);
 assert.equal(strikeContains(o,{x:0,z:6},f,STRIKES[2]),true);
 assert.equal(strikeContains(o,{x:0,z:-5},f,STRIKES[3]),true);
 assert.equal(strikeContains(o,{x:0,z:7},f,STRIKES[3]),false);
});
test('cancel interrupts pending impact; timing does not multiply hits at high FPS',()=>{
 const count=(dt)=>{const c=new ComboChain();c.press();let hits=0;for(let t=0;t<.6;t+=dt)hits+=c.step(dt).filter(e=>e.type==='impact').length;return hits;};
 assert.equal(count(1/30),1);assert.equal(count(1/144),1);
 const c=new ComboChain();c.press();c.step(.05);c.reset();assert.equal(c.step(.5).length,0);
});
