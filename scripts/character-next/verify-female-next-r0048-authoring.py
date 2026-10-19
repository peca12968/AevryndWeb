"""Read actual rejected pilots; retain only explicit anatomical authoring.

The complete character appearance is restored unchanged. No dense groom or
appearance promotion, no claim that all child paths are valid.
"""
import bpy,importlib.util,numpy as np,json,time,sys
from pathlib import Path
from mathutils import Vector
sp=importlib.util.spec_from_file_location('auth48',Path(__file__).with_name('build-female-next-r0048-anatomical-groom.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
E=a.E;S=a.S;b=a.b;f=a.f;v=a.v;RETAIN=S/'aevrynd-female-next-r0048-anatomical-authoring-retained.blend'
def main():
    start=time.time();bpy.ops.wm.open_mainfile(filepath=str(a.SRC));before=f.state();V,T=b.evaluated(bpy.data.objects[b.BODY],True);tri=V[T];tree=a.i.i.tree(V,T);rows=[]
    for tag,path,folder in [('A',a.PILOT,E),('C',S/'aevrynd-female-next-r0048-c-control-spline-pilot.blend',E/'c-control-spline')]:
        summary=json.loads((folder/'pilot-summary.json').read_text());assert b.sha(path)==summary['sha256'];bpy.ops.wm.open_mainfile(filepath=str(path));state=f.state();assert all(state['meshes'][n]==r for n,r in before['meshes'].items());assert all(state['materials'][n]==r for n,r in before['materials'].items());assert state['skinFields']==before['skinFields']and state['stage']==before['stage']and state['curves']==before['curves']
        o=bpy.data.objects['AFN48_REPRESENTATIVE_ACTUAL_FIBRES'];P=np.array([[p.co[:3]for p in s.points]for s in o.data.splines]);mx=np.array(o.matrix_world);P=P@mx[:3,:3].T+mx[:3,3];r=np.array([[p.radius*o.data.bevel_depth for p in s.points]for s in o.data.splines]);cache=np.load(folder/'pilot-paths.npz');err=float(np.max(abs(P-cache['positions'])));assert err<2e-7 and np.max(abs(r-cache['radii']))<1e-10
        audit=a.g.check(P,r,tree,tri);assert audit['status']=='FAIL_OR_UNRESOLVED';assert all(x['curve']>=29 for x in audit['failureSamples']);rows.append({'tag':tag,'source':str(path),'sha256':b.sha(path),'bytes':path.stat().st_size,'reopened':True,'originalBodySkinOpticsGroomStageExact':True,'pilotCurves':len(P),'nativePointsPerCurve':a.N,'savedReadbackMaxErrorM':err,'actualSavedBodyContact':audit,'source29PrimaryGuidesHaveNoBodyCrossings':True,'fullCandidateGenerated':False})
    # Validate and retain original primary guides only, never failed followers.
    primary=P[:29];primaryR=r[:29];primaryContact=a.g.check(primary,primaryR,tree,tri);assert primaryContact['status']=='PASS_TESTED_STATIC_CAPSULES';other={}
    for name in before['meshes']:
        if name==b.BODY:continue
        vv,tt=b.evaluated(bpy.data.objects[name],True);ot=a.i.i.tree(vv,tt);other[name]=a.g.check(primary,primaryR,ot,vv[tt],roots=False);assert other[name]['status']=='PASS_TESTED_STATIC_CAPSULES',name
    domain=bpy.data.objects['AFN48_ANATOMICAL_SCALP_DOMAIN'];ids=np.array([x.value for x in domain.data.attributes['AFN48_BodyTriangle'].data],dtype='i4');verts=np.array([v.co[:]for v in domain.data.vertices]);faces=np.array([p.vertices[:]for p in domain.data.polygons],dtype='i4');assert np.max(abs(verts[faces]-V[T[ids]]))<2e-7
    Q=V[T[ids]].mean(1);az,el=a.angular(Q);lo=np.interp(az,a.BOUNDARY[:,0],a.BOUNDARY[:,1]);area=np.linalg.norm(np.cross(V[T[ids,1]]-V[T[ids,0]],V[T[ids,2]]-V[T[ids,0]]),axis=1)*.5;roots,normal,tid,bc=a.follicles(V,T,ids,area,lo,el);lineage=json.loads((E/'c-control-spline/pilot-lineage.json').read_text());pilotids=lineage['rootIds'];rooterr=float(np.max(abs(P[29:,0]-roots[pilotids])));assert rooterr<2e-7;states={}
    for j,R0 in enumerate(roots):
        state=a.g.cap.solid.classify(tree,tri,Vector(R0));states[state]=states.get(state,0)+1
        if j%6000==0:print('R48_ROOT_ANCHORS',j,a.COUNT,states,flush=True)
    assert states=={'outside':a.COUNT},states;np.savez_compressed(E/'anatomical-root-bindings.npz',triangleIds=tid,barycentric=bc.astype('f4'),normal=normal.astype('f4'),rootPositions=roots.astype('f4'))
    controls=json.loads((E/'primary-guides.json').read_text())['guides'];nativeControls=[]
    for row in controls:
        o=bpy.data.objects['AFN48_CTRL_'+row['name']];sp=o.data.splines[0];K=np.array([p.co[:]for p in sp.bezier_points]);L=np.array([p.handle_left[:]for p in sp.bezier_points]);H=np.array([p.handle_right[:]for p in sp.bezier_points]);assert len(o.data.splines)==1 and sp.type=='BEZIER'and np.isfinite(K).all();assert np.max(abs(K-np.array(row['knotsM'])))<2e-7;nativeControls.append({'object':o.name,'knotsM':K.tolist(),'handleLeftM':L.tolist(),'handleRightM':H.tolist(),'rootBodyTriangle':row['bodyTriangle'],'rootBarycentric':row['barycentric']})
    # Export actual saved native controls, not a claim of live child deformation.
    a.save('native-control-export.json',{'source':str(S/'aevrynd-female-next-r0048-c-control-spline-pilot.blend'),'controls':nativeControls,'scope':'Actual native editable full-path Bezier controls and static body-root lineage. Failed interpolation solvers not qualified. No claim of live groom,simulation or engine rig.'})
    failed=bpy.data.objects['AFN48_REPRESENTATIVE_ACTUAL_FIBRES'];bpy.data.objects.remove(failed,do_unlink=True);old=bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'];old.hide_render=False;old.hide_set(False);collection=bpy.data.collections.new('AFN48_AUTHORING_SCALP_AND_PRIMARY_GUIDES');bpy.context.scene.collection.children.link(collection)
    for o in list(bpy.context.scene.objects):
        if o.name.startswith('AFN48_'):
            for col in list(o.users_collection):col.objects.unlink(o)
            collection.objects.link(o);o.hide_render=True;o.hide_set(True)
    state=f.state();assert state==before;bpy.context.scene['AFN48_status']='RETAIN_ANATOMICAL_AUTHORING_ONLY_NO_APPEARANCE_OR_GROOM_PROMOTION';b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(RETAIN),compress=True)
    a.save('authoring-reopen-verification.json',{'status':'PASS_EXACT_STATIC_AUTHORING_DATA_NOT_HAIRSTYLE_ACCEPTANCE','rejectedPilots':rows,'retainedSource':str(RETAIN),'retainedSourceSha256':b.sha(RETAIN),'retainedSourceBytes':RETAIN.stat().st_size,'retainedCompleteAppearanceEqualsWorkingR42B':True,'exactOriginalSkinTriangleDomain':{'triangles':len(ids),'actualBodyTriMapping':True,'notCollisionProxy':True},'all24000RootBindings':{'states':states,'outsideCurrentWholeBody':True,'representativeRootReadbackMaxErrorM':rooterr,'scope':'Static root points only, not any24kchild path or hair-self/continuous contact certificate'},'primary29ActualPolyBodyContact':primaryContact,'primary29OtherOriginalMeshes':other,'actualNativeBezierControlsExported':len(nativeControls),'unqualified':['Dense hair interpolation','Continuous Bezier control-curve contact between sampled POLY points','Hair self contact','Dynamic deforming-scalp binding','Hair physics','Runtime/LOD/CPU/GPU/memory','Appearance acceptance'],'seconds':time.time()-start});f.E=E;f.render('retained-authoring',('face',));a.i.ch.review.extras('retained-authoring',E)
    # Region-only diagnostic. The separately rendered mesh is visualized with
    # 0.3mm normal stand-off to avoid coplanar flicker; never saved/adopted as skin.
    old.hide_render=True;domain.hide_render=False;domain.hide_set(False);domain.data.materials.clear();mat=bpy.data.materials.new('AFN48_DIAGNOSTIC_DOMAIN_CYAN');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.015,.35,.45,1);bs.inputs['Roughness'].default_value=.8;domain.data.materials.append(mat)
    for vert in domain.data.vertices:vert.co+=vert.normal*.0003
    f.render('domain-diagnostic',('face','oblique','profile'));print('R48_VERIFIED_AUTHORING',states,len(nativeControls),time.time()-start,flush=True)
def retained_only():
    bpy.ops.wm.open_mainfile(filepath=str(a.SRC));before=f.state();bpy.ops.wm.open_mainfile(filepath=str(RETAIN));assert f.state()==before;assert bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'].hide_render is False;assert 'AFN48_REPRESENTATIVE_ACTUAL_FIBRES'not in bpy.data.objects
    export=json.loads((E/'native-control-export.json').read_text());assert len(export['controls'])==29
    for row in export['controls']:
        o=bpy.data.objects[row['object']];sp=o.data.splines[0];assert o.hide_render;assert np.array_equal(np.array([p.co[:]for p in sp.bezier_points]),np.array(row['knotsM']));assert np.array_equal(np.array([p.handle_left[:]for p in sp.bezier_points]),np.array(row['handleLeftM']));assert np.array_equal(np.array([p.handle_right[:]for p in sp.bezier_points]),np.array(row['handleRightM']))
    domain=bpy.data.objects['AFN48_ANATOMICAL_SCALP_DOMAIN'];assert domain.hide_render and len(domain.data.polygons)==30142;a.save('retained-source-final-readback.json',{'status':'PASS_REOPENED_RETAINED_SOURCE_APPEARANCE_EXACT','source':str(RETAIN),'sha256':b.sha(RETAIN),'originalVisibleDataAndStageExact':True,'originalHairVisible':True,'rejectedFollowersRemoved':True,'nativeBezierControlsExact':29,'actualBodyDomainFaces':len(domain.data.polygons),'coverageWarning':'Initial artist-designated region only. Actual diagnostic views show sideburn/temple and low nape coverage still incomplete; do not claim the anatomical hairline is finished or use this mask as an accepted follicle distribution.'});print('R48_RETAINED_REOPEN_PASS',flush=True)
if __name__=='__main__':
    if '--retained-only'in sys.argv:retained_only()
    else:main()
