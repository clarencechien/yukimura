"""Shared cord geometry: three-strand braided cords, wrapped knots and strand fringes.

Used by neck_cords.py and waist_cord.py. All functions add to a bmesh; paths are (n, 3)
arrays in normalized body space.
"""
import numpy as np
import bmesh
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
