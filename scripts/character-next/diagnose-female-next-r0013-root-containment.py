"""Resolve the one B turn-right root classification without rerunning full strands."""
import bpy,json,importlib.util
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('verify',Path(__file__).with_name('verify-female-next-r0013-native-groom.py'));verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
S,E,solid=verify.S,verify.E,verify.solid
bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0013-b-native-envelope-hair-study.blend'));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'turn-right');V,T,tree=solid.data(bpy.data.objects['AFN_R0008_Body']);V=np.array(V,dtype=np.float64);tri=V[np.array(T,dtype=np.int32)];rows=[]
for o in bpy.data.objects:
    if o.type!='CURVES' or not o.name.startswith('AFN13_'):continue
    P,rr=verify.native_paths(o)
    for ci,(p,r) in enumerate(zip(P,rr)):
        state=solid.classify(tree,tri,Vector(p[0]))
        if state=='outside':continue
        ds=[tree.find_nearest(Vector(v))[3] for v in p];winding=solid.winding(tri,p[0]);segments=[]
        for j in range(min(12,len(p)-1)):
            gap,method=verify.route.capsule.segment_test(p[j],p[j+1],ds[j],ds[j+1],float(max(r[j],r[j+1])),tree,tri);segments.append({'index':j,'gapLowerBoundM':gap,'method':method,'nextPointWinding':solid.winding(tri,p[j+1]) if j<2 else None})
        rows.append({'object':o.name,'curve':ci,'state':state,'rootWinding':winding,'root':p[0].tolist(),'nearestRootSurfaceDistanceM':ds[0],'firstSegments':segments})
(E/'b-root-containment-diagnosis.json').write_text(json.dumps({'pose':'turn-right','rootClassificationFailures':rows,'scope':'Only anomalous root classification and its initial segments; no acceptance override.'},indent=2)+'\n');print('AFN13_ROOT_DIAG='+json.dumps(rows),flush=True)
