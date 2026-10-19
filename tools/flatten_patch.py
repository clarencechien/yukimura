"""Flatten geometry that stands in front of a fitted surface without leaving folded shards.

Projecting a bump (e.g. a fused tassel) straight back onto a surface collapses its wrapped sides
into overlapping, flipped triangles. After the projection, the moved vertices are relaxed to the
average of their neighbours in the surface's (x, z) chart with the unmoved boundary held fixed
(Tutte embedding), which unfolds the patch, then put back on the surface.
"""
import numpy as np
from scipy import sparse


def flatten_relaxed(co, faces_flat, starts, counts, inside, surface_y, in_front=0., iterations=400):
    """co: (n, 3) vertices (modified in place); faces as flat vertex list + loop starts/counts;
    inside: vertex mask of the region; surface_y(x, z) -> y of the fitted surface (front = -y).
    Returns the mask of moved vertices."""
    move = inside & (co[:, 1] < surface_y(co[:, 0], co[:, 2]) + in_front)
    # glTF import splits vertices on UV seams: relax on welded ids, or each seam island shrinks
    # on its own and tears holes.
    _, canon = np.unique(np.round(co / 1e-6).astype(np.int64), axis=0, return_inverse=True)
    canon = canon.ravel(); n = canon.max() + 1
    rows, cols = [], []
    for s, c in zip(starts, counts):
        f = canon[faces_flat[s:s + c]]
        for k in range(c): rows += [f[k], f[(k + 1) % c]]; cols += [f[(k + 1) % c], f[k]]
    A = sparse.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)); A.data[:] = 1
    deg = np.asarray(A.sum(1)).ravel()
    pos = np.zeros((n, 3)); pos[canon] = co
    mv = np.zeros(n, bool); mv[canon[move]] = True
    m = mv & (deg > 0)
    xz = pos[:, [0, 2]].copy()
    for _ in range(iterations):
        xz[m] = (A @ xz)[m] / deg[m, None]
    pos[mv, 0] = xz[mv, 0]; pos[mv, 2] = xz[mv, 1]
    pos[mv, 1] = surface_y(pos[mv, 0], pos[mv, 2])
    move = mv[canon]
    co[move] = pos[canon[move]]
    return move


def surround_colour(mesh, image, centres, ring):
    """Median base colour of the faces selected by `ring`, converted from the texture's sRGB
    encoding to linear for a Principled base colour."""
    W, H = image.size; tex = np.empty(W * H * 4, np.float32); image.pixels.foreach_get(tex); tex = tex.reshape(H, W, 4)
    uv = np.empty(len(mesh.loops) * 2, np.float32); mesh.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    st = np.empty(len(mesh.polygons), np.int32); mesh.polygons.foreach_get('loop_start', st)
    sel = np.where(ring)[0]
    u = uv[st[sel]]
    c = tex[np.clip((u[:, 1] * H).astype(int), 0, H - 1), np.clip((u[:, 0] * W).astype(int), 0, W - 1), :3]
    c = np.median(c, 0)                                               # robust to lacing / gilt edges
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


def dissolve_collapsed(mesh, vertex_mask, dist=1e-5):
    """Relaxation squashes formerly folded triangles to zero area: dissolve them in the patch."""
    import bmesh
    bm = bmesh.new(); bm.from_mesh(mesh); bm.verts.ensure_lookup_table()
    edges = list({e for i in np.where(vertex_mask)[0] for e in bm.verts[i].link_edges})
    before = len(bm.faces)
    bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=edges)
    after = len(bm.faces); bm.to_mesh(mesh); bm.free()
    return before - after
