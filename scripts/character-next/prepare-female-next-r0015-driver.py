"""Extract and validate a Blender-independent single-head-yaw skinning fixture."""
import bpy,bmesh,json,math,importlib.util,time
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('flow',Path(__file__).with_name('build-female-next-r0014-scalp-flow.py'));flow=importlib.util.module_from_spec(spec);spec.loader.exec_module(flow)
R,S=flow.R,flow.S;E=R/'Evidence/character-female-next/r0015-guide-dynamics';E.mkdir(parents=True,exist_ok=True);SRC=S/'aevrynd-female-next-r0014-c-review.blend'

def rotate(V,axis,pivot,angle,weights,mode):
    x=V-pivot
    if mode=='DQS':
        theta=2*np.arctan2(weights*math.sin(angle*.5),1-weights+weights*math.cos(angle*.5));c=np.cos(theta)[:,None];s=np.sin(theta)[:,None];return pivot+x*c+np.cross(axis,x)*s+(x@axis)[:,None]*axis*(1-c)
    c=math.cos(angle);s=math.sin(angle);out=x*c+np.cross(axis,x)*s+(x@axis)[:,None]*axis*(1-c)
    return V+weights[:,None]*(out-x)

def evaluated_vertices(body):
    ob=body.evaluated_get(bpy.context.evaluated_depsgraph_get());v=np.empty(len(ob.data.vertices)*3,dtype=np.float32);ob.data.vertices.foreach_get('co',v);M=np.array(ob.matrix_world,dtype=np.float64);return v.reshape(-1,3).astype(np.float64)@M[:3,:3].T+M[:3,3]

def main():
    start=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig'];flow.solid.stage.set_pose(rig,'neutral');body=bpy.data.objects['AFN_R0008_Body'];mods=[m for m in body.modifiers if m.type=='ARMATURE'];assert len(mods)==1
    others=[b.name for b in rig.pose.bones if np.max(np.abs(np.array(b.matrix_basis)-np.eye(4)))>1e-5];assert not others,others
    head=rig.matrix_world@rig.pose.bones['head'].matrix;axis=np.array(head.col[1][:3]);axis/=np.linalg.norm(axis);pivot=np.array(head.translation);V=evaluated_vertices(body);body.data.calc_loop_triangles();T=np.array([t.vertices for t in body.data.loop_triangles],dtype=np.int32)
    descendants={'head'};changed=True
    while changed:
        old=len(descendants);descendants.update(b.name for b in rig.data.bones if b.parent and b.parent.name in descendants);changed=len(descendants)>old
    W=[];sums=[]
    for v in body.data.vertices:
        groups=[(body.vertex_groups[g.group].name,g.weight) for g in v.groups if body.vertex_groups[g.group].name in rig.data.bones and rig.data.bones[body.vertex_groups[g.group].name].use_deform];total=sum(w for _,w in groups);sums.append(total);W.append(sum(w for name,w in groups if name in descendants)/total if total else 0.)
    W=np.array(W);mode='DQS' if mods[0].use_deform_preserve_volume else 'LBS';checks=[]
    for degree in (-25,-12,12,25):
        rig.pose.bones['head'].rotation_euler[1]=math.radians(degree);bpy.context.view_layer.update();actual=evaluated_vertices(body);pred=rotate(V,axis,pivot,math.radians(degree),W,mode);error=np.linalg.norm(actual-pred,axis=1);checks.append({'headYawDegrees':degree,'maximumWorldVertexErrorM':float(error.max()),'rmsErrorM':float(np.sqrt(np.mean(error**2)))});assert error.max()<.000002,(degree,error.max(),mode)
    flow.solid.stage.set_pose(rig,'neutral');quads=np.array([p.vertices for p in body.data.polygons],dtype=np.int32);included=np.min(V[quads][:,:,2],axis=1)>1.30;top=np.flatnonzero(V[:,2]>1.30)
    # A float32 hull-vertex optimization missed a 4.82 um extremum in the first
    # probe. Use every selected body vertex; do not loosen containment tolerance.
    candidate=top.astype(np.int32);g=np.load(S/'aevrynd-female-next-r0014-c-clump-guides.npz');A=g['planeNormals'];support_checks=[]
    excluded=np.unique(quads[~included].ravel());radial=V-pivot;perp=radial-(radial@axis)[:,None]*axis;z_bound=V[:,2]+W*2*math.sin(math.radians(25)*.5)*np.linalg.norm(np.cross(axis,[0.,0.,1.]))*np.linalg.norm(perp,axis=1);excluded_max_z=float(z_bound[excluded].max())
    for degree in (-25,0,25):
        q=rotate(V,axis,pivot,math.radians(degree),W,mode);b=np.max(q[candidate]@A.T,axis=0)+.000002;maximum=max(float(np.max(q[block]@A.T-b)) for block in np.array_split(top,16));support_checks.append({'yawDegrees':degree,'maximumBodyVertexPlaneViolationM':maximum});assert maximum<=0,maximum
    G=g['guides'].astype(np.float64);roots=G[:,0];selected=[int(np.argmax(roots[:,0]))]
    while len(selected)<48:
        distance=np.min(np.linalg.norm(roots[:,None,:]-roots[np.array(selected)][None,:,:],axis=2),axis=1);selected.append(int(np.argmax(distance)))
    binds=json.loads((S/'aevrynd-female-next-r0014-guide-bindings.json').read_text());selected=np.array(selected,dtype=np.int32);ids=np.array([binds[i]['bodyVertices'] for i in selected]);weights=np.array([binds[i]['barycentric'] for i in selected]);restTri=V[ids]
    def frame(P):
        x=P[:,1]-P[:,0];x/=np.linalg.norm(x,axis=1,keepdims=True);n=np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]);n/=np.linalg.norm(n,axis=1,keepdims=True);y=np.cross(n,x);return np.stack((x,y,n),axis=-1)
    F=frame(restTri);anchor=np.einsum('ij,ijk->ik',weights,restTri)+F[:,:,2]*.00020;assert np.max(np.linalg.norm(anchor-G[selected,0],axis=1))<.000001
    cache=E/'driver-model.npz';np.savez_compressed(cache,bodyRestVertices=V.astype(np.float32),bodyTriangles=T,headWeights=W.astype(np.float64),supportVertexIds=candidate,headAxisWorld=axis,headPivotWorld=pivot,planeNormals=A,selectedGuideIds=selected,guides=G[selected].astype(np.float32),guideBodyVertices=ids,guideBarycentrics=weights,restGuideFrames=F)
    result={'source':str(SRC),'sourceSha256':flow.route.sha(SRC),'driverData':str(cache),'driverDataSha256':flow.route.sha(cache),'skinningMode':mode,'singleHeadYawProtocolOnly':True,'headDescendantBones':sorted(descendants),'bodyVertices':len(V),'topBodyVertices':len(top),'supportCandidateVertices':len(candidate),'supportSlackM':.000002,'includedBodyFaces':'Quads whose every rest vertex is above z 1.30 m are contained by the support proxy. All omitted/crossing quads have their vertex Z under the reported analytic yaw bound; guides must remain strictly above it.','excludedBodyVertexMaximumZBoundOver25DegreeYawM':excluded_max_z,'analyticBlenderComparisons':checks,'supportContainmentChecks':support_checks,'guidesSelected':selected.tolist(),'guideCount':48,'fullGroomGuideCount':len(G),'status':'PASS_DRIVER_EXTRACTION_AND_SAMPLED_SKINNING_MATCH','limits':['Only head local-Y yaw, all other bone poses neutral.','Representative 48-guide diagnostic before full 424 guides and child interpolation.','Driver match at listed angles is not a full motion/collision certificate.'],'wallSeconds':time.time()-start}
    (E/'driver-verification.json').write_text(json.dumps(result,indent=2)+'\n');print('AFN15_DRIVER='+json.dumps(result),flush=True)

if __name__=='__main__':main()
