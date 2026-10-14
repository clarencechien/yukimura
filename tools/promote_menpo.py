"""Install reviewed v18 menpo without altering the shared texture inventory."""
from pathlib import Path
import json
import shutil
import struct

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'.tmp/menpo-v18'
OUT=ROOT/'public/models'
manifest=json.loads((OUT/'manifest.json').read_text())
for kind in ['yukimura','ieyasu']:
    info=json.loads((STAGE/f'{kind}.json').read_text())
    source=STAGE/'models'/f'{kind}.glb'
    raw=source.read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
    assert len(g['skins'])==1 and len(g['skins'][0]['joints'])==92
    assert len(g['materials'])==5 and len(g['images'])==7
    assert info['triangles']<=80000 and info['bytes']<6100000
    for image in g['images']:
        assert (OUT/image['uri']).read_bytes()==(STAGE/'models'/image['uri']).read_bytes()
    shutil.copy2(source,OUT/source.name)
    variant=manifest['variants'][kind]
    variant.update({k:info[k] for k in ['triangles','bytes','bones','materials']})
    variant['menpo']={k:v for k,v in info['menpo'].items() if k!='first_vertex'}
    variant['human_head']['neck_blend']='v18: spine-to-head blend at z=1.64–1.74 m; jaw fully follows head'
    bake=OUT/('hero-bake.json' if kind=='yukimura' else 'ieyasu-bake.json')
    d=json.loads(bake.read_text());d['runtime_triangles']=info['triangles']
    d['runtime_note']='Original armor bake; MPFB arms; Rocketbox head; fitted menpo shares existing fittings atlas.'
    bake.write_text(json.dumps(d,indent=2)+'\n')
manifest['generator']='modular-samurai-v18-human-head-menpo'
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Installed fitted menpo; unchanged 14 model textures and 5 commander materials')
