"""Split TRELLIS.2 PBR texels into lacquer, gilding and dark under-armour.

The generator gives the red lacquer metallic ~0.7, which renders as copper, and drifts
about a third of the reds toward orange. These helpers work on float RGBA arrays
(sRGB-encoded base color, glTF metallic/roughness in G/B) and return corrected arrays.
"""
import numpy as np
from scipy import ndimage

REFERENCE_RED_HUE = 4.0  # degrees, measured lacquer in reference.png (~109,29,22)
GILT_HUE = 40.0  # degrees, aged brass trims in reference.png


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)


def rgb_to_hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    v = rgb.max(-1); c = v - rgb.min(-1)
    s = np.where(v > 1e-6, c / np.maximum(v, 1e-6), 0)
    safe = np.maximum(c, 1e-6)
    h = np.where(v == r, ((g - b) / safe) % 6, np.where(v == g, (b - r) / safe + 2, (r - g) / safe + 4)) * 60
    return np.where(c > 1e-6, h, 0), s, v


def hsv_to_rgb(h, s, v):
    c = v * s; hp = (h % 360) / 60; x = c * (1 - np.abs(hp % 2 - 1)); m = v - c
    z = np.zeros_like(h); i = np.floor(hp).astype(int) % 6
    table = [(c, x, z), (x, c, z), (z, c, x), (z, x, c), (x, z, c), (c, z, x)]
    out = np.zeros(h.shape + (3,))
    for k, (r, g, b) in enumerate(table):
        sel = i == k
        out[sel] = np.stack([r[sel], g[sel], b[sel]], -1)
    return out + m[..., None]


def masks(rgb, metal):
    """Soft weights for lacquer red, gilt trim and dark under-armour (they need not sum to 1).

    TRELLIS.2 renders the reference's brass trims as bright, metallic copper (hue 16-32 deg,
    value > 0.3); the lacquer sits at hue 0-12 deg and darker. Trim wins where both overlap.
    """
    h, s, v = rgb_to_hsv(rgb)
    hue_red = np.abs(((h + 180) % 360) - 180)  # distance from 0 degrees
    gold = smoothstep(13, 20, h) * (1 - smoothstep(58, 68, h)) * smoothstep(.22, .32, s) \
        * smoothstep(.27, .37, v) * smoothstep(.42, .58, metal)
    red = (1 - smoothstep(14, 24, hue_red)) * smoothstep(.30, .45, s) * smoothstep(.06, .12, v) * (1 - gold)
    dark = (1 - smoothstep(.10, .20, v)) * (1 - red) * (1 - gold)
    return h, s, v, red, gold, dark


def correct(color, mr):
    """Return (color, metallic_roughness, coat) float arrays shaped like the inputs."""
    rgb = color[..., :3]
    rough, metal = mr[..., 1], mr[..., 2]
    h, s, v, red, gold, dark = masks(rgb, metal)
    # Gilding in the reference is edging only. Wide gilt areas (TRELLIS's bronze back plate,
    # calf backs) survive a morphological opening; trims do not. Those panels become lacquer.
    radius = max(2, round(8 * color.shape[0] / 2048))
    disk = ndimage.iterate_structure(ndimage.generate_binary_structure(2, 1), radius)
    hard = gold > .5
    panel = ndimage.binary_dilation(ndimage.binary_opening(hard, disk), disk) & hard
    panel = np.clip(ndimage.gaussian_filter(panel.astype(np.float32), radius / 4) * 1.5, 0, 1) * (gold > .05)
    red = np.clip(red + gold * panel, 0, 1); gold = gold * (1 - panel)
    # Pull orange-drifted reds back toward the reference lacquer, keeping per-texel variation.
    delta = ((h + 180) % 360) - 180 - REFERENCE_RED_HUE
    new_h = np.where(red > 0, REFERENCE_RED_HUE + delta * (1 - .65 * red) * (1 - panel), h)
    new_s = np.clip(s * (1 + .08 * red), 0, 1) * (1 - panel) + np.clip(s * 1.6, .6, .8) * panel
    new_v = v * (1 - .06 * red) * (1 - .4 * panel)
    fixed = hsv_to_rgb(new_h, new_s, new_v)
    # Gilt trim: copper -> aged brass of the reference, keeping the generated value variation.
    gilt = hsv_to_rgb(np.full_like(h, GILT_HUE), np.clip(s * 1.25, .45, .68), np.clip(v * 1.3, 0, .82))
    out = color.copy()
    out[..., :3] = rgb * (1 - red - gold)[..., None] + fixed * red[..., None] + gilt * gold[..., None]
    other = np.clip(1 - red - gold - dark, 0, 1)
    new_metal = np.clip(gold * 1.0 + dark * .12 + other * metal * .35, 0, 1)
    new_rough = np.clip(red * .44 + gold * np.clip(rough, .28, .42) + dark * .58 + other * np.clip(rough, .4, .7), .05, 1)
    norm = np.maximum(red + gold + dark + other, 1e-6)
    new_rough = np.where(norm > 1, new_rough / norm, new_rough)
    out_mr = mr.copy(); out_mr[..., 1] = new_rough; out_mr[..., 2] = new_metal
    coat = np.zeros_like(color); coat[..., :3] = (red * .15)[..., None]; coat[..., 3] = 1
    stats = {'gilt_panels_to_lacquer_fraction': float(panel.mean()), 'panel_opening_radius_texels': radius, 'red_fraction': float(red.mean()), 'gold_fraction': float(gold.mean()), 'dark_fraction': float(dark.mean()),
             'mean_metallic_before': float(metal.mean()), 'mean_metallic_after': float(new_metal.mean()),
             'red_metallic_before': float((metal * red).sum() / max(red.sum(), 1e-6)),
             'red_metallic_after': float((new_metal * red).sum() / max(red.sum(), 1e-6))}
    return out, out_mr, coat, stats
