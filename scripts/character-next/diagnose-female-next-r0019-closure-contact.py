"""Distinguish native closure issues from the repaired socket, without parameter sweeps."""
import bpy,json,importlib.util
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('build',Path(__file__).with_name('build-female-next-r0019-native-blink.py'));build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
S,E,SRC,solid=build.S,build.E,build.SRC,build.solid
def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC));solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');body=bpy.data.objects['AFN_R0008_Body'];P=build.positions(body).astype(np.float64);d=np.load(S/'aevrynd-female-next-r0019-native-blink-data.npz');native=d['nativeNeutral'].astype(np.float64);delta=d['deltaL'].astype(np.float64)+d['deltaR'].astype(np.float64);offset=P-native;changed=(np.linalg.norm(delta,axis=1)+np.linalg.norm(offset,axis=1))>0
    optics={o.name:solid.data(o) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN6_')};rows=[]
    for name,Q in (('current-repaired-open',P),('current-repaired-closed',P+delta),('native-open',native),('native-closed',native+delta)):
        body.data.vertices.foreach_set('co',Q.astype(np.float32).ravel());body.data.update();bpy.context.view_layer.update();V,T,tree=solid.data(body);Tn=np.array(T,np.int32);ids=np.flatnonzero(changed[Tn].any(axis=1));sub=BVHTree.FromPolygons(V,Tn[ids].tolist(),all_triangles=True);pairs=[]
        for a,b in sub.overlap(tree):
            a=int(ids[a])
            if a==b or not set(T[a]).isdisjoint(T[b]):continue
            pairs.append(tuple(sorted((a,b))))
        pairs=sorted(set(pairs));samples=[]
        for a,b in pairs[:80]:
            va,vb=Tn[a],Tn[b];samples.append({'triangles':[a,b],'vertices':[va.tolist(),vb.tolist()],'centroids':[np.mean(np.array([V[i] for i in va]),axis=0).tolist(),np.mean(np.array([V[i] for i in vb]),axis=0).tolist()],'maximumOriginalSocketOffsetM':float(np.linalg.norm(offset[np.r_[va,vb]],axis=1).max()),'maximumClosureMoveM':float(np.linalg.norm(delta[np.r_[va,vb]],axis=1).max())})
        rows.append({'case':name,'affectedBodySelfTrianglePairs':len(pairs),'opticalTrianglePairs':{n:len(tree.overlap(v[2])) for n,v in optics.items()},'selfSamples':samples})
    # Save old raw-key attachment contact counts already observed, not new geometry.
    build.save('closure-contact-root-cause.json',{'cases':rows,'comparisonScope':'Four defined baseline/closure geometries, identical fixed optics. No style or strength sweep. The native baseline has not undergone the r0008 socket correction.','nextDecision':'Use the comparison and localized offending facets to decide whether native closure, socket displacement or both need a topology-aware corrective. Do not accept static optical clearance as a complete blink gate.'})
    print('R0019_CONTACT_DIAGNOSIS '+json.dumps([(x['case'],x['affectedBodySelfTrianglePairs'],sum(x['opticalTrianglePairs'].values())) for x in rows]),flush=True)
if __name__=='__main__':main()
