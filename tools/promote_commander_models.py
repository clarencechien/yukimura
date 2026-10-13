"""Promote staged commander exports while preserving the two troop GLBs."""
from pathlib import Path
import json,struct,shutil,hashlib
ROOT=Path(__file__).resolve().parent.parent
STAGE=ROOT/'.tmp/commanders-v13';OUT=ROOT/'public/models'
old=json.loads((OUT/'manifest.json').read_text());new=json.loads((STAGE/'models/manifest.json').read_text())
for name in ('yukimura','ieyasu'):
 raw=(STAGE/'models'/f'{name}.glb').read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
 for im in g['images']:
  uri=im['uri'];assert uri.startswith('shared/') and '..' not in uri
  data=(STAGE/'models'/uri).read_bytes();assert hashlib.sha256(data).hexdigest()[:16]==Path(uri).stem
  (OUT/uri).write_bytes(data)
 (OUT/f'{name}.glb').write_bytes(raw);old['variants'][name]=new['variants'][name]
for file in ('hero-bake.json','ieyasu-bake.json'):shutil.copyfile(STAGE/'models'/file,OUT/file)
shared={}
for name in old['variants']:
 raw=(OUT/f'{name}.glb').read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
 for im in g['images']:shared[im['uri']]=(OUT/im['uri']).stat().st_size
for uri in old['shared_textures']:
 if uri not in shared:(OUT/uri).unlink()
old.update(generator=new['generator'],unique_source_parts=new['unique_source_parts'],shared_textures=shared,shared_texture_bytes=sum(shared.values()))
(OUT/'manifest.json').write_text(json.dumps(old,indent=2)+'\n')
shutil.copyfile(STAGE/'samurai-kit.blend',ROOT/'assets/source/samurai-kit.blend')
print(json.dumps({n:old['variants'][n] for n in ('yukimura','ieyasu')},indent=2))
