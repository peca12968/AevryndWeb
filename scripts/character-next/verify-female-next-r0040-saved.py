"""Reopen actual private C native curves; do not extrapolate guide proof."""
import bpy,importlib.util,time,json
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('children40',Path(__file__).with_name('build-female-next-r0040-guided-children.py'));ch=importlib.util.module_from_spec(sp);sp.loader.exec_module(ch)
ad=ch.ad;rt=ch.rt;rod=ch.rod;f=ch.f;b=ch.b;E=ch.E;PVT=ch.PVT

def main():
    start=time.time();bpy.ops.wm.open_mainfile(filepath=str(ch.OUT));source_sha=b.sha(ch.OUT)
    obj=bpy.data.objects['AFN40_C_PRIVATE_GUIDED_CHILDREN'];guide=bpy.data.objects['AFN40_C_PRIVATE_EDITABLE_GUIDES'];p,r=ad.read_native(obj);g,gr=ad.read_native(guide)
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);f.flowcheck.cap.math_controls()
    proof=f.flowcheck.check(g,gr,tree,V[T]);(PVT/'c-saved-guides-body.json').write_text(json.dumps(proof,indent=2)+'\n')
    obj.hide_render=True;guide.hide_render=True;retained=f.state();roots=np.array([x[0] for x in p]);guideRoots=np.array([x[0] for x in g])
    assert all(np.isfinite(x).all() for x in p+r+g+gr)
    baseline=rod.c.PRIVATE/'aevrynd-female-next-r0039-c1-surface-transfer-study.blend';bpy.ops.wm.open_mainfile(filepath=str(baseline));old=bpy.data.objects['AFN39_C1_PRIVATE_SURFACE_TRANSFER'];bp,br=ad.read_native(old)
    childroot=float(np.linalg.norm(roots-np.array([x[0] for x in bp]),axis=1).max());assert childroot<1.5e-7
    bpy.ops.wm.open_mainfile(filepath=str(rod.SRC));assert f.state()==retained
    rest=np.load(PVT/'a-rebuilt-guide-paths.npz')['restPositionsWorld'].astype('f8');guideRootError=float(np.linalg.norm(guideRoots-rest[:,0],axis=1).max());assert guideRootError<1.5e-7
    pilot=json.loads((E/'c-child-pilot.json').read_text());ids=np.linspace(0,len(p)-1,256,dtype='i4')
    (PVT/'c-pilot-global-lineage.json').write_text(json.dumps({'selectedActualChildCurveIds':ids.tolist(),'failureSamplesWithActualIds':[{**x,'actualChildCurve':int(ids[x['curve']])} for x in pilot['failureSamples']]},indent=2)+'\n')
    safe={k:proof[k] for k in ('status','curves','segments','unqualifiedSegments','minimumCertifiedClearanceLowerBoundM','minimumSampledCVSurfaceGapM','methods','numericalAllowanceM','scope')}
    ad.save('c-reopened-verification.json',{'source':str(ch.OUT),'sourceSha256':source_sha,'allDataFinite':True,'completeOwnedBodyEyeSkinLashBrowAndStageExact':True,'childCurves':len(p),'childPoints':sum(map(len,p)),'all376SavedNativeGuideBody':safe,'guideRootErrorM':guideRootError,'originalC1ChildRootErrorM':childroot,'rootStandOffM':.00018,'representativeChildBody':{k:pilot[k] for k in ('status','curves','segments','unqualifiedSegments','minimumCertifiedClearanceLowerBoundM','minimumSampledCVSurfaceGapM')},'pilotCurveMapping':'private/c-pilot-global-lineage.json','guideDoesNotProveChildren':True,'childAllBodySelfOpticalTissueClothingDynamicsRuntime':'NOT_QUALIFIED','sourceWorkingSceneUnmodified':True,'seconds':time.time()-start})
    print('R40_REOPENED_DONE',proof['status'],proof['unqualifiedSegments'],childroot,guideRootError,time.time()-start,flush=True)

if __name__=='__main__':main()
