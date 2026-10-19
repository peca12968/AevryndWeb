"""Own full-head anatomical domain and same-head authored spline groom.

Root area is selected on actual evaluated skin, not helper-hair. Explicit
guide knots have no shared exit ring, imported paths, loft or velocity field.
Bounded representative actual-root finite capsules gate the full preview.
"""
import bpy,importlib.util,json,time,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
sp=importlib.util.spec_from_file_location('head48',Path(__file__).with_name('inspect-female-next-r0043-ocular-junction.py'));i=importlib.util.module_from_spec(sp);sp.loader.exec_module(i)
b=i.b;f=i.f;v=i.v;R=b.R;S=b.S;E=R/'Evidence/character-female-next/r0048-anatomical-groom';E.mkdir(exist_ok=True);SRC=S/'aevrynd-female-next-r0042-b-shadow-quality-review.blend';OUT=S/'aevrynd-female-next-r0048-a-anatomical-wave-groom.blend';PILOT=S/'aevrynd-female-next-r0048-a-anatomical-guide-pilot.blend';N=160;COUNT=24000
g=f.flowcheck;C=np.array((0.,-.015,1.490))
METHOD='Own anatomical skin-face domain,29independent editable Bezier controls, same-head root-normal-oriented3nearest guide interpolation with no cross-part mixing, native POLY followers. Not donor transfer,old-root delta,global loft/flow or skin-track crop. Prior stopped methods remain stopped.'
INTERPOLATION='Same-current-head root-normal orientation and three inverse-distance-cubed nearest same-part weights. Imported source paths not used. Child validation is independent.'
# Own manually designated anatomical hairline control points (azimuth,
# elevation). They are an artist's initial boundary on this head, not a scan
# of follicles. Ear arches stay above pinnae; rear regions descend to nape.
BOUNDARY=np.array([[-math.pi,-.65],[-2.7,-.62],[-2.3,-.50],[-2.0,-.35],[-1.8,-.10],[-1.55,.05],[-1.3,.10],[-1.0,.18],[-.75,.33],[-.45,.44],[0.,.48],[.4,.46],[.7,.35],[1.,.20],[1.3,.12],[1.55,.06],[1.8,-.09],[2.,-.33],[2.3,-.48],[2.7,-.61],[math.pi,-.65]])
# name / scalp azimuth,elevation / independent 3D route knots in metres.
# A separate root + exit handle is derived from the real skin normal; no
# common exit station and no old/new-source or donor path transfer.
GUIDES=[
('L_front_edge',-.28,.55,[[-.047,-.123,1.548],[-.080,-.137,1.505],[-.096,-.125,1.453],[-.108,-.109,1.403],[-.092,-.112,1.351]]),
('L_front_inner',-.40,.85,[[-.061,-.119,1.568],[-.101,-.126,1.515],[-.112,-.107,1.456],[-.101,-.093,1.398],[-.117,-.082,1.335]]),
('L_front_crown',-.28,1.28,[[-.057,-.074,1.579],[-.105,-.094,1.531],[-.115,-.085,1.471],[-.104,-.073,1.412],[-.126,-.064,1.354],[-.111,-.070,1.305]]),
('L_temple_low',-1.02,.25,[[-.088,-.065,1.514],[-.104,-.075,1.477],[-.099,-.074,1.426],[-.117,-.053,1.380],[-.102,-.048,1.326]]),
('L_temple_mid',-.90,.65,[[-.096,-.075,1.556],[-.117,-.073,1.503],[-.108,-.055,1.446],[-.126,-.044,1.391],[-.108,-.052,1.332]]),
('L_side_top',-1.20,1.12,[[-.082,-.030,1.578],[-.119,-.040,1.533],[-.123,-.030,1.475],[-.111,-.020,1.413],[-.132,-.002,1.354],[-.116,-.016,1.302]]),
('L_ear_top',-1.50,.22,[[-.092,-.014,1.517],[-.109,-.009,1.477],[-.102,.008,1.432],[-.119,.026,1.385],[-.100,.028,1.337]]),
('L_side_mid',-1.62,.66,[[-.103,.016,1.553],[-.124,.020,1.500],[-.113,.038,1.445],[-.131,.045,1.386],[-.113,.030,1.324]]),
('L_rear_top',-2.05,1.10,[[-.065,.067,1.572],[-.109,.085,1.522],[-.120,.098,1.465],[-.102,.112,1.412],[-.121,.111,1.354],[-.099,.098,1.307]]),
('L_behind_ear',-2.03,-.18,[[-.082,.057,1.486],[-.096,.071,1.452],[-.089,.090,1.412],[-.107,.101,1.365],[-.090,.092,1.319]]),
('L_occipital',-2.34,.40,[[-.073,.096,1.533],[-.091,.116,1.483],[-.083,.129,1.428],[-.101,.125,1.371],[-.078,.118,1.318]]),
('L_nape',-2.55,-.38,[[-.053,.094,1.469],[-.067,.111,1.433],[-.059,.119,1.393],[-.077,.124,1.349],[-.061,.110,1.306]]),
('L_rear_part',-2.94,.79,[[-.029,.092,1.567],[-.051,.122,1.517],[-.047,.141,1.458],[-.062,.137,1.403],[-.046,.145,1.347],[-.058,.126,1.294]]),
('L_low_nape',-3.02,-.48,[[-.014,.101,1.457],[-.029,.117,1.421],[-.019,.129,1.379],[-.036,.126,1.332],[-.025,.114,1.291]]),
('R_front_edge',.28,.57,[[.054,-.122,1.551],[.087,-.124,1.519],[.094,-.115,1.473],[.111,-.100,1.427],[.100,-.094,1.381]]),
('R_front_sweep',.24,1.13,[[.060,-.079,1.576],[.105,-.102,1.538],[.115,-.093,1.485],[.101,-.086,1.433],[.121,-.067,1.375],[.106,-.076,1.319]]),
('R_temple_low',.98,.29,[[.088,-.066,1.518],[.105,-.073,1.478],[.101,-.061,1.430],[.119,-.039,1.382],[.106,-.044,1.333]]),
('R_temple_high',.83,.82,[[.094,-.069,1.566],[.117,-.073,1.520],[.122,-.053,1.466],[.108,-.040,1.409],[.130,-.023,1.353],[.116,-.038,1.309]]),
('R_side_crown',1.25,1.25,[[.082,-.012,1.579],[.121,-.016,1.539],[.128,.002,1.480],[.111,.016,1.421],[.133,.032,1.364],[.117,.015,1.308]]),
('R_ear_top',1.48,.24,[[.092,-.012,1.519],[.109,-.007,1.480],[.103,.012,1.433],[.120,.027,1.388],[.103,.021,1.344]]),
('R_side_mid',1.64,.68,[[.104,.021,1.558],[.124,.033,1.510],[.116,.049,1.451],[.134,.057,1.393],[.116,.045,1.337]]),
('R_rear_crown',2.08,1.16,[[.069,.068,1.577],[.109,.087,1.533],[.120,.103,1.477],[.104,.118,1.420],[.123,.113,1.362],[.103,.102,1.311]]),
('R_behind_ear',2.05,-.16,[[.082,.060,1.489],[.097,.076,1.454],[.089,.092,1.414],[.107,.105,1.368],[.092,.093,1.324]]),
('R_occipital',2.37,.43,[[.073,.099,1.538],[.092,.119,1.491],[.082,.133,1.435],[.103,.127,1.378],[.081,.118,1.324]]),
('R_nape',2.55,-.36,[[.055,.096,1.473],[.070,.113,1.438],[.060,.124,1.396],[.079,.127,1.351],[.062,.112,1.309]]),
('R_rear_part',2.93,.84,[[.031,.094,1.572],[.054,.125,1.524],[.048,.143,1.467],[.065,.140,1.411],[.049,.148,1.355],[.060,.129,1.302]]),
('R_low_nape',3.01,-.46,[[.017,.103,1.462],[.031,.120,1.428],[.021,.133,1.384],[.038,.129,1.338],[.026,.117,1.298]]),
('C_front_part',.04,1.48,[[.046,-.076,1.580],[.087,-.101,1.550],[.113,-.102,1.501],[.105,-.085,1.447],[.124,-.062,1.390],[.107,-.061,1.334]]),
('C_back_part',3.12,1.47,[[.018,.062,1.582],[.033,.113,1.542],[.027,.141,1.486],[.044,.143,1.429],[.031,.153,1.371],[.045,.134,1.315]])]
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def norm(x):return x/max(np.linalg.norm(x),1e-30)
def angular(P):
    Q=P-C;return np.arctan2(Q[:,0],-Q[:,1]),np.arctan2(Q[:,2],np.linalg.norm(Q[:,:2],axis=1))
def scalp_domain(V,T):
    Q=V[T].mean(1);az,el=angular(Q);lower=np.interp(az,BOUNDARY[:,0],BOUNDARY[:,1]);cross=np.cross(V[T[:,1]]-V[T[:,0]],V[T[:,2]]-V[T[:,0]]);area=np.linalg.norm(cross,axis=1)*.5;dot=np.einsum('ij,ij->i',cross,Q-C);keep=(el>=lower)&(Q[:,2]>1.410)&(dot>0)&(area>1e-14);ids=np.flatnonzero(keep)
    # Domain stores exact original triangles, not a smoothed collision proxy.
    verts,inv=np.unique(T[ids],return_inverse=True);mesh=bpy.data.meshes.new('AFN48_ANATOMICAL_SCALP_DOMAIN');mesh.from_pydata(V[verts].tolist(),[],inv.reshape(-1,3).tolist());mesh.update();att=mesh.attributes.new('AFN48_BodyTriangle','INT','FACE');att.data.foreach_set('value',ids.astype('i4'));uv=mesh.uv_layers.new(name='AFN48_ScalpUV');a,e=angular(V[verts]);lo=np.interp(a,BOUNDARY[:,0],BOUNDARY[:,1]);coords=np.column_stack(((a+math.pi)/(2*math.pi),(e-lo)/(math.pi*.5-lo)))
    for loop in mesh.loops:uv.data[loop.index].uv=coords[loop.vertex_index]
    o=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(o);o.hide_render=True;o.hide_set(True);o['aevrynd_layer']='EDITABLE_ANATOMICAL_SCALP_REGION';o['scope']='Exact evaluated current body triangles in artist-designated hairline boundary. UV is authoring chart, not measured scalp mapping. Not a moving scalp rig or separate collision proxy.';return ids,area[ids],lower[ids],el[ids],o
def root(tree,tri,az,el):
    direction=norm(np.array((.071*np.cos(el)*np.sin(az),-.09*np.cos(el)*np.cos(az),.073*np.sin(el))));hit,n,tid,d=tree.ray_cast(Vector(C+.3*direction),Vector(-direction),.4);assert hit is not None,(az,el);n=norm(np.array(n));assert n@direction>.15
    A=tri[tid];xy=np.linalg.lstsq(np.column_stack((A[1]-A[0],A[2]-A[0])),np.array(hit)-A[0],rcond=None)[0];bc=np.r_[1-xy.sum(),xy];assert bc.min()>-1e-3;return np.array(hit)+n*.00018,n,{'bodyTriangle':int(tid),'barycentric':bc.tolist(),'surfaceM':list(hit),'normal':n.tolist(),'rootOffsetM':.00018,'rootParam':[az,el]}
def sample(K,T):
    Q=[]
    for j in range(len(K)-1):
        for t in np.linspace(0,1,33)[:-1]:Q.append((2*t**3-3*t*t+1)*K[j]+(t**3-2*t*t+t)*T[j]+(-2*t**3+3*t*t)*K[j+1]+(t**3-t*t)*T[j+1])
    Q=np.array(Q+[K[-1]]);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(Q,axis=0),axis=1))];return np.column_stack([np.interp(np.linspace(0,arc[-1],N),arc,Q[:,j])for j in range(3)])
def make_guides(tree,tri):
    paths=[];records=[];normals=[]
    for name,az,el,knots in GUIDES:
        R0,n,record=root(tree,tri,az,el);K=np.vstack((R0,R0+n*.008,np.array(knots)));T=np.zeros_like(K);T[0]=n*.008;T[1]=(K[2]-K[0])*.40;T[2:-1]=(K[3:]-K[1:-2])*.38;T[-1]=(K[-1]-K[-2])*.55;paths.append(sample(K,T));normals.append(n);records.append(dict(record,name=name,knotsM=K.tolist(),tangentsM=T.tolist()))
        d=bpy.data.curves.new('AFN48_CTRL_'+name,'CURVE');d.dimensions='3D';sp=d.splines.new('BEZIER');sp.bezier_points.add(len(K)-1)
        for p,k,t in zip(sp.bezier_points,K,T):p.co=k;p.handle_left_type='FREE';p.handle_right_type='FREE';p.handle_left=k-t/3;p.handle_right=k+t/3
        o=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(o);o.hide_render=True;o.hide_set(True);o['aevrynd_layer']='EDITABLE_PRIMARY_GROOM_GUIDE';o['scope']='Own complete same-head path; rebuild followers from recorded controls. Not a simulation or live Blender modifier.'
    return np.array(paths),np.array(normals),records
def follicles(V,T,ids,area,lo,el):
    rng=np.random.default_rng(480048);weight=area*np.clip((el-lo)/.10,0,1);weight/=weight.sum();tid=rng.choice(ids,size=COUNT,p=weight);uv=rng.random((COUNT,2));flip=uv.sum(1)>1;uv[flip]=1-uv[flip];bc=np.column_stack((1-uv.sum(1),uv));points=np.einsum('ni,nij->nj',bc,V[T[tid]]);nn=np.cross(V[T[tid,1]]-V[T[tid,0]],V[T[tid,2]]-V[T[tid,0]]);nn/=np.linalg.norm(nn,axis=1)[:,None];return points+nn*.00018,nn,tid,bc
def rotation(A,B):
    cross=np.cross(A,B);dot=float(A@B);K=np.array(((0,-cross[2],cross[1]),(cross[2],0,-cross[0]),(-cross[1],cross[0],0)));return np.eye(3)+K+K@K/max(1+dot,1e-12)
def followers(roots,normals,G,GN,which):
    output=[];lineage=[];rng=np.random.default_rng(480148);u=np.linspace(0,1,N)
    for ci in which:
        R0=roots[ci];nn=normals[ci];D=np.linalg.norm(G[:,0]-R0,axis=1);same=(G[:,0,0]*R0[0]>=0)|(abs(G[:,0,0])<.009);D[~same]=np.inf;near=np.argsort(D)[:3];w=1/np.maximum(D[near],.001)**3;w/=w.sum();P=np.zeros((N,3))
        for gi,weight in zip(near,w):P+=weight*((G[gi]-G[gi,0])@rotation(GN[gi],nn).T)
        P+=R0;P[0]=R0
        # Fine variation is newly authored on this shape, not the shape's basis.
        phase=float(rng.uniform(0,2*math.pi));amp=float(rng.uniform(.00010,.00035));tangent=np.gradient(P,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-30);axis=np.cross(tangent,np.tile(nn,(N,1)));axis/=np.maximum(np.linalg.norm(axis,axis=1)[:,None],1e-30);P+=axis*(amp*np.sin(u*7*math.pi+phase)*np.sin(math.pi*u)**2)[:,None]
        length=np.linalg.norm(np.diff(P,axis=0),axis=1).sum();trim=float(rng.uniform(.94,1));P=np.column_stack([np.interp(u*trim,u,P[:,j])for j in range(3)]);P[0]=R0;output.append(P);lineage.append({'rootId':int(ci),'guides':near.tolist(),'weights':w.tolist(),'trimFraction':trim,'pretrimLengthM':float(length)})
    return np.array(output),lineage
def main():
    tick=time.time();full='--full'in sys.argv;assert b.sha(SRC)=='d62c180a5af61f6f8d800926b101738c89a8fbe7785fe1054fd655fd018824da'
    if full:assert json.loads((E/'pilot-body-contact.json').read_text())['status']=='PASS_TESTED_STATIC_CAPSULES'
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state();scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=4;body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);tree=i.i.tree(V,T);tri=V[T]
    save('round-contract.json',{'revision':'female-next-r0048','previousGoalTurnClassification':'progress: r47 rejected actual complete card candidate and distinct81guide pilot, independently confirmed failed contacts, archived/pushed6232cbf; no appearance gain','source':str(SRC),'sourceSha256':b.sha(SRC),'mainDefects':['Cap and separated straight curtain shape with weak side/nape coverage','Staring eyes','Flat skin'],'chosenDefect':'Complete hairstyle with explicit anatomical scalp coverage and independently composed shoulder-length waves','hypothesis':'Actual current scalp triangle area roots across temple/ear/rear/nape plus individually authored full3D routes can provide natural coverage, asymmetry and depth without imported cards or common exit rings','method':METHOD,'expectedVisibleChange':'Continuous readable hairline and ear/nape transition; layered wavy asymmetric silhouette rather than flat straight curtains','smallTest':'29authored roots plus representative extreme and median actual-domain child roots. Actual160point finite capsules before dense preview. No collision-driven point pushing or root movement.','reject':['Any unresolved representative finite capsule/root containment','Coarse silhouette inflated,helmet,sheets,tubes or unconvincing complete style','No whole-head appearance benefit','Any unrelated skin/mesh/lighting change'],'resources':{'startUTC':'2026-10-19 16:14:04 UTC','checkpointUTC':'2026-10-19 16:59:04 UTC','threads':4,'heavyJobsAtOnce':1,'nativeFibresMaximum':COUNT,'pointsPerFibre':N,'newNodeServers':0},'scope':'Static full-character authoring; new root distribution is explicit anatomical redesign, no hair dynamics/self/continuous or engine acceptance.'})
    ids,area,lo,el,domain=scalp_domain(V,T);G,GN,records=make_guides(tree,tri);roots,normals,tid,bc=follicles(V,T,ids,area,lo,el);nearest=np.argmin(np.linalg.norm(roots[:,None]-G[None,:,0],axis=2),axis=1);pilotids=[]
    for k in range(len(G)):
        choose=np.flatnonzero(nearest==k)
        if not len(choose):continue
        delta=roots[choose]-G[k,0]
        for axis in range(3):pilotids.extend([int(choose[np.argmin(delta[:,axis])]),int(choose[np.argmax(delta[:,axis])])])
        pilotids.append(int(choose[np.argmin(np.linalg.norm(delta,axis=1))]))
    pilotids=np.array(sorted(set(pilotids)),dtype='i4');which=np.arange(COUNT)if full else pilotids;P,lineage=followers(roots,normals,G,GN,which);rad=np.broadcast_to(np.linspace(.00004,.000002,N),(len(P),N)).copy()
    save('anatomical-domain.json',{'originalBodySignature':before['meshes'][b.BODY],'actualSourceTriangleCount':len(ids),'areaM2':float(area.sum()),'boundaryAzimuthElevation':BOUNDARY.tolist(),'regionIntent':'Frontal boundary,temple and above-ear arches,behind-ear descent,occipital and nape. Own artist-designated scalp anatomy on visible current head, not captured follicle truth.','rootWorldBoundsM':[roots.min(0).tolist(),roots.max(0).tolist()],'rootCountsBelowZ1_47':int((roots[:,2]<1.47).sum()),'headDomainIsSeparateEditableMesh':True,'domainSurfaceNotUsedAsCollisionProxy':True});save('primary-guides.json',{'guides':records,'interpolation':INTERPOLATION})
    np.savez_compressed(E/'anatomical-root-bindings.npz',triangleIds=tid,barycentric=bc.astype('f4'),normal=normals.astype('f4'),rootPositions=roots.astype('f4'))
    if not full:
        audit=g.check(np.concatenate((G,P)),np.broadcast_to(np.linspace(.00004,.000002,N),(len(G)+len(P),N)),tree,tri);save('pilot-body-contact.json',audit);save('pilot-lineage.json',{'rootIds':pilotids.tolist(),'followers':lineage,'primaryGuides':len(G),'representativeFollowers':len(P)})
        hair=g.guides(np.concatenate((G,P)),body,bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'].data.materials[0]);hair.name='AFN48_REPRESENTATIVE_ACTUAL_FIBRES';hair.data.bevel_depth=.00004
        for spline in hair.data.splines:spline.points.foreach_set('radius',np.linspace(1,.05,N).astype('f4'))
        np.savez_compressed(E/'pilot-paths.npz',positions=np.concatenate((G,P)).astype('f4'),radii=np.broadcast_to(np.linspace(.00004,.000002,N),(len(G)+len(P),N)).astype('f4'));output=PILOT;label='pilot'
    else:
        # Copy a known-good native format block; no old points or modifiers.
        old=bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'];d=old.data.copy();d.name='AFN48_ANATOMICAL_WAVE_FIBRES';d.remove_curves(indices=list(range(4,len(d.curves))));d.resize_curves([N]*4);d.add_curves([N]*(COUNT-4));d.position_data.foreach_set('vector',P.astype('f4').ravel());d.attributes['radius'].data.foreach_set('value',rad.astype('f4').ravel());d.attributes['curve_type'].data.foreach_set('value',[1]*COUNT);d.attributes['material_index'].data.foreach_set('value',[x%len(d.materials)for x in range(COUNT)]);hair=bpy.data.objects.new(d.name,d);scene.collection.objects.link(hair);hair.matrix_world=Matrix.Identity(4);hair['aevrynd_layer']='SCALP_HAIR_FIBRES';hair['scope']='Static visual candidate from explicit anatomical roots and own full-path guides. Editable native curves and rebuildable controls, no dynamic rig.';actual,rr=v.hair_arrays(hair);assert np.array_equal(actual,P.astype('f4'))and np.array_equal(rr,rad.astype('f4'));output=OUT;label='a-after';np.savez_compressed(E/'native-root-bindings.npz',triangleIds=tid,barycentric=bc.astype('f4'),normal=normals.astype('f4'),rootPositions=roots.astype('f4'));save('follower-lineage.json',{'followers':lineage});audit={'status':'NOT_RUN_FULL_GROOM_VISUAL_REVIEW_FIRST'}
    old=bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'];old.hide_render=True;old.hide_set(True);bpy.context.view_layer.update();after=f.state();assert all(after['meshes'][name]==x for name,x in before['meshes'].items());assert all(after['materials'][name]==x for name,x in before['materials'].items());assert after['skinFields']==before['skinFields']and after['stage']==before['stage'];assert all(after['curves'][name]==x for name,x in before['curves'].items());b.camera('face');scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True);save(('build-summary.json'if full else'pilot-summary.json'),{'output':str(output),'sha256':b.sha(output),'sourceSha256':b.sha(SRC),'fullCandidate':full,'primaryGuides':len(G),'representativeFollowers':len(pilotids),'curves':COUNT if full else len(G)+len(P),'pointsPerCurve':N,'actualNativeRootDistributionIsNew':True,'originalBodySkinOpticsStageUnchanged':True,'bodyContact':audit,'seconds':time.time()-tick});f.E=E;f.render(label,('face','oblique','profile'));i.ch.review.extras(label,E);print('R48_READY',label,len(P),audit['status'],time.time()-tick,flush=True)
if __name__=='__main__':main()
