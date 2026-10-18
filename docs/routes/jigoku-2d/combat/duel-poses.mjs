// Authored key poses, held on the existing rule timeline. No extra attack frames or damage.
export function enemyDuelPose(stage,age,recoveryFrom){
  if(stage==='windup')return age<160?0:16;
  if(stage==='strike')return 17;
  if(stage==='recovery'&&recoveryFrom==='attack')return age<160?17:age<360?18:0;
  return 0;
}
export function enemyBinding(pose,rig){return pose>=16?rig.duelBindings[pose-16]:rig.bindings[pose];}
export function enemyTexture(pose){return pose>=16?{key:'enemyDuel',frame:pose-16}:pose>=12?{key:'enemyLow',frame:pose-12}:{key:'warrior',frame:pose};}
