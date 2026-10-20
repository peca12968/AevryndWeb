"""Owned authoring/import policy for the verified legacy particle width subset.

Pinned Blender5.2.2 d13f752e3b9c Cycles source: particle root/tip values are
diameters times radius_scale; native Curves radius is already a radius.
This utility is not a collision, biological calibration or runtime hair system.
"""
import math

def legacy_particle_point_radii(settings, point_count):
    """Convert the verified equal-root/tip profile, including close-tip.

    Reject unsupported profiles rather than silently changing authored shape.
    Returns object-space radii; transform scaling belongs to the caller.
    """
    if point_count < 2:
        raise ValueError('A strand needs at least two points')
    if float(settings['shape']) != 0.0:
        raise ValueError('This verified import policy supports source shape0 only')
    scale=float(settings['radius_scale'])
    root=float(settings['root_radius'])
    tip=float(settings['tip_radius'])
    if not all(math.isfinite(v) and v >= 0 for v in (scale,root,tip)):
        raise ValueError('Invalid source diameter or scale')
    if root != tip:
        raise ValueError('Unequal diameters need actual normalized arc coordinates')
    out=[.5*scale*(root+(tip-root)*i/(point_count-1)) for i in range(point_count)]
    if settings['use_close_tip']:
        out[-1]=0.0
    return out
