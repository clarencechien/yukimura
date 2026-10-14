"""Install the reviewed v22 commanders, retaining shared textures and crowd rigs."""
from pathlib import Path
import hashlib,json,shutil,struct
ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'.tmp/wrist-v22'
OUT=ROOT/'public/models'
config=json.loads((ROOT/'assets/source/weapon-grips.json').read_text())
validation=json.loads((STAGE/'validation.json').read_text())
assert validation['passed']
assert validation['config_sha256']==hashlib.sha256((ROOT/'assets/source/weapon-grips.json').read_bytes()).hexdigest()
manifest=json.loads((OUT/'manifest.json').read_text())
staged=[]
for kind in ['yukimura','ieyasu']:
    source=STAGE/f'models/{kind}.glb';raw=source.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==validation['models'][kind]['glb_sha256'],'Candidate changed after review'
    g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
    assert len(g['skins'])==1 and len(g['skins'][0]['joints'])==92
    assert len(g['materials'])==5 and len(g['images'])==7
    triangles=sum(g['accessors'][p['indices']]['count']//3 for m in g['meshes'] for p in m['primitives'])
    assert triangles<90000 and len(raw)<7000000
    for image in g['images']:
        assert (OUT/image['uri']).read_bytes()==(STAGE/'models'/image['uri']).read_bytes(),'Shared texture changed'
    face=json.loads((ROOT/f'.tmp/menpo-v21/{kind}.json').read_text())['menpo']
    face={k:v for k,v in face.items() if k not in ['first_vertex','technique_trial']}
    variant=manifest['variants'][kind]
    variant.update({'triangles':triangles,'bytes':len(raw),'bones':92,'materials':5,'menpo':face,
        'grip_study':{'version':'v22','authored_clips':list(config[kind]['clips']),
            'spacing_m':{k:v['spacing'] for k,v in config[kind]['clips'].items()},
            'runtime_ik':False,'source_sha256':hashlib.sha256(raw).hexdigest()}})
    staged.append((kind,source,triangles))
# Validate both candidates before replacing either runtime model.
for kind,source,triangles in staged:
    shutil.copy2(source,OUT/source.name)
    bake=OUT/('hero-bake.json' if kind=='yukimura' else 'ieyasu-bake.json')
    data=json.loads(bake.read_text());data['runtime_triangles']=triangles
    data['runtime_note']='v22: original armor atlas, MPFB articulated hands, Rocketbox head, slim menpo and authored weapon grip poses.'
    bake.write_text(json.dumps(data,indent=2)+'\n')
manifest['generator']='modular-samurai-v22-authored-weapon-grips'
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copy2(ROOT/'assets/source/weapon-grips.json',OUT/'weapon-grips.json')
print('Installed reviewed v22 commanders; rebake crowd palettes before publishing.')
