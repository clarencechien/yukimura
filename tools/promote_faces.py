"""Install v17 heads after visual/animation review, retaining shared crowd assets."""
from pathlib import Path
import hashlib
import json
import shutil
import struct

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'.tmp/face-v17'
OUT=ROOT/'public/models'
manifest=json.loads((OUT/'manifest.json').read_text())
for kind in ['yukimura','ieyasu']:
    info=json.loads((STAGE/f'{kind}.json').read_text())
    source=STAGE/'models'/f'{kind}.glb'
    raw=source.read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
    assert len(g['skins'])==1 and len(g['skins'][0]['joints'])==92
    assert len(g['materials'])==5 and len(g['images'])==7
    for im in g['images']:
        p=STAGE/'models'/im['uri'];data=p.read_bytes()
        assert hashlib.sha256(data).hexdigest()[:16]==p.stem
        shutil.copy2(p,OUT/im['uri'])
    shutil.copy2(source,OUT/source.name)
    v=manifest['variants'][kind]
    v.update({k:info[k] for k in ['triangles','bytes','materials','bones']})
    v['textures']=7;v['human_head']={'version':info['version'],'source':'Microsoft Rocketbox Male Adult 10',
        'license':'MIT','source_sha256':info['source_sha256'],'vertices':info['head']['vertices'],
        'deform_bones':info['head']['deform_bones'],'runtime_facial_animation':False}
    bake=OUT/('hero-bake.json' if kind=='yukimura' else 'ieyasu-bake.json')
    d=json.loads(bake.read_text());d['runtime_triangles']=info['triangles']
    d['runtime_note']='Original armor bake; MPFB arms; fitted cords; Rocketbox-derived head with authored skin material.'
    bake.write_text(json.dumps(d,indent=2)+'\n')
manifest['generator']='modular-samurai-v17-human-heads'
textures={}
for kind in manifest['variants']:
    raw=(OUT/f'{kind}.glb').read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
    for im in g['images']:textures[im['uri']]=(OUT/im['uri']).stat().st_size
manifest['shared_textures']=textures;manifest['shared_texture_bytes']=sum(textures.values())
manifest['shared_fittings_lods']['commander']['material_sections']=5
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copy2(ROOT/'assets/research/character-candidates/rocketbox-LICENSE.txt',OUT/'LICENSE-Rocketbox.txt')
print('Installed human heads:',{k:manifest['variants'][k]['triangles'] for k in ['yukimura','ieyasu']})
