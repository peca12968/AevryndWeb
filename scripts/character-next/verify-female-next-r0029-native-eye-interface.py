"""Reopened full-sculpt neutral contact, containment and changed-region self test."""
import bpy,importlib.util,json,hashlib,gc,time
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('b29',Path(__file__).with_name('build-female-next-r0029-native-eye-interface.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
b=q.b;E=q.E
DIRS=[Vector(x).normalized() for x in ((1,.371,.193),(-.317,1,.233),(.217,-.181,1),(-1,-.211,.317),(.193,.271,-1))]
def parity(tree,p):
    values=[]
    for d in DIRS:
        origin=Vector(p.tolist());count=0
        for _ in range(200):
            hit=tree.ray_cast(origin,d,5.0)[0]
            if hit is None:break
            origin=hit+d*1e-7;count+=1
        else:return {'classification':'unresolved','reason':'200-ray-hit cap'}
        values.append(count%2)
    return {'classification':('inside' if values[0] else 'outside') if len(set(values))==1 else 'unresolved','fiveRayParities':values,'rayAdvanceM':1e-7}
def tree(v,t):return BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True,epsilon=0.0)
def changed_self(v,t,changed,full):
    ids=np.flatnonzero(np.any(changed[t],axis=1));partial=tree(v,t[ids]);pairs=full.overlap(partial);result=set()
    for a,local in pairs:
        c=int(ids[local]);a=int(a)
        if a==c or not set(t[a]).isdisjoint(t[c]):continue
        result.add(tuple(sorted((a,c))))
    return {'affectedTriangleCount':len(ids),'nonAdjacentTrianglePairs':len(result),'pairs':sorted(result)[:32]},result
def main():
    start=time.time();report=q.read('build-verification.json');assert b.sha(q.OUT)==report['outputSha256'];assert b.sha(q.SRC)==report['sourceSha256']
    bpy.ops.wm.open_mainfile(filepath=str(q.SRC));body=bpy.data.objects[b.BODY];vb,tb=b.evaluated(body,True);raw_before=np.array([list(v.co) for v in body.data.vertices]);original_cfg=b.config(bpy.context.scene);source_signatures={o.name:q.signature(o) for o in bpy.data.objects if o.type=='MESH'}
    bpy.ops.wm.open_mainfile(filepath=str(q.OUT));body=bpy.data.objects[b.BODY];v,t=b.evaluated(body,True);assert np.array_equal(tb,t);raw_after=np.array([list(v.co) for v in body.data.vertices]);native_changed=np.flatnonzero(np.any(raw_before!=raw_after,axis=1));assert set(native_changed)<=set(report['nativeChangedVertices']);assert b.config(bpy.context.scene)==original_cfg
    eyes={o.name:b.evaluated(o,True) for o in bpy.data.objects if o.type=='MESH' and '.eye.' in o.name}
    for n in eyes:assert q.signature(bpy.data.objects[n])==source_signatures[n]
    assert b.mesh_signature(body.data)['uv']==source_signatures[b.BODY]['mesh']['uv'];assert not bpy.data.libraries and not bpy.data.texts and not bpy.data.armatures
    full=tree(v,t);contacts={}
    for name,(p,pt) in eyes.items():
        other=tree(p,pt);pairs=full.overlap(other);sample=[full.find_nearest(Vector(x.tolist()))[3] for x in p];center=(p.min(0)+p.max(0))*.5
        contacts[name]={'bodyEyeTrianglePairs':len(pairs),'eyeCenterBodyContainment':parity(full,center),'eyeVertexSampleUnsignedMinimumGapM':float(min(sample)),'pairExamples':[[int(a),int(c)] for a,c in pairs[:24]],'scope':'Complete level3 body surface and full fixed eye mesh. No inner-wall exclusion. Gap is vertex-sampled, not exact full-surface minimum.'}
    exact_changed=np.any(v!=vb,axis=1);after_self,after_pairs=changed_self(v,t,exact_changed,full);del full;gc.collect();before_full=tree(vb,t);before_self,before_pairs=changed_self(vb,t,exact_changed,before_full);del before_full;gc.collect()
    newpairs=after_pairs-before_pairs
    edges=np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True);areas=np.linalg.norm(np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]),axis=1)*.5
    clean=all(c['bodyEyeTrianglePairs']==0 and c['eyeCenterBodyContainment']['classification']=='outside' for c in contacts.values()) and after_self['nonAdjacentTrianglePairs']==0 and not np.any(counts!=2) and not np.any(areas<1e-14) and np.isfinite(v).all()
    result={'source':str(q.OUT),'sourceSha256':b.sha(q.OUT),'savedFileOpened':True,'nativeChangedVertexCount':len(native_changed),'fullBodyEvaluatedVertices':len(v),'fullBodyEvaluatedTriangles':len(t),'eyeGeometryAndTransformsExact':True,'baseTopologyAndUVPreserved':True,'sameRenderingSettings':True,'contact':contacts,'changedRegionSelfBefore':before_self,'changedRegionSelfAfter':after_self,'newNonAdjacentSelfPairs':len(newpairs),'newSelfPairExamples':[list(x) for x in sorted(newpairs)[:32]],'exactChangedEvaluatedVertexCount':int(exact_changed.sum()),'bodyBoundaryEdges':int((counts==1).sum()),'bodyNonManifoldEdges':int((counts>2).sum()),'minimumBodyTriangleAreaM2':float(areas.min()),'nonFiniteBodyCoordinates':int((~np.isfinite(v)).sum()),'status':'PASS_NEUTRAL_FULL_SURFACE_AND_CHANGED_REGION_SELF_SCOPE' if clean else 'FAIL_NEUTRAL_OR_SELF_SCOPE','seconds':time.time()-start,'limits':['Neutral static only; no gaze/blink/continuous animation proof.','Existing iris/cornea/pupil/wetline layers still absent.','Whole body self-contact outside the exactly changed triangle region was not tested.','Unsigned vertex-sampled gap is not an exact complete-surface signed minimum.','No hair/cloth/rig/runtime/LOD/performance acceptance or appearance score.']};q.save('saved-static-verification.json',result)
    print('R0029_VERIFY_DONE',json.dumps({'status':result['status'],'contact':contacts,'selfBefore':before_self,'selfAfter':after_self,'seconds':result['seconds']}),flush=True)
if __name__=='__main__':main()
