"""Independent control readback and bounded actual render-surface contacts.

First neutral and fully closed endpoints. Hard failure stops expansion to the
other quarter poses. Never infer continuous contact from these discrete states.
"""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,importlib.util,gc,sys
sp=importlib.util.spec_from_file_location('verify59build',Path(__file__).with_name('build-female-next-r0059-authored-blink.py'));k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
old=k.f.flowcheck.module('old59contact','verify-female-next-r0050-neutral-rest.py')
b=k.b;f=k.f;E=k.E;PREV=k.PREV
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def h(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def native_curves(o):
    d=o.data;P=np.empty(len(d.position_data)*3,dtype='f4');d.position_data.foreach_get('vector',P);R=np.empty(len(d.position_data),dtype='f4');d.attributes['radius'].data.foreach_get('value',R)
    return {'P':h(P),'R':h(R),'counts':[c.points_length for c in d.curves],'matrix':list(sum((list(row) for row in o.matrix_world),[])),'materials':[f.v.v32.material_signature(m) for m in d.materials]}
def mesh_data(body):
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();V=np.empty(len(me.vertices)*3,dtype='f4');me.vertices.foreach_get('co',V);V=V.reshape(-1,3).astype('f8');mx=np.array(body.matrix_world);V=V@mx[:3,:3].T+mx[:3,3];T=np.empty(len(me.loop_triangles)*3,dtype='i4');me.loop_triangles.foreach_get('vertices',T);mi=np.empty(len(me.loop_triangles),dtype='i4');me.loop_triangles.foreach_get('material_index',mi);polys=np.empty(len(me.loop_triangles),dtype='i4');me.loop_triangles.foreach_get('polygon_index',polys);ev.to_mesh_clear();return V,T.reshape(-1,3),mi,polys
def contact_pose(V,T,mi,polys,moved):
    full=old.selfcheck.tree(V,T);broad,pairs=old.selfcheck.changed_self(V,T,moved,full);bad=[]
    for i,j in sorted(pairs):
        pts=old.exact.intersections(V[T[i]],V[T[j]])
        if pts:bad.append({'triangles':[int(i),int(j)],'polygons':[int(polys[i]),int(polys[j])],'materials':[int(mi[i]),int(mi[j])],'pointsM':[p.tolist() for p in pts[:4]]})
    byRole={}
    for row in bad:
        name='/'.join(map(str,sorted(row['materials'])));byRole[name]=byRole.get(name,0)+1
    # Explicit complete skin-vs-optics and skin-vs-wetline surfaces, including
    # shared vertices refined only against their exact topological join.
    skin=np.flatnonzero((mi==4)|(mi==5));skinTree=old.selfcheck.tree(V,T[skin]);interfaces={}
    for label,roles in [('optical',(0,2,3)),('wetline',(7,))]:
        ids=np.flatnonzero(np.isin(mi,roles));tree=old.selfcheck.tree(V,T[ids]);candidates=skinTree.overlap(tree);unqualified=[];legal=0;false=0
        for ai,bi in candidates:
            ia=int(skin[ai]);ib=int(ids[bi]);points=old.exact.intersections(V[T[ia]],V[T[ib]])
            if not points:false+=1;continue
            shared=sorted(set(T[ia])&set(T[ib]));expected=V[shared] if shared else []
            if old.exact.on_expected(points,expected,tolerance=1e-6):legal+=1
            else:unqualified.append({'triangles':[ia,ib],'polygons':[int(polys[ia]),int(polys[ib])],'materials':[int(mi[ia]),int(mi[ib])],'pointsM':[p.tolist() for p in points[:4]],'sharedVertexIDs':[int(x) for x in shared]})
        interfaces[label]={'broadPairs':len(candidates),'refinedNoIntersection':false,'exactSharedTopologicalJoinOnly':legal,'unqualifiedSurfacePairs':len(unqualified),'failures':unqualified[:40]}
        del tree
    result={'actualRenderVertices':len(V),'actualRenderTriangles':len(T),'changedRegionTriangleCount':broad['affectedTriangleCount'],'changedRegionNonAdjacentBroadPairs':len(pairs),'changedRegionActualNonAdjacentSelfPairs':len(bad),'selfPairsByMaterial':byRole,'selfFailureExamples':bad[:50],'allSkinVsOcularSurfaces':interfaces,'status':'FAIL_OR_UNRESOLVED' if bad or any(x['unqualifiedSurfacePairs'] for x in interfaces.values()) else 'PASS_TESTED_SURFACE_INTERSECTION_SCOPE','scope':'Actual render-level body. All non-adjacent changed-region/body self surfaces, complete skin-vs-optics and skin-vs-wetline pairs with exact shared-source join refinement. No blanket eye-region exclusion.','notCertified':'Adjacent-triangle foldovers outside explicit interfaces, positive thickness, facial-hair finite capsules/self, whole unchanged-body self and continuous motion. No global signed minimum-distance claim.','interfaceNumericalAllowanceM':1e-6}
    del full,skinTree;gc.collect();return result
def main():
    tick=time.time();a=json.loads((E/'a-build-summary.json').read_text());source=Path(a['source']);out=Path(a['output']);history='--history-readback' in sys.argv
    if history:
        root=b.R/'sites-engine-journey/assets-source/aevrynd-character/female-next';source=root/source.name;out=root/out.name
    assert b.sha(source)==a['sourceSha256'] and b.sha(out)==a['outputSha256'];raw=np.load(E/'native-blink-pose-data.npz')
    bpy.ops.wm.open_mainfile(filepath=str(source));body=bpy.data.objects[k.BODY];baseMesh=b.mesh_signature(body.data);baseKeys={p.name:h(np.array([v.co[:] for v in p.data],dtype='f4')) for p in body.data.shape_keys.key_blocks};baseMats=[f.v.v32.material_signature(m) for m in body.data.materials];baseStage=f.v.stage();baseCurves={o.name:native_curves(o) for o in bpy.context.scene.objects if o.type=='CURVES'}
    bpy.ops.wm.open_mainfile(filepath=str(out));body=bpy.data.objects[k.BODY];ctrl=bpy.data.objects[k.CTRL];assert b.mesh_signature(body.data)==baseMesh and [f.v.v32.material_signature(m) for m in body.data.materials]==baseMats and f.v.stage()==baseStage
    for name,sig in baseKeys.items():assert h(np.array([v.co[:] for v in body.data.shape_keys.key_blocks[name].data],dtype='f4'))==sig
    assert {name:native_curves(bpy.data.objects[name]) for name in baseCurves}==baseCurves
    assert not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    images=[]
    for image in bpy.data.images:
        if image.source not in ('FILE','TILED'):continue
        p=Path(bpy.path.abspath(image.filepath));assert image.source=='FILE' and image.filepath.startswith('//') and p.exists()
        if history:assert p.resolve().is_relative_to(root.resolve())
        images.append({'relativePath':image.filepath,'sha256':b.sha(p)})
    assert len(images)==15
    action=ctrl.animation_data.action;ctrl.animation_data.action=None
    def set_controls(left,right):
        ctrl['blink_left']=left;ctrl['blink_right']=right;ctrl.update_tag();bpy.context.view_layer.update()
    rows=[]
    for name,left,right in [('neutral',0.,0.)]+[(f'both_{i:03d}',i/100,i/100) for i in (25,50,75,100)]+[('left_100',1.,0.),('right_100',0.,1.)]:
        set_controls(left,right);entry={'pose':name,'controls':[left,right]}
        for label in ('lashes','brows'):
            q=k.flat(bpy.data.objects['AFN57_NATIVE_'+label.upper()]);err=float(np.linalg.norm(q-raw[label+'_'+name],axis=1).max());assert err<1e-6;entry[label+'MaximumNativeSampleErrorM']=err
        rows.append(entry)
    drivers=[fc for obj in [body]+[bpy.data.objects['AFN59_'+x.upper()+'_NATIVE_POINT_POSES'] for x in ('lashes','brows')] for fc in obj.data.shape_keys.animation_data.drivers]
    assert all(fc.driver.is_valid and fc.driver.is_simple_expression for fc in drivers)
    save('history-functional-readback.json' if history else 'a-functional-verification.json',{'source':str(out),'sha256':b.sha(out),'reopenedWithAutoRunDisabled':True,'nativeBodyBaseTopologyUVOriginalFemaleShapeAndMaterialsExact':True,'originalNativeCurveBasePositionsRadiiCountsMaterialsMatricesExact':True,'stageExact':True,'validSimpleNativeDrivers':len(drivers),'noFrameHandlersOrLinkedLibraries':True,'relativeResourceImages':images,'independentControlReadback':rows,'function':'Actual native shape keys and GeometryNodes sample-by-point-ID following. Hidden point carriers are authoring controls, not a skeletal rig or formal component layer claim.','approximation':'Native quarter-step samples; interpolated hair-root frame between samples is not exact native rotation or a continuous-contact certificate.','seconds':time.time()-tick})
    if history:
        print('R59_HISTORY_FUNCTIONAL_REOPENED',len(drivers),len(images),time.time()-tick,flush=True);return
    # Endpoints first; if either fails, do not spend more checking other poses.
    for md in body.modifiers:
        if md.type=='SUBSURF':md.levels=md.render_levels
    set_controls(0,0);V0,T0,mi0,p0=mesh_data(body);set_controls(1,1);V1,T1,mi1,p1=mesh_data(body);moved=np.linalg.norm(V1-V0,axis=1)>1e-9
    result={'source':str(out),'sourceSha256':b.sha(out),'algorithmControls':old.exact.geometry_controls(),'status':'RUNNING','poses':{},'changedEvaluatedVertexCount':int(moved.sum())};save('a-contact-verification.json',result)
    for name,V,T,mi,p in [('neutral',V0,T0,mi0,p0),('closed',V1,T1,mi1,p1)]:
        row=contact_pose(V,T,mi,p,moved);result['poses'][name]=row;save('a-contact-verification.json',result);print('R59_ACTUAL_CONTACT',name,row['status'],row['changedRegionActualNonAdjacentSelfPairs'],{n:x['unqualifiedSurfacePairs'] for n,x in row['allSkinVsOcularSurfaces'].items()},flush=True)
    failed=any(x['status']!='PASS_TESTED_SURFACE_INTERSECTION_SCOPE' for x in result['poses'].values())
    result['status']='FAIL_ENDPOINT_CONTACT_STOP_OTHER_POSES' if failed else 'PASS_TWO_ENDPOINT_SURFACE_SCOPE_ONLY'
    result['otherQuarterPoses']='NOT_RUN_AFTER_ENDPOINT_FAILURE' if failed else 'NOT_YET_TESTED'
    result['continuousContactsFullHairSelfRigClothesRuntime']='NOT_ACCEPTED';result['seconds']=time.time()-tick;save('a-contact-verification.json',result)
    print('R59_VERIFIED',result['status'],time.time()-tick,flush=True)
if __name__=='__main__':main()
