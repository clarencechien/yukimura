"""Deterministic shared pigment/ORM/normal atlas; Blender's bundled NumPy only.
No downloads, image generation, baking service or per-character texture copies on disk.
"""
import bpy
import numpy as np
import math

TILES = {'lamella':0, 'skirt':1, 'cloth':2, 'cape':3, 'gold':4,
         'steel':5, 'wood':6, 'lace':7, 'skin':8, 'eye':9,
         'helmet':10, 'leather':11, 'bracer':12, 'banner':13, 'mask':14, 'boot':15}
SIZE=1024

def make_atlas():
    n=SIZE//4
    y,x=np.mgrid[0:n,0:n].astype(float);u=x/(n-1);v=y/(n-1)
    rng=np.random.default_rng(1615)
    pigment=np.zeros((SIZE,SIZE,4),dtype=np.float32)
    orm=np.zeros_like(pigment);normal=np.zeros_like(pigment)
    for name,i in TILES.items():
        grain=rng.normal(0,.012,(n,n))
        brush=.035*np.sin(u*83+np.sin(v*14)*3)*np.sin(v*27+u*13)
        # Broad rubbed pigment patches plus fine dry-brush grain, not uniform plastic.
        blotch=.10*np.sin(u*18+np.sin(v*11)*2)*np.sin(v*23+np.sin(u*13))
        shade=np.clip(.80+brush+grain+blotch,.48,1)
        rough=np.full((n,n),.78);metal=np.zeros((n,n));height=np.zeros((n,n))
        if name in ('lamella','skirt','helmet','bracer','mask'):
            rows=1 if name in ('lamella','helmet','mask') else 5
            row=(v*rows)%1
            edge=np.minimum(row,1-row)
            seam=np.exp(-edge*75)
            shade*=1-seam*.60
            shade+=np.exp(-((row-.085)/.025)**2)*.17
            height+=np.minimum(edge*10,1)*.12
            # Punched lamellar plates, paired dark silk lacing and rubbed gilt edges.
            col=(u*6)%1
            for pos in ((.26,.40,.76,.90) if name in ('lamella','skirt','bracer') else ()):
                stitch=np.exp(-((col-pos)/.034)**2)*((row>.24)&(row<.69))
                shade*=1-stitch*.48;height+=stitch*.10
                hole=np.exp(-((col-pos)/.085)**2-((row-.22)/.065)**2)
                shade*=1-hole*.7
            border=np.exp(-np.minimum(u,1-u)*110)
            shade*=1-border*.55
            # Sparse dry-brush lacquer chips, biased toward worn plate edges.
            chips=(rng.random((n,n))>.97)&((edge<.14)|(np.sin(u*69+v*38)>.94))
            shade=np.where(chips,1.18,shade);height-=chips*.09
            shade*=1-((np.sin(u*38+v*17)*np.sin(v*39-u*8))>.83)*.24
            for _ in range(33):
                sx,sy=rng.random(2);length=rng.uniform(.015,.12)
                scratch=(np.abs(u-sx-(v-sy)*.22)<.0018)&(v>sy)&(v<sy+length)
                shade=np.where(scratch,1.05,shade);height-=scratch*.08
            # Lacquer gets broad, broken highlights; exposed chips are metallic.
            rough[:]=.43;rough+=seam*.25+blotch*.65;metal[:]=.08;metal[chips]=.58
        elif name in ('cloth','cape','banner','boot','leather'):
            folds=(np.sin(u*math.pi*8+np.sin(v*5)*.7)+1)*.5
            shade*=.76+.24*folds
            shade+=.018*np.sin(u*790)*np.sin(v*790)
            height+=folds*.18
            hem=np.exp(-np.minimum(u,1-u)*100)+np.exp(-np.minimum(v,1-v)*100)
            shade*=1-np.minimum(hem,1)*.34
            # Chalky dust near hems, fibres and scattered scuffed pigment.
            shade+=((1-v)**4)*np.maximum(0,grain+brush)*1.8
            shade+=((np.sin(u*490+v*19)>.97)&(rng.random((n,n))>.6))*.09
            rough[:]=.95
        elif name=='gold':
            shade=.92+brush*.6+grain
            filigree=np.exp(-(np.sin(u*36+np.sin(v*22)*2)/.20)**2)
            shade*=1-filigree*.16;height+=filigree*.05;metal[:]=.52;rough[:]=.40
        elif name=='steel':
            shade*=.65+.35*np.abs(u-.5)*2
            shade+=.08*np.sin(u*260+v*2);metal[:]=.82;rough[:]=.40
        elif name=='wood':
            shade*=.65+.35*np.sin(u*120+np.sin(v*9))**2;rough[:]=.88
        elif name=='lace':
            weave=(np.sin(u*65+v*75)*np.sin(u*65-v*75)+1)*.5
            shade*=.58+.42*weave;height+=weave*.12;rough[:]=.90
        elif name=='skin':
            shade*=.78+.22*np.sin(v*math.pi);rough[:]=.86
        else:shade[:]=.55;rough[:]=.80
        # Very restrained ochre scumble (vertex color supplies each army's palette).
        rgb=np.stack((shade,shade*.97,shade*.91),axis=-1)
        dy,dx=np.gradient(height)
        normals=np.stack((-dx*7,-dy*7,np.ones_like(dx)),axis=-1)
        normals/=np.linalg.norm(normals,axis=-1,keepdims=True)
        yy=(i//4)*n;xx=(i%4)*n
        pigment[yy:yy+n,xx:xx+n,:3]=np.clip(rgb,0,1)
        orm[yy:yy+n,xx:xx+n,:3]=np.stack((np.ones_like(rough),rough,metal),axis=-1)
        normal[yy:yy+n,xx:xx+n,:3]=normals*.5+.5
    result=[]
    for name,data,colorspace in [('pigment',pigment,'sRGB'),('surface',orm,'Non-Color'),('relief',normal,'Non-Color')]:
        data[:,:,3]=1
        # Keep normal/ORM at 512; pigment gets the detail budget.
        if name!='pigment':data=data[::2,::2].copy()
        im=bpy.data.images.new('shared_painted_'+name,width=data.shape[1],height=data.shape[0],alpha=False)
        im.colorspace_settings.name=colorspace;im.pixels.foreach_set(data.ravel());im.pack();result.append(im)
    return result

def surface_for(name,role):
    if role=='gold':return 'gold'
    if name.startswith('kusazuri.hero.') and role=='armor':return 'lamella'
    if name.startswith('cuirass.hero.') and role=='armor':return 'mask'
    if name.startswith('cape'):return 'cape'
    if name.startswith('sashimono.cloth'):return 'banner'
    if name.startswith('kusazuri'):return 'skirt'
    if name.startswith(('cuirass.band','sode.')) and role=='armor':return 'lamella'
    if name.startswith(('shin_plate','forearm','haidate')) and role=='armor':return 'bracer'
    if name.startswith('menpo'):return 'mask'
    if name.startswith('boot'):return 'boot'
    if role=='armor':return 'helmet'
    return role if role in TILES else 'leather'

def map_uv(obj,name,role):
    """Surface-aware atlas islands, inset 5px to survive mipmapping."""
    uv=obj.data.uv_layers.active or obj.data.uv_layers.new(name='PaintedAtlas')
    uv.name='PaintedAtlas'
    tile=TILES[surface_for(name,role)]
    if obj.get('authored_uv'):
        for loop in uv.data:
            u,v=loop.uv
            loop.uv=((tile%4+.02+.96*u)/4,(tile//4+.02+.96*v)/4)
        return
    coords=[v.co for v in obj.data.vertices]
    lo=[min(p[a] for p in coords) for a in range(3)];hi=[max(p[a] for p in coords) for a in range(3)]
    # Largest two dimensions are a safe default for straps, weapons and sheets.
    axes=sorted(range(3),key=lambda a:hi[a]-lo[a],reverse=True)
    if name.startswith(('cape','sashimono.cloth','cuirass.band','kabuto','menpo','face','kusazuri','sode')):axes=[0,2]
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            p=coords[obj.data.loops[li].vertex_index]
            a,b=axes[:2]
            u=(p[a]-lo[a])/max(hi[a]-lo[a],.001);v=(p[b]-lo[b])/max(hi[b]-lo[b],.001)
            if name.startswith(('cuirass.band','kabuto.dome','neck.scarf','thigh','shin.','upper_arm','forearm')):
                u=(math.atan2(p.y,p.x)/(2*math.pi)+.5)
                v=(p.z-lo[2])/max(hi[2]-lo[2],.001)
            if name.startswith('kusazuri'):
                vi=obj.data.loops[li].vertex_index;u=(vi%4)/3;v=1-(vi//4)/5
            if name.startswith('sode.'):
                vi=obj.data.loops[li].vertex_index;u=(vi%5)/4;v=(vi//5)/2
            uv.data[li].uv=((tile%4+.02+.96*u)/4,(tile//4+.02+.96*v)/4)

def painted_material(name,images,color=(1,1,1,1),vertex=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=color;m.use_backface_culling=False
    nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF')
    pigment,orm,normal=images
    tex=nodes.new('ShaderNodeTexImage');tex.image=pigment
    mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[1].default_value=color
    if vertex:
        vc=nodes.new('ShaderNodeVertexColor');vc.layer_name='Color';links.new(vc.outputs['Color'],mix.inputs[1])
    links.new(tex.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color'])
    t=nodes.new('ShaderNodeTexImage');t.image=orm
    split=nodes.new('ShaderNodeSeparateColor');links.new(t.outputs['Color'],split.inputs[0]);links.new(split.outputs['Green'],bs.inputs['Roughness']);links.new(split.outputs['Blue'],bs.inputs['Metallic'])
    t=nodes.new('ShaderNodeTexImage');t.image=normal
    bump=nodes.new('ShaderNodeNormalMap');bump.inputs['Strength'].default_value=.38
    links.new(t.outputs['Color'],bump.inputs['Color']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    return m
