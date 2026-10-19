"""Position-based dynamics for cords and tassel threads draped on the armour.

Particles joined by stretch (i, i+1) and bend (i, i+2) constraints, gravity, damping, pins,
collision against the character surface (a BVH from bpy, with a vertex KD-tree broad phase)
with Coulomb-style friction, and particle-particle repulsion between different ropes.
Units are normalized body space (height 2 = about 1.8 m), so gravity is scaled to match.
"""
import numpy as np
from scipy.spatial import cKDTree
from mathutils import Vector

UNITS_PER_METRE = 2 / 1.8


class Collider:
    """Surface of the character: push particles out to `radius` along the nearest face normal."""

    def __init__(self, bvh, vertices):
        self.bvh = bvh; self.kd = cKDTree(vertices)

    def resolve(self, p, radius, active):
        d, _ = self.kd.query(p, distance_upper_bound=.03)
        idx = np.where(active & np.isfinite(d))[0]
        contact = np.zeros(len(p), bool); normal = np.zeros_like(p)
        for i in idx:
            loc, n, _, dist = self.bvh.find_nearest(Vector(p[i]), .05)
            if loc is None: continue
            loc = np.array(loc); n = np.array(n)
            depth = np.dot(p[i] - loc, n)
            if depth < radius[i]:
                p[i] += n * (radius[i] - depth); contact[i] = True; normal[i] = n
        return contact, normal


class RopeSystem:
    def __init__(self):
        self.x = []; self.invm = []; self.r = []; self.rope = []; self.edges = []; self.bends = []
        self.n_ropes = 0

    def add_rope(self, points, mass, radius, stretch=1., bend=.0, pin_first=False, pin_last=False, slack=1.):
        """Chain through `points`; rest lengths = initial spacing x slack. Returns particle indices."""
        start = len(self.x); n = len(points); rid = self.n_ropes; self.n_ropes += 1
        for k, q in enumerate(points):
            pinned = (k == 0 and pin_first) or (k == n - 1 and pin_last)
            self.x.append(np.asarray(q, float)); self.invm.append(0. if pinned else 1. / mass)
            self.r.append(radius); self.rope.append(rid)
        for k in range(n - 1):
            self.edges.append((start + k, start + k + 1, np.linalg.norm(np.subtract(points[k + 1], points[k])) * slack, stretch))
        for k in range(n - 2):
            if bend > 0:
                self.bends.append((start + k, start + k + 2, np.linalg.norm(np.subtract(points[k + 2], points[k])), bend))
        return list(range(start, start + n))

    def link(self, i, j, rest=None, stiffness=1.):
        """Extra distance constraint (e.g. a cord end joined to a knot particle)."""
        rest = np.linalg.norm(np.subtract(self.x[i], self.x[j])) if rest is None else rest
        self.edges.append((i, j, rest, stiffness))

    def set_mass(self, i, mass, radius=None):
        self.invm[i] = 1. / mass
        if radius is not None: self.r[i] = radius

    def pin(self, i): self.invm[i] = 0.

    def _solve(self, p, invm, cons):
        if not len(cons): return
        i, j, rest, k = cons
        d = p[j] - p[i]; L = np.linalg.norm(d, axis=1); L = np.maximum(L, 1e-9)
        w = invm[i] + invm[j]; ok = w > 0
        c = ((L - rest) / L * k)[:, None] * d
        acc = np.zeros_like(p); cnt = np.zeros(len(p))
        wi = np.where(ok, invm[i] / np.where(ok, w, 1), 0)[:, None]; wj = np.where(ok, invm[j] / np.where(ok, w, 1), 0)[:, None]
        np.add.at(acc, i, wi * c); np.add.at(acc, j, -wj * c)
        np.add.at(cnt, i, 1); np.add.at(cnt, j, 1)
        p += 1.5 * acc / np.maximum(cnt, 1)[:, None]

    def simulate(self, collider, seconds=2.5, dt=1 / 240, iterations=24, damping=.985, friction=.6,
                 self_collide=True, collide_every=6, gravity=True, log=None):
        x = np.array(self.x); v = np.zeros_like(x); invm = np.array(self.invm); r = np.array(self.r)
        rope = np.array(self.rope); free = invm > 0
        E = np.array(self.edges, dtype=object)
        cons = (np.array([e[0] for e in self.edges], int), np.array([e[1] for e in self.edges], int),
                np.array([e[2] for e in self.edges]), np.array([e[3] for e in self.edges])) if len(E) else ()
        bends = (np.array([b[0] for b in self.bends], int), np.array([b[1] for b in self.bends], int),
                 np.array([b[2] for b in self.bends]), np.array([b[3] for b in self.bends])) if self.bends else ()
        g = np.array([0, 0, -9.81 * UNITS_PER_METRE]) if gravity else np.zeros(3)
        steps = int(seconds / dt); contact_total = 0
        for step in range(steps):
            v[free] += g * dt; v *= damping
            p = x + v * dt
            contact = np.zeros(len(p), bool); normal = np.zeros_like(p)
            for it in range(iterations):
                self._solve(p, invm, cons)
                if bends: self._solve(p, invm, bends)
                if it % collide_every == collide_every - 1 or it == iterations - 1:
                    c, n = collider.resolve(p, r, free)
                    contact |= c; normal[c] = n[c]
                    if self_collide:
                        tree = cKDTree(p); pairs = tree.query_pairs(2 * r.max(), output_type='ndarray')
                        if len(pairs):
                            i, j = pairs[:, 0], pairs[:, 1]
                            other = rope[i] != rope[j]
                            i, j = i[other], j[other]
                            d = p[j] - p[i]; L = np.linalg.norm(d, axis=1); minL = r[i] + r[j]
                            hit = (L < minL) & (L > 1e-9)
                            i, j, d, L, minL = i[hit], j[hit], d[hit], L[hit], minL[hit]
                            w = invm[i] + invm[j]; ok = w > 0
                            corr = ((minL - L) / L)[:, None] * d
                            acc = np.zeros_like(p)
                            np.add.at(acc, i[ok], -(invm[i[ok]] / w[ok])[:, None] * corr[ok])
                            np.add.at(acc, j[ok], (invm[j[ok]] / w[ok])[:, None] * corr[ok])
                            p += acc * .5
            newv = (p - x) / dt
            if contact.any():                                          # friction on the surface
                n = normal[contact]; vn = (newv[contact] * n).sum(1, keepdims=True) * n
                newv[contact] = vn * 0 + (newv[contact] - vn) * (1 - friction)
            v = np.where(free[:, None], newv, 0); x = np.where(free[:, None], p, x)
            contact_total = int(contact.sum())
            if log and step % 120 == 0: log(f'step {step}/{steps} contacts {contact_total} max speed {np.linalg.norm(v, axis=1).max():.3f}')
        self.x = list(x)
        return {'particles': len(x), 'ropes': self.n_ropes, 'steps': steps, 'dt': dt, 'iterations': iterations,
                'final_contacts': contact_total, 'final_max_speed': float(np.linalg.norm(v, axis=1).max())}
