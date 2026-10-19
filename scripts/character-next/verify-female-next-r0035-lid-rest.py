"""Reopened full-sculpt neutral rest, actual optics, changed self and hair proof."""
import bpy,importlib.util,json,time,hashlib,gc
from pathlib import Path
import numpy as np
from mathutils import Vector
spec=importlib.util.spec_from_file_location('k35',Path(__file__).with_name('build-female-next-r0035-lid-rest.py'));k=importlib.util.module_from_spec(spec);spec.loader.exec_module(k)
i=k.i;g=k.g;b=k.b;E=k.E
v29=g.module('v29verify35','verify-female-next-r0029-native-eye-interface.py');v30=g.module('v30verify35','verify-female-next-r0030-eye-optics.py');v32=g.module('v32verify35','verify-female-next-r0032-registered-skin.py')

def save(n,x):i.save(n,x)
def read(n):return json.loads((E/n).read_text(encoding='utf8'))
def hair_arrays(o):
    d=o.data;sizes=[c.points_length for c in d.curves];assert len(set(sizes))==1
    p=np.empty(len(d.points)*3,dtype='f4');d.position_data.foreach_get('vector',p);r=np.empty(len(d.points),dtype='f4');d.attributes['radius'].data.foreach_get('value',r);return p.reshape(-1,sizes[0],3),r.reshape(-1,sizes[0])
def materials(names):return {n:[v32.material_signature(m) for m in bpy.data.objects[n].data.materials] for n in names}
def fields(body):
    out={}
    for name in ('AFN32_RegisteredCC0UVW','AFN32_PigmentWeight','AFN32_Roughness'):
        attr=body.data.attributes[name];n=3 if attr.data_type=='FLOAT_VECTOR' else 1;a=np.empty(len(attr.data)*n,dtype='f4');attr.data.foreach_get('vector' if n==3 else 'value',a);out[name]={'type':attr.data_type,'domain':attr.domain,'sha256':hashlib.sha256(a.tobytes()).hexdigest()}
    return out
def visible_state():return {o.name:g.signature(o) for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render}
def stage():return {'config':b.config(bpy.context.scene),'lights':[(o.name,list(o.location),list(o.rotation_euler),list(o.scale),o.data.energy,list(o.data.color)) for o in bpy.context.scene.objects if o.type=='LIGHT'],'hairPrimitive':bpy.context.scene.render.hair_type,'hairSubdivision':bpy.context.scene.render.hair_subdiv}

def changed_region_hair(VB,V,T,changed,bt,P,r,source_proof,source_hash):
    assert source_proof['status']=='PASS_REOPENED_STATIC_SCOPE';assert source_proof['bodyContact']['status']=='PASS_TESTED_STATIC_CAPSULES';assert not source_proof['bodyContact']['rootFailures']
    h=hashlib.sha256();h.update(VB.tobytes());h.update(T.tobytes());assert h.hexdigest()==source_proof['nineOriginalVisibleMeshesAndUVExact'][b.BODY]['worldSha256']
    tids=np.flatnonzero(np.any(changed[T],axis=1));both=np.concatenate((VB[T[tids]].reshape(-1,3),V[T[tids]].reshape(-1,3)));lo=both.min(0);hi=both.max(0)
    # The unchanged oriented mesh and identical patch boundary make the
    # before-minus-after surface a closed difference contained in this AABB.
    # Root winding outside it is therefore unchanged from the exact old proof.
    roots=P[:,0];sep=np.maximum(lo-roots,roots-hi).max(1);assert np.all(sep>1e-6)
    rr=np.maximum(r[:,:-1],r[:,1:])+1e-6;seglo=np.minimum(P[:,:-1],P[:,1:])-rr[...,None];seghi=np.maximum(P[:,:-1],P[:,1:])+rr[...,None]
    axis_sep=np.maximum(lo-seghi,seglo-hi).max(2);mask=axis_sep<=0.;candidates=np.argwhere(mask);fail=[];minimum=float(np.min(axis_sep[~mask])) if np.any(~mask) else float('inf');methods={}
    actual_triangles=V[T] if len(candidates) else None
    for ci,j in candidates:
        A=P[ci,j];B=P[ci,j+1];da=bt.find_nearest(Vector(A))[3];db=bt.find_nearest(Vector(B))[3];gap,method=g.cap.segment_test(A,B,da,db,float(max(r[ci,j],r[ci,j+1])),bt,actual_triangles);minimum=min(minimum,gap);methods[method]=methods.get(method,0)+1
        if gap<=0:fail.append({'curve':int(ci),'segment':int(j),'gapLowerBoundM':gap,'method':method})
    original_lower=source_proof['bodyContact']['minimumCertifiedClearanceLowerBoundM']
    return {'status':'PASS_UPDATED_NEUTRAL_BODY_SCOPE' if not fail else 'FAIL_UPDATED_BODY_CONTACT','totalFibres':len(P),'totalSegments':P.shape[0]*(P.shape[1]-1),'changedBodyTriangles':len(tids),'unchangedBodyTriangles':len(T)-len(tids),'changedPatchBeforeAfterAabbM':{'min':lo.tolist(),'max':hi.tolist()},'aabbExcludedChangedRegionSegments':int((~mask).sum()),'newDirectCompleteCapsuleChecks':len(candidates),'unqualifiedNewSegments':len(fail),'minimumNewChangedRegionClearanceLowerBoundM':minimum,'combinedInheritedAndNewGlobalClearanceLowerBoundM':min(original_lower,minimum),'methods':methods,'failureSamples':fail[:50],'allRootsOutsideChangedPatchAabb':True,'minimumRootAxisSeparationFromChangedPatchAabbM':float(sep.min()),'inheritance':{'sourceBodyGeometrySha256':h.hexdigest(),'sourceBodyMatchesOldProof':True,'sourceHairPositionsRadiiAndWorldMatrixExact':True,'sourcePhysicalProof':'r0033-parted-bob/c-saved-fibre-verification.json','newInputSourceSha256':source_hash,'scope':'Old complete capsule proof covers exactly unchanged body triangles. Every changed-region candidate segment is retested, all other complete capsules are excluded by expanded segment AABB. Root winding is unchanged outside the closed difference patch AABB. No CV-only or guide-to-child inference.'},'scopeLimits':['Neutral pose only','No hair/hair self, dynamics, cloth, rig, runtime or engine performance','Clearance lower bounds are not exact full-surface shortest distances']}

def main():
    start=time.time();report=read('b-build-verification.json');path=Path(report['output']);assert b.sha(path)==report['outputSha256'] and b.sha(k.SRC)==report['sourceSha256'];b.E=E
    bpy.ops.wm.open_mainfile(filepath=str(k.SRC));s=bpy.context.scene;before=visible_state();names=list(before);mat_before=materials(names);field_before=fields(bpy.data.objects[b.BODY]);stage_before=stage();body=bpy.data.objects[b.BODY];VB,TB=b.evaluated(body,True);native_before=np.array([list(v.co) for v in body.data.vertices]);polys=[list(p.vertices) for p in body.data.polygons]
    hair=next(o for o in s.objects if o.type=='CURVES' and not o.hide_render);hair_name=hair.name;hp,hr=hair_arrays(hair);hm=np.array(hair.matrix_world);hair_mats=[v32.material_signature(m) for m in hair.data.materials]
    old=__import__('json').loads((E.parent/'r0033-parted-bob/c-saved-fibre-verification.json').read_text());old_cache=np.load(Path(old['cache']));assert np.array_equal(hp,old_cache['positions']) and np.array_equal(hr,old_cache['radii']) and np.array_equal(hm,np.array(old['worldMatrix']))
    bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;body=bpy.data.objects[b.BODY];after=visible_state();V,T=b.evaluated(body,True);assert np.array_equal(T,TB) and [list(p.vertices) for p in body.data.polygons]==polys
    assert all(after[n]==before[n] for n in before if n!=b.BODY);assert after[b.BODY]['native']['uv']==before[b.BODY]['native']['uv'];assert fields(body)==field_before and materials(names)==mat_before and stage()==stage_before
    native_after=np.array([list(v.co) for v in body.data.vertices]);native_changed=np.flatnonzero(np.any(native_before!=native_after,axis=1));assert set(native_changed)==set(report['nativeChangedVertices'])
    hair=bpy.data.objects[hair_name];p,r=hair_arrays(hair);assert np.array_equal(p,hp) and np.array_equal(r,hr) and np.array_equal(np.array(hair.matrix_world),hm) and [v32.material_signature(m) for m in hair.data.materials]==hair_mats;assert not hair.modifiers and all(x.value==1 for x in hair.data.attributes['curve_type'].data);assert s.render.hair_type=='STRIP' and s.render.hair_subdiv==0
    changed=np.any(V!=VB,axis=1);bt=i.tree(V,T);contacts={}
    for n in names:
        if n==b.BODY:continue
        ev,et=b.evaluated(bpy.data.objects[n],True);pairs=bt.overlap(i.tree(ev,et));state=v29.parity(bt,ev[0]);
        if state['classification']=='unresolved':state=v30.winding_classification(V,T,ev[0])
        contacts[n]={'bodyOpticalTrianglePairs':len(pairs),'examples':[[int(x),int(y)] for x,y in pairs[:12]],'anchorBodyContainment':state,'vertexSampleUnsignedMinimumGapM':float(min(bt.find_nearest(Vector(x))[3] for x in ev)),'gapScope':'Every optical vertex sampled to actual full body; not exact full-surface signed minimum'}
    self_after,pairs_after=v29.changed_self(V,T,changed,bt);scans={side:i.aperture(bt,i.tree(*i.outer(side)),np.array(i.FITS[side]['centerM'])) for side in ('L','R')}
    root_tri=old_cache['rootTriangles'];root_faces_exact=bool(np.array_equal(V[T[root_tri]],VB[TB[root_tri]]));assert root_faces_exact
    world=p.astype('f8')@hm[:3,:3].T+hm[:3,3];world_r=r.astype('f8')*np.linalg.norm(hm[:3,:3],ord=2);hair_proof=changed_region_hair(VB,V,T,changed,bt,world,world_r,old,b.sha(k.SRC));save('b-updated-hair-contact.json',hair_proof)
    del bt;gc.collect();source_tree=i.tree(VB,TB);self_before,pairs_before=v29.changed_self(VB,TB,changed,source_tree);del source_tree;gc.collect()
    selected=np.flatnonzero(np.any(changed[T],axis=1));old_norm=np.cross(VB[T[selected,1]]-VB[T[selected,0]],VB[T[selected,2]]-VB[T[selected,0]]);new_norm=np.cross(V[T[selected,1]]-V[T[selected,0]],V[T[selected,2]]-V[T[selected,0]]);old_area=np.linalg.norm(old_norm,axis=1);new_area=np.linalg.norm(new_norm,axis=1);cosine=np.einsum('ij,ij->i',old_norm,new_norm)/np.maximum(old_area*new_area,1e-30)
    scan_before=read('aperture-topology-inspection.json')['scans'];summary={side:{'beforeCentral':scan_before[side][10],'afterCentral':scans[side][10],'centralUpperLoweringM':scan_before[side][10]['upperZ']-scans[side][10]['upperZ'],'afterUpperIrisOcclusionApproxM':.00499-scans[side][10]['upperAboveEyeCenterM'],'allScannedVisibleRunsAtMostOne':all(x.get('visibleSampleRuns',0)<=1 for x in scans[side])} for side in scans};save('b-aperture-measurement.json',{'before':scan_before,'after':scans,'summary':summary,'scope':'Actual front eye/body exterior visibility switch, BVH float precision; iris occlusion approximation uses recorded4.99mm iris radius. Not a universal biometric target.'})
    render_before=read('before-renders.json')['rows'];render_after=read('b-after-renders.json')['rows'];keys=('view','light','cameraMatrix','lens','resolution','engine','viewTransform','look','exposure','gamma','lights','world');assert len(render_before)==len(render_after)==6 and all({k:x[k] for k in keys}=={k:y[k] for k in keys} for x,y in zip(render_before,render_after));assert not bpy.data.libraries and not bpy.data.texts
    b.camera('face');s.camera.data.lens=85;s.render.filepath=str(E/'b-reopened-face.png');bpy.ops.render.render(write_still=True)
    good=all(v['bodyOpticalTrianglePairs']==0 and v['anchorBodyContainment']['classification']=='outside' for v in contacts.values()) and self_after['nonAdjacentTrianglePairs']==0 and hair_proof['status']=='PASS_UPDATED_NEUTRAL_BODY_SCOPE' and np.isfinite(V).all() and new_area.min()*.5>1e-14
    result={'status':'PASS_REOPENED_NEUTRAL_REST_SCOPE' if good else 'FAIL_CONTACT_OR_STRUCTURE','source':str(path),'sourceSha256':b.sha(path),'originalSource':str(k.SRC),'originalSourceSha256':b.sha(k.SRC),'nativeChangedVertices':native_changed.tolist(),'evaluatedChangedVertices':int(changed.sum()),'topologyAndUVExact':True,'threeSkinFieldsAndAllSourceMaterialsExact':True,'eightOpticalMeshesTransformsExact':True,'allHairPositionsRadiiTransformsMaterialsExact':True,'allHairRootTrianglesExact':root_faces_exact,'hairPrimitive':'STRIP','hairSubdivision':0,'matchedSixRenderConditionsExact':True,'contacts':contacts,'changedRegionSelfBefore':self_before,'changedRegionSelfAfter':self_after,'newNonAdjacentSelfPairs':len(pairs_after-pairs_before),'changedTriangleOrientationDiagnostic':{'minimumNormalDotCosine':float(cosine.min()),'relativeNormalReversals':int((cosine<0).sum()),'minimumAreaRatio':float((new_area/old_area).min()),'minimumChangedTriangleAreaM2':float(new_area.min()*.5),'scope':'Normal rotation versus source is a diagnostic, not alone a proof of triangle inversion.'},'apertureSummary':summary,'hairContact':hair_proof,'seconds':time.time()-start,'limits':['Neutral static rest only; no blink/gaze/continuous motion qualification','Eye wetline/lacrimal tissue, brows/lashes, full oral system and realistic scalp hair remain missing or unaccepted','Body self contact outside exact changed triangle neighborhood not newly tested','Sampled gaps/visibility/normal diagnostics are not exact complete-surface signed distances','No rig, clothing, export, LOD, engine performance or female acceptance']};save('b-saved-rest-verification.json',result);print('R35_REOPENED_DONE',json.dumps({'status':result['status'],'pairs':{n:x['bodyOpticalTrianglePairs'] for n,x in contacts.items()},'self':self_after,'aperture':summary,'hair':{'candidates':hair_proof['newDirectCompleteCapsuleChecks'],'fail':hair_proof['unqualifiedNewSegments']},'seconds':time.time()-start}),flush=True)
if __name__=='__main__':main()
