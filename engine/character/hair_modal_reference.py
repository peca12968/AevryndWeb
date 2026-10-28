"""Aevrynd offline reference for the r214 four-region display-hair model.

Coordinates are world metres. This reproduces the native Blender modal
controls; it is not a production renderer or a collision/strand solver.
"""
import numpy as np


def wind_velocity(seconds):
    """The fixed, recorded r214 wind input, in world x/y metres per second."""
    if seconds < 0.3 or seconds > 1.0:
        return np.zeros(2)
    if seconds < 0.5:
        u = (seconds - 0.3) / 0.2
    elif seconds > 0.8:
        u = (1.0 - seconds) / 0.2
    else:
        u = 1.0
    u = np.clip(u, 0.0, 1.0)
    return np.array([3.0, 0.75]) * (u * u * (3.0 - 2.0 * u))


def simulate(parameters):
    """Return recorded-frame region offsets: [frame, four regions, xyz]."""
    mass = np.asarray(parameters['regionMassKg'], dtype='f8')
    stiffness = (np.asarray(parameters['materialSpringNPerM'], dtype='f8')
                 + np.asarray(parameters['gravityRestoringNPerM'], dtype='f8'))
    damping = np.asarray(parameters['dampingKgPerS'], dtype='f8')
    area = np.asarray(parameters['regionEffectiveAreaM2'], dtype='f8')
    lever = np.asarray(parameters['geometricVolumeLeverArmM'], dtype='f8')
    if mass.shape != (4,) or not np.all(mass > 0) or not np.all(lever > 0):
        raise ValueError('Expected four positive region masses and lever arms')
    dt = float(parameters['dtSeconds'])
    fps = int(parameters['fps'])
    frames = int(parameters['frames'])
    substeps = round(1.0 / (fps * dt))
    if frames < 2 or substeps < 1 or abs(substeps * fps * dt - 1.0) > 1e-10:
        raise ValueError('Simulation step must divide the recorded frame interval')
    coupling = float(parameters['neighborSpringNPerM'])
    rho = float(parameters['airDensityKgPerM3'])
    drag = float(parameters['dragCoefficient'])
    position = np.zeros((4, 2))
    velocity = np.zeros((4, 2))
    result = [np.zeros((4, 3))]
    for step in range((frames - 1) * substeps):
        relative = wind_velocity(step * dt)[None, :] - velocity
        speed = np.linalg.norm(relative, axis=1)
        force = 0.5 * rho * drag * area[:, None] * speed[:, None] * relative
        force -= stiffness[:, None] * position + damping[:, None] * velocity
        for i, j in [(0, 1), (0, 2), (1, 3), (2, 3)]:
            spring = coupling * (position[j] - position[i])
            force[i] += spring
            force[j] -= spring
        velocity += dt * force / mass[:, None]
        position += dt * velocity
        if np.max(np.linalg.norm(position, axis=1) / lever) >= 0.6:
            raise ValueError('Recorded reduced-model domain exceeded; do not clamp')
        if (step + 1) % substeps == 0:
            rise = lever - np.sqrt(lever * lever - np.sum(position * position, axis=1))
            result.append(np.column_stack([position, rise]))
    return np.asarray(result)


def deform_world_mesh(rest_world, region_weights, offsets):
    """Apply the same complete-vertex modal basis as the native shape keys."""
    rest = np.asarray(rest_world, dtype='f8')
    weights = np.asarray(region_weights, dtype='f8')
    offsets = np.asarray(offsets, dtype='f8')
    if rest.ndim != 2 or rest.shape[1] != 3 or weights.shape != (len(rest), 4):
        raise ValueError('Expected vertex-aligned world positions and four mode weights')
    if offsets.shape != (4, 3) or not np.isfinite(offsets).all():
        raise ValueError('Expected finite four-region world offsets')
    return rest + weights @ offsets
