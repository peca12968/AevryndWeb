"""Rebuild the exact B fibres from the portable authoring cache with safe RNA lists.

This is an I/O repair, not a new geometry candidate. Exact saved-strand equality
is required before inheriting the B sampled-static collision evidence.
"""
import bpy,json,importlib.util,hashlib,time
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('verify',Path(__file__).with_name('verify-female-next-r0013-native-groom.py'));verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
spec=importlib.util.spec_from_file_location('build',Path(__file__).with_name('build-female-next-r0013-native-groom.py'));build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
S,E,route=verify.S,verify.E,verify.route

def fibres():
    h=hashlib.sha256()
    for o in sorted((o for o in bpy.data.objects if o.type=='CURVES' and o.name.startswith('AFN13_')),key=lambda o:o.name):
        P,rr=verify.native_paths(o);h.update(o.name.encode())
        for p,r in zip(P,rr):h.update(p.tobytes());h.update(r.tobytes())
        for c in o.data.attributes['material_index'].data:h.update(int(c.value).to_bytes(4,'little',signed=True))
        h.update(json.dumps([m.name for m in o.data.materials]).encode())
    return h.hexdigest()

def main():
    start=time.time();src=S/'aevrynd-female-next-r0013-b-native-envelope-hair-study.blend';proof=json.loads((E/'b-resolved-static-verification.json').read_text());assert proof['status']=='PASS_TESTED_STATIC_SURFACE_SCOPE' and len(proof['poses'])==5 and route.sha(src)==proof['candidateSha256']
    bpy.ops.wm.open_mainfile(filepath=str(src));before=verify.original_state();old=fibres();rig=bpy.data.objects['AFN_R0005_Rig'];mats=sorted((m for m in bpy.data.materials if m.name.startswith('AFN13_ChestnutKeratin')),key=lambda m:m.name)
    matrices={o.name:(o.matrix_parent_inverse.copy(),o.matrix_basis.copy()) for o in bpy.data.objects if o.type=='CURVES' and o.name.startswith('AFN13_')}
    copies={o.name:o.data.copy() for o in bpy.data.objects if o.type=='CURVES' and o.name.startswith('AFN13_')}
    for o in list(bpy.data.objects):
        if o.type=='CURVES' and o.name.startswith('AFN13_'):
            data=o.data;bpy.data.objects.remove(o,do_unlink=True);bpy.data.hair_curves.remove(data)
    cache=S/'aevrynd-female-next-r0013-b-native-hair-data.npz';d=np.load(cache);P=d['positions'];rr=d['radii'];offsets=d['offsets'];layers=d['layers']
    for li,name in enumerate(('AFN13_PRIMARY_MASS','AFN13_SECONDARY_CLUMPS','AFN13_HAIRLINE_FINE','AFN13_FLYAWAYS')):
        ids=np.flatnonzero(layers==li);paths=[P[offsets[i]:offsets[i+1]] for i in ids];radii=[rr[offsets[i]:offsets[i+1]] for i in ids];o=build.native(name,paths,radii,rig,mats,copied_data=copies[name]);o.matrix_parent_inverse,o.matrix_basis=matrices[name];bpy.context.view_layer.update()
    assert before==verify.original_state();new=fibres();assert new==old,(old,new)
    dest=S/'aevrynd-female-next-r0013-b-safe-io-native-envelope-hair-study.blend';bpy.context.scene['aevrynd_release_state']='STATIC_RESEARCH_PORTABLE_CACHE_REBUILT_NOT_RUNTIME';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    (E/'safe-io-cache-rebuild.json').write_text(json.dumps({'source':str(src),'sourceSha256':route.sha(src),'output':str(dest),'outputSha256':route.sha(dest),'cacheSha256':route.sha(cache),'originalStateEquality':True,'savedWorldFibresRadiiMaterialsEquality':True,'fibreSha256':new,'collisionEvidenceInheritedFrom':'b-resolved-static-verification.json','geometryCandidate':'B_UNCHANGED','repair':'Copy valid native curve datablocks loaded from B, rewrite positions/radii/material fields from portable cache, assign integer fields with Python lists, restore exact original transforms. No operator or stock dynamics graphs. Does not assert a proven crash root cause.','wallSeconds':time.time()-start},indent=2)+'\n');print('AFN13_SAFE_IO_REBUILD_DONE',flush=True)

if __name__=='__main__':main()
