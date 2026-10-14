"""Continuous embossed menpo: annular mouth topology, cheeks and nasal wings.

Photo-led proportions, shared commander atlas and head bone. No downloaded art.
"""
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from detail_commanders import Fittings


def sculpted_menpo(mesh, kind):
    skin = next(i for i, m in enumerate(mesh.data.materials) if m.name.startswith('human skin /'))
    polys = [list(p.vertices) for p in mesh.data.polygons if p.material_index == skin]
    skin_tree = BVHTree.FromPolygons([v.co for v in mesh.data.vertices], polys)
    out = Fittings(kind)
    role = 3 if kind == 'yukimura' else 1
    weight = {'body.head': 1.0}
    segments, rings = 80, 18
    scale = 1.025 if kind == 'ieyasu' else 1

    def sculpt(x, z):
        # Embossed facial masses, not a radial offset of the human skin.
        ax = abs(x)
        y = -.253 + .095 * (ax / .125) ** 2
        y -= .036 * math.exp(-(x/.018)**2 - ((z-1.904)/.046)**4)  # nasal bridge
        y -= .064 * math.exp(-(x/.022)**2 - ((z-1.861)/.021)**2)  # rounded nose tip
        y -= .040 * math.exp(-((ax-.029)/.012)**2 - ((z-1.850)/.014)**2)  # alae
        y -= .052 * math.exp(-((ax-.074)/.026)**2 - ((z-1.849)/.023)**2)  # cheek bosses
        y += .010 * math.exp(-((ax-(.041+(1.848-z)*.46))/.006)**2 - ((z-1.821)/.032)**4)
        y -= .015 * math.exp(-(x/.060)**4 - ((z-1.812)/.010)**2)  # upper lip
        y -= .031 * math.exp(-(x/.054)**4 - ((z-1.750)/.023)**2)  # rounded chin
        # Paired embossed cheek creases above the nasolabial folds.
        crease = 1.869 - (ax-.05)*.35
        y += .005 * math.exp(-((z-crease)/.0035)**2 - ((ax-.075)/.024)**4)
        hit, _, _, _ = skin_tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
        if hit is not None:
            y = min(y, hit.y-.012)
        return y

    vertices = []
    for row in range(rings+1):
        t = row/rings
        for col in range(segments):
            a = col/segments*math.tau
            c, s = math.cos(a), math.sin(a)
            ix = .056*c
            iz = 1.794+.020*s-.011*math.exp(-(c/.38)**2)*max(s,0)
            ox = .123*c*(1-.25*max(-s,0))
            oz = 1.812+.088*s+.036*math.exp(-(c/.20)**2)*max(s,0)+.018*abs(c)**1.5*max(s,0)
            x = (ix+(ox-ix)*t)*scale
            z = iz+(oz-iz)*t
            vertices.append(Vector((x,sculpt(x,z),z)))
    exterior = []
    for row in range(rings):
        for col in range(segments):
            a=row*segments+col; b=row*segments+(col+1)%segments
            c=b+segments; d=a+segments
            exterior.extend([(a,d,c),(a,c,b)])
    # Use exactly the exported triangle layout for dense skin clearance probes.
    mesh.data.calc_loop_triangles()
    probes = []
    for tri in mesh.data.loop_triangles:
        if tri.material_index != skin: continue
        a,b,c=[mesh.data.vertices[i].co for i in tri.vertices]
        probes.extend([a,b,c,(a+b)/2,(b+c)/2,(a+c)/2,(a+b+c)/3])
    for _ in range(12):
        hull=BVHTree.FromPolygons(vertices,exterior)
        corrections={}
        for p in probes:
            hit,_,face,_=hull.ray_cast(Vector((p.x,-1,p.z)),Vector((0,1,0)),2)
            if hit is None: continue
            missing=.010-(p.y-hit.y)
            if missing>.00001:
                for i in exterior[face]: corrections[i]=max(corrections.get(i,0),missing)
        if not corrections: break
        for i,delta in corrections.items(): vertices[i].y-=delta
    # Near the concave underside of the human nose, also check the nearest
    # oriented skin surface for both faces of the 2 mm plate. This catches
    # oblique clearance that a forward-only ray does not describe.
    for p in vertices:
        for _ in range(12):
            clear=True
            for thickness in [0,.002]:
                q=p+Vector((0,thickness,0))
                hit,normal,_,distance=skin_tree.find_nearest(q)
                if distance<.001 or (q-hit).dot(normal)<.0001: clear=False
            if clear: break
            p.y-=.001
        assert clear, 'Embossed plate fails oriented skin clearance'
    # Keep the forged plate symmetric even if nearest-triangle selection at a
    # sharp skin crease differs between sides or after a rigid head rotation.
    for row in range(rings+1):
        for col in range(segments):
            mirror=(segments//2-col)%segments
            if col>mirror: continue
            a=vertices[row*segments+col];b=vertices[row*segments+mirror]
            a.y=b.y=min(a.y,b.y)-.003
    hull=BVHTree.FromPolygons(vertices,exterior)

    def front(x,z,offset=.001):
        hit,_,_,_=hull.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
        return Vector((x,(hit.y if hit is not None else sculpt(x,z))-offset,z))

    n=len(vertices)
    vertices += [p+Vector((0,.002,0)) for p in vertices]
    faces=exterior+[tuple(i+n for i in reversed(f)) for f in exterior]
    for row in [0,rings]:
        for col in range(segments):
            a=row*segments+col;b=row*segments+(col+1)%segments
            faces.append((a,b,b+n,a+n) if row==0 else (b,a,a+n,b+n))
    out.add(vertices,faces,[(i%segments/segments,(i//segments)/(rings+1)) for i in range(n)]*2,[weight]*len(vertices),role)
    shell_count=len(vertices)
    dark_ids=set();hair_ids=set()

    # Thick rolled mouth lip and lower/outer rim are actual rounded geometry.
    for row,radius in [(0,.0045),(rings,.0018)]:
        points=[vertices[row*segments+c]+Vector((0,-.001,0)) for c in range(segments)]
        out.tube([(p,weight) for p in points+[points[0]]],radius,role,6)
    # Recessed interior with a continuous mouth perimeter, no quad-shaped hole.
    opening=[vertices[c]+Vector((0,.004,0)) for c in range(segments)]
    center=sum(opening,Vector())/segments
    start=len(out.v)
    out.add(opening+[center],[(c,(c+1)%segments,segments) for c in range(segments)],[(0,0)]*(segments+1),[weight]*(segments+1),0)
    dark_ids.update(range(start,len(out.v)))

    # Elliptical nostril sockets: a raised ala surrounds a recessed dark well.
    for side in [-1,1]:
        center_x=side*.029;center_z=1.846
        rim=[];well=[]
        for i in range(20):
            a=i/20*math.tau
            x=center_x+.010*math.cos(a);z=center_z+.0055*math.sin(a)
            rim.append(front(x,z,.003))
            well.append(front(x,z,.001))
        out.tube([(p,weight) for p in rim+[rim[0]]],.0030,role,6)
        start=len(out.v)
        center=front(center_x,center_z,.001)
        out.add(well+[center],[(i,(i+1)%20,20) for i in range(20)],[(0,0)]*21,[weight]*21,0)
        dark_ids.update(range(start,len(out.v)))
    # Small mounting rivets distinguish forged plate from a cloth face cover.
    for side in [-1,1]:
        for z in [1.858,1.792]:
            out.eyelet((front(side*.098,z,.002),weight),(side*.35,-1,0),.0024)
    # Mouth hardware and moustache are fitted onto the same sculpted surface.
    if kind=='ieyasu':
        for side in [-1,1]:
            for strand in range(12):
                points=[]
                for j in range(8):
                    t=j/7;x=side*(.012+.047*t)
                    z=1.818+.009*math.sin(t*math.pi)+(strand-5.5)*.0012
                    points.append((front(x,z,.004+(strand%3)*.0005),weight))
                start=len(out.v);out.tube(points,.0009,0,4);hair_ids.update(range(start,len(out.v)))
        for i in range(9):
            x=(i-4)*.010
            p=front(x,1.808,.003)
            out.add([p+Vector((-.003,0,0)),p+Vector((.003,0,0)),p+Vector((.002,0,-.006)),p+Vector((-.002,0,-.006))],[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)],[weight]*4,2)
    mat=next(m for m in mesh.data.materials if m.name=='samurai woven cords and fittings')
    ob=out.object(mat);ob.name='embossed menpo with continuous lip'
    assert ob.data.polygons[0].normal.y < 0
    colors=ob.data.color_attributes['Color'];uv=ob.data.uv_layers.active
    for loop in ob.data.loops:
        i=loop.vertex_index
        if out.roles[i]==role:
            colors.data[loop.index].color=(.25,.014,.008,1) if kind=='yukimura' else (.045,.043,.035,1)
        if i in dark_ids:colors.data[loop.index].color=(.001,.001,.001,1)
        if i in hair_ids:colors.data[loop.index].color=(.25,.23,.19,1)
        if out.roles[i] in (role,0):
            # Avoid a cloth normal pattern over embossed metal and dark recesses.
            center=Vector((.75,.75 if role==3 else .25)) if out.roles[i]==role else Vector((.25,.25))
            uv.data[loop.index].uv=center+(uv.data[loop.index].uv-center)*.008
    return ob,{'shell_vertices':shell_count,'vertices':len(out.v),'shell_thickness_m':.002,
        'minimum_authored_front_clearance_m':.010,'mouth_opening':True,'eye_openings':0,
        'reference_form':'embossed menpo: continuous lip, alar sockets, cheek bosses, rounded chin',
        'shared_material':mat.name,'bone':'body.head','new_textures':0,
        'topology':{'angular_segments':segments,'radial_rings':rings,'sculpted_shell_triangles':len(exterior)*2+segments*4}}
