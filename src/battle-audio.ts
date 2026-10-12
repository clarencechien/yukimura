/** Synthesized impact / spear / drum cues; no download and no audio before a gesture. */
export class BattleAudio {
 private context?:AudioContext;private master?:GainNode;private noise?:AudioBuffer;
 private voices=0;private lastHit=0;muted=false;
 constructor(){try{this.muted=localStorage.getItem('sanada-muted')==='1';}catch{}}
 unlock(){
  if(!this.context){
   this.context=new AudioContext();this.master=this.context.createGain();this.master.gain.value=this.muted?0:.28;this.master.connect(this.context.destination);
   this.noise=this.context.createBuffer(1,this.context.sampleRate,this.context.sampleRate);const data=this.noise.getChannelData(0);
   for(let i=0;i<data.length;i++)data[i]=Math.random()*2-1;
  }
  void this.context.resume().catch(()=>{});
 }
 toggle(){this.muted=!this.muted;try{localStorage.setItem('sanada-muted',this.muted?'1':'0');}catch{}if(this.master)this.master.gain.value=this.muted?0:.28;}
 pause(value:boolean){if(this.context)void(value?this.context.suspend():this.context.resume()).catch(()=>{});}
 private tone(freq:number,duration:number,level:number,end=40){
  const c=this.context;if(!c||c.state!=='running'||this.muted||this.voices>18)return;this.voices++;
  const osc=c.createOscillator(),gain=c.createGain();osc.type='triangle';osc.frequency.setValueAtTime(freq,c.currentTime);osc.frequency.exponentialRampToValueAtTime(end,c.currentTime+duration);
  gain.gain.setValueAtTime(level,c.currentTime);gain.gain.exponentialRampToValueAtTime(.001,c.currentTime+duration);osc.connect(gain);gain.connect(this.master!);osc.start();osc.stop(c.currentTime+duration);
  osc.onended=()=>{osc.disconnect();gain.disconnect();this.voices--;};
 }
 private hiss(duration:number,cutoff:number,level:number){
  const c=this.context;if(!c||c.state!=='running'||this.muted||this.voices>18)return;this.voices++;
  const source=c.createBufferSource(),filter=c.createBiquadFilter(),gain=c.createGain();source.buffer=this.noise!;filter.type='bandpass';filter.frequency.setValueAtTime(cutoff,c.currentTime);filter.frequency.exponentialRampToValueAtTime(220,c.currentTime+duration);filter.Q.value=.7;
  gain.gain.setValueAtTime(level,c.currentTime);gain.gain.exponentialRampToValueAtTime(.001,c.currentTime+duration);source.connect(filter);filter.connect(gain);gain.connect(this.master!);source.start();source.stop(c.currentTime+duration);source.onended=()=>{source.disconnect();filter.disconnect();gain.disconnect();this.voices--;};
 }
 swing(index:number){this.hiss(.16+index*.035,1100+index*320,.6);}
 hit(heavy=false){const now=this.context?.currentTime||0;if(now-this.lastHit<.035)return;this.lastHit=now;this.tone(heavy?100:170,heavy?.26:.13,.75);this.hiss(.085,2400,.9);this.tone(860,.11,.15,260);}
 dash(){this.hiss(.30,1500,.65);}
 ultimate(final=false){this.tone(final?70:110,final?.65:.42,1.3,32);this.hiss(final?.55:.32,650,1);}
 hurt(){this.tone(90,.18,.7,45);}
}
