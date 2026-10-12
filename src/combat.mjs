// Attack timing is the authority for damage, animation, trails and input buffering.
export const STRIKES=Object.freeze([
 {name:'壹 · 朱槍橫掃',clip:'slash',duration:.34,impact:.11,range:4.5,arc:2.9,damage:2,push:5,lift:1.2,lunge:.8,hitstop:.035},
 {name:'貳 · 返刃連斬',clip:'reverse',duration:.38,impact:.13,range:4.8,arc:3.5,damage:2,push:6,lift:2,lunge:.65,hitstop:.04},
 {name:'參 · 破陣突刺',clip:'thrust',duration:.46,impact:.17,range:6.4,arc:1.1,damage:3,push:10,lift:3,lunge:1.65,hitstop:.055},
 {name:'終 · 赤旋烈風',clip:'spin',duration:.64,impact:.28,range:6.1,arc:Math.PI*2,damage:4,push:12,lift:6,lunge:.45,hitstop:.085},
]);
export const MUSOU_PULSES=[.30,.54,.78,1.02,1.34];
export const MUSOU_DURATION=1.72;
export function strikeContains(origin,target,facing,strike){
 const dx=target.x-origin.x,dz=target.z-origin.z,d=Math.hypot(dx,dz);
 if(d>strike.range)return false;
 if(d<.65||strike.arc>=Math.PI*2-.01)return true;
 const length=Math.hypot(facing.x,facing.z)||1;
 return (dx*facing.x+dz*facing.z)/(d*length)>=Math.cos(strike.arc/2);
}
export class ComboChain {
 /** @type {{index:number,time:number,hit:boolean}|null} */
 active=null;next=0;idle=0;buffered=false;requested=false;
 press(){if(this.active)this.buffered=true;else this.requested=true;}
 reset(){this.active=null;this.next=0;this.idle=0;this.buffered=false;this.requested=false;}
 step(dt,held=false){
  const events=[];
  if(!this.active){
   this.idle+=dt;if(this.idle>.7)this.next=0;
   if(held||this.requested){this.active={index:this.next,time:0,hit:false};this.requested=false;this.idle=0;events.push({type:'begin',index:this.next});}
  }
  if(!this.active)return events;
  this.active.time+=dt;
  const strike=STRIKES[this.active.index];
  if(!this.active.hit&&this.active.time>=strike.impact){this.active.hit=true;events.push({type:'impact',index:this.active.index});}
  if(this.active.time>=strike.duration){
   this.next=(this.active.index+1)%STRIKES.length;this.active=null;this.idle=0;
   if(this.buffered){this.requested=true;this.buffered=false;}
  }
  return events;
 }
}
