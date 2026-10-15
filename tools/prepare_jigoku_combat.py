"""Package the single generated arena and derive collision tips from the Blender rig.

No per-frame image generation or figure edits. Original arena stays in source assets.
"""
from pathlib import Path
import hashlib,json
from PIL import Image
from yari_rigid_pose import pose
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/routes/jigoku-2d/combat'
source=ROOT/'assets/source/jigoku-2d/combat-arena.png'
Image.open(source).convert('RGB').save(OUT/'arena.webp',quality=90,method=6)
rig=ROOT/'assets/source/jigoku-2d/yari-rigid/rig.json'
c=json.loads(rig.read_text());points=[]
for frame in range(1,37):
    transforms,_,_=pose(frame,c);x,y=transforms['weapon'][0]
    points.append({'x':35+(1520+x+256)*.5,'y':90+(350+y+128)*.5})
track={'fps':30,'frames':points,'activeFrames':[14,15],
       'rigConfigSHA256':hashlib.sha256(rig.read_bytes()).hexdigest(),
       'note':'Manual source blade tip (1520,350), transformed with actual rigid pose. World canvas 1200x750; hero texture top-left (35,90), rendered width 1024.'}
(OUT/'spear-track.json').write_text(json.dumps(track,indent=2)+'\n')
(OUT/'art-provenance.json').write_text(json.dumps({
 'arenaSource':str(source.relative_to(ROOT)),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'method':'One image_gen environment illustration referencing art/01-battlefield-concept.png. Requested empty stone arena, warm left and cool right. No characters. No reproducible generator seed supplied.',
 'generatedFile':'exec-2ed2eaef-9d04-40fa-bc11-0de4abfb2d01.png','dimensions':list(Image.open(source).size),
 'runtimeCopy':'arena.webp','runtimeSHA256':hashlib.sha256((OUT/'arena.webp').read_bytes()).hexdigest(),
 'character':'Existing Blender rigid body animation, warm-left atlases, no new render or image generation.',
 'seal':'Procedural Phaser vector graphic and particles, not a humanoid enemy.'},indent=2)+'\n')
print('Prepared arena and 36 rig-derived tip coordinates.')
