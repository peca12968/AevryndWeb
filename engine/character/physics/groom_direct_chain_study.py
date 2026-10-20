"""Aevrynd research: simultaneous chain stretch and vector-curvature constraints.

Own NumPy implementation; not a Cosserat/direct-rod paper reproduction. No twist,
friction, self collision, CCD or validated engine runtime. External body response
must refresh actual surfaces; a callback is not an exclusion certificate.
"""
import numpy as np

STATUS = 'UNACCEPTED_R0093_RESEARCH_NOT_ENGINE_RUNTIME'


def tridiagonal(diag, off, rhs):
    a, b = diag.copy(), rhs.copy()
    for i in range(1, a.shape[1]):
        f = off[:, i-1] / a[:, i-1]
        a[:, i] -= f * off[:, i-1]
        b[:, i] -= f * b[:, i-1]
    out = np.empty_like(b)
    out[:, -1] = b[:, -1] / a[:, -1]
    for i in range(a.shape[1]-2, -1, -1):
        out[:, i] = (b[:, i]-off[:, i]*out[:, i+1])/a[:, i]
    return out


class DirectChains:
    def __init__(self, rest, radius, dt=1/96, young=3e9, density=1300.):
        self.x = np.asarray(rest, 'f8').copy()
        self.rest = self.x.copy()
        self.v = np.zeros_like(self.x)
        self.radius = np.asarray(radius, 'f8')
        self.length = np.linalg.norm(np.diff(self.x, axis=1), axis=2)
        assert self.x.ndim == 3 and (self.length > 1e-8).all()
        self.ds = self.length.mean(axis=1)
        mass = density*np.pi*self.radius**2*self.ds[:, None]
        mass[:, [0, -1]] *= .5
        self.w = 1/mass
        self.w[:, 0] = 0
        self.dt = dt
        self.as_ = self.length/(young*np.pi*self.radius[:, :-1]**2)/dt**2
        self.ab = self.ds[:, None]**3/(young*np.pi*self.radius[:, 1:-1]**4/4)/dt**2
        self.curvature = self.x[:, :-2]-2*self.x[:, 1:-1]+self.x[:, 2:]
        # Banded Cholesky of J W J^T + compliance/dt^2, J=(1,-2,1).
        w = self.w
        a = w[:, :-2]+4*w[:, 1:-1]+w[:, 2:]+self.ab
        b = -2*(w[:, 1:-2]+w[:, 2:-1])
        c = w[:, 2:-2]
        self.d = np.empty_like(a)
        self.e = np.zeros_like(a)
        self.f = np.zeros_like(a)
        for i in range(a.shape[1]):
            if i > 1: self.f[:, i] = c[:, i-2]/self.d[:, i-2]
            if i: self.e[:, i] = (b[:, i-1]-self.f[:, i]*self.e[:, i-1])/self.d[:, i-1]
            self.d[:, i] = np.sqrt(a[:, i]-self.e[:, i]**2-self.f[:, i]**2)
        assert np.isfinite(self.d).all() and (self.d > 0).all()

    def bend_solve(self, target, lamb):
        rhs = -(self.x[:, :-2]-2*self.x[:, 1:-1]+self.x[:, 2:]-target)-self.ab[..., None]*lamb
        y = np.empty_like(rhs)
        for i in range(rhs.shape[1]):
            v = rhs[:, i].copy()
            if i: v -= self.e[:, i, None]*y[:, i-1]
            if i > 1: v -= self.f[:, i, None]*y[:, i-2]
            y[:, i] = v/self.d[:, i, None]
        z = np.empty_like(y)
        for i in range(rhs.shape[1]-1, -1, -1):
            v = y[:, i].copy()
            if i+1 < rhs.shape[1]: v -= self.e[:, i+1, None]*z[:, i+1]
            if i+2 < rhs.shape[1]: v -= self.f[:, i+2, None]*z[:, i+2]
            z[:, i] = v/self.d[:, i, None]
        delta = np.zeros_like(self.x)
        delta[:, :-2] += z
        delta[:, 1:-1] -= 2*z
        delta[:, 2:] += z
        self.x += self.w[..., None]*delta
        lamb += z

    def stretch_solve(self, lamb):
        edge = np.diff(self.x, axis=1)
        length = np.maximum(np.linalg.norm(edge, axis=2), 1e-12)
        n = edge/length[..., None]
        a = self.w[:, :-1]+self.w[:, 1:]+self.as_
        off = -self.w[:, 1:-1]*np.einsum('nki,nki->nk', n[:, :-1], n[:, 1:])
        z = tridiagonal(a, off, -(length-self.length)-self.as_*lamb)
        delta = np.zeros_like(self.x)
        delta[:, :-1] -= n*z[..., None]
        delta[:, 1:] += n*z[..., None]
        self.x += self.w[..., None]*delta
        lamb += z

    def advance(self, roots, curvature, contact, iterations=6):
        old = self.x.copy()
        self.v *= np.exp(-1.5*self.dt)
        self.v[..., 2] -= 9.81*self.dt
        self.x += self.v*self.dt
        self.x[:, 0] = roots
        ls = np.zeros_like(self.length)
        lb = np.zeros_like(self.curvature)
        for _ in range(iterations):
            self.bend_solve(curvature, lb)
            self.stretch_solve(ls)
            self.x[:, 0] = roots
            contact(self.x)
            self.x[:, 0] = roots
        self.v = (self.x-old)/self.dt
        self.v[:, 0] = 0
        strain = abs(np.linalg.norm(np.diff(self.x, axis=1), axis=2)/self.length-1)
        return {'maximumRelativeEdgeStrain':float(strain.max()),
                'p99RelativeEdgeStrain':float(np.quantile(strain,.99)),
                'maximumVelocityMS':float(np.linalg.norm(self.v,axis=2).max())}
