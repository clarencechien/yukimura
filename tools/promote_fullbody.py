"""Install reviewed commander GLBs; leave soldier meshes and atlases intact."""
from pathlib import Path
import json,shutil,hashlib,struct,argparse
parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group();mode.add_argument('--physique',action='store_true');mode.add_argument('--detail',action='store_true');args=parser.parse_args()
ROOT=Path(__file__).resolve().parent.parent;stage=ROOT/('.tmp/detail-v16' if args.detail else '.tmp/physique-v15' if args.physique else '.tmp/fullbody-v14');out=ROOT/'public/models'
report=json.loads((out/'manifest.json').read_text())
for kind in (('yukimura','ieyasu','ashigaru','tokugawa') if args.detail else ('yukimura','ieyasu')):
    info=json.loads((stage/f'{kind}.json').read_text());src=stage/'models'/f'{kind}.glb';raw=src.read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
    commander=kind in ('yukimura','ieyasu')
    assert len(g['skins'][0]['joints'])==(92 if commander else 18)
    for im in g['images']:
        uri=im['uri'];data=(stage/'models'/uri).read_bytes();assert hashlib.sha256(data).hexdigest()[:16]==Path(uri).stem
        (out/uri).write_bytes(data)
    shutil.copyfile(src,out/src.name)
    variant=report['variants'][kind];variant.update({k:info[k] for k in ('triangles','bones','materials','bytes','source_bones') if k in info});variant['textures']=len(g['images'])
    if commander:variant['rig']='mpfb-body-v14';variant['continuous_wrists']=True
    if args.detail:
        variant['shared_fittings']='v16';variant['fittings_lod']='commander' if commander else 'crowd'
        if commander:variant['wrists_vs_v15']=info['wrists_vs_v15']
    if args.physique:variant['physique']=info['physique']
    elif not args.detail:variant.pop('physique',None)
    if not commander:continue
    name='hero-bake.json' if kind=='yukimura' else 'ieyasu-bake.json';bake=json.loads((out/name).read_text());bake['runtime_triangles']=info['triangles'];bake['runtime_note']='Original painted armor bake retained; continuous MPFB arms and fitted kote use separate material sections.';(out/name).write_text(json.dumps(bake,indent=2)+'\n')
report['generator']='modular-samurai-v16-shared-fittings' if args.detail else 'modular-samurai-v15-warrior-physique' if args.physique else 'modular-samurai-v14-fullbody-retarget'
if args.detail:
    shared={}
    for kind in report['variants']:
        raw=(out/f'{kind}.glb').read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
        for im in g['images']:shared[im['uri']]=(out/im['uri']).stat().st_size
    report['shared_textures']=shared;report['shared_texture_bytes']=sum(shared.values())
    for name in ('forged-detail.png','woven-detail.png'):shutil.copyfile(stage/'look'/name,ROOT/'public/look'/name)
    report['shared_fittings_source']='tools/detail_commanders.py';report['shared_fittings_lods']={'commander':{'material_sections':4},'crowd':{'material_sections':1}}
    detail_maps={}
    for name in ('forged-detail.png','woven-detail.png'):
        data=(ROOT/'public/look'/name).read_bytes();detail_maps[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'resolution':512}
    detail_manifest={'source':'tools/detail_commanders.py','maps':detail_maps,'channels':'R albedo, G normal Y, B roughness, A normal X','shared_by':['yukimura','ieyasu','ashigaru','tokugawa'],'runtime_distance_lod':False}
    (ROOT/'public/look/details.json').write_text(json.dumps(detail_manifest,indent=2)+'\n')
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('Installed reviewed models:',report['generator'])
