"""Independent actual saved neutral ocular-junction scope verification.
Whole finite lash capsules, actual tissue/eye/body triangles and exact welded
skin interfaces. No all-character, blink, continuous or engine extrapolation.
"""
import bpy,importlib.util,json,time,hashlib,copy
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('build43v',Path(__file__).with_name('build-female-next-r0043-lid-apposition.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
i=a.i;f=a.f;b=a.b;v=a.v;E=a.E;S=a.S
old=f.flowcheck.module('verify37r43','verify-female-next-r0037-eye-margin.py')
def save(n,x):a.save(n,x)
def fields(mesh):
    out={}
    for name in ('AFN32_RegisteredCC0UVW','AFN32_PigmentWeight','AFN32_Roughness'):
        ar=mesh.attributes[name];n=3 if ar.data_type=='FLOAT_VECTOR' else 1;v=np.empty(len(ar.data)*n,dtype='f4');ar.data.foreach_get('vector' if n==3 else 'value',v);out[name]=hashlib.sha256(v.tobytes()).hexdigest()
    mesh.calc_loop_triangles();loops=np.array([x.loops[:] for x in mesh.loop_triangles],dtype='i4')
    for uv in mesh.uv_layers:
        v=np.empty(len(uv.data)*2,dtype='f4');uv.data.foreach_get('uv',v);out['triUV:'+uv.name]=hashlib.sha256(v.reshape(-1,2)[loops].tobytes()).hexdigest()
    return out
def main():
    start=time.time();build=json.loads((E/f'{a.LABEL}-build-summary.json').read_text());assert b.sha(a.OUT)==build['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(a.SRC));source=f.state();V0,T0=b.evaluated(bpy.data.objects[b.BODY],True);body=bpy.data.objects[b.BODY];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();sourceFields=fields(me);ev.to_mesh_clear();hair0=i.ch.rod.m.eval_arrays(bpy.data.objects[f.OLD])
    bpy.ops.wm.open_mainfile(filepath=str(a.OUT));body=bpy.data.objects[b.BODY];after=f.state();V,T=b.evaluated(body,True);assert np.array_equal(T,T0);assert after['materials']==source['materials'] and after['skinFields']==source['skinFields'] and after['curves']==source['curves'] and after['stage']==source['stage'];changedNames={b.BODY}|{x['object'] for x in build['patches']+build['lashes']};assert all(after['meshes'][name]==value for name,value in source['meshes'].items() if name not in changedNames);assert b.mesh_signature(body.data)==source['meshes'][b.BODY]['native'];hair=i.ch.rod.m.eval_arrays(bpy.data.objects[f.OLD]);assert all(np.array_equal(x,y) for x,y in zip(hair,hair0));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert fields(me)==sourceFields;ev.to_mesh_clear()
    moved=np.any(V!=V0,axis=1);assert np.max(np.abs(V[:,[0,2]]-V0[:,[0,2]]))<1e-9;bt=old.tree(V,T);changedFaces=np.flatnonzero(np.any(moved[T],axis=1));partial=old.tree(V,T[changedFaces]);pairs=bt.overlap(partial);bad=set()
    for x,j in pairs:
        y=int(changedFaces[j]);x=int(x)
        if x!=y and set(T[x]).isdisjoint(T[y]) and old.intersections(V[T[x]],V[T[y]]):bad.add(tuple(sorted((x,y))))
    bodySelf={'changedVertices':int(moved.sum()),'affectedTriangles':len(changedFaces),'actualNonAdjacentSelfPairs':len(bad),'examples':sorted(bad)[:20]};save('a-body-self.json',bodySelf)
    optics={};od={}
    for side in ('L','R'):
        for part in ('Sclera','Cornea','Iris','Pupil'):
            n=f'AFN30_{side}_{part}';pv,pt=b.evaluated(bpy.data.objects[n],True);ot=old.tree(pv,pt);pairs=bt.overlap(ot);state=old.v.v29.parity(bt,pv[0])
            if state['classification']=='unresolved':state=old.v.v30.winding_classification(V,T,pv[0])
            optics[n]={'actualBodyTrianglePairs':len(pairs),'surfaceAnchorBodyState':state};od[n]=(pv,pt,ot)
    #R37 source triangle lineage remains valid because actual T is locked exact.
    tissue=json.loads((b.R/'Evidence/character-female-next/r0037-eye-margin/c-review-tissue-bindings.json').read_text());bindings=json.loads((b.R/'Evidence/character-female-next/r0037-eye-margin/c-final-lash-bindings.json').read_text());newbindings=copy.deepcopy(bindings);N=np.zeros_like(V);tv=V[T];fn=np.cross(tv[:,1]-tv[:,0],tv[:,2]-tv[:,0])
    for k in range(3):np.add.at(N,T[:,k],fn)
    N/=np.maximum(np.linalg.norm(N,axis=1)[:,None],1e-30);P=[];R=[];display={};meshSelf={};rootError=0.;controlError=0.;first=0
    for record in bindings['meshRecords']:
        name=record['object'];o=bpy.data.objects[name];pv,pt=b.evaluated(o,True);display[name]=(pv,pt,old.tree(pv,pt));rings=pv.reshape(record['curves'],258,3)[:,:256].reshape(-1,32,8,3);paths=rings.mean(2);radii=np.linalg.norm(rings-paths[:,:,None],axis=3).max(2);P.append(paths);R.append(radii);selfBad=[(int(x),int(y)) for x,y in display[name][2].overlap(display[name][2]) if x<y and set(pt[x]).isdisjoint(pt[y]) and old.intersections(pv[pt[x]],pv[pt[y]])];meshSelf[name]={'actualNonAdjacentSelfPairs':len(selfBad),'examples':selfBad[:15]}
        ctrl=bpy.data.objects[name.replace('_Lashes','_LashControls')];gp,gr=v.hair_arrays(ctrl);mx=np.array(ctrl.matrix_world);gp=gp.astype('f8')@mx[:3,:3].T+mx[:3,3];controlError=max(controlError,float(np.linalg.norm(gp-paths,axis=2).max()))
        for k in range(record['curves']):
            row=newbindings['roots'][first+k];bc=np.array(row['barycentric']);face=T[row['bodyTriangle']]
            if a.CONSISTENT:
                oldface=V0[face];newface=V[face];n0=np.cross(oldface[1]-oldface[0],oldface[2]-oldface[0]);n0/=np.linalg.norm(n0);n1=np.cross(newface[1]-newface[0],newface[2]-newface[0]);n1/=np.linalg.norm(n1);normal=a.rotation(n0,n1)@np.array(row['normal'])
            else:normal=bc@N[face];normal/=np.linalg.norm(normal)
            foot=bc@V[face];expected=foot+normal*row['standOffM'];rootError=max(rootError,float(np.linalg.norm(paths[k,0]-expected)));row['normal']=normal.tolist();row['surfaceM']=foot.tolist()
        first+=record['curves']
    P=np.concatenate(P);R=np.concatenate(R);assert np.isfinite(P).all() and (R>0).all() and rootError<3e-7 and controlError<3e-7
    cacheFile=S/f'aevrynd-female-next-r0043-{a.LABEL}-lashes.npz';np.savez_compressed(cacheFile,positionsWorld=P.astype('f4'),radiiWorld=R.astype('f4'));newbindings.update(source=str(a.OUT),sourceSha256=b.sha(a.OUT),cache=str(cacheFile),cacheSha256=b.sha(cacheFile),scope='Current actual closed-mesh ring centres/radii and actual body follicle triangle/barycentric rest bindings. Neutral only, no live skin or physics.');save('a-lash-bindings.json',newbindings);tissue.update(source=str(a.OUT),sourceSha256=b.sha(a.OUT),parentBindingSource='r0037-c-review-tissue-bindings',scope='Exact same body triangle topology and barycentric source-node lineage, rebuilt on current body rest geometry.');save('a-tissue-bindings.json',tissue)
    bodyCaps=old.v.g.check(P,R,bt,V[T]);save('a-lash-body.json',bodyCaps);lashOptics={n:old.v.g.check(P,R,data[2],data[0][data[1]],roots=False) for n,data in od.items()}
    ids,gap,_,_=old.f.contacts(P,R,1e-6);keep=ids[:,0]//31!=ids[:,1]//31;ids=ids[keep];gap=gap[keep];exact=[]
    def component(ci):
        rec=next(x for x in bindings['meshRecords'] if x['firstCurve']<=ci<x['firstCurve']+x['curves']);k=ci-rec['firstCurve'];pv,pt,ot=display[rec['object']];pv=pv[k*258:(k+1)*258];pt=pt[k*512:(k+1)*512]-k*258;return pv,pt,old.tree(pv,pt)
    for ca,cb in sorted({(int(x//31),int(y//31)) for x,y in ids[gap<=1e-6]}):
        av,at,ab=component(ca);bv,btt,bb=component(cb);cross=[(int(x),int(y)) for x,y in ab.overlap(bb) if old.intersections(av[at[x]],bv[btt[y]])];stateA=old.v.v30.winding_classification(bv,btt,av[128:136].mean(0));stateB=old.v.v30.winding_classification(av,at,bv[128:136].mean(0));exact.append({'fibres':[ca,cb],'surfacePairs':len(cross),'anchorA':stateA,'anchorB':stateB,'qualified':not cross and stateA['classification']=='outside' and stateB['classification']=='outside'})
    lashSelf={'broadCapsulePairs':int((gap<=1e-6).sum()),'actualClosedMeshRefinement':exact,'unqualifiedDisplayedFibrePairs':sum(not x['qualified'] for x in exact),'sameMeshSelf':meshSelf};save('a-lash-self.json',lashSelf)
    tissues={};tg={}
    for rec in tissue['patches']:
        name=rec['object'];o=bpy.data.objects[name];pv,pt=b.evaluated(o,True);ot=old.tree(pv,pt);tg[name]=(pv,pt,ot);expected=np.array([np.array(x['weights'])@V[x['indices']] for x in rec['nodes']]);err=float(np.linalg.norm(pv[:rec['baseNodeCount']]-expected,axis=1).max());attachment=old.body_attachment(o,pv,pt,bt,V,T,rec);selfbad=[(int(x),int(y)) for x,y in ot.overlap(ot) if x<y and set(pt[x]).isdisjoint(pt[y]) and old.intersections(pv[pt[x]],pv[pt[y]])];caps=old.v.g.check(P,R,ot,pv[pt]);op={n:len(ot.overlap(data[2])) for n,data in od.items()};edges,counts=old.v.v30.edges(pt);components=old.v.v30.component_count(len(pv),edges);offsets=np.array([np.linalg.norm(pv[rec['topVertices'][j]]-pv[j]) for j in range(rec['baseNodeCount'])]);j=int(offsets.argmax());anchor=(pv[rec['topVertices'][j]]+pv[j])*.5;anchorState=old.v.v29.parity(bt,anchor)
        if anchorState['classification']=='unresolved':anchorState=old.v.v30.winding_classification(V,T,anchor)
        tissues[name]={'baseReconstructionMaxM':err,'bodyAttachment':attachment,'actualSelfPairs':len(selfbad),'selfExamples':selfbad[:10],'opticalTrianglePairs':op,'lashCapsules':caps,'components':components,'boundaryEdges':int((counts==1).sum()),'nonManifoldEdges':int((counts>2).sum()),'interiorAnchorBodyState':anchorState};save('a-tissue-progress.json',tissues);print('R43_TISSUE',name,attachment['unqualifiedNonAttachmentPairs'],len(selfbad),sum(op.values()),caps['unqualifiedSegments'],flush=True)
    between={};names=list(tg)
    for k,n in enumerate(names):
        pv,pt,ot=tg[n]
        for other in names[k+1:]:
            qv,qt,oo=tg[other];cross=[(int(x),int(y)) for x,y in ot.overlap(oo) if old.intersections(pv[pt[x]],qv[qt[y]])];between[n+' / '+other]=len(cross)
    browHair={};lo=np.minimum(V[moved].min(0),V0[moved].min(0))-1e-6;hi=np.maximum(V[moved].max(0),V0[moved].max(0))+1e-6
    for name in source['curves']:
        o=bpy.data.objects[name];hp,hr=v.hair_arrays(o);mx=np.array(o.matrix_world);hp=hp.astype('f8')@mx[:3,:3].T+mx[:3,3];hr=hr.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2);low=np.minimum(hp[:,:-1],hp[:,1:])-np.maximum(hr[:,:-1],hr[:,1:])[...,None];high=np.maximum(hp[:,:-1],hp[:,1:])+np.maximum(hr[:,:-1],hr[:,1:])[...,None];candidate=np.argwhere(np.all(high>=lo,axis=2)&np.all(low<=hi,axis=2));badrows=[]
        for ci,j in candidate:
            aa,bb=hp[ci,j:j+2];da=partial.find_nearest(Vector(aa))[3];db=partial.find_nearest(Vector(bb))[3];gap,method=old.v.g.cap.segment_test(aa,bb,da,db,float(max(hr[ci,j:j+2])),partial,V[T[changedFaces]])
            if gap<=0:badrows.append({'curve':int(ci),'segment':int(j),'gap':gap})
        browHair[name]={'totalSegments':int(low.shape[0]*low.shape[1]),'excludedChangedBodyRegionSegments':int(low.shape[0]*low.shape[1]-len(candidate)),'directAffectedSegments':len(candidate),'unqualifiedChangedRegionSegments':len(badrows),'failures':badrows[:15],'lashCapsules':old.v36.scalp_contact(P,R,hp,hr)}
    good=not bad and all(x['actualBodyTrianglePairs']==0 and x['surfaceAnchorBodyState']['classification']=='outside' for x in optics.values()) and bodyCaps['status']=='PASS_TESTED_STATIC_CAPSULES' and all(x['status']=='PASS_TESTED_STATIC_CAPSULES' for x in lashOptics.values()) and lashSelf['unqualifiedDisplayedFibrePairs']==0 and all(x['actualNonAdjacentSelfPairs']==0 for x in meshSelf.values())
    good=good and all(x['baseReconstructionMaxM']<2e-7 and x['bodyAttachment']['unqualifiedNonAttachmentPairs']==x['actualSelfPairs']==x['boundaryEdges']==x['nonManifoldEdges']==0 and x['components']==1 and x['interiorAnchorBodyState']['classification']=='outside' and sum(x['opticalTrianglePairs'].values())==0 and x['lashCapsules']['status']=='PASS_TESTED_STATIC_CAPSULES' for x in tissues.values()) and not any(between.values()) and all(x['unqualifiedChangedRegionSegments']==0 and x['lashCapsules']['status']=='PASS_NEUTRAL_SCALP_BROW_CAPSULE_SEPARATION' for x in browHair.values())
    save('a-saved-verification.json',{'status':'PASS_TESTED_NEUTRAL_JUNCTION_SCOPE' if good else 'FAIL_OR_UNRESOLVED_NEUTRAL_JUNCTION','source':str(a.OUT),'sourceSha256':b.sha(a.OUT),'originalSource':str(a.SRC),'originalSourceSha256':b.sha(a.SRC),'nativeCageUVSkinFieldsMaterialsStageUnrelatedMeshesCurvesExact':True,'evaluatedSkinFieldsAndTriangleCornerUVExact':True,'actualScalpRestExact':True,'bodyTriangleOrderExact':True,'bodySelf':bodySelf,'optics':optics,'rootMaximumErrorM':rootError,'lashControlMeshMaximumErrorM':controlError,'lashBody':bodyCaps,'lashOptics':lashOptics,'lashSelf':lashSelf,'tissues':tissues,'betweenTissues':between,'browScalpAffectedBody':browHair,'seconds':time.time()-start,'scope':'Actual saved neutral rest only. No blink/gaze/continuous or full scalp/self/motion/runtime inference. Conservative capsule overlaps refined against actual closed meshes. No arbitrary body-region exclusions.'});print('R43_SAVED_GATE',good,time.time()-start,flush=True)
if __name__=='__main__':main()
