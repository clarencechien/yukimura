"""Rasterize per-texel object-space position and normal of a mesh in its UV space (NumPy)."""
import numpy as np


def rasterize(mesh, size):
    """Returns pos (size, size, 4; alpha = covered) and nrm (size, size, 3), row 0 = UV v 0."""
    mesh.calc_loop_triangles()
    tri_loops = np.empty(len(mesh.loop_triangles) * 3, np.int32); mesh.loop_triangles.foreach_get('loops', tri_loops); tri_loops = tri_loops.reshape(-1, 3)
    loop_vert = np.empty(len(mesh.loops), np.int32); mesh.loops.foreach_get('vertex_index', loop_vert)
    uvs = np.empty(len(mesh.loops) * 2, np.float32); mesh.uv_layers.active.data.foreach_get('uv', uvs); uvs = uvs.reshape(-1, 2)
    co = np.empty(len(mesh.vertices) * 3, np.float32); mesh.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    vn = np.empty(len(mesh.vertices) * 3, np.float32); mesh.vertices.foreach_get('normal', vn); vn = vn.reshape(-1, 3)
    pos = np.zeros((size, size, 4), np.float32); nrm = np.zeros((size, size, 3), np.float32)
    T = uvs[tri_loops] * size - .5                                     # texel centres at integer coords
    V = loop_vert[tri_loops]
    lo = np.floor(T.min(1)).astype(int); hi = np.ceil(T.max(1)).astype(int)
    extent = (hi - lo).max(1) + 1
    for bucket in [2, 4, 8, 16, 32, 64, 128, 256]:
        sel = np.where((extent <= bucket) & (extent > bucket // 2) if bucket > 2 else extent <= 2)[0]
        gy, gx = np.mgrid[0:bucket, 0:bucket]; offs = np.stack([gx.ravel(), gy.ravel()], 1)
        for chunk in np.array_split(sel, max(1, len(sel) * bucket * bucket // 8_000_000 + 1)):
            if not len(chunk): continue
            px = lo[chunk, None, :] + offs[None]
            a_, b_ = T[chunk, 0, None], T[chunk, 1, None]; c_ = T[chunk, 2, None]
            v0, v1, v2 = b_ - a_, c_ - a_, px - a_
            den = v0[..., 0] * v1[..., 1] - v1[..., 0] * v0[..., 1]
            den = np.where(np.abs(den) < 1e-12, 1e-12, den)
            w1 = (v2[..., 0] * v1[..., 1] - v1[..., 0] * v2[..., 1]) / den
            w2 = (v0[..., 0] * v2[..., 1] - v2[..., 0] * v0[..., 1]) / den
            w0 = 1 - w1 - w2
            inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4) & (px[..., 0] >= 0) & (px[..., 1] >= 0) & (px[..., 0] < size) & (px[..., 1] < size)
            ti, ki = np.nonzero(inside)
            w = np.stack([w0[ti, ki], w1[ti, ki], w2[ti, ki]], 1)[..., None]
            verts = V[chunk[ti]]; x, y = px[ti, ki, 0], px[ti, ki, 1]
            pos[y, x, :3] = (co[verts] * w).sum(1); pos[y, x, 3] = 1
            nrm[y, x] = (vn[verts] * w).sum(1)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-8)
    return pos, nrm
