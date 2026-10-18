"""A globally routed groom on a conservative expanded convex head envelope.

The r0012 CC0-derived guides supply only scalp anchors and style directions.
No nearest-body point pushing is used to route the free lengths.
"""
import bpy,bmesh,json,math,hashlib,importlib.util,time,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(r'D:\Download\Aevrynd'); S=R/'engine/assets/characters/female-next/source'
E=R/'Evidence/character-female-next/r0013-envelope-hair'; E.mkdir(parents=True,exist_ok=True)
SRC=S/'aevrynd-female-next-r0011-b-ridge-skin-brows-study.blend'
STYLE=S/'aevrynd-female-next-r0012-b-hair-data.npz'
spec=importlib.util.spec_from_file_location('capsule',Path(__file__).with_name('verify-female-next-r0012-hair-segments.py'))
capsule=importlib.util.module_from_spec(spec);spec.loader.exec_module(capsule); solid=capsule.solid
solid.stage.eyes.E=E
C=np.array((0.,-.036,1.475)); ENVELOPE_MARGIN=.002; EXTRA_RADIAL=.001

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def envelope(V):
    # Include all vertices above this plane; lower triangles cannot touch paths
    # constrained above 1.34 m, even with the maximum 60 micrometre radius.
    P=V[V[:,2]>1.30]; bm=bmesh.new()
    for p in P:bm.verts.new(p)
    result=bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
    hull_faces=[f for f in result['geom'] if isinstance(f,bmesh.types.BMFace)]
    bm.normal_update(); normals=[]; offsets=[]; faces=[]; positions=[]
    used=list({v for f in hull_faces for v in f.verts}); indices={v:i for i,v in enumerate(used)}
    positions=[list(v.co) for v in used]
    for f in hull_faces:
        n=np.array(f.normal,dtype=np.float64); h=float(n@(np.array(f.verts[0].co)-C))
        if h<0:n=-n;h=-h
        normals.append(n);offsets.append(h);faces.append([indices[v] for v in f.verts])
    bm.free(); A=np.array(normals);b=np.array(offsets)
    raw_violation=max(float((A@p-b).max()) for p in P-C)
    # Face normals from BMesh are float32. Use actual float64 support values,
    # rather than trusting face orientation/offset rounding, for halfspaces.
    # Additional axis normals guarantee a bounded outer polytope.
    A=np.vstack((A,np.eye(3),-np.eye(3)))
    b=np.concatenate([np.max((P-C)@chunk.T,axis=0) for chunk in np.array_split(A,max(1,math.ceil(len(A)/128)))])
    # A convex combination of included vertices is also contained. This proves
    # containment of every original triangle whose three vertices were included.
    violation=max(float((A@p-b).max()) for p in P-C)
    assert violation<2e-6,violation
    m=bpy.data.meshes.new('AFN13_CONSERVATIVE_HEAD_HULL');m.from_pydata(positions,[],faces);m.update()
    o=bpy.data.objects.new(m.name,m);bpy.context.scene.collection.objects.link(o);o.hide_render=True;o.hide_viewport=True
    o['aevrynd_layer']='COLLISION_PROXY';o['offsetPlaneMarginM']=ENVELOPE_MARGIN
    return A,b,{'bodyVerticesIncluded':len(P),'hullVertices':len(positions),'hullFaces':len(faces),'rawFacePlaneViolationM':raw_violation,'bodyVertexMaximumPlaneViolationM':violation,'supportOffsetsRecomputedFloat64':True,'includedAboveZ':1.30,'pathMinimumAllowedZ':1.34,'offsetPlaneMarginM':ENVELOPE_MARGIN,'extraRadialM':EXTRA_RADIAL,'proof':'Support halfspaces contain all selected body vertices and their fully selected triangles. Expanded halfspaces contain their Minkowski sum with a 2 mm ball. Final complete capsules are separately checked against actual body.'}

def shell(p,A,b,margin=ENVELOPE_MARGIN,extra=EXTRA_RADIAL):
    delta=p-C
    if p[2]<C[2]:
        # Below the cranial centre follow horizontal cross-sections. A 3D ray
        # here would incorrectly stretch the bob down to the proxy neck base.
        length=float(np.linalg.norm(delta[:2]));u=np.array((delta[0]/length,delta[1]/length,0.));dot=A@u
        residual=b+margin-A[:,2]*delta[2]
        assert residual.min()>-2e-6,'Cross-section centre not contained'
        t=float(np.min(residual[dot>1e-10]/dot[dot>1e-10]))+extra
        q=p.copy();q[:2]=C[:2]+u[:2]*max(t,length);return q
    length=float(np.linalg.norm(delta));u=delta/max(length,1e-12);dot=A@u
    t=float(np.min((b[dot>1e-10]+margin)/dot[dot>1e-10]))+extra
    return C+u*max(t,length)

def shell_batch(P,A,b,margins,extras):
    """Vectorized equivalent of shell; reduces Python/BLAS dispatch overhead."""
    P=np.asarray(P,dtype=np.float64);delta=P-C;low=P[:,2]<C[2]
    length=np.linalg.norm(delta,axis=1);length[low]=np.linalg.norm(delta[low,:2],axis=1)
    u=delta/length[:,None];u[low,2]=0
    dot=u@A.T;residual=b[None,:]+np.asarray(margins)[:,None]-np.where(low,delta[:,2],0)[:,None]*A[None,:,2]
    assert np.min(residual[low])>-2e-6 if low.any() else True
    ratio=np.full_like(dot,np.inf);np.divide(residual,dot,out=ratio,where=dot>1e-10)
    t=np.min(ratio,axis=1)+np.asarray(extras);out=C+u*np.maximum(t,length)[:,None];out[low,2]=P[low,2]
    return out

def check_paths(paths,radii,tree,tri):
    failures=[];methods={};minimum=float('inf');segments=0;inside=0;cvmin=float('inf');fallbacks=[];bad_roots=[]
    for ci,(P,rr) in enumerate(zip(paths,radii)):
        ds=[tree.find_nearest(Vector(p))[3] for p in P]
        state=solid.classify(tree,tri,Vector(P[0]))
        if state=='unresolved' and ds[0]>.000001:
            winding=solid.winding(tri,P[0])
            state='outside' if abs(winding)<1e-6 else ('inside' if abs(abs(winding)-1)<1e-6 else 'unresolved')
            fallbacks.append({'curve':ci,'root':P[0].tolist(),'winding':winding,'resolved':state})
        inside+=state!='outside'
        if state!='outside':bad_roots.append({'curve':ci,'state':state,'root':P[0].tolist()})
        cvmin=min(cvmin,float(np.min(np.array(ds)-rr)))
        for j in range(len(P)-1):
            gap,method=capsule.segment_test(P[j],P[j+1],ds[j],ds[j+1],float(max(rr[j],rr[j+1])),tree,tri)
            segments+=1;minimum=min(minimum,gap);methods[method]=methods.get(method,0)+1
            if gap<=0:failures.append({'curve':ci,'segment':j,'method':method,'gapLowerBoundM':gap,'a':P[j].tolist(),'b':P[j+1].tolist()})
    return {'status':'PASS_TESTED_BODY_CAPSULES' if not failures and not inside else 'FAIL_OR_UNRESOLVED','curves':len(paths),'segments':segments,'unqualifiedSegments':len(failures),'rootContainmentFailures':inside,'rootFailureSamples':bad_roots[:100],'float64WindingFallbacks':fallbacks,'minimumCapsuleClearanceLowerBoundM':minimum,'minimumSampledCVGapM':cvmin,'methods':methods,'failureSamples':failures[:100],'scope':'Actual body against complete piecewise-linear capsules with maximum endpoint radius and 1 um numerical allowance. Static pose being tested only; not self collision, other components or motion.'}

def parent_head(o,rig):
    o.parent=rig;o.parent_type='BONE';o.parent_bone='head';o.matrix_basis=Matrix.Identity(4);o.matrix_parent_inverse=Matrix.Identity(4);bpy.context.view_layer.update();o.matrix_parent_inverse=o.matrix_world.inverted();bpy.context.view_layer.update()
    assert np.max(np.abs(np.array(o.matrix_world)-np.eye(4)))<1e-5

def legacy_guides(paths,rig):
    d=bpy.data.curves.new('AFN13_GUIDES','CURVE');d.dimensions='3D';d.bevel_depth=.00006;d.bevel_resolution=0;d.use_fill_caps=True
    for P in paths:
        p=d.splines.new('POLY');p.points.add(len(P)-1);p.points.foreach_set('co',np.column_stack((P,np.ones(len(P)))).astype(np.float32).ravel())
    o=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(o);parent_head(o,rig);o.hide_render=True;o['aevrynd_layer']='EDITABLE_GUIDES'
    return o

def main():
    start=time.time();capsule.math_controls();soft='--soft-roots' in sys.argv;label='b' if soft else 'a'
    contract={'source':str(SRC),'sourceSha256':sha(SRC),'previousGoalTurn':'progress: requested v3 prompt redesign saved and pushed; no model improvement claimed','primaryDefect':'Ear and side-head crossings persist between otherwise outside guide/CV samples; sparse artificial groom silhouette.','hypothesis':'Route free lengths on a conservative global outer envelope, with verified real-skin attachment corridors, to remove ear pockets before child interpolation.','expectedVisibleChange':'Continuous outward fall around ears and neck without local kinks; preserve part and bob silhouette. Material change is a separate diagnostic.','smallestExperiment':'252 complete guide capsule paths before any child hair is generated.','rejectIf':'Any unresolved guide/body capsule, root containment, extreme silhouette inflation or lost scalp attachment.','costLimit':{'threads':8,'guideCount':252,'initialPointsPerGuide':66,'childMaximum':24000,'renderSamples':32,'renderViewsMaximum':4},'reference':'CC0 MakeHuman Hair Editor raw guide data already archived in r0012; geometry routing and all code here authored for Aevrynd.'}
    if soft:contract.update({'hypothesis':'Exclude the ear/side-head root band and replace perpendicular root poles with a smooth envelope offset ramp along the guide flow.','reasonForSecondCandidate':'Saved A has one ear attachment crossing and visible brush-like root poles. B changes root domain and attachment path, not density.'})
    (E/(label+'-iteration-contract.json')).write_text(json.dumps(contract,indent=2)+'\n')
    bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');body=bpy.data.objects['AFN_R0008_Body'];body.data.calc_loop_triangles()
    V,T,tree=solid.data(body);V=np.array(V,dtype=np.float64);tri=V[np.array(T,dtype=np.int32)];A,b,info=envelope(V)
    G=np.load(STYLE)['guides'].astype(np.float64);bindings=json.loads((R/'Evidence/character-female-next/r0012-layered-hair/b-volume-guide-transfer.json').read_text())['bindings'];paths=[];excluded=[]
    for gi,g in enumerate(G):
        root=g[0];n=np.array(bindings[gi]['normal']);n/=np.linalg.norm(n)
        if soft and root[2]<1.485 and root[1]<-.012:excluded.append(gi);continue
        # Fixed attachment corridor leaves the actual skin before joining the
        # globally routed exterior. No local nearest-surface projection loop.
        samples=np.column_stack([np.interp(np.linspace(0,31,64),np.arange(32),g[:,axis]) for axis in range(3)])
        if soft:
            ramp=np.clip(np.linspace(0,1,64)/.15,0,1);ramp=ramp*ramp*(3-2*ramp)
            paths.append(np.vstack((root,[shell(p,A,b,.00015+.00185*ramp[j],.00005+.00095*ramp[j]) for j,p in enumerate(samples) if j>0])))
        else:paths.append(np.vstack((root,root+n*.001,[shell(p,A,b) for p in samples])))
    assert min(p[:,2].min() for p in paths)>1.34
    radii=[np.full(len(p),.00006) for p in paths];audit=check_paths(paths,radii,tree,tri)
    print('AFN13_GUIDE_AUDIT='+json.dumps({k:v for k,v in audit.items() if k!='failureSamples'}),flush=True)
    legacy_guides(paths,rig)
    offsets=np.cumsum([0]+[len(p) for p in paths]);np.savez_compressed(S/f'aevrynd-female-next-r0013-{label}-envelope-guides.npz',positions=np.concatenate(paths).astype(np.float32),offsets=offsets,planeNormals=A,planeOffsets=b)
    bpy.context.scene['aevrynd_revision']=f'female-next-r0013-{label}-envelope-guides';bpy.context.scene['aevrynd_release_state']='GUIDE_DIAGNOSTIC_NOT_PROMOTED'
    bpy.context.preferences.filepaths.save_version=0;dest=S/f'aevrynd-female-next-r0013-{label}-envelope-guides.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    result={'source':str(SRC),'sourceSha256':sha(SRC),'output':str(dest),'outputSha256':sha(dest),'styleInputSha256':sha(STYLE),'envelope':info,'guideBodyCheck':audit,'excludedReferenceRootIds':excluded,'rootDomain':'For B, roots below z 1.485 m require y >= -0.012 m behind the ear band. This is an authored scalp boundary, not an anatomical universal. A uses the complete transferred source domain.','rootBindingsSource':'r0012/b-volume-guide-transfer.json, exact unchanged r0011 body','wallSeconds':time.time()-start,'nextStageAllowed':audit['status']=='PASS_TESTED_BODY_CAPSULES','overallScore':None,'runtimePromotion':False}
    (E/(('b-' if soft else '')+'guide-envelope-verification.json')).write_text(json.dumps(result,indent=2)+'\n')
    print('AFN13_GUIDES_DONE',flush=True)

if __name__=='__main__':main()
