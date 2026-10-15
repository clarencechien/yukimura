// Fixed-stance duel rules; enemy damage uses declared range + strike timing, not blade pixels.
export const DUEL_TIMING={waiting:1200,windup:850,strike:180,recovery:1400,guard:580,cooldown:1100};
export class DuelState {
  constructor(emit){this.emit=emit;this.enabled=false;this.reset();}
  reset(){this.playerHP=3;this.blocks=0;this.stage='waiting';this.age=0;this.guard=0;this.cooldown=0;this.result=null;}
  get active(){return this.enabled&&!this.result;}
  get guarding(){return this.guard>0;}
  defend(){if(!this.active||this.cooldown>0)return false;this.guard=DUEL_TIMING.guard;this.cooldown=DUEL_TIMING.cooldown;this.emit({type:'guard'});return true;}
  interrupt(dead=false){
    if(!this.active)return;
    if(dead){this.result='victory';this.guard=0;this.emit({type:'victory'});return;}
    const interrupted=this.stage==='windup';this.stage='recovery';this.age=0;
    if(interrupted)this.emit({type:'interrupt'});
  }
  update(dt,range){
    if(!this.active)return;
    this.guard=Math.max(0,this.guard-dt);this.cooldown=Math.max(0,this.cooldown-dt);this.age+=dt;
    if(this.age<DUEL_TIMING[this.stage])return;
    this.age=0;
    if(this.stage==='waiting'||this.stage==='recovery'){
      this.stage='windup';this.emit({type:'warning'});
    }else if(this.stage==='windup'){
      this.stage='strike';
      if(range==='far')this.emit({type:'enemy-miss'});
      else if(this.guarding){this.blocks++;this.emit({type:'block'});}
      else{this.playerHP--;if(this.playerHP===0)this.result='defeat';this.emit({type:this.result?'defeat':'player-hit'});}
    }else this.stage='recovery';
  }
}
