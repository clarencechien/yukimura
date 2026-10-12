import {test} from 'node:test';
import assert from 'node:assert/strict';
import {tuning,applyHit,inRange,nextCycle} from '../src/rules.mjs';
test('new game plus increases enemy threat and clamps invalid cycles',()=>{const a=tuning('normal',1),b=tuning('normal',2);assert.ok(b.damage>a.damage);assert.ok(b.spawn<a.spawn);assert.ok(b.bossHealth>a.bossHealth);assert.equal(tuning('normal',-3).cycle,1);assert.equal(tuning('normal',Infinity).cycle,20);});
test('story and hard are meaningfully distinct',()=>{const a=tuning('story',1),b=tuning('hard',1);assert.ok(a.health>b.health);assert.ok(a.damage<b.damage);});
test('combat range includes edge, excludes distant foes; damage cannot heal',()=>{assert.ok(inRange({x:0,z:0},{x:3,z:4},5));assert.ok(!inRange({x:0,z:0},{x:3,z:4},4.99));assert.equal(applyHit(10,20),0);assert.equal(applyHit(10,-5),10);});
test('progression caps at supported cycle',()=>{assert.equal(nextCycle(1),2);assert.equal(nextCycle(20),20);});
