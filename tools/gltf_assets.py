"""Extract identical embedded atlases once; retain binary GLB geometry/animation."""
import json
import struct
import hashlib

def share_images(path):
    raw=path.read_bytes();length=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+length]);start=20+length+8;binary=raw[start:]
    removed=set();shared={}
    for image in doc.get('images',[]):
        index=image.pop('bufferView');view=doc['bufferViews'][index];offset=view.get('byteOffset',0)
        data=binary[offset:offset+view['byteLength']]
        filename='shared/'+hashlib.sha256(data).hexdigest()[:16]+'.png'
        target=path.parent/filename;target.parent.mkdir(exist_ok=True);target.write_bytes(data)
        image['uri']=filename;removed.add(index);shared[filename]=len(data)
    packed=bytearray();views=[];mapping={}
    for index,view in enumerate(doc['bufferViews']):
        if index in removed:continue
        while len(packed)%4:packed.append(0)
        offset=view.get('byteOffset',0);copy=dict(view);copy['byteOffset']=len(packed)
        packed.extend(binary[offset:offset+view['byteLength']]);mapping[index]=len(views);views.append(copy)
    def remap(value):
        if isinstance(value,dict):
            for k,v in value.items():
                if k=='bufferView':value[k]=mapping[v]
                else:remap(v)
        elif isinstance(value,list):
            for v in value:remap(v)
    doc['bufferViews']=views;remap(doc)
    while len(packed)%4:packed.append(0)
    doc['buffers'][0]['byteLength']=len(packed)
    js=json.dumps(doc,separators=(',',':')).encode()
    js+=b' '*((-len(js))%4)
    total=12+8+len(js)+8+len(packed)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,total)+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(packed),b'BIN\0')+packed)
    return shared
