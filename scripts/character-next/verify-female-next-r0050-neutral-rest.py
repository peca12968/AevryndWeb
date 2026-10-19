"""Actual saved full-resolution neutral-rest contact and authoring proof.

Fixed static pose only. Continuous-field injectivity does not replace mesh
intersection tests. Structural source tissue joins retain their exact lineage.
"""
import bpy,importlib.util,json,time,hashlib,gc,numpy as np
from pathlib import Path
from mathutils import Vector
sp=importlib.util.spec_from_file_location('neutral50verify',Path(__file__).with_name('build-female-next-r0050-neutral-rest.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
b=a.b;f=a.f;v=a.v;i=a.i;E=a.E;S=a.S;exact=f.flowcheck.module('exact50','verify-female-next-r0037-eye-margin.py');selfcheck=f.flowcheck.module('self50','verify-female-next-r0029-native-eye-interface.py')
def save(n,x):a.save(n,x)
def actual_pairs(P,T,Q,U,pairs,limit=30):
    bad=[]
    for x,y in pairs:
        hits=exact.intersections(P[T[x]],Q[U[y]])
        if hits:bad.append({'triangles':[int(x),int(y)],'pointsM':[p.tolist()for p in hits[:4]]})
    return {'bvhPairs':len(pairs),'actualSurfaceIntersectionPairs':len(bad),'witnesses':bad[:limit]}
def changed_self(P,T,moved,tree):
    broad,pairs=selfcheck.changed_self(P,T,moved,tree);actual=[]
    for x,y in pairs:
        points=exact.intersections(P[T[x]],P[T[y]])
        if points:actual.append({'triangles':[int(x),int(y)],'pointsM':[p.tolist()for p in points[:4]]})
    return {'affectedTriangles':broad['affectedTriangleCount'],'broadNonAdjacentPairs':len(pairs),'actualNonAdjacentPairs':len(actual),'actualPairs':actual[:40]}
def meshself(P,T,tree):
    pairs=[(int(x),int(y))for x,y in tree.overlap(tree)if x<y and set(T[x]).isdisjoint(T[y])];return actual_pairs(P,T,P,T,pairs)
def main():
    tick=time.time();build=json.loads((E/'a-build-summary.json').read_text());assert b.sha(a.OUT)==build['outputSha256'];assert b.sha(a.SRC)==build['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=str(a.SRC));before=f.state();VB,T=b.evaluated(bpy.data.objects[b.BODY],True);native={n:b.mesh_signature(bpy.data.objects[n].data)for n in before['meshes']};bpy.ops.wm.open_mainfile(filepath=str(a.OUT));controller=bpy.data.objects[a.CONTROL];attr=controller.data.attributes[a.ATTRIBUTE];assert abs(attr.data[0].value-a.ANGLE)<1e-7;after=f.state();assert after['materials']==before['materials']and after['skinFields']==before['skinFields']and after['curves']==before['curves']and after['stage']==before['stage'];assert all(b.mesh_signature(bpy.data.objects[n].data)==sig for n,sig in native.items());V,TT=b.evaluated(bpy.data.objects[b.BODY],True);assert np.array_equal(T,TT);moved=np.linalg.norm(V-VB,axis=1)>1e-9;full=selfcheck.tree(V,T);results={'status':'RUNNING','source':str(a.OUT),'sha256':b.sha(a.OUT),'sourceVertices':len(V),'sourceTriangles':len(T),'changedBodyVertices':int(moved.sum()),'nativeGeometryUVMaterialsFieldsAndScalpCurvesExact':True};optics={};opticalData={}
    for side in ('L','R'):
        for part in ('Sclera','Cornea','Iris','Pupil'):
            name=f'AFN30_{side}_{part}';P,U=b.evaluated(bpy.data.objects[name],True);tree=selfcheck.tree(P,U);opticalData[name]=(P,U,tree);row=actual_pairs(V,T,P,U,full.overlap(tree));row['interiorAnchorAgainstBody']=selfcheck.parity(full,P.mean(0));optics[name]=row
    results['bodyOptics']=optics;results['changedBodySelfAfter']=changed_self(V,T,moved,full);save('a-contact-progress.json',results);print('R50_BODY_GATE',sum(r['actualSurfaceIntersectionPairs']for r in optics.values()),results['changedBodySelfAfter']['actualNonAdjacentPairs'],flush=True)
    sourceTree=selfcheck.tree(VB,T);results['changedBodySelfBefore']=changed_self(VB,T,moved,sourceTree);del sourceTree;gc.collect();triids=np.flatnonzero(np.any(moved[T],axis=1));oldN=np.cross(VB[T[triids,1]]-VB[T[triids,0]],VB[T[triids,2]]-VB[T[triids,0]]);newN=np.cross(V[T[triids,1]]-V[T[triids,0]],V[T[triids,2]]-V[T[triids,0]]);oldArea=np.linalg.norm(oldN,axis=1);newArea=np.linalg.norm(newN,axis=1);results['triangleShapeDiagnostic']={'minimumAreaM2':float(newArea.min()*.5),'minimumAreaRatio':float((newArea/oldArea).min()),'minimumSourceTargetNormalCos':float((np.einsum('ij,ij->i',oldN,newN)/oldArea/newArea).min()),'scope':'Diagnostic, not sole inversion/self-contact certificate.'}
    if any(r['actualSurfaceIntersectionPairs']for r in optics.values())or results['changedBodySelfAfter']['actualNonAdjacentPairs']:
        results['status']='FAIL_BODY_SELF_OR_FIXED_OPTICS_STOP';save('a-contact-progress.json',results);return
    records=json.loads((b.R/'Evidence/character-female-next/r0037-eye-margin/c-review-tissue-bindings.json').read_text());tissues={};otherData={};good=True
    for record in records['patches']:
        name=record['object'];P,U=b.evaluated(bpy.data.objects[name],True);tree=selfcheck.tree(P,U);expected=np.array([np.array(q['weights'])@V[q['indices']]for q in record['nodes']]);err=float(np.linalg.norm(P[:record['baseNodeCount']]-expected,axis=1).max());bodyJoin=exact.body_attachment(bpy.data.objects[name],P,U,full,V,T,record);self=meshself(P,U,tree);opt={n:actual_pairs(P,U,Q,W,tree.overlap(qt))for n,(Q,W,qt)in opticalData.items()};j=int(np.argmax(np.linalg.norm(P[record['topVertices']]-P[:record['baseNodeCount']],axis=1)));anchor=(P[j]+P[record['topVertices'][j]])*.5;anchorBody=selfcheck.parity(full,anchor);row={'sourceBaseBarycentricReadbackMaxM':err,'sourceJoinInterfaceAllowanceM':1e-6,'bodyAttachment':bodyJoin,'actualSelf':self,'fixedOptics':opt,'interiorAnchorAgainstBody':anchorBody};tissues[name]=row;otherData[name]=(P,U,tree);good=good and err<1e-6 and bodyJoin['unqualifiedNonAttachmentPairs']==0 and self['actualSurfaceIntersectionPairs']==0 and all(r['actualSurfaceIntersectionPairs']==0 for r in opt.values())and anchorBody['classification']=='outside';results['tissues']=tissues;save('a-contact-progress.json',results);print('R50_TISSUE',name,err,bodyJoin['unqualifiedNonAttachmentPairs'],self['actualSurfaceIntersectionPairs'],flush=True)
    lashes={}
    for name in [n for n in before['meshes']if n.endswith('_Lashes')]:
        P,U=b.evaluated(bpy.data.objects[name],True);tree=selfcheck.tree(P,U);bodyContact=actual_pairs(P,U,V,T,tree.overlap(full));self=meshself(P,U,tree);opt={n:actual_pairs(P,U,Q,W,tree.overlap(qt))for n,(Q,W,qt)in opticalData.items()};assert len(P)%258==0;components=len(P)//258;anchors=np.array([P[k*258+16*8:k*258+17*8].mean(0)for k in range(components)]);classifications=[selfcheck.parity(full,p)['classification']for p in anchors];row={'closedMeshComponents':components,'actualBodyContact':bodyContact,'actualSelf':self,'fixedOptics':opt,'componentInteriorAnchorsAgainstBody':{state:classifications.count(state)for state in set(classifications)},'scope':'Actual deformed closed surface tests and component anchors, not old undeformed fibre capsules/radii.'};lashes[name]=row;otherData[name]=(P,U,tree);good=good and bodyContact['actualSurfaceIntersectionPairs']==self['actualSurfaceIntersectionPairs']==0 and all(r['actualSurfaceIntersectionPairs']==0 for r in opt.values())and all(s=='outside'for s in classifications);results['lashes']=lashes;save('a-contact-progress.json',results);print('R50_LASH',name,bodyContact['actualSurfaceIntersectionPairs'],self['actualSurfaceIntersectionPairs'],flush=True)
    between={};names=list(otherData)
    for index,name in enumerate(names):
        P,U,tree=otherData[name]
        for other in names[index+1:]:
            Q,W,qt=otherData[other];row=actual_pairs(P,U,Q,W,tree.overlap(qt));between[name+' / '+other]=row;good=good and row['actualSurfaceIntersectionPairs']==0
    results['betweenWetAndLashMeshes']=between
    # All original native scalp/brow complete finite segments vs changed-region
    # body and changed wet/lash AABBs, not representative guide-only checks.
    both=np.concatenate((VB[T[triids]].reshape(-1,3),V[T[triids]].reshape(-1,3)));patchLo=both.min(0);patchHi=both.max(0);curves={}
    for name in before['curves']:
        o=bpy.data.objects[name];P,rr=v.hair_arrays(o);mx=np.array(o.matrix_world);P=P.astype('f8')@mx[:3,:3].T+mx[:3,3];rr=rr.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2);radius=np.maximum(rr[:,:-1],rr[:,1:])+1e-6;lo=np.minimum(P[:,:-1],P[:,1:])-radius[...,None];hi=np.maximum(P[:,:-1],P[:,1:])+radius[...,None];sep=np.maximum(patchLo-hi,lo-patchHi).max(2);ids=np.argwhere(sep<=0);bad=[];minimum=float(sep[sep>0].min())if np.any(sep>0)else None
        for ci,j in ids:
            A,B=P[ci,j],P[ci,j+1];d0=full.find_nearest(Vector(A))[3];d1=full.find_nearest(Vector(B))[3];gap,method=f.flowcheck.cap.segment_test(A,B,d0,d1,float(max(rr[ci,j],rr[ci,j+1])),full,V[T])
            if gap<=0:bad.append({'curve':int(ci),'segment':int(j),'gapLowerBoundM':float(gap),'method':method})
        objects={}
        for objname,(Q,W,qt)in otherData.items():
            sep2=np.maximum(Q.min(0)-hi,lo-Q.max(0)).max(2);candidate=np.argwhere(sep2<=0);fails=[]
            for ci,j in candidate:
                A,B=P[ci,j],P[ci,j+1];d0=qt.find_nearest(Vector(A))[3];d1=qt.find_nearest(Vector(B))[3];gap,method=f.flowcheck.cap.segment_test(A,B,d0,d1,float(max(rr[ci,j],rr[ci,j+1])),qt,Q[W])
                if gap<=0:fails.append({'curve':int(ci),'segment':int(j),'gapLowerBoundM':float(gap),'method':method})
            objects[objname]={'completeSegments':int(sep2.size),'aabbExcluded':int((sep2>0).sum()),'directSegments':len(candidate),'unqualifiedSegments':len(fails),'failures':fails[:20]};good=good and not fails
        curves[name]={'curves':len(P),'completeSegments':int(sep.size),'bodyChangedPatchAabbExcluded':int((sep>0).sum()),'directBodySegments':len(ids),'newUnqualifiedBodySegments':len(bad),'bodyFailures':bad[:20],'minimumAabbAxisSeparationBoundM':minimum,'wetLashMeshes':objects,'scope':'Changed-region update only; exact unchanged source curve/body relations remain under their prior limited scope,not newly certified globally. Same actual originalpoints/radii/worldpose.'};good=good and not bad;results['originalCurveChangedRegionUpdate']=curves;save('a-contact-progress.json',results);print('R50_CURVES',name,len(ids),len(bad),flush=True)
    eyeSummary={}
    for side in ('L','R'):
        eye=i.i.outer(side);scans=i.i.aperture(full,i.i.tree(*eye),np.array(i.i.FITS[side]['centerM']),[0.]);row=scans[0];eyeSummary[side]={'centralAperture':row,'physicalIrisRadiusM':.00565,'centralUpperIrisCoverageM':.00565-row['upperAboveEyeCenterM'],'scope':'Actual geometry-only source exterior rays; not refracted apparent pupil/MRD or medical diagnosis.'}
    results['eyeRestMeasurements']=eyeSummary;domain=bpy.data.objects['AFN48_ANATOMICAL_SCALP_DOMAIN'];domainTri=np.array([r.value for r in domain.data.attributes['AFN48_BodyTriangle'].data],dtype='i4');assert not np.any(moved[T[domainTri]]);results['r48ScalpDomainOriginalSourceTrianglesUnchanged']=True
    # The native control remains zero-reversible after independent reopening.
    attr.data[0].value=0.;bpy.context.view_layer.update();atZero=f.state();assert atZero==before;attr.data[0].value=a.ANGLE;bpy.context.view_layer.update();results['zeroControlRestoresCompleteSourceStateExact']=True;results['status']='PASS_STATED_STATIC_NEUTRAL_SCOPE'if good else'FAIL_OR_UNQUALIFIED_ATTACHMENT_OR_CURVE_SCOPE';results['limits']=['Not a blink or facial/skeletal rig','Fixed neutral source only; no animated/continuous contact qualification','Continuous-map angular bound is not alone finite-mesh contact proof','AABB axis bounds and sampled ray coverage are not exact global signed minimum distances','No hair-self,dynamics,clothes,oral motion or runtime/LOD/CPU/GPU/memory acceptance'];results['seconds']=time.time()-tick;save('a-saved-static-verification.json',results);print('R50_STATIC_VERIFICATION',results['status'],time.time()-tick,flush=True)
if __name__=='__main__':main()
