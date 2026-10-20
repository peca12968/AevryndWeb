"""Narrow ctypes bridge to the Aevrynd-owned standalone C++ contact kernel."""
from pathlib import Path
import ctypes as C,numpy as np
R=Path(r'D:\Download\Aevrynd');DLL=R/'Evidence/character-female-next/r0062-packed-bundle/native/aevrynd_shaft_contacts.dll'
class Stats(C.Structure):
    _fields_=[('candidates',C.c_int64),('active',C.c_int64),('corrections',C.c_int64),('colours',C.c_int64),('minimumGap',C.c_double)]
lib=C.CDLL(str(DLL));lib.aevrynd_shaft_contact_abi.restype=C.c_int;assert lib.aevrynd_shaft_contact_abi()==C.sizeof(Stats)
array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');lib.aevrynd_shaft_contacts.argtypes=[array,array,array,C.c_int,C.c_int,C.c_double,C.c_double,C.POINTER(Stats)];lib.aevrynd_shaft_contacts.restype=C.c_int

def project(x,radii,w,gap=3e-6,residual=1e-7):
    assert x.ndim==3 and x.shape[2]==3 and radii.shape==w.shape==x.shape[:2]
    stats=Stats();status=lib.aevrynd_shaft_contacts(x,radii,w,x.shape[0],x.shape[1],gap,residual,C.byref(stats))
    if status:raise RuntimeError(f'Aevrynd native finite contact kernel failed: {status}')
    return int(stats.corrections),float(stats.minimumGap),stats
