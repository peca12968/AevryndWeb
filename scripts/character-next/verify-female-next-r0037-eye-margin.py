"""Reopened exact skin-attached tissue seams and complete static lash capsules.

Expected shared anatomical bases are separately proved through source-triangle
lineage. Only the welded seam/footprint is allowed; arbitrary region exclusions
or geometry penetration away from that footprint are not accepted.
"""
import bpy,importlib.util,json,time,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
g=module('g37','build-female-next-r0037-eye-margin.py');b=g.b;v=g.v;E=g.E;S=g.S
f=module('f36','solve-female-next-r0036-brow-contacts.py');v36=module('v36','verify-female-next-r0036-brows.py')
PREFIX='c' if '--variant-c' in sys.argv else 'b'
def tree(V,T):return BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
def inside(p,T,tol=1e-8):
    co=np.linalg.lstsq(np.column_stack((T[1]-T[0],T[2]-T[0])),p-T[0],rcond=None)[0];q=np.array((1-co.sum(),co[0],co[1]));return q.min()>=-tol
def intersections(A,B):
    na=np.cross(A[1]-A[0],A[2]-A[0]);nb=np.cross(B[1]-B[0],B[2]-B[0]);na/=np.linalg.norm(na);nb/=np.linalg.norm(nb);da=(A-B[0])@nb;db=(B-A[0])@na;eps=1e-10
    if da.min()>eps or da.max()<-eps or db.min()>eps or db.max()<-eps:return []
    if np.linalg.norm(np.cross(na,nb))<1e-7 and max(abs(da))<1e-8:
        # Coplanar convex clipping in the most stable two-dimensional plane.
        axes=np.delete(np.arange(3),np.argmax(abs(na)));p=[x[axes].copy() for x in A];clip=B[:,axes];area=np.cross(clip[1]-clip[0],clip[2]-clip[0]);clip=clip if area>=0 else clip[::-1]
        for c,d in zip(clip,np.roll(clip,-1,axis=0)):
            old=p;p=[]
            if not old:break
            def side(x):return float(np.cross(d-c,x-c))
            for x,y in zip(old,old[1:]+old[:1]):
                dx,dy=side(x),side(y)
                if dx>=-1e-15:p.append(x)
                if (dx>0 and dy<0) or (dx<0 and dy>0):p.append(x+(y-x)*dx/(dx-dy))
        if not p:return []
        result=[];M=np.column_stack((A[1,axes]-A[0,axes],A[2,axes]-A[0,axes]))
        for x in p:co=np.linalg.lstsq(M,x-A[0,axes],rcond=None)[0];result.append(A[0]+co[0]*(A[1]-A[0])+co[1]*(A[2]-A[0]))
        return result
    out=[]
    for T,Q,dist in ((A,B,da),(B,A,db)):
        for j in range(3):
            k=(j+1)%3
            if abs(dist[j])<=eps and inside(T[j],Q):out.append(T[j])
            if dist[j]*dist[k]<0:
                p=T[j]+(T[k]-T[j])*dist[j]/(dist[j]-dist[k])
                if inside(p,Q):out.append(p)
    return out
def on_expected(points,expected,tolerance=1e-6):
    if not points:return True
    if not len(expected):return False
    expected=np.array(expected);points=np.array(points)
    if len(expected)==1:return bool(np.all(np.linalg.norm(points-expected[0],axis=1)<=tolerance))
    if len(expected)==2:
        d=expected[1]-expected[0];t=np.clip((points-expected[0])@d/max(d@d,1e-30),0,1);return bool(np.all(np.linalg.norm(points-expected[0]-t[:,None]*d,axis=1)<=tolerance))
    return False
def geometry_controls():
    a=np.array(((0.,0.,0.),(1.,0.,0.),(0.,1.,0.)))
    assert not intersections(a,a+np.array((0.,0.,.01)))
    crossing=np.array(((.25,.25,-1.),(.25,.25,1.),(.25,.75,0.)));assert len(intersections(a,crossing))>=2
    edge=np.array(((0.,0.,0.),(1.,0.,0.),(1.,-1.,0.)));assert on_expected(intersections(a,edge),a[:2],1e-8)
    overlap=a+np.array((.2,.2,0.));assert intersections(a,overlap) and not on_expected(intersections(a,overlap),a[:2],1e-8)
    vertex=np.array(((0.,0.,0.),(-1.,0.,1.),(0.,-1.,1.)));assert on_expected(intersections(a,vertex),a[:1],1e-8)
    offset=np.array((.03,-.12,1.46));assert len(intersections(a*.001+offset,crossing*.001+offset))>=2
    return {'separateParallel':True,'nonCoplanarCrossing':True,'coplanarSharedEdge':True,'coplanarAreaOverlapNotSeam':True,'sharedVertexOnly':True,'millimetreTranslatedCrossing':True}
def body_attachment(o,P,PT,bt,V,T,record):
    own=tree(P,PT);pairs=own.overlap(bt);legal_base=0;legal_seam=0;false=0;bad=[];source_faces=record['facesSourceBodyTriangle'];roles=record['facesRole'];boundary=set(record['boundaryBaseNodes']);foot_count=record['baseNodeCount']
    for ai,bi in pairs:
        source=source_faces[ai];aa=P[PT[ai]];bb=V[T[bi]]
        if roles[ai]=='base' and source==bi:legal_base+=1;continue
        pts=intersections(aa,bb)
        if not pts:false+=1;continue
        if roles[ai]=='base':common=set(T[source])&set(T[bi]);expected=V[np.array(sorted(common),dtype='i4')] if common else []
        else:expected=[P[j] for j in PT[ai] if j<foot_count and j in boundary]
        if on_expected(pts,expected):legal_seam+=1
        else:bad.append({'tissueTriangle':int(ai),'bodyTriangle':int(bi),'role':roles[ai],'sourceTriangle':source,'intersectionPoints':[p.tolist() for p in pts[:6]],'expectedPoints':np.array(expected).tolist()})
    return {'bodyBVHBroadphasePairs':len(pairs),'provedSharedSourceBaseFacetPairs':legal_base,'provedSourceEdgeOrWeldSeamPairs':legal_seam,'floatBroadphaseNoFloat64Intersection':false,'unqualifiedNonAttachmentPairs':len(bad),'failureSamples':bad[:40],'scope':'Shared source base facets and exact welded source-skin boundary are anatomical joins. Every other candidate is refined by actual float64 triangle intersection and must be disjoint; no blanket eye-region exclusion.','interfaceToleranceM':1e-6}
def main():
    start=time.time();g.save('triangle-math-controls.json',geometry_controls());build=g.read('c-final-build.json' if PREFIX=='c' else 'b-build.json');path=Path(build['output']);assert b.sha(path)==build['outputSha256'];binding_file='c-final-lash-bindings.json' if PREFIX=='c' and (E/'c-final-lash-bindings.json').exists() else ('c-exact-lash-bindings.json' if PREFIX=='c' and (E/'c-exact-lash-bindings.json').exists() else PREFIX+'-lash-bindings.json');bindings=g.read(binding_file);tissue=g.read('c-review-tissue-bindings.json' if PREFIX=='c' else 'a-tissue-bindings.json');cache=np.load(bindings['cache']);assert b.sha(Path(bindings['cache']))==bindings['cacheSha256']
    bpy.ops.wm.open_mainfile(filepath=str(g.SRC));original=g.state();assert json.loads(json.dumps(original))==build['originalState'];bpy.ops.wm.open_mainfile(filepath=str(path));after=g.state();assert after['meshes']==original['meshes'] and after['curves']==original['curves'] and after['skinFields']==original['skinFields'] and after['stage']==original['stage']
    changed=set(build['changedOriginalMaterials']);assert all(after['materials'][name]==original['materials'][name] for name in original['materials'] if name not in changed)
    s=bpy.context.scene;assert s.render.hair_type=='STRIP' and s.render.hair_subdiv==0;body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);bt=tree(V,T);P=[];R=[];raw=[];rrraw=[];matrices={}
    displayed_meshes={};mesh_self={}
    for name in bindings['objects']:
        o=bpy.data.objects[name];mx=np.array(o.matrix_world);matrices[name]=mx.tolist()
        if PREFIX=='c':
            record=next(r for r in bindings['meshRecords'] if r['object']==name);vv,tt=b.evaluated(o,True);rings=vv.reshape(record['curves'],258,3)[:,:256].reshape(-1,32,8,3);p=rings.mean(2);r=np.linalg.norm(rings-p[:,:,None],axis=3).max(2);P.append(p);R.append(r);own=tree(vv,tt);pairs=[(int(a),int(z)) for a,z in own.overlap(own) if a<z and set(tt[a]).isdisjoint(tt[z]) and intersections(vv[tt[a]],vv[tt[z]])];ed,co=v.v30.edges(tt);component=v.v30.component_count(len(vv),ed);displayed_meshes[name]=(vv,tt,own);mesh_self[name]={'vertices':len(vv),'triangles':len(tt),'components':component,'expectedFibres':record['curves'],'boundaryEdges':int((co==1).sum()),'nonManifoldEdges':int((co>2).sum()),'nonAdjacentTriangleSelfPairs':len(pairs),'examples':pairs[:20]}
        else:
            p,r=v.hair_arrays(o);raw.append(p);rrraw.append(r);P.append(p.astype('f8')@mx[:3,:3].T+mx[:3,3]);R.append(r.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2));assert not o.modifiers and all(a.value==1 for a in o.data.attributes['curve_type'].data)
    if PREFIX=='b':assert np.array_equal(np.concatenate(raw),cache['positions']) and np.array_equal(np.concatenate(rrraw),cache['radii'])
    P=np.concatenate(P);R=np.concatenate(R);assert np.isfinite(P).all() and (R>0).all();root_rows=bindings['roots'];maxroot=0
    if PREFIX=='c':assert np.linalg.norm(P-cache['positionsWorld'],axis=2).max()<3e-7 and np.max(abs(R-cache['radiiWorld']))<2e-7
    for p,row in zip(P,root_rows):
        ids=T[row['bodyTriangle']];assert ids.tolist()==row['bodyVertices'];bc=np.array(row['barycentric']);assert bc.min()>=0 and abs(bc.sum()-1)<1e-10;skin=bc@V[ids];target=skin+np.array(row['normal'])*row['standOffM'];maxroot=max(maxroot,float(np.linalg.norm(target-p[0])))
    assert maxroot<3e-7
    body_caps=v.g.check(P,R,bt,V[T]);g.save(PREFIX+'-lash-body-capsules.json',body_caps);ids,gap,_,_=f.contacts(P,R,1e-6);keep=(ids[:,0]//31!=ids[:,1]//31) if PREFIX=='c' else np.ones(len(ids),dtype=bool);ids=ids[keep];gap=gap[keep];self_audit={'candidatePairs':len(ids),'unqualifiedCapsulePairs':int((gap<=1e-6).sum()),'minimumTestedPairGapM':float(gap.min()) if len(gap) else None,'failures':[{'segments':ids[j].tolist(),'gapM':float(gap[j])} for j in np.flatnonzero(gap<=1e-6)[:30]]};self_audit['scope']='All different-strand capsules plus complete actual displayed mesh self surfaces' if PREFIX=='c' else 'Conservative capsules, same-shaft nonadjacent segments included';g.save(PREFIX+'-lash-self.json',self_audit)
    if PREFIX=='c':
        exact_rows=[]
        def component(ci):
            rec=next(a for a in bindings['meshRecords'] if a['firstCurve']<=ci<a['firstCurve']+a['curves']);j=ci-rec['firstCurve'];vv,tt,_=displayed_meshes[rec['object']];offset=j*258;cv=vv[offset:offset+258];ct=tt[j*512:(j+1)*512]-offset;return cv,ct,tree(cv,ct)
        for ca,cb in sorted({(int(a//31),int(z//31)) for a,z in ids[gap<=1e-6]}):
            av,at,ab=component(ca);bv,bt2,bb=component(cb);cross=[(int(i),int(j)) for i,j in ab.overlap(bb) if intersections(av[at[i]],bv[bt2[j]])];anchor_a=av[16*8:17*8].mean(0);anchor_b=bv[16*8:17*8].mean(0);a_in_b=v.v30.winding_classification(bv,bt2,anchor_a);b_in_a=v.v30.winding_classification(av,at,anchor_b);exact_rows.append({'fibres':[ca,cb],'actualSurfacePairs':len(cross),'anchorAAgainstB':a_in_b,'anchorBAgainstA':b_in_a,'qualified':not cross and a_in_b['classification']=='outside' and b_in_a['classification']=='outside'})
        self_audit['exactDisplayedClosedMeshRefinement']=exact_rows
        self_audit['unqualifiedDisplayedInterstrandPairs']=sum(not r['qualified'] for r in exact_rows)
        self_audit['meaning']='Positive broadphase capsule overlap is not declared zero. Actual displayed closed surface intersections plus complete float64 winding of one interior anchor each resolve remaining overlap/containment. Same-shaft displayed mesh self surfaces are also checked.'
        g.save(PREFIX+'-lash-self.json',self_audit)
    optical={};optical_data={}
    for side in ('L','R'):
        for part in ('Sclera','Cornea','Iris','Pupil'):
            name=f'AFN30_{side}_{part}';vv,tt=b.evaluated(bpy.data.objects[name],True);ot=tree(vv,tt);optical_data[name]=(vv,tt,ot);optical[name]=v.g.check(P,R,ot,vv[tt],roots=False)
    g.save(PREFIX+'-lash-optics.json',optical)
    tissues={};tissue_geometry={};local_mesh=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();local=np.array([list(q.co) for q in local_mesh.vertices]);body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    for record in tissue['patches']:
        name=record['object'];o=bpy.data.objects[name];pp,tt=b.evaluated(o,True);own=tree(pp,tt);source_nodes=record['nodes'];base_expected=np.array([np.array(n['weights'])@local[n['indices']] for n in source_nodes]);actual_base=np.array([list(q.co) for q in o.data.vertices[:record['baseNodeCount']]]);error=np.linalg.norm(actual_base-base_expected,axis=1);assert error.max()<2e-7 and np.array_equal(np.array(o.matrix_world),np.array(body.matrix_world));attachment=body_attachment(o,pp,tt,bt,V,T,record);self_pairs=[(int(a),int(z)) for a,z in own.overlap(own) if a<z and set(tt[a]).isdisjoint(tt[z]) and intersections(pp[tt[a]],pp[tt[z]])];edges,counts=v.v30.edges(tt);components=v.v30.component_count(len(pp),edges);area=np.linalg.norm(np.cross(pp[tt[:,1]]-pp[tt[:,0]],pp[tt[:,2]]-pp[tt[:,0]]),axis=1)*.5;optics={n:len(own.overlap(data[2])) for n,data in optical_data.items()};caps=v.g.check(P,R,own,pp[tt]);g.save(name+'-lash-capsules.json',caps)
        # One interior tissue anchor outside body, together with closed surface
        # and only exact attachment joins, excludes hidden body containment.
        offsets=np.array([np.linalg.norm(pp[record['topVertices'][j]]-pp[j]) for j in range(record['baseNodeCount'])]);anchor_id=int(offsets.argmax());anchor=(pp[record['topVertices'][anchor_id]]+pp[anchor_id])*.5;anchor_state=v.v29.parity(bt,anchor)
        if anchor_state['classification']=='unresolved':anchor_state=v.v30.winding_classification(V,T,anchor)
        row={'vertices':len(pp),'triangles':len(tt),'connectedComponents':components,'boundaryEdges':int((counts==1).sum()),'nonManifoldEdges':int((counts>2).sum()),'nonAdjacentSelfPairs':len(self_pairs),'selfExamples':self_pairs[:20],'minimumTriangleAreaM2':float(area.min()),'baseSourceReconstructionMaxM':float(error.max()),'bodyAttachment':attachment,'opticalTrianglePairs':optics,'lashCapsules':caps,'interiorAnchorBodyState':anchor_state};tissues[name]=row;tissue_geometry[name]=(pp,tt,own);g.save(PREFIX+'-tissue-contact-progress.json',tissues);print('R37_TISSUE',name,'badBody',attachment['unqualifiedNonAttachmentPairs'],'self',len(self_pairs),'badLash',caps['unqualifiedSegments'],flush=True)
    between={};names=list(tissue_geometry)
    for k,a in enumerate(names):
        for z in names[k+1:]:
            pa,ta,ba=tissue_geometry[a];pz,tz,bz=tissue_geometry[z];bad=[(int(i),int(j)) for i,j in ba.overlap(bz) if intersections(pa[ta[i]],pz[tz[j]])];between[a+' / '+z]={'actualTrianglePairs':len(bad),'examples':bad[:15]}
    hair={}
    for name in original['curves']:
        o=bpy.data.objects[name];hp,hr=v.hair_arrays(o);mx=np.array(o.matrix_world);hp=hp.astype('f8')@mx[:3,:3].T+mx[:3,3];hr=hr.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2);hair[name]={'lashCapsules':v36.scalp_contact(P,R,hp,hr),'tissues':{}}
        for n,(pv,pt,pbt) in tissue_geometry.items():
            # Exact complete segment AABB exclusion or full finite capsule test.
            lo=np.minimum(hp[:,:-1],hp[:,1:])-np.maximum(hr[:,:-1],hr[:,1:])[...,None]-1e-6;hi=np.maximum(hp[:,:-1],hp[:,1:])+np.maximum(hr[:,:-1],hr[:,1:])[...,None]+1e-6;sep=np.maximum(pv.min(0)-hi,lo-pv.max(0)).max(2);candidate=np.argwhere(sep<=0);bad=[]
            for ci,j in candidate:
                aa,bb=hp[ci,j],hp[ci,j+1];da=pbt.find_nearest(Vector(aa))[3];db=pbt.find_nearest(Vector(bb))[3];gap,method=v.g.cap.segment_test(aa,bb,da,db,float(max(hr[ci,j],hr[ci,j+1])),pbt,pv[pt])
                if gap<=0:bad.append({'curve':int(ci),'segment':int(j),'gapM':gap})
            hair[name]['tissues'][n]={'totalSegments':int(sep.size),'completeSegmentAABBExcluded':int((sep>0).sum()),'directSegments':len(candidate),'unqualifiedSegments':len(bad),'failureSamples':bad[:15]}
    g.save(PREFIX+'-existing-hair-contact.json',hair);good=body_caps['status']=='PASS_TESTED_STATIC_CAPSULES' and (self_audit['unqualifiedDisplayedInterstrandPairs']==0 if PREFIX=='c' else self_audit['unqualifiedCapsulePairs']==0) and all(a['status']=='PASS_TESTED_STATIC_CAPSULES' for a in optical.values())
    for row in tissues.values():good=good and row['connectedComponents']==1 and row['boundaryEdges']==row['nonManifoldEdges']==row['nonAdjacentSelfPairs']==row['bodyAttachment']['unqualifiedNonAttachmentPairs']==0 and sum(row['opticalTrianglePairs'].values())==0 and row['lashCapsules']['status']=='PASS_TESTED_STATIC_CAPSULES' and row['interiorAnchorBodyState']['classification']=='outside' and row['minimumTriangleAreaM2']>1e-15
    good=good and all(row['actualTrianglePairs']==0 for row in between.values()) and all(row['lashCapsules']['status']=='PASS_NEUTRAL_SCALP_BROW_CAPSULE_SEPARATION' and all(t['unqualifiedSegments']==0 for t in row['tissues'].values()) for row in hair.values())
    if PREFIX=='c':
        good=good and build['contactRelaxation']['maximumDisplacementM']<=build['contactRelaxation']['maximumAllowedDisplacementM']
        for record in mesh_self.values():good=good and record['components']==record['expectedFibres'] and record['boundaryEdges']==record['nonManifoldEdges']==record['nonAdjacentTriangleSelfPairs']==0
        mesh_names=list(displayed_meshes)
        for ai,aa in enumerate(mesh_names):
            for bb in mesh_names[ai+1:]:good=good and not displayed_meshes[aa][2].overlap(displayed_meshes[bb][2])
    before=g.read('before-renders.json');after=g.read(PREFIX+'-after-renders.json');assert len(before)==len(after)==3
    for aa,bb in zip(before,after):assert {k:z for k,z in aa.items() if k!='path'}=={k:z for k,z in bb.items() if k!='path'}
    g.render(PREFIX+'-reopened',('face',));out={'status':'PASS_REOPENED_ATTACHED_EYE_MARGIN_NEUTRAL_SCOPE' if good else 'FAIL_OR_UNRESOLVED_ATTACHED_EYE_MARGIN','source':str(path),'sourceSha256':b.sha(path),'baseline':str(g.SRC),'baselineSha256':b.sha(g.SRC),'originalAllBodyEyeGeometryUVSkinBrowScalpAndStageExact':True,'changedOriginalMaterials':sorted(changed),'allLashNativeArraysExact':True if PREFIX=='b' else None,'displayedClosedLashMeshProof':mesh_self if PREFIX=='c' else None,'actualLashWorldMatrices':matrices,'maxRootBindingErrorM':maxroot,'lashCount':len(P),'lashSegments':len(P)*31,'bodyCapsules':body_caps,'lashSelf':self_audit,'optics':optical,'tissues':tissues,'betweenTissues':between,'existingHair':hair,'matchedThreeFullHeadViews':True,'seconds':time.time()-start,'limits':['Neutral static only, no blink/gaze/face rig/deforming attachment or continuous motion contact','Shared source-skin base/welded boundary is an intentional anatomical interface, separately counted from non-attachment crossings','Wet mucosal geometry is not a fluid meniscus bridging the original globe/body gap','Eye surface atlas is CC0 artistic detail, not measured subject albedo or captured3D optics','No scalp hairstyle/self/dynamics, body/clothing rig, engine/export/LOD/performance or female acceptance']};g.save(PREFIX+'-saved-verification.json',out);print('R37_REOPENED_DONE',out['status'],time.time()-start,flush=True)
if __name__=='__main__':main()
