"""Shared CC0 grip geometry and exact weapon-relative hand transforms.

The 18-bone gameplay rig is retained: hands are fixed grips driven by hand bones,
not a new finger-animation rig. The offline 22-bone study supplies the shape.
"""
from pathlib import Path
import json
from mathutils import Matrix,Vector
from samurai_rig import point,weapon_point
DATA=json.loads((Path(__file__).resolve().parent.parent/'assets/vendor/mpfb/commander-grip.json').read_text())
SCALE=.022*.90/DATA['shaft_radius']
def basis(sign):
    # Right hand: thumb towards -X, fingers down, palm towards the actor front.
    return Matrix(((-sign,0,0),(0,0,-1),(0,-1,0)))
def grip_frame(side):
    sign=-1 if side=='L' else 1;b=basis(sign)
    wrist=point(sign*.47,-.16,.94)
    center=wrist+b@Vector(DATA['shaft_center'])*SCALE
    axis=(b@Vector(DATA['shaft_axis'])).normalized()
    return wrist,center,axis

def rest_attachment(side):
    wrist,center,axis=grip_frame(side)
    origin=point(.47,-.16,.91)
    target=(weapon_point(Vector((.47,-.16,1.91)))-origin).normalized()
    rotation=axis.rotation_difference(target).to_matrix().to_4x4()
    return Matrix.Translation(origin) @ rotation @ Matrix.Translation(-center)

def add_anatomical_hands(mesh):
    names=[]
    for sign in (-1,1):
        wrist=point(sign*.47,-.16,.94);b=basis(sign)
        for label,data,role in [('anatomy',DATA,'cloth'),('plate',DATA['plate'],'armor')]:
            coords=[]
            for v in data['vertices']:
                p=wrist+b@Vector(v)*SCALE
                coords.append((p.x/.82,(p.y+max(0,p.z-1.05)*.10)/.90,p.z/1.25))
            faces=data['faces'] if sign==1 else [list(reversed(f)) for f in data['faces']]
            o=mesh(f'glove.hero.{label}.{sign}',coords,faces,role)
            for p in o.data.polygons:p.use_smooth=True
            if label=='anatomy':o['source_license']='CC0-1.0';o['source_commit']=DATA['commit']
            names.append(o.name)
    return names
