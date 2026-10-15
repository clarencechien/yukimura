"""Catch visible body clipping in the near-range combat viewport, for both atlases."""
from pathlib import Path
import json
import math
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/routes/jigoku-2d/combat'
art = json.loads((OUT / 'enemy-art.json').read_text())
rig = json.loads((OUT / 'enemy-rig.json').read_text())
checks = []
for suffix, size in [('-hd', art['hdFrame']), ('', art['mobileFrame'])]:
    atlas = Image.open(OUT / f'ghost-warrior{suffix}.webp').convert('RGBA')
    w, h = size
    assert atlas.size == (w * art['atlasColumns'], h * art['atlasRows'])
    assert max(atlas.size) <= 4096
    for index, pose in enumerate(art['poses']):
        x, y = index % art['atlasColumns'] * w, index // art['atlasColumns'] * h
        # Ignore nearly transparent filtering fringes; inspect the visible silhouette.
        box = atlas.crop((x, y, x+w, y+h)).getchannel('A').point(lambda a: 255 if a > 16 else 0).getbbox()
        assert box, ('Empty pose', suffix, pose['pose'])
        hd_ratio = art['hdFrame'][0] / w
        left, top, right, bottom = box
        world = [970+(left*hd_ratio-576)*rig['worldScale'],
                 574+(top*hd_ratio-690)*rig['worldScale'],
                 970+(right*hd_ratio-576)*rig['worldScale'],
                 574+(bottom*hd_ratio-690)*rig['worldScale']]
        assert 0 <= world[0] < world[2] <= 1200, ('Horizontal body clipping', suffix, pose['pose'], world)
        assert 0 <= world[1] < world[3] <= 750, ('Vertical body clipping', suffix, pose['pose'], world)
        checks.append({'atlas': suffix or 'mobile', 'pose': pose['pose'], 'worldBounds': world})
feet=[rig['bindings'][index]['footContacts'] for index in [2,3,4]]
foot_steps=[[math.dist(a,b)*rig['worldScale'] for a,b in zip(before,after)] for before,after in zip(feet,feet[1:])]
assert max(max(step) for step in foot_steps)<35, ('Authored sole-center jump',foot_steps)
(OUT / 'art-check.json').write_text(json.dumps({
    'passed': True, 'scope': '12 body silhouettes in both atlases, alpha > 16, at near-range root (970,574) in 1200x750 viewport. Excludes separate arm/weapon layers; not a foot-slip or anatomy test.',
    'manualSoleCenterStepsWorld':foot_steps,
    'checks': checks,
}, indent=2)+'\n')
print('24 body-silhouette boundary checks passed; both atlases fit the viewport and 4096 texture limit.')
