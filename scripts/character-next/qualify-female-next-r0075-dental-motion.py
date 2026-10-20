"""Actual saved-surface readback and bounded analytic inter-arch separation only."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,hashlib,time
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0075-occlusion-authoring';OLD=E.parent/'r0074-oral-controls';MARGIN=1e-6
def read(p):return json.loads(p.read_text(encoding='utf8'))
def arr(data,prop,n,width=1,dtype='f4'):
    a=np.empty((n,width),dtype);data.foreach_get(prop,a.ravel());return a if width>1 else a[:,0]
def geom(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;p=arr(d.vertices,'co',len(d.vertices),3).astype('f8');a=np.array(o.matrix_world);return d,p@a[:3,:3].T+a[:3,3]
def hair(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;p=arr(d.position_data,'vector',len(d.position_data),3).astype('f8');a=np.array(o.matrix_world);return p@a[:3,:3].T+a[:3,3]
def signature(o):
    d=o.data;h=hashlib.sha256();h.update(arr(d.vertices,'co',len(d.vertices),3).tobytes());h.update(arr(d.loops,'vertex_index',len(d.loops),dtype='i4').tobytes())
    for uv in d.uv_layers:h.update(arr(uv.data,'uv',len(uv.data),2).tobytes())
    for k in d.shape_keys.key_blocks:
        if not k.name.startswith('AFN75_'):h.update(k.name.encode());h.update(arr(k.data,'co',len(k.data),3).tobytes())
    for v in d.vertices:
        for g in v.groups:h.update(np.array([g.group,g.weight],'f8').tobytes())
    return h.hexdigest()
def tooth_ids(o,charts):
    d=o.data;lookup={int(f):i for i,c in enumerate(charts) for f in c['faces']};ids=arr(d.attributes['AFN60_NativeFaceID'].data,'value',len(d.polygons),dtype='i4');owner=np.full(len(d.vertices),-1,'i4')
    for f in d.polygons:
        i=lookup[int(ids[f.index])];vv=np.array(f.vertices);assert np.all((owner[vv]<0)|(owner[vv]==i));owner[vv]=i
    assert owner.min()>=0;return owner
def directions(points):
    bm=bmesh.new()
    for p in points:bm.verts.new(p)
    bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False);bm.normal_update();center=points.mean(0);out=[]
    for f in bm.faces:
        n=np.array(f.normal,dtype='f8');n/=np.linalg.norm(n)
        if np.dot(np.array(f.verts[0].co)-center,n)<0:n=-n
        out.append(n)
    bm.free();out=np.unique(np.r_[np.round(out,8),np.eye(3),-np.eye(3)],axis=0);out/=np.linalg.norm(out,axis=1)[:,None];return out
def prove_interval(A,B,C,support,a,b,depth=0):
    f0=C+A*np.cos(a)+B*np.sin(a);f1=C+A*np.cos(b)+B*np.sin(b);minimum=np.minimum(f0,f1);critical=np.mod(np.arctan2(B,A)+np.pi,2*np.pi);active=(critical>=a)&(critical<=b);minimum=np.where(active,np.minimum(minimum,C-np.hypot(A,B)),minimum);gap=minimum.min(0)-support;bound=float(gap.max())-MARGIN
    if bound>0:return True,bound,1,depth
    if depth>=10:return False,bound,1,depth
    middle=(a+b)*.5;left=prove_interval(A,B,C,support,a,middle,depth+1)
    if not left[0]:return left
    right=prove_interval(A,B,C,support,middle,b,depth+1);return right[0],min(left[1],right[1]),left[2]+right[2],max(left[3],right[3])
def main():
    tick=time.time();old=read(OLD/'c-build-summary.json');bpy.ops.wm.open_mainfile(filepath=old['output']);s=bpy.context.scene;s.frame_set(1);native_names=list(read(E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values());assert len(native_names)==5 and all(bpy.data.objects[n].data.shape_keys for n in native_names);native={n:signature(bpy.data.objects[n]) for n in native_names};skin='AFN74_SKIN_AND_EXISTING_OCULAR_LINING';hn=['AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES'];source={}
    for f in (1,7,13,25,31,37):
        s.frame_set(f);bpy.context.view_layer.update();source[f]={'skin':geom(bpy.data.objects[skin])[1].copy(),'hair':{n:hair(bpy.data.objects[n]).copy() for n in hn}}
    s.frame_set(1);d,oldlower=geom(bpy.data.objects['AFN74_LOWER_TEETH_RIGID']);oldlower=oldlower.copy();ref=read(E/'c-build-summary.json');assert hashlib.sha256(Path(ref['output']).read_bytes()).hexdigest()==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();assert {n:signature(bpy.data.objects[n]) for n in native_names}==native;assert not bpy.data.libraries
    upper=bpy.data.objects['AFN74_UPPER_TEETH_RIGID'];lower=bpy.data.objects['AFN74_LOWER_TEETH_RIGID'];ud,U=geom(upper);ld,L=geom(lower);L=L.copy();translation=(L-oldlower).mean(0);translation_error=float(np.linalg.norm((L-oldlower)-translation,axis=1).max());assert translation_error<1e-6
    edges=arr(ld.edges,'vertices',len(ld.edges),2,'i4');length=np.linalg.norm(L[edges[:,1]]-L[edges[:,0]],axis=1);rows=[];upperrest=U.copy();jaw=bpy.data.objects['AFN74_RIGID_JAW'];M0=np.array(jaw.matrix_world);axis=np.array(jaw.rotation_axis_angle[1:],dtype='f8');axis/=np.linalg.norm(axis);local=arr(lower.data.vertices,'co',len(lower.data.vertices),3).astype('f8');parallel=(local@axis)[:,None]*axis;perp=local-parallel;cross=np.cross(axis,local);C=parallel@M0[:3,:3].T+M0[:3,3];A=perp@M0[:3,:3].T;B=cross@M0[:3,:3].T
    for f,value in ((1,0),(7,.5),(13,1),(25,1),(31,.5),(37,0)):
        s.frame_set(f);bpy.context.view_layer.update();ctrl=bpy.data.objects['AFN74_ORAL_CONTROLS'];assert abs(ctrl['jaw_open']-value)<1e-6;_,p=geom(lower);theta=float(jaw.rotation_axis_angle[0]);pred=C+A*np.cos(theta)+B*np.sin(theta);trajectory_error=float(np.linalg.norm(p-pred,axis=1).max());assert trajectory_error<MARGIN
        full=ref['openingAngleRadiansUnchanged'];keys=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'].data.shape_keys.key_blocks;expected_arc={'RADIAL':np.cos(full*value)-1-value*(np.cos(full)-1),'TANGENT':np.sin(full*value)-value*np.sin(full)}
        for name,expected in expected_arc.items():assert abs(keys['AFN75_MANDIBULAR_ARC_'+name].value-expected)<1e-6
        strain=float(np.abs(np.linalg.norm(p[edges[:,1]]-p[edges[:,0]],axis=1)/length-1).max());assert strain<1e-5;skinerror=float(np.linalg.norm(geom(bpy.data.objects[skin])[1]-source[f]['skin'],axis=1).max());assert skinerror<1e-6;hairerrors={n:float(np.linalg.norm(hair(bpy.data.objects[n])-source[f]['hair'][n],axis=1).max()) for n in hn};assert max(hairerrors.values())<1e-6;uppererror=float(np.linalg.norm(geom(upper)[1]-upperrest,axis=1).max());assert uppererror<1e-6
        rows.append({'frame':f,'jawOpen':value,'lowerDentalMaximumRelativeEdgeStrain':strain,'actualAnalyticTrajectoryMaximumErrorM':trajectory_error,'externalSkinMaximumDifferenceFromR74M':skinerror,'hairMaximumDifferencesFromR74M':hairerrors,'upperDentalMaximumMotionM':uppererror});print('R75_READBACK_FRAME',f,skinerror,strain,flush=True)
    theta=ref['openingAngleRadiansUnchanged'];s.frame_set(1);bpy.context.view_layer.update();charts=read(OLD/'source-oral-uv-islands.json')[3:];up=tooth_ids(upper,[v for v in charts if v['jawAffected']==0]);low=tooth_ids(lower,[v for v in charts if v['jawAffected']>0]);proof=[]
    for j in range(16):
        points=U[up==j];n=directions(points);support=(points@n.T).max(0)
        for i in range(16):
            selected=low==i;aa=A[selected]@n.T;bb=B[selected]@n.T;cc=C[selected]@n.T;passed,bound,leaves,depth=prove_interval(aa,bb,cc,support,0,theta);proof.append({'upperTooth':j,'lowerTooth':i,'passed':passed,'conservativeDistanceLowerBoundAfterMarginM':bound,'certifiedAngularIntervals':leaves,'maximumSubdivisionDepth':depth});print('R75_INTERARCH_INTERVAL',j,i,passed,bound,flush=True)
    images=[]
    for im in bpy.data.images:
        if im.packed_file or im.source!='FILE':continue
        p=Path(bpy.path.abspath(im.filepath));assert p.is_file();images.append({'relative':im.filepath,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    result={'status':'PASS_SCOPED_SAVED_OPERATION_AND_ANALYTIC_INTERARCH_CLEARANCE' if all(v['passed'] for v in proof) else 'SAVED_OPERATION_PASS_INTERARCH_CONTINUOUS_MODEL_UNPROVEN','source':ref['output'],'sha256':ref['outputSha256'],'originalFiveNativeCagesUVKeysAndWeightsPreserved':True,'wholeArchTranslationM':translation.tolist(),'maximumNonTranslationResidualFromR74M':translation_error,'actualSampledOperation':rows,'interarchProof':proof,'numericalTrajectoryAllowanceM':MARGIN,'proofScope':'Actual finite dental mesh vertices and all triangles,16x16 opposing tooth pairs, explicit rigid jaw analytic trajectory angle0..original full angle, fixed neutral Head pose. One separating support plane on each angular interval bounds every actual upper vertex and every swept lower vertex.','trueGlobalMinimumOrSignedDistanceM':None,'notQualified':['Adjacent teeth self contact is NOT repaired or waived.','Gum-root joining/solid volumes, tongue/body continuous contact, other head/body actions, hair/cloth and engine remain unaccepted.','No smooth subdivision limit surface beyond the actual baked dental mesh is claimed.'],'externalTextures':images,'seconds':time.time()-tick};(E/'c-independent-operation-and-interarch.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('R75_SCOPED_QUALIFICATION',result['status'],time.time()-tick,flush=True)
if __name__=='__main__':main()
