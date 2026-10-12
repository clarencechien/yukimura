export const DIFFICULTIES={story:{health:180,damage:.55,spawn:1.4},normal:{health:120,damage:1,spawn:1},hard:{health:95,damage:1.4,spawn:.72}};
export function tuning(difficulty,cycle){const d=DIFFICULTIES[difficulty]||DIFFICULTIES.normal;const n=Math.max(1,Math.min(20,Math.floor(Number(cycle)||1)));return {...d,cycle:n,enemyHealth:2+Math.floor((n-1)/2),speed:1+(n-1)*.065,damage:d.damage*(1+(n-1)*.18),spawn:Math.max(.25,d.spawn/(1+(n-1)*.15)),bossHealth:80+(n-1)*25};}
export function inRange(a,b,r){return Math.hypot(a.x-b.x,a.z-b.z)<=r;}
export function applyHit(hp,damage){return Math.max(0,hp-Math.max(0,damage));}
export function nextCycle(n){return Math.min(20,n+1);}
