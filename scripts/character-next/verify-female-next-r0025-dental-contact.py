"""Closed-crown surfaces and all-pair fixed-jaw sweep separation bounds."""
import bpy,importlib.util,json,math,time
from pathlib import Path
import numpy as np
from mathutils import Vector
spec=importlib.util.spec_from_file_location('build25',Path(__file__).with_name('build-female-next-r0025-dental-contact.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
ALLOWANCE=.000005
def weight(w):
    master=bpy.data.objects['AFN24_MouthControl'];master['open']=float(w);master.update_tag(refresh={'OBJECT'});bpy.context.scene.frame_set(bpy.context.scene.frame_current+1);bpy.context.view_layer.update()
def swept_support(local_points,zero_matrix,n,theta):
    q=local_points;projected=zero_matrix[:3,:3].T@n;A=q[:,1]*projected[1]+q[:,2]*projected[2];B=-q[:,2]*projected[1]+q[:,1]*projected[2];D=q[:,0]*projected[0]+zero_matrix[:3,3]@n
    maximum=np.maximum(D+A,D+A*math.cos(theta)+B*math.sin(theta));phase=np.arctan2(B,A)
    for k in (-1,0,1):
        candidate=phase+k*2*math.pi;active=(candidate>=0)&(candidate<=theta);maximum[active]=np.maximum(maximum[active],D[active]+np.sqrt(A[active]**2+B[active]**2))
    return float(maximum.max())
def main():
    report=json.loads((b.E/'a-build-verification.json').read_text(encoding='utf8'));path=Path(report['output']);assert b.sha(path)==report['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['AFN_R0005_Rig'];b.prior.solid.stage.set_pose(rig,'neutral');parts=[bpy.data.objects[row['name']] for row in report['teeth']];meta={row['name']:row for row in report['teeth']}
    weight(0.);neutral={o.name:b.prior.evaluate(o) for o in parts};quality=[]
    lower_control=bpy.data.objects['AFN24_LowerRigidControl'];lower_zero_matrix=np.array(lower_control.matrix_world,np.float64)
    for control_name in ('AFN24_UpperRigidControl','AFN24_LowerRigidControl'):
        control=bpy.data.objects[control_name];assert control.rotation_mode=='AXIS_ANGLE' and np.linalg.norm(np.array(control.rotation_axis_angle[1:])-np.array((1.,0.,0.)))<1.e-8
        drivers=list(control.animation_data.drivers);assert len(drivers)==1 and drivers[0].data_path=='rotation_axis_angle' and drivers[0].array_index==0 and drivers[0].driver.is_valid
        assert drivers[0].driver.variables[0].targets[0].id.name=='AFN24_MouthControl' and not control.animation_data.action
    assert all(not o.modifiers and o.parent.name=='AFN24_'+meta[o.name]['jaw'].title()+'RigidControl' and np.max(np.abs(np.array(o.matrix_basis)-np.eye(4)))<1.e-8 for o in parts)
    for o in parts:
        P,T,tree=b.prior.solid.data(o);p=np.array(P,np.float64);tri=p[np.array(T)];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
        edge_use={}
        for face in o.data.polygons:
            ids=list(face.vertices)
            for a,c in zip(ids,ids[1:]+ids[:1]):key=tuple(sorted((a,c)));edge_use.setdefault(key,[]).append(1 if a<c else -1)
        boundary=sum(len(v)==1 for v in edge_use.values());bad=sum(len(v)!=2 or sum(v)!=0 for v in edge_use.values());selfpairs=[(i,j) for i,j in tree.overlap(tree) if i<j and set(T[i]).isdisjoint(T[j])]
        quality.append({'name':o.name,'boundaryEdges':boundary,'nonManifoldOrInconsistentEdges':bad,'nonAdjacentSelfPairs':len(selfpairs),'minimumTriangleAreaM2':float(area.min()),'degenerateTriangles':int((area<1.e-14).sum()),'triangles':len(T)})
    rows=[];pivot=np.array(bpy.data.objects['AFN24_LowerRigidControl'].location,np.float64);prior=json.loads((b.prior.E/'b-build-verification.json').read_text(encoding='utf8'));theta=math.radians(prior['objects']['teeth']['AFN24_LowerTeeth']['angleDegrees'])
    for w in (0.,.05,.1,.15,.2):
        start=time.time();weight(w);V,T,body=b.prior.solid.data(bpy.data.objects['AFN_R0008_Body']);snapshots={o.name:b.prior.solid.data(o) for o in parts};pair_count=0;bad_pairs=[];body_count=0;body_bad=[];tissue=[];pose_error=0.
        for i,o in enumerate(parts):
            P,F,tree=snapshots[o.name];p=np.array(P,np.float64)
            if meta[o.name]['jaw']=='lower':
                a=theta*w/.2;rot=np.array(((1,0,0),(0,math.cos(a),-math.sin(a)),(0,math.sin(a),math.cos(a))));expected=(neutral[o.name]-pivot)@rot.T+pivot
            else:expected=neutral[o.name]
            pose_error=max(pose_error,float(np.linalg.norm(p-expected,axis=1).max()))
            hits=body.overlap(tree);body_count+=len(hits)
            if hits:body_bad.append({'name':o.name,'trianglePairs':len(hits),'samples':hits[:6]})
            for other in parts[i+1:]:
                pair_count+=1;hits=tree.overlap(snapshots[other.name][2])
                if hits:bad_pairs.append({'pair':[o.name,other.name],'trianglePairs':len(hits),'samples':hits[:6]})
            for name in ('AFN24_ContinuousGingivalLining','AFN24_Tongue'):
                count=len(tree.overlap(b.prior.solid.data(bpy.data.objects[name])[2]));tissue.append({'tooth':o.name,'tissue':name,'trianglePairs':count})
        rows.append({'weight':w,'allDentalObjectPairs':pair_count,'intersectingDentalPairs':bad_pairs,'toothBodyTrianglePairs':body_count,'toothBodyFailures':body_bad,'rigidEvaluatorMaximumErrorM':pose_error,'rawDentalTissueIntersections':tissue,'wallSeconds':time.time()-start})
        b.save('a-static-verification.json',{'asset':str(path),'assetSha256':b.sha(path),'status':'REVIEW_SURFACE_AND_SWEEP_RESULTS','quality':quality,'poses':rows,'scope':'All closed-crown surfaces, all 496 dental object pairs and full body in five static mouth weights. Tissue contacts reported raw, not accepted/excluded. No full mouth or runtime pass.'})
        print('R0025_STATIC',w,'DENTAL_FAILING_PAIRS',len(bad_pairs),'BODY_PAIRS',body_count,'RIGID_ERROR',pose_error,flush=True)
    bounds=[]
    for i,o in enumerate(parts):
        for p in parts[i+1:]:
            a,c=meta[o.name],meta[p.name]
            if a['jaw']==c['jaw']:
                n=np.array(c['sourceCentreM'])-np.array(a['sourceCentreM']);n/=np.linalg.norm(n);lower=float((neutral[p.name]@n).min()-(neutral[o.name]@n).max());method='Shared rigid jaw: neutral separating-plane support gap invariant under jaw/head rigid transform.'
            else:
                upper,lowerobj=(o,p) if a['jaw']=='upper' else (p,o);n=np.array(meta[upper.name]['sourceCentreM'])-np.array(meta[lowerobj.name]['sourceCentreM']);n/=np.linalg.norm(n)
                lower=float((neutral[upper.name]@n).min())-swept_support(b.prior.positions(lowerobj),lower_zero_matrix,n,theta);method='Upper static support minus lower local-vertex sinusoid maximum over the complete fixed-X hinge interval, including its saved zero-pose parent matrix; convex interpolation covers mesh triangles.'
            bounds.append({'pair':[o.name,p.name],'sameJaw':a['jaw']==c['jaw'],'supportSeparationLowerBoundM':lower-ALLOWANCE,'numericalAllowanceM':ALLOWANCE,'method':method})
    good=all(row['supportSeparationLowerBoundM']>0 for row in bounds)
    b.save('a-dental-sweep-verification.json',{'asset':str(path),'assetSha256':b.sha(path),'status':'PASS_FULL_DENTAL_PAIR_SWEEP' if good else 'FAIL_OR_UNRESOLVED_DENTAL_PAIR_SWEEP','pairs':bounds,'minimumSeparationLowerBoundM':min(row['supportSeparationLowerBoundM'] for row in bounds),'weightInterval':[0,.2],'hingeRadians':[0,theta],'pivotM':pivot.tolist(),'lowerZeroPoseMatrix':lower_zero_matrix.tolist(),'motionContract':'No tooth modifiers/basis transforms; each object parented to its declared jaw. Each jaw has one valid fixed-X angle driver from MouthControl.open, no control action.','actualDriverVsAnalyticalMaximumErrorM':max(r['rigidEvaluatorMaximumErrorM'] for r in rows),'scope':'Only all 496 repaired tooth-to-tooth pairs under the defined common rigid upper control and fixed-X lower hinge, with stated 5um numerical allowance. Original head neutral; a shared rigid head transform preserves nonintersection. Does not cover body/gingiva/tongue, facial morphs, other head deformations or runtime.'})
    good_quality=all(r['boundaryEdges']==r['nonManifoldOrInconsistentEdges']==r['nonAdjacentSelfPairs']==r['degenerateTriangles']==0 for r in quality);good_static=all(not r['intersectingDentalPairs'] and not r['toothBodyTrianglePairs'] and r['rigidEvaluatorMaximumErrorM']<5.e-7 for r in rows)
    b.save('a-verification-summary.json',{'asset':str(path),'assetSha256':b.sha(path),'closedCrownTopologyPass':good_quality,'fiveStateDentalAndBodyPass':good_static,'fullDentalPairSweepPass':good,'wholeMouthAccepted':False,'minimumSweptDentalSupportLowerBoundM':min(row['supportSeparationLowerBoundM'] for row in bounds),'limitations':['Tooth-root/gingival joins require structural acceptance; raw intersections remain.','Existing tongue/lining contacts and mouth-body lining motion remain unresolved.','No complete expression, hair dynamics/self, full body/clothing, engine or female acceptance.']})
    print('R0025_GATES',good_quality,good_static,good,'MIN_SWEEP_BOUND',min(r['supportSeparationLowerBoundM'] for r in bounds),flush=True)
if __name__=='__main__':main()
