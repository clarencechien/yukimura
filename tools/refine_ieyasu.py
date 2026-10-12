"""Black/gold commander assembled from the hero's forged armour library.
The fern frontlet and stylised aoi are game designs, not a museum reconstruction.
"""
import math
IEYASU_COLORS={'armor':(.028,.041,.032,1),'gold':(.58,.39,.14,1),
              'cloth':(.027,.025,.022,1),'cape':(.095,.079,.045,1),
              'lace':(.56,.47,.30,1),'skin':(.15,.085,.045,1),'steel':(.62,.69,.72,1)}

def commander_parts(hero_details):
    return [n for n in hero_details if not n.startswith(('antler.','helmet.coin.','yari.')) and '.coin.' not in n]

def refine_ieyasu(mesh,rod,sphere):
    names=[]
    def keep(obj):names.append(obj.name);return obj
    # Fern-like layered frontlet, replacing Yukimura's antlers completely.
    for side in [-1,1]:
        for i in range(7):
            z=1.80+i*.049;x=side*(.025+i*.012)
            end=(side*(.24-i*.012),-.198,1.92+i*.067)
            keep(mesh(f'kabuto.ieyasu.fern.{side}.{i}',[(x,-.22,z),(end[0],end[1],end[2]),(end[0]+side*.035,end[1],end[2]+.047),(x+side*.023,-.224,z-.015),(x,-.231,z+.028)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(3,2,1,0)],'gold'))
        keep(rod(f'kabuto.ieyasu.stem.{side}',(side*.026,-.222,1.80),(side*.109,-.20,2.23),.012,'gold',tip=.006,sides=10))
    # Three heart-shaped leaves in a circular frame, two chest/helmet emblems.
    for prefix,cy,cz,radius in [('cuirass.ieyasu',-.217,1.20,.098),('kabuto.ieyasu',-.208,1.754,.057)]:
        for j in range(3):
            angle=j*math.tau/3
            verts=[(0,cy-.013,cz)]
            for k in range(24):
                a=k*math.tau/24
                x=16*math.sin(a)**3/18*radius*.57
                z=(13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a))/18*radius*.55+radius*.36
                verts.append((x*math.cos(angle)+z*math.sin(angle),cy,cz+z*math.cos(angle)-x*math.sin(angle)))
            faces=[(0,1+k,1+(k+1)%24) for k in range(24)]
            keep(mesh(f'{prefix}.aoi.{j}',verts,faces,'gold'))
        for k in range(40):
            a=k*math.tau/40;b=(k+1)*math.tau/40
            keep(rod(f'{prefix}.ring.{k}',(math.sin(a)*radius,cy,cz+math.cos(a)*radius),(math.sin(b)*radius,cy,cz+math.cos(b)*radius),.004,'gold',sides=6))
    # Silver moustache and fuller cheek plates give the masked face its own age.
    for side in [-1,1]:
        for j in range(3):
            keep(rod(f'menpo.ieyasu.whisker.{side}.{j}',(side*.018,-.218,1.523-j*.005),(side*(.087+j*.006),-.198,1.512-j*.012),.003,'steel',tip=.001,sides=5))
    # Ridged, slightly curved tachi: shared weapon rig, new blade silhouette.
    rows=[(.47,-.16,1.08),(.48,-.16,1.34),(.515,-.16,1.64),(.57,-.16,1.96)]
    verts=[]
    for i,(x,y,z) in enumerate(rows):
        w=.030 if i<3 else .002
        verts.extend([(x-w,y,z),(x,y-.012,z),(x+w,y,z),(x,y+.012,z)])
    faces=[(i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j) for i in range(3) for j in range(4)]+[(3,2,1,0),(12,13,14,15)]
    keep(mesh('katana.ieyasu.blade',verts,faces,'steel'))
    return names
