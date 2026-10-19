"""Independent layer/lineage/actual rendered-surface endpoint verification."""
from pathlib import Path
import bpy,numpy as np,json,time,gc,importlib.util,sys
sp=importlib.util.spec_from_file_location('build60verify',Path(__file__).with_name('build-female-next-r0060-cavity-repair.py'));k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
v59=k.f.flowcheck.module('verify59for60','verify-female-next-r0059-blink.py');exact=v59.old.exact;selfcheck=v59.old.selfcheck;b=k.b;f=k.f;E=k.E
PREFIX='b' if '--variant-b' in sys.argv else 'a'
def save(n,x):
    if PREFIX=='b' and n.startswith('a-'):n='b-'+n[2:]
    (E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n',encoding='utf8')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def mesh(o,quads=False):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();P=np.empty(len(me.vertices)*3,dtype='f4');me.vertices.foreach_get('co',P);mx=np.array(o.matrix_world,dtype='f8');V=P.reshape(-1,3).astype('f8')@mx[:3,:3].T+mx[:3,3];me.calc_loop_triangles();T=np.empty(len(me.loop_triangles)*3,dtype='i4');me.loop_triangles.foreach_get('vertices',T);T=T.reshape(-1,3);mi=np.empty(len(T),dtype='i4');me.loop_triangles.foreach_get('material_index',mi);poly=np.empty(len(T),dtype='i4');me.loop_triangles.foreach_get('polygon_index',poly);fi=np.empty(len(me.polygons),dtype='i4');me.attributes['AFN60_NativeFaceID'].data.foreach_get('value',fi);result={'V':V,'T':T,'mi':mi,'nativeTriangleFace':fi[poly]}
    if quads:
        counts=np.empty(len(me.polygons),dtype='i4');me.polygons.foreach_get('loop_total',counts);assert np.all(counts==4);corners=np.empty(len(me.loops),dtype='i4');me.loops.foreach_get('vertex_index',corners);result.update(quads=V[corners.reshape(-1,4)],nativeQuadFace=fi)
    ev.to_mesh_clear();return result
def join(parts):
    V=[];T=[];mi=[];ids=[];off=0
    for row in parts:
        V.append(row['V']);T.append(row['T']+off);mi.append(row['mi']);ids.append(row['nativeTriangleFace']);off+=len(row['V'])
    return np.concatenate(V),np.concatenate(T),np.concatenate(mi),np.concatenate(ids)
def contacts(V,T,mi,sourcefi,affected):
    full=selfcheck.tree(V,T);broad,pairs=selfcheck.changed_self(V,T,affected,full);bad=[]
    for i,j in sorted(pairs):
        points=exact.intersections(V[T[i]],V[T[j]])
        if points:bad.append({'triangles':[int(i),int(j)],'sourceFaces':[int(sourcefi[i]),int(sourcefi[j])],'materials':[int(mi[i]),int(mi[j])],'pointsM':[p.tolist() for p in points[:4]]})
    groups={name:np.flatnonzero(np.isin(mi,roles)) for name,roles in [('allTissue',(4,5,7)),('skin',(4,5)),('lining',(7,)),('optics',(0,2,3))]};interfaces={}
    for label,aa,bb in [('allTissueVsOptics','allTissue','optics'),('skinVsLining','skin','lining')]:
        A=groups[aa];B=groups[bb];at=selfcheck.tree(V,T[A]);bt=selfcheck.tree(V,T[B]);candidates=at.overlap(bt);failures=[];legal=0;false=0
        for ia,ib in candidates:
            i=int(A[ia]);j=int(B[ib]);points=exact.intersections(V[T[i]],V[T[j]])
            if not points:false+=1;continue
            shared=sorted(set(T[i])&set(T[j]));expected=V[shared] if shared else []
            if exact.on_expected(points,expected,1e-6):legal+=1
            else:failures.append({'triangles':[i,j],'sourceFaces':[int(sourcefi[i]),int(sourcefi[j])],'materials':[int(mi[i]),int(mi[j])],'pointsM':[p.tolist() for p in points[:4]]})
        interfaces[label]={'broadPairs':len(candidates),'refinedNoIntersection':false,'exactSharedTopologicalJoinOnly':legal,'unqualifiedPairs':len(failures),'failures':failures[:50]};del at,bt
    counts={}
    for row in bad:
        label='/'.join(map(str,sorted(row['materials'])));counts[label]=counts.get(label,0)+1
    result={'actualVertices':len(V),'actualTriangles':len(T),'affectedTriangles':broad['affectedTriangleCount'],'nonAdjacentSelfBroadPairs':len(pairs),'actualNonAdjacentSelfPairs':len(bad),'selfPairsByMaterial':counts,'selfWitnesses':bad[:50],'completeInterfaces':interfaces,'status':'FAIL_OR_UNRESOLVED' if bad or any(x['unqualifiedPairs'] for x in interfaces.values()) else 'PASS_TESTED_ENDPOINT_SURFACE_SCOPE','scope':'All new actual tissues including replacement wet lining against original optical surfaces. Affected blink AND rebuilt cavity non-adjacent self surfaces. Skin/lining topological joins refined geometrically, not blanket-excluded.','notCertified':'Adjacent foldovers outside explicit skin/lining pairs, tissue thickness, native lash/brow finite/self, whole unchanged body self, intermediate/continuous motion and engine.','distanceDefinition':'Float64 triangle intersection witnesses establish contact/crossing locations. No exact signed global penetration-depth minimum.','joinNumericalAllowanceM':1e-6};del full;gc.collect();return result
def main():
    tick=time.time();a=read(E/(PREFIX+'-build-summary.json'));source=Path(a['source']);out=Path(a['output']);assert b.sha(source)==a['sourceSha256'] and b.sha(out)==a['outputSha256'];rawnp=np.load(E/'native-component-lineage.npz');raw={name:rawnp[name] for name in rawnp.files};corr=np.load(E/'a-native-cavity-corrections.npz');partsNames=[a['visibleComponents'][str(i)] for i in range(5)]
    bpy.ops.wm.open_mainfile(filepath=str(source));old=bpy.data.objects[k.k.BODY];originalSig=b.mesh_signature(old.data);stage=f.v.stage();originalCurves={o.name:v59.native_curves(o) for o in bpy.context.scene.objects if o.type=='CURVES'}
    bpy.ops.wm.open_mainfile(filepath=str(out));old=bpy.data.objects['AFN60_ORIGINAL_SOURCE_CAGE'];assert old.hide_render and b.mesh_signature(old.data)==originalSig and f.v.stage()==stage;assert {name:v59.native_curves(bpy.data.objects[name]) for name in originalCurves}==originalCurves
    facesCovered=[];verticesCovered=[];lineage=[];caps=set()
    for row in a['nativeInteriorCorrections'].values():caps.update(row['originalPatchFaces'])
    for ci,name in enumerate(partsNames):
        o=bpy.data.objects[name];d=o.data;ids=np.array([p.value for p in d.attributes['AFN60_NativeVertexID'].data],dtype='i4');fi=np.array([p.value for p in d.attributes['AFN60_NativeFaceID'].data],dtype='i4');P=np.array([p.co[:] for p in d.vertices],dtype='f4');assert np.array_equal(P,raw['positions'][ids]);assert np.array_equal(np.array(o.matrix_world),raw['matrix']);assert [f.v.v32.material_signature(m) for m in d.materials]==[f.v.v32.material_signature(m) for m in old.data.materials]
        for keyname in ('AFN57_Supplied_Female_Morph','AFN59_Blink_Left','AFN59_Blink_Right'):
            expected=raw[keyname].astype('f8').copy()
            if ci==4 and keyname.startswith('AFN59_Blink_'):expected+=corr[keyname.rsplit('_',1)[1]]-corr['Neutral']
            assert np.array_equal(np.array([p.co[:] for p in d.shape_keys.key_blocks[keyname].data],dtype='f4'),expected[ids].astype('f4'))
        if ci==4 and PREFIX=='b':
            extra=np.load(E/'b-limit-surface-correction.npz');assert np.array_equal(ids,extra['nativeVertexIDs']);assert np.array_equal(np.array([p.co[:] for p in d.shape_keys.key_blocks['AFN60_Cavity_Repair'].data],dtype='f4'),extra['finalRepairKey'])
        facesCovered.extend(fi.tolist());verticesCovered.extend(ids.tolist());lineage.append({'object':name,'sourceComponent':ci,'nativeVertices':len(ids),'nativeFaces':len(fi),'originalIDLineageAndMorphsExact':True})
    assert sorted(facesCovered)==list(range(len(raw['polygonCounts']))) and sorted(verticesCovered)==list(range(len(raw['positions'])))
    assert not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    images=[]
    for image in bpy.data.images:
        if image.source not in ('FILE','TILED'):continue
        p=Path(bpy.path.abspath(image.filepath));assert image.source=='FILE' and image.filepath.startswith('//') and p.exists();images.append({'path':image.filepath,'sha256':b.sha(p)})
    assert len(images)==15
    # Establish actual partition invariance on all original optical quad corners.
    # The original cage is enabled only in this read-only verifier, never rendered.
    old.hide_set(False);originalID=old.data.attributes.new('AFN60_NativeFaceID','INT','FACE');originalID.data.foreach_set('value',np.arange(len(old.data.polygons),dtype='i4'))
    for o in [old]+[bpy.data.objects[name] for name in partsNames]:
        for md in o.modifiers:
            if md.type=='SUBSURF':md.levels=md.render_levels
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();original=mesh(old,True);derived=[];comparison=[]
    for ci,name in enumerate(partsNames):
        row=mesh(bpy.data.objects[name],True);derived.append(row);ids=row['nativeQuadFace'];wanted=np.unique(ids);idx=np.flatnonzero(np.isin(original['nativeQuadFace'],wanted));originalOrder=idx[np.argsort(original['nativeQuadFace'][idx],kind='stable')];candidateOrder=np.argsort(ids,kind='stable');assert len(originalOrder)==len(candidateOrder)
        err=np.linalg.norm(row['quads'][candidateOrder]-original['quads'][originalOrder],axis=2);info={'object':name,'maximumActualQuadCornerChangeM':float(err.max())}
        if ci<4:assert err.max()<1e-6;info['opticalPartitionPreservesActualSurface']=True
        else:
            outer=~np.isin(ids[candidateOrder],list(caps));info['maximumOutsideNativeSocketPatchChangeM']=float(err[outer].max());info['deletedGhostNativeFaces']=int(584);assert len(row['T'])==2*16*(35630-584)
        comparison.append(info)
    V0,T0,mi0,f0=join(derived);assert len(T0)==1178816
    bpy.context.scene.frame_set(21);bpy.context.view_layer.update();closedParts=[mesh(bpy.data.objects[name],True) for name in partsNames];V1,T1,mi1,f1=join(closedParts);assert V1.shape==V0.shape and len(T1)==len(T0)
    originalClosed=mesh(old,True);closedComparison=[]
    for ci,row in enumerate(closedParts):
        ids=row['nativeQuadFace'];wanted=np.unique(ids);idx=np.flatnonzero(np.isin(originalClosed['nativeQuadFace'],wanted));originalOrder=idx[np.argsort(originalClosed['nativeQuadFace'][idx],kind='stable')];candidateOrder=np.argsort(ids,kind='stable');err=np.linalg.norm(row['quads'][candidateOrder]-originalClosed['quads'][originalOrder],axis=2);entry={'object':partsNames[ci],'maximumActualQuadCornerChangeM':float(err.max())}
        if ci<4:assert err.max()<1e-6
        else:entry['maximumOutsideNativeSocketPatchChangeM']=float(err[~np.isin(ids[candidateOrder],list(caps))].max())
        closedComparison.append(entry)
    moved=np.linalg.norm(V1-V0,axis=1)>1e-9
    for T,fi in ((T0,f0),(T1,f1)):moved[np.unique(T[np.isin(fi,list(caps))])]=True
    save('a-functional-lineage-verification.json',{'source':str(out),'sourceSha256':b.sha(out),'reopened':True,'layers':lineage,'originalNativeFacesAndVerticesCoveredExactlyOnce':True,'originalSourceCageRetainedUnmodified':True,'oldCurveBaseGeometryRadiiMaterialsMatricesExact':True,'originalMaterialsAndStageExact':True,'actualPartitionSurfaceComparison':comparison,'actualClosedPartitionSurfaceComparison':closedComparison,'closedControls':[bpy.data.objects[k.k.CTRL]['blink_left'],bpy.data.objects[k.k.CTRL]['blink_right']],'relativeImages':images,'actualRenderedNativeGhostFaceRemoval':584,'actualRenderTriangles':len(T0),'limitations':'Outer shells remain combined sclera/cornea; iris/pupil one connected surface. Body/oral/lining combined. Not full layer, follicle, blink/rig/runtime acceptance. Native fixed rim can move after subdivision; measured above.','seconds':time.time()-tick})
    result={'source':str(out),'sourceSha256':b.sha(out),'status':'RUNNING','algorithmControls':exact.geometry_controls(),'poses':{}};save('a-contact-verification.json',result)
    for label,V,T,mi,fi in [('neutral',V0,T0,mi0,f0),('closed',V1,T1,mi1,f1)]:
        row=contacts(V,T,mi,fi,moved);result['poses'][label]=row;save('a-contact-verification.json',result);print('R60_SURFACE_CONTACT',label,row['actualNonAdjacentSelfPairs'],{n:x['unqualifiedPairs'] for n,x in row['completeInterfaces'].items()},flush=True)
    result['status']='FAIL_ENDPOINT_INTERFACES_STOP_EXPANSION' if any(r['status']!='PASS_TESTED_ENDPOINT_SURFACE_SCOPE' for r in result['poses'].values()) else 'PASS_TWO_ENDPOINT_SURFACE_SCOPE_ONLY';result['facialHairAndContinuousMotion']='NOT_ACCEPTED';result['seconds']=time.time()-tick;save('a-contact-verification.json',result);print('R60_ASSEMBLY_VERIFIED',result['status'],time.time()-tick,flush=True)
if __name__=='__main__':main()
