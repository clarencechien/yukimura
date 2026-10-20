"""A procedural Japanese spear with a red-lacquered shaft (朱槍): a su-yari, or by default a jumonji-yari
(十文字槍, the cross-bladed spear associated with Sanada Yukimura).

Built along +Z from the butt at the origin; plain glTF materials, no textures. Proportions follow
an omi-yari scaled to the given length: iron ishizuki, red shaft, gilt kuchigane and habaki, and a
triangular-section (sankaku) blade.
"""
import math
import bmesh, bpy

def _mat(name, color, metal, rough):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    return m

def build(length=3.0, blade=.30, radius=.017, sides=10, jumonji=True, arm=.19):
    """Returns a mesh object (not linked to a scene collection)."""
    mats = [_mat('yari lacquer', (.42, .02, .015), 0, .32), _mat('yari iron', (.03, .03, .035), .9, .45),
            _mat('yari gilt', (.75, .52, .18), 1, .3), _mat('yari steel', (.62, .64, .66), 1, .18)]
    bm = bmesh.new()
    def ring(z, r, n=sides, rot=0):
        return [bm.verts.new((r * math.cos(rot + 2 * math.pi * k / n), r * math.sin(rot + 2 * math.pi * k / n), z)) for k in range(n)]
    def bridge(a, b, mat):
        for k in range(len(a)):
            f = bm.faces.new((a[k], a[(k + 1) % len(a)], b[(k + 1) % len(b)], b[k])); f.material_index = mat
    shaft_top = length - blade
    # (z, radius, material of the band below this ring)
    rings = [(0, radius * .8, None), (.09, radius * 1.05, 1), (.1, radius, 1), (shaft_top - .13, radius, 0),
             (shaft_top - .12, radius * 1.15, 0), (shaft_top - .02, radius * 1.15, 2), (shaft_top, radius * .75, 2)]
    prev = None
    for z, r, mat in rings:
        cur = ring(z, r)
        if prev is None: f = bm.faces.new(list(reversed(cur))); f.material_index = 1
        else: bridge(prev, cur, mat)
        prev = cur
    # sankaku blade: a triangle that tapers to the point; the flat face looks forward along -Y
    w = radius * 1.7
    base = ring(shaft_top, w, 3, math.pi / 2)
    bridge(ring(shaft_top, radius * .75, 3, math.pi / 2), base, 3)
    mid = ring(shaft_top + blade * .25, w * .95, 3, math.pi / 2); bridge(base, mid, 3)
    tip = bm.verts.new((0, 0, length))
    for k in range(3):
        f = bm.faces.new((mid[k], mid[(k + 1) % 3], tip)); f.material_index = 3
    if jumonji:
        # two side blades at the foot of the main blade, swept slightly toward the point
        z0 = shaft_top + .025; h = .02; t = radius * .45
        for sign in (1, -1):
            root = [bm.verts.new((0, -t, z0)), bm.verts.new((0, 0, z0 - h)), bm.verts.new((0, t, z0)), bm.verts.new((0, 0, z0 + h))]
            mid = [bm.verts.new((sign * arm * .55, -t * .8, z0 + .012)), bm.verts.new((sign * arm * .55, 0, z0 - h * .55 + .012)),
                   bm.verts.new((sign * arm * .55, t * .8, z0 + .012)), bm.verts.new((sign * arm * .55, 0, z0 + h * 1.1 + .012))]
            tip_s = bm.verts.new((sign * arm, 0, z0 + .045))
            for k in range(4):
                f = bm.faces.new((root[k], root[(k + 1) % 4], mid[(k + 1) % 4], mid[k])); f.material_index = 3
                f = bm.faces.new((mid[k], mid[(k + 1) % 4], tip_s)); f.material_index = 3
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('yari'); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    for poly in me.polygons: poly.use_smooth = poly.material_index in (0, 1, 2)
    return bpy.data.objects.new('yari', me)
