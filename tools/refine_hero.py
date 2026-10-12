"""Hero-only armour kit. Authored in the same rest space as the shared soldiers.

Closed curved plates, continuous antlers and shaped cloth replace coarse kit parts.
Low-poly parts feed the dedicated high-poly bake and 18-bone rig; no paid service.
"""
import math
import bpy
from mathutils import Vector

HERO_COLORS = {'armor':(.34,.011,.017,1), 'gold':(.68,.44,.15,1),
               'skin':(.13,.065,.035,1), 'steel':(.67,.74,.79,1)}

def refine_hero(parts, mesh, rod, sphere, cube):
    added = []

    def keep(obj):
        added.append(obj.name)
        return obj

    def plate(name, rows, role='armor', thickness=.008, bevel=.003):
        """Quad grid with actual thickness, authored UVs and small edge catchlights."""
        h, w = len(rows), len(rows[0])
        obj = mesh(name, [p for row in rows for p in row],
                   [(r*w+c, r*w+c+1, (r+1)*w+c+1, (r+1)*w+c)
                    for r in range(h-1) for c in range(w-1)], role)
        uv = obj.data.uv_layers.new(name='PaintedAtlas')
        for loop in obj.data.loops:
            vi = loop.vertex_index
            uv.data[loop.index].uv = ((vi % w)/(w-1), 1-(vi//w)/(h-1))
        obj['authored_uv'] = True
        if thickness:
            mod = obj.modifiers.new('forged plate thickness', 'SOLIDIFY')
            mod.thickness = thickness; mod.offset = 0
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=mod.name)
        if bevel:
            mod = obj.modifiers.new('worn rounded edge', 'BEVEL')
            mod.width = bevel; mod.segments = 2; mod.affect = 'EDGES'
            mod.angle_limit = .6
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=mod.name)
        # Continuous normals on curved lacquer avoid a hard edge (and duplicate
        # glTF vertices) at every grid cell. Keep the menpo's sculpted planes crisp.
        if role=='armor' and not name.startswith('menpo'):
            for poly in obj.data.polygons:poly.use_smooth=True
        return keep(obj)

    def tube(name, points, radii, role, sides=8):
        """Continuous tapered branch/cord; avoids stacked cone joints."""
        verts = []
        for i, p in enumerate(points):
            tangent = Vector(points[min(i+1, len(points)-1)]) - Vector(points[max(0, i-1)])
            tangent.normalize()
            axis = tangent.cross(Vector((0, 1, 0))).normalized()
            other = tangent.cross(axis).normalized()
            for j in range(sides):
                a = j*math.tau/sides
                verts.append(Vector(p)+radii[i]*(axis*math.cos(a)+other*math.sin(a)))
        faces = [(r*sides+j, r*sides+(j+1)%sides, (r+1)*sides+(j+1)%sides, (r+1)*sides+j)
                 for r in range(len(points)-1) for j in range(sides)]
        faces += [tuple(range(sides-1, -1, -1)), tuple(range((len(points)-1)*sides, len(points)*sides))]
        obj = keep(mesh(name, verts, faces, role))
        for poly in obj.data.polygons: poly.use_smooth = True
        return obj

    def stitch(name, a, b, role='cloth', radius=.006):
        return keep(rod(name, a, b, radius, role, sides=6))

    def crest(name, x, y, z, radius, flat=False):
        # Six mon with square centres, flat brass faces; not wire hoops.
        n = 16; verts = []
        for depth in [0, .005 if flat else .009]:
            for inner in [False, True]:
                for i in range(n):
                    a = i*math.tau/n
                    r = radius*.31/max(abs(math.cos(a)), abs(math.sin(a))) if inner else radius
                    verts.append((x+math.cos(a)*r, y-depth, z+math.sin(a)*r))
        faces = []
        for i in range(n):
            j = (i+1)%n
            faces += [(i,j,n+j,n+i), (2*n+i,3*n+i,3*n+j,2*n+j),
                      (i,2*n+i,2*n+j,j), (n+i,n+j,3*n+j,3*n+i)]
        # Extrusion is toward -Y. The original winding pointed into the solid,
        # which double-sided rendering hid but selected-to-active baking exposed.
        return keep(mesh(name, verts, [tuple(reversed(face)) for face in faces], 'gold'))

    # A fitted do: broad upper chest and distinct waist. Four forged horizontal
    # sections instead of ten equally spaced rings around a cylindrical body.
    levels = [(1.36,.285,.172),(1.27,.310,.199),(1.17,.295,.198),(1.06,.267,.177),(.956,.253,.164)]
    for band in range(4):
        z0,rx0,ry0 = levels[band]; z1,rx1,ry1 = levels[band+1]
        for back in [False, True]:
            rows = []
            for row in range(4):
                t = row/3; z = z0+(z1-z0)*t
                rx = rx0+(rx1-rx0)*t; ry = ry0+(ry1-ry0)*t
                line = []
                for col in range(13):
                    a = (col/12-.5)*math.pi
                    y = max(0,math.cos(a))**.55*ry*(1 if back else -1)
                    line.append((math.sin(a)*rx,y,z+.006*math.cos(a)))
                rows.append(line)
            plate(f'cuirass.hero.{band}.{back}', rows, thickness=.013)
        for sign in [-1,1]:
            for x in [.11,.235]:
                y = -ry1*math.sqrt(max(0,1-(x/rx1)**2))-.01
                keep(sphere(f'cuirass.hero.rivet.{band}.{sign}.{x}',(sign*x,y,z1+.028),(.006,.005,.006),'gold',8,4))
    for side in [-1,1]:
        # Shoulder straps wrap over the do, dark edging and brass terminals.
        rows = [[(side*(.16+c*.047), -.177+t*.34,1.333+.04*math.sin(t*math.pi)) for c in range(2)] for t in [0,.25,.5,.75,1]]
        plate(f'cuirass.hero.strap.{side}', rows, 'cloth', .012)
        for z in [1.287,1.327]:
            stitch(f'cuirass.hero.buckle.{side}.{z}',(side*.163,-.191,z),(side*.205,-.191,z),'gold',.007)

    # Smooth dome with a flattened crown and shaped projecting peak.
    rows=[]
    for row in range(9):
        t=row/8; phi=t*math.pi*.5
        rows.append([(math.cos(a)*(.018+.201*math.sin(phi)),.014+math.sin(a)*(.015+.192*math.sin(phi)),1.694+.191*math.cos(phi)**.75)
                     for a in [j*math.tau/32 for j in range(33)]])
    obj=plate('kabuto.hero.dome',rows,thickness=.009,bevel=0)
    for p in obj.data.polygons:p.use_smooth=True
    plate('kabuto.hero.peak', [[(u*.221,-.152-(1-u*u)*(.074+t*.067),1.691-t*.026+(u*u)*.003) for u in [-1,-.75,-.5,-.25,0,.25,.5,.75,1]] for t in [0,.5,1]],thickness=.014)
    for j in range(12):
        a=j*math.tau/12
        pts=[(math.cos(a)*(.02+.203*math.sin(t)),.014+math.sin(a)*(.017+.194*math.sin(t)),1.694+.194*math.cos(t)**.75) for t in [.08,.3,.55,.8,1.05,1.3,1.52]]
        tube(f'kabuto.hero.rib.{j}',pts,[.004]*len(pts),'armor',6)
    for row in range(5):
        rows=[]
        for t in [0,.5,1]:
            rx=.214+row*.012+t*.012; ry=.201+row*.010+t*.014
            rows.append([(math.cos(a)*rx,.015+math.sin(a)*ry,1.685-row*.040-t*.048)
                         for a in [-.30+j*(math.pi+.60)/24 for j in range(25)]])
        plate(f'kabuto.hero.shikoro.{row}',rows,thickness=.009)
        for j in range(11):
            a=-.20+j*(math.pi+.4)/10
            x=math.cos(a)*(.226+row*.012); y=.015+math.sin(a)*(.218+row*.010)
            stitch(f'kabuto.hero.lace.{row}.{j}',(x,y,1.676-row*.040),(x*1.024,y*1.024,1.645-row*.040),radius=.005)
    for side in [-1,1]:
        plate(f'kabuto.hero.cheekwing.{side}',[[(side*.213,-.112,1.683),(side*.278,-.077,1.708)],[(side*.226,-.102,1.581),(side*.279,-.060,1.599)]],thickness=.012)

    # A dark full menpo silhouette, stern cheeks, central nasal ridge and lip.
    # Only the eye slit exposes skin; this closes the old toy-like pale muzzle.
    keep(sphere('face.hero',(0,-.013,1.586),(.129,.117,.137),'skin',24,12))
    plate('menpo.hero.base',[
        [(-.133,-.108,1.605),(-.083,-.163,1.598),(0,-.177,1.574),(.083,-.163,1.598),(.133,-.108,1.605)],
        [(-.137,-.116,1.541),(-.083,-.191,1.535),(0,-.214,1.531),(.083,-.191,1.535),(.137,-.116,1.541)],
        [(-.116,-.113,1.479),(-.062,-.183,1.460),(0,-.194,1.459),(.062,-.183,1.460),(.116,-.113,1.479)],
        [(-.07,-.118,1.443),(-.035,-.151,1.420),(0,-.164,1.412),(.035,-.151,1.420),(.07,-.118,1.443)]], 'armor', .012,.003)
    plate('menpo.hero.nose',[[(-.033,-.178,1.591),(0,-.218,1.598),(.033,-.178,1.591)],
                             [(-.045,-.195,1.537),(0,-.237,1.538),(.045,-.195,1.537)]], 'armor', .008)
    for side in [-1,1]:
        plate(f'menpo.hero.cheek.{side}',[[(side*.029,-.201,1.531),(side*.076,-.197,1.552),(side*.123,-.146,1.564)],
                                         [(side*.044,-.202,1.506),(side*.088,-.180,1.514),(side*.126,-.138,1.537)]], 'armor', .006)
        stitch(f'mask.hero.brow.{side}',(side*.026,-.171,1.619),(side*.121,-.149,1.636),'cloth',.012)
        stitch(f'mask.hero.eye.{side}',(side*.037,-.176,1.611),(side*.109,-.160,1.620),'eye',.005)
        stitch(f'mask.hero.mouth.{side}',(0,-.210,1.485),(side*.067,-.194,1.493),'eye',.006)
        tube(f'mask.hero.chinlace.{side}',[(side*.144,-.096,1.58),(side*.158,-.118,1.49),(side*.067,-.172,1.417)], [.008,.008,.009],'lace')
    for row in range(3):
        plate(f'neck.hero.gorget.{row}', [[(u*.126,-.118-.041*(1-u*u),1.416-row*.028-t*.032) for u in [-1,-.5,0,.5,1]] for t in [0,1]],thickness=.008)

    # Continuous organic antlers, lower splay and deliberately unequal tips.
    for side in [-1,1]:
        paths=[[(.134,.005,1.843),(.195,.013,1.945),(.273,.022,2.078),(.302,.041,2.25),(.281,.062,2.408),(.315,.072,2.505)],
               [(.218,.018,1.988),(.354,.021,2.075),(.409,.04,2.208),(.402,.052,2.31)],
               [(.294,.04,2.195),(.214,.016,2.289),(.201,.012,2.391)],
               [(.291,.059,2.383),(.371,.06,2.435),(.391,.058,2.519)]]
        for branch,points in enumerate(paths):
            coords=[(x*side,y,z+(.017*math.sin(i*1.3) if side<0 else 0)) for i,(x,y,z) in enumerate(points)]
            radii=[(.036 if branch==0 else .020)*(1-i/(len(points)-.3)) for i in range(len(points))]
            tube(f'antler.hero.{side}.{branch}',coords,radii,'horn',10)
        tube(f'antler.hero.socket.{side}',[(side*.132,.005,1.837),(side*.162,.008,1.889)],[.045,.043],'gold',12)
    for i in range(3):
        for j in range(2):
            obj=crest(f'helmet.coin.hero.{i}.{j}',(i-1)*.066,-.197,1.731+j*.060,.026)
            for v in obj.data.vertices:
                # Match the dome, including the disc rims; no floating flat badge.
                c=max(0,min(1,(v.co.z-1.694)/.191))**(1/.75)
                s=math.sqrt(1-c*c);rx=.018+.201*s;ry=.015+.192*s
                relief=.006 if v.co.y<-.198 else .002
                v.co.y=.014-ry*math.sqrt(max(0,1-(v.co.x/rx)**2))-relief
            obj=crest(f'cuirass.hero.coin.{i}.{j}',(i-1)*.087,-.209,1.176+j*.079,.032,True)
            for v in obj.data.vertices:
                for band in range(4):
                    z0,rx0,ry0=levels[band];z1,rx1,ry1=levels[band+1]
                    if z1<=v.co.z<=z0:
                        t=(z0-v.co.z)/(z0-z1);rx=rx0+(rx1-rx0)*t;ry=ry0+(ry1-ry0)*t
                        relief=.009 if v.co.y<-.210 else .006
                        v.co.y=-ry*max(0,1-(v.co.x/rx)**2)**.275-relief
                        break

    # Broad, rounded sode hang over the arms in five solid lames.
    for side in [-1,1]:
        for row in range(5):
            def pos(u,t):
                x=side*(.335+row*.029+t*.045+.080*math.cos(u*math.pi/2))
                y=u*(.184-row*.003)
                z=1.405-row*.058-t*.066-.036*u*u
                return (x,y,z)
            plate(f'sode.hero.{side}.{row}',[[pos(u,t) for u in [-1,-.66,-.33,0,.33,.66,1]] for t in [0,.5,1]],thickness=.011)
            for u in [-.8,-.3,.3,.8]:
                a=Vector(pos(u,.17));b=Vector(pos(u,.84));a.x+=side*.011;b.x+=side*.011
                stitch(f'sode.hero.lace.{side}.{row}.{u}',a,b,radius=.006)
            for u in [-.93,.93]:
                p=Vector(pos(u,.78));p.x+=side*.01
                keep(sphere(f'sode.hero.rivet.{side}.{row}.{u}',p,(.006,.006,.006),'gold',6,4))
        plate(f'sode.hero.crown.{side}',[[(side*(.248+t*.19),u*.158,1.396+.04*math.sin(t*math.pi)-.038*u*u) for u in [-1,-.5,0,.5,1]] for t in [0,.33,.66,1]],thickness=.012)

    # Seven separate skirt tassets. Five overlapping plates per tasset and
    # longitudinal cords create real breaks in silhouette, not a printed skirt.
    for panel in range(7):
        angle=math.pi+panel*math.tau/7
        for row in range(5):
            def pos(u,t):
                depth=row+t
                a=angle+u*.34
                r=.257+depth*.022
                return (math.sin(a)*r,math.cos(a)*r*.78,.911-depth*.063+.008*(1-u*u))
            plate(f'kusazuri.hero.{panel}.{row}',[[pos(u,t) for u in [-1,-.5,0,.5,1]] for t in [0,.6,1.12]],thickness=.009)
            for u in [-.68,.68]:
                a=Vector(pos(u,.15));b=Vector(pos(u,.87))
                a.x*=1.021;a.y*=1.021;b.x*=1.021;b.y*=1.021
                stitch(f'kusazuri.hero.cord.{panel}.{row}.{u}',a,b,radius=.005)
            # Bright, restrained rivets at the outer lower corners.
            if row in [0,4]:
                for u in [-.85,.85]:
                    p=Vector(pos(u,.85));p.x*=1.026;p.y*=1.026
                    keep(sphere(f'kusazuri.hero.rivet.{panel}.{row}.{u}',p,(.005,.005,.005),'gold',6,3))

    # Tapered vambraces over cloth; raised splints with broad lacquer planes.
    for side in [-1,1]:
        keep(rod(f'upper_arm.hero.{side}',(side*.31,0,1.32),(side*.43,-.025,1.10),.089,'cloth',tip=.078,sides=16))
        keep(rod(f'forearm.hero.underlay.{side}',(side*.43,-.025,1.10),(side*.47,-.16,.94),.074,'cloth',tip=.061,sides=12))
        for strip in range(3):
            rows=[]
            for t in [0,.3,.7,1]:
                z=1.099-t*.145;x=side*(.43+t*.04);y=-.034-t*.115
                rows.append([(x+side*math.sin(a)*(.085-t*.016),y-math.cos(a)*(.085-t*.016),z)
                             for a in [(strip-1)*.54+(c/2-.5)*.49 for c in range(3)]])
            plate(f'forearm.hero.{side}.{strip}',rows,thickness=.009)

    # Gathered hakama: broad mid-thigh folds tighten into the knee instead of
    # flat black apron rectangles. Eight broad pleats remain legible at distance.
    for side in [-1,1]:
        rows=[]
        for i,(z,r) in enumerate([(.86,.13),(.79,.153),(.69,.161),(.58,.15),(.50,.125),(.465,.089)]):
            rows.append([(side*.145+math.cos(a)*r*(1+.085*math.cos(a*8+i*.3)),
                          .013+math.sin(a)*r*.89*(1+.085*math.cos(a*8+i*.3)),z)
                         for a in [j*math.tau/32 for j in range(33)]])
        plate(f'thigh.hero.hakama.{side}',rows,'cloth',.004,0)

        # Low tabi profile and curved toe; a thin sole replaces the block boot.
        rows=[]
        for z,rx,ry,cy in [(.009,.077,.145,-.075),(.036,.077,.145,-.075),(.080,.070,.133,-.067),(.13,.050,.079,-.018)]:
            rows.append([(side*.145+math.cos(a)*rx,cy+math.sin(a)*ry,z) for a in [j*math.tau/16 for j in range(17)]])
        plate(f'boot.hero.tabi.{side}',rows,'cloth',.006,0)
        stitch(f'sandal.hero.toe.{side}',(side*.145,-.197,.076),(side*.145,-.082,.118),'lace',.009)

    # Cape is a continuous draped surface; torn edges are fine irregular tips
    # rather than large triangular holes. The six-coin motif follows its folds.
    def cloth(u,t):
        x=(u-.5)*(.48+t*.52)-.14*t*t
        y=.203+t*.26+math.sin(u*math.pi*7+t*2)*(.012+t*.048)
        z=1.396-t*1.065
        return (x,y,z)
    rows=[]
    for r in range(27):
        t=r/26;line=[]
        for c in range(23):
            u=c/22;x,y,z=cloth(u,t)
            if r==26:z+=.026*math.sin(c*2.9)+.027*math.cos(c*5.2)
            if c in [0,22]:x+=.013*math.sin(r*2.1)*t
            line.append((x,y,z))
        rows.append(line)
    obj=plate('cape.hero.drape',rows,'cape',.003,0)
    for p in obj.data.polygons:p.use_smooth=True
    # Actual cloth inlay (discs with square openings), lightly inset into folds.
    for i in range(3):
        for j in range(2):
            x,y,z=cloth(.5+(i-1)*.15,.24+j*.083)
            obj=crest(f'cape.hero.coin.{i}.{j}',x,y+.014,z,.032,True)
            for v in obj.data.vertices:
                t=(1.396-v.co.z)/1.065;u=(v.co.x+.14*t*t)/(.48+t*.52)+.5
                v.co.y=cloth(u,t)[1]+.005
    # Fabric collar and two bronze cloak clasps.
    for side in [-1,1]:
        tube(f'neck.hero.fold.{side}',[(side*.18,.09,1.37),(side*.137,-.105,1.381),(0,-.151,1.367)], [.027,.024,.018],'cape',10)
        keep(sphere(f'cuirass.hero.clasp.{side}',(side*.19,-.16,1.354),(.029,.011,.028),'gold',12,6))

    # Higher quality shaft bindings and faceted, ridged jumonji blades.
    # Compact closed gauntlets, articulated fingers around the grip and a thumb.
    for side in [-1,1]:
        keep(sphere(f'glove.hero.{side}',(side*.47,-.16,.91),(.061,.063,.071),'cloth',12,8))
        plate(f'glove.hero.plate.{side}',[[(side*.47+u*.048,-.204,1.0-t*.062) for u in [-1,0,1]] for t in [0,.5,1]],'armor',.006,.002)
        for j in range(4):
            x=side*.47+(j-1.5)*.021
            tube(f'finger.hero.{side}.{j}',[(x,-.209,.935),(x,-.221,.915),(x,-.198,.887),(x,-.175,.891)], [.010,.011,.010,.008],'cloth',6)
        tube(f'finger.hero.thumb.{side}',[(side*.515,-.178,.948),(side*.512,-.217,.927),(side*.495,-.211,.906)],[.015,.013,.009],'cloth',8)
    keep(mesh('yari.hero.blade',[(.47,-.16,3.02),(.52,-.16,2.72),(.47,-.188,2.65),(.42,-.16,2.72),(.47,-.132,2.65)],[(0,1,2),(0,2,3),(0,3,4),(0,4,1),(1,4,3,2)],'steel'))
    for side in [-1,1]:
        keep(mesh(f'yari.hero.cross.{side}',[(.47,-.16,2.776),(.47+side*.225,-.16,2.77),(.47+side*.30,-.16,2.733),(.47+side*.225,-.16,2.697),(.47,-.16,2.69),(.47+side*.12,-.181,2.733),(.47+side*.12,-.139,2.733)],[(0,1,5),(1,2,5),(2,3,5),(3,4,5),(4,0,5),(1,0,6),(2,1,6),(3,2,6),(4,3,6),(0,4,6)],'steel'))
    for z in [.72,.99,2.46,2.56]:
        tube(f'yari.hero.ferrule.{z}',[(.47,-.16,z),(.47,-.16,z+.028)],[.028,.028],'gold',12)
    for j in range(16):
        z=1.0+j*.023
        pts=[(.47+math.cos(a)*.025,-.16+math.sin(a)*.025,z+a/math.tau*.02) for a in [k*math.tau/8 for k in range(9)]]
        tube(f'yari.hero.binding.{j}',pts,[.005]*9,'cape',6)
    return added


def hero_parts(names):
    """Keep limbs, straps and weapons shared; replace only authored hero regions."""
    replaced = ('cuirass.band','cuirass_lace','cuirass.rivet','rokumon',
                'kabuto.','helmet.coin','antler.','menpo','mask.mouth',
                'sode.','sode_lace','kusazuri.','cape','neck.scarf',
                'forearm.','bracer.inlay','kote.splint','face','eye.','thigh.','haidate.',
                'upper_arm.','boot.','yari.blade','yari.cross.','glove.','finger.')
    return [name for name in names if not name.startswith(replaced)]
