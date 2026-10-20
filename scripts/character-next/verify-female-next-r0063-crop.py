"""Read actual saved crop: unchanged complete anatomy, root lineage and contact.

Self broad phase is conservative midpoint spheres around finite capsules.
An early exact witness can reject; an unfinished scan is NEVER a whole pass.
"""
from pathlib import Path
import bpy,numpy as np,json,time,sys
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
import importlib.util
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('build63verify','build-female-next-r0063-layered-crop.py');g=m.g;k=g.k
v=module('read61for63','verify-female-next-r0061-complete-groom.py')
pair=module('finite63','hair-female-next-r0062-finite-pairs.py');E=m.E

def hair(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;Q=np.empty(len(d.position_data)*3,'f4');d.position_data.foreach_get('vector',Q);rr=np.empty(len(d.position_data),'f4');d.attributes['radius'].data.foreach_get('value',rr)
    assert all(c.points_length==m.N for c in d.curves);assert np.array_equal(np.array(o.matrix_world),np.eye(4))
    return Q.reshape(-1,m.N,3),rr.reshape(-1,m.N)

def self_witness(Q,R):
    tick=time.time();A,B=pair.endpoints(Q);mid=(A+B)/2;half=np.linalg.norm(B-A,axis=1)/2;rr=np.maximum(R[:,:-1],R[:,1:]).ravel().astype('f8');N=m.N-1
    tree=KDTree(len(A))
    for i,p in enumerate(mid):tree.insert(Vector(p),i)
    tree.balance();largest=float((half+rr).max());tested=0;witness=[];min_gap=None
    # A strict early rejection is enough to prevent adoption, not an
    # exhaustive total count. No failed fibre is deleted from the candidate.
    for i in range(len(A)):
        neighbours=tree.find_range(Vector(mid[i]),float(half[i]+rr[i]+largest+1e-6))
        ids=np.array([j for _,j,_ in neighbours if j>i and not (i//N==j//N and j-i<=1)],dtype='i4')
        if not len(ids):continue
        delta=np.linalg.norm(mid[ids]-mid[i],axis=1);ids=ids[delta<=half[i]+half[ids]+rr[i]+rr[ids]+1e-6]
        if not len(ids):continue
        ds=pair.distance(np.repeat(A[i,None],len(ids),axis=0),np.repeat(B[i,None],len(ids),axis=0),A[ids],B[ids]);gap=ds-rr[i]-rr[ids];tested+=len(ids);min_gap=float(gap.min()) if min_gap is None else min(min_gap,float(gap.min()))
        for j,d,gg in zip(ids[gap<1e-6],ds[gap<1e-6],gap[gap<1e-6]):
            witness.append({'segments':[int(i),int(j)],'fibres':[int(i//N),int(j//N)],'centrelineDistanceM':float(d),'physicalGapM':float(gg),'reason':'physicalOverlap' if gg<0 else 'numericalClearanceInsufficient'})
        if len(witness)>=16:break
        if i and i%20000==0:print('R63_SELF_SCANNED',i,len(A),tested,flush=True)
    return {'status':'REJECT_ACTUAL_FINITE_SELF_WITNESSES' if witness else 'PASS_TESTED_ALL_FINITE_PAIRS','scannedThroughSegment':int(i),'totalActualSegments':len(A),'exactCandidatePairsTested':tested,'earlyStoppedAfterWitnesses':bool(witness),'failureCountIsGlobalTotal':False,'witnesses':witness[:32],'minimumAmongRefinedCandidatesM':min_gap,'exactGlobalMinimumM':None,'numericalClearanceM':1e-6,'seconds':time.time()-tick,'broadPhase':'Conservative actual segment midpoint sphere radius halfLength+maxEndpointRadius; pair sphere overlap then float64 exact finite segment distance. Connected immediate same-curve joints only excluded.'}

def main():
    tick=time.time();ref=json.loads((E/'a-build-summary.json').read_text());assert m.sha(m.OUT)==ref['outputSha256'];assert m.sha(m.SRC)==ref['sourceSha256']
    names=list(json.loads((E.parent/'r0060-ocular-assembly/b-build-summary.json').read_text())['visibleComponents'].values())
    bpy.ops.wm.open_mainfile(filepath=str(m.SRC));stage=k.f.v.stage();before={n:v.mesh_signature(bpy.data.objects[n]) for n in names};face={n:k.v59.native_curves(bpy.data.objects[n]) for n in ('AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES')};v.raise_subdivision();poses={}
    for frame in (1,21):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();poses[frame]={n:v.digest(k.mesh(bpy.data.objects[n])['V']) for n in names}
    bpy.ops.wm.open_mainfile(filepath=str(m.OUT));after={n:v.mesh_signature(bpy.data.objects[n]) for n in names};assert before==after;assert face=={n:k.v59.native_curves(bpy.data.objects[n]) for n in face}
    now=k.f.v.stage();assert now['lights']==stage['lights']
    for key in ('transform','look','exposure','gamma','world'):assert now['config'][key]==stage['config'][key]
    v.raise_subdivision()
    for frame in (1,21):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();assert poses[frame]=={n:v.digest(k.mesh(bpy.data.objects[n])['V']) for n in names}
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();ob=bpy.data.objects[m.NAME];Q,rr=hair(ob);raw=np.load(E/'a-crop-authoring.npz');assert np.array_equal(Q,raw['positions']) and np.array_equal(rr,raw['radii']);assert np.isfinite(Q).all() and np.isfinite(rr).all() and (rr>0).all()
    for n,key,kind,field,size in [('AFN63_RestRenderTriangle','rootRecords','i4','value',1),('AFN63_NativeScalpFace','rootRecords','i4','value',1),('AFN63_RestBarycentric','rootRecords','f4','vector',3),('AFN63_Region','regions','i4','value',1),('AFN63_TuftDomain','tufts','i4','value',1)]:
        a=ob.data.attributes[n];assert a.domain=='CURVE';ar=np.empty(len(Q)*size,kind);a.data.foreach_get(field,ar)
        expected=raw[key]
        if n=='AFN63_RestRenderTriangle':expected=expected[:,0]
        elif n=='AFN63_NativeScalpFace':expected=expected[:,1]
        elif n=='AFN63_RestBarycentric':expected=expected[:,2:]
        assert np.array_equal(ar,expected.astype(kind).ravel())
    images=[]
    for im in bpy.data.images:
        if im.source=='FILE':
            p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.exists();im.reload();images.append({'relative':im.filepath,'sha256':m.sha(p)})
    assert len(images)==15;assert not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    parts=[k.mesh(bpy.data.objects[n]) for n in names];body=parts[4];rec=raw['rootRecords'];root=np.einsum('ij,ijk->ik',rec[:,2:],body['V'][body['T'][rec[:,0].astype('i4')]]);error=np.linalg.norm(root-Q[:,0],axis=1);assert error.max()<1e-6
    m.save('a-native-readback.json',{'source':str(m.OUT),'sha256':m.sha(m.OUT),'status':'PASS_SCOPED_NATIVE_READBACK','actualFibres':len(Q),'actualPoints':int(Q.size//3),'finiteSegments':len(Q)*(m.N-1),'originalBodyOpticMeshesKeysUVMaterialsExact':True,'originalNeutralClosedRenderPositionsExact':True,'originalFacialFibresExact':True,'originalLightsSkinExposureExact':True,'relativeTextures':images,'positionsRadiiRootTuftAttributesExact':True,'maximumRestRootErrorM':float(error.max()),'rootJoinOrDynamicBindingAccepted':False,'fullCharacterAccepted':False,'seconds':time.time()-tick})
    print('R63_NATIVE_READBACK_PASS',len(Q),time.time()-tick,flush=True)
    m.save('a-finite-self-falsification.json',self_witness(Q,rr));print('R63_SELF_VERDICT_SAVED',flush=True)
    if '--body' in sys.argv:
        V,T,mi,fi=k.join(parts);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);result=k.f.flowcheck.check(Q[:,1:],rr[:,1:],tree,V[T],roots=False)
        # The aggregate includes open iris surfaces: it cannot be classified
        # as one solid. Classify the closed body separately, and exclude each
        # optical component by actual bounds only if every anchor is outside.
        bt=BVHTree.FromPolygons(body['V'].tolist(),body['T'].tolist(),all_triangles=True);body_tri=body['V'][body['T']];bad=[];anchors=Q[:,1];owners=[]
        for ci,p in enumerate(anchors):
            state=k.f.flowcheck.cap.solid.classify(bt,body_tri,Vector(p))
            if state!='outside':bad.append({'curve':ci,'state':state})
        for row,name in zip(parts[:4],names[:4]):
            lo=row['V'].min(0);hi=row['V'].max(0);inside=np.all((anchors>=lo)&(anchors<=hi),axis=1);owners.append({'component':name,'anchorsInsideBounds':int(inside.sum())})
        if bad or any(o['anchorsInsideBounds'] for o in owners):result['status']='FAIL_OR_UNRESOLVED'
        result.update(source=str(m.OUT),sha256=m.sha(m.OUT),closedBodyAnchorFailures=bad,opticalBoundsExclusion=owners,scope='All actual free finite hair capsules vs all five evaluated render-level body/optical surfaces at neutral; body containment tested separately from open iris sheets. Anatomical first root segments excluded, joins and dynamics unaccepted.',seconds=time.time()-tick)
        m.save('a-free-shaft-body-verification.json',result);print('R63_BODY_VERDICT',result['status'],time.time()-tick,flush=True)

if __name__=='__main__':main()
