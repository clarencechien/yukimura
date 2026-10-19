"""Shared cord geometry: three-strand braided cords, wrapped knots and strand fringes.

Used by neck_cords.py and waist_cord.py. All functions add to a bmesh; paths are (n, 3)
arrays in normalized body space.
"""
import numpy as np
import bmesh
from pathlib import Path
from mathutils import Vector


def catmull(points, per=8):
    P = [points[0]] + list(points) + [points[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = map(np.asarray, P[i - 1:i + 3])
        for t in np.linspace(0, 1, per, endpoint=False):
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.asarray(points[-1])); return np.array(out)

def frames(path):
    T = np.gradient(path, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)
    N = [np.cross(T[0], [0, 1, 0]) if abs(T[0][1]) < .9 else np.cross(T[0], [1, 0, 0])]; N[0] /= np.linalg.norm(N[0])
    for i in range(1, len(T)):                                          # parallel transport
        v = N[-1] - T[i] * np.dot(N[-1], T[i]); N.append(v / np.linalg.norm(v))
    N = np.array(N); return T, N, np.cross(T, N)

def tube(bm, path, radius, sides=8, cap=True):
    T, N, B = frames(path); rings = []
    for c, n, b, r in zip(path, N, B, np.broadcast_to(radius, len(path))):
        rings.append([bm.verts.new(Vector(c + r * (np.cos(t) * n + np.sin(t) * b))) for t in np.linspace(0, 2 * np.pi, sides, endpoint=False)])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(sides): bm.faces.new((r0[k], r0[(k + 1) % sides], r1[(k + 1) % sides], r1[k]))
    if cap:
        bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])

def braided_cord(bm, path, R, pitch=None):
    """Three twisted strands around the path: reads as a braided kumihimo cord."""
    pitch = pitch or 5.5 * R
    T, N, B = frames(path); s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    for k in range(3):
        ang = 2 * np.pi * s / pitch + k * 2 * np.pi / 3
        strand = path + .5 * R * (np.cos(ang)[:, None] * N + np.sin(ang)[:, None] * B)
        tube(bm, strand, .58 * R, sides=7)

def knot(bm, centre, R):
    """Wrapped knot head: a squashed ball with three wrapping bands."""
    sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=R)
    for v in sph['verts']: v.co = Vector(centre) + Vector((v.co.x * 1.1, v.co.y * .9, v.co.z * .85))
    for dz in (-.45, 0, .45):
        ring = np.array([[np.cos(t) * R * 1.12 * np.sqrt(max(1 - dz * dz, .2)), np.sin(t) * R * .95 * np.sqrt(max(1 - dz * dz, .2)), dz * R * .85] for t in np.linspace(0, 2 * np.pi, 25)]) + centre
        tube(bm, ring, R * .14, sides=5, cap=False)

def fringe(bm, top, length, R, rng, strands=34):
    """Tassel fringe: a full bundle of fine strands from under the knot, flared and swaying."""
    for i in range(strands):
        t = rng.uniform(0, 2 * np.pi); rr = R * np.sqrt(rng.uniform(.05, 1))
        start = top + np.array([np.cos(t) * rr, np.sin(t) * rr * .8, 0])
        L = length * rng.uniform(.78, 1.0); flare = rng.uniform(1.15, 1.6)
        sway = rng.normal(0, .12 * R, 2)
        zs = np.linspace(0, 1, 8)
        path = np.array([start + np.array([np.cos(t) * rr * (flare - 1) * z + sway[0] * z * z, np.sin(t) * rr * (flare - 1) * z * .8 + sway[1] * z * z, -L * z]) for z in zs])
        tube(bm, path, R * .085 * (1 - .35 * zs), sides=5)


def loop(bm, centre, R, width, height, tilt, side):
    """A flat bow loop beside a knot (reference waist knot), as a braided ring."""
    t = np.linspace(0, 2 * np.pi, 33)
    ring = np.stack([side * (width / 2 + width / 2 * np.cos(t)), -.003 * np.sin(t) ** 2, height / 2 * np.sin(t)], 1)
    c, s = np.cos(tilt), np.sin(tilt)
    ring = ring @ np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]]).T + centre
    braided_cord(bm, ring, R)


def resample(path, spacing):
    """Uniform arc-length resampling of a polyline (linear between input points)."""
    path = np.asarray(path, float)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
    n = max(int(s[-1] / spacing), 2) + 1; t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, path[:, k]) for k in range(3)], 1)


def kumihimo(bm, path, R, pitch=None, strands=12, sides=5):
    """Round kumihimo braid: half the strands spiral each way and alternate over/under where
    they cross (radius modulated at four times the twist rate; opposite sign per direction),
    over a solid core so the braid reads as one cord."""
    path = resample(catmull(list(path), 4) if len(path) > 3 else path, R * .3)
    pitch = pitch or 6 * R
    T, N, B = frames(path); s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    w = 2 * np.pi / pitch; half = strands // 2
    tube(bm, path, R * .62, sides=8)
    for k in range(strands):
        sgn = 1 if k < half else -1
        base = 2 * np.pi * (k % half) / half + (0 if sgn > 0 else np.pi / half)
        ang = base + sgn * w * s
        rr = R * .7 + sgn * R * .1 * np.sin(half * w * s)
        strand = path + rr[:, None] * (np.cos(ang)[:, None] * N + np.sin(ang)[:, None] * B)
        tube(bm, strand, R * .24, sides=sides)


def monkey_fist(bm, centre, u, v, w, R, wraps=3, core=2.6, flat=.78, roll=np.pi / 4, cord=None):
    """Decorative ball knot (monkey's fist): two sets of braided wraps around crossing axes.
    Set A circles the u axis, set B the v axis (both rolled about w by `roll`, so the front shows
    diagonal crossings as in the reference). Wrap radii alternate by one cord radius so the sets
    weave over/under at every crossing; the ball is flattened toward the armour (w scale)."""
    cord = cord or kumihimo
    c, s = np.cos(roll), np.sin(roll)
    U, V = c * u + s * v, -s * u + c * v
    spacing = 2 * R; offs = (np.arange(wraps) - (wraps - 1) / 2) * spacing
    t = np.linspace(0, 2 * np.pi, 49)
    for i, o in enumerate(offs):                                      # set A: circles in the V-w plane
        along = np.cos(t) * core * R                                  # position along V
        r = core * R + R * np.cos(np.pi * along / spacing + i * np.pi)
        path = centre + o * U + (np.cos(t) * r)[:, None] * V + (np.sin(t) * r * flat)[:, None] * w
        cord(bm, path, R)
    for j, o in enumerate(offs):                                      # set B: circles in the U-w plane
        along = np.cos(t) * core * R
        r = core * R - R * np.cos(np.pi * along / spacing + j * np.pi)
        path = centre + o * V + (np.cos(t) * r)[:, None] * U + (np.sin(t) * r * flat)[:, None] * w
        cord(bm, path, R)
    return (core + 1.5) * R                                           # outer radius


def coil(bm, centre, axis, e1, e2, radius_fn, z0, z1, turns, R, sides=5):
    """Wrapping of thin cord around an axis: radius_fn(t) gives the wrap radius at t in [0, 1]."""
    t = np.linspace(0, 1, int(turns * 24))
    pts = np.array([centre + axis * (z0 + (z1 - z0) * u) + radius_fn(u) * (np.cos(2 * np.pi * turns * u) * e1 + np.sin(2 * np.pi * turns * u) * e2) for u in t])
    tube(bm, pts, R, sides=sides)


def braid_textures(out_dir, size=512, strands=8, colour=(.2, .01, .009)):
    """Tileable kongo-gumi braid: strands spiral both ways and the top one alternates in a
    checkerboard, giving the chevron of a round kumihimo. Writes a tangent-space normal map
    (U = around the cord, V = along it, one pitch per tile) and a colour map darkened in the
    grooves. Returns (colour_path, normal_path)."""
    from PIL import Image
    y, x = np.mgrid[0:size, 0:size] / size
    a1 = x * strands + y * 4; a2 = x * strands - y * 4
    f1, f2 = a1 % 1, a2 % 1
    prof = lambda f: np.sqrt(np.clip(1 - (2 * f - 1) ** 2, 0, 1))
    fibre = lambda f: .9 + .1 * np.cos(2 * np.pi * 3 * f)
    h1, h2 = prof(f1) * fibre(f2), prof(f2) * fibre(f1)
    top = (np.floor(a1) + np.floor(a2)) % 2 == 0
    h = np.where(top, np.maximum(h1, .55 * h2), np.maximum(h2, .55 * h1))
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * size / 2 / 28; gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * size / 2 / 28
    n = np.stack([-gx, gy, np.ones_like(h)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    normal = ((n * .5 + .5) * 255).astype(np.uint8)
    shade = (.4 + .6 * h)[..., None]
    lin = np.array(colour) * shade
    srgb = np.where(lin <= .0031308, lin * 12.92, 1.055 * np.power(np.clip(lin, 1e-9, 1), 1 / 2.4) - .055)
    cp, np_ = Path(out_dir) / 'braid-color.png', Path(out_dir) / 'braid-normal.png'
    Image.fromarray((np.clip(srgb, 0, 1) * 255).astype(np.uint8)).save(cp); Image.fromarray(normal).save(np_)
    return cp, np_


def braid_tube(bm, path, R, pitch=None, sides=14, cap=True):
    """Smooth cord with UVs for the braid textures (U around, V = length / pitch)."""
    uvl = bm.loops.layers.uv.verify()
    path = resample(catmull(list(path), 4) if len(path) > 3 else path, R * .5)
    pitch = pitch or 4 * R
    T, N, B = frames(path); s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    rings = [[bm.verts.new(Vector(c + R * (np.cos(t) * n + np.sin(t) * b))) for t in np.linspace(0, 2 * np.pi, sides + 1)[:-1]] for c, n, b in zip(path, N, B)]
    for i in range(len(rings) - 1):
        for k in range(sides):
            f = bm.faces.new((rings[i][k], rings[i][(k + 1) % sides], rings[i + 1][(k + 1) % sides], rings[i + 1][k]))
            for loop, (du, di) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
                loop[uvl].uv = ((k + du) / sides, s[i + di] / pitch)
    if cap:
        for ring in (rings[0][::-1], rings[-1]):
            f = bm.faces.new(ring)
            for loop in f.loops: loop[uvl].uv = (.5, 0)
