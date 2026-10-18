"""Own authored side-swept fringe on existing validated scalp anchors.

No official-reference coordinates, textures, nodes or program are imported.
Change whole frontal guide flow, not tip jitter/density/material/exposure.
"""
import bpy,importlib.util,json,math,time,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
spec=importlib.util.spec_from_file_location('locks27',Path(__file__).with_name('build-female-next-r0017-volume-locks.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
R,S=old.R,old.S;E=R/'Evidence/character-female-next/r0027-hair-redesign';E.mkdir(exist_ok=True)
SKIN_LOFT='--skin-loft' in sys.argv;LABEL='b' if SKIN_LOFT else 'a'
SRC=S/'aevrynd-female-next-r0023-b-neutral-review.blend';DST=S/f'aevrynd-female-next-r0027-{LABEL}-swept-fringe-study.blend';GUIDES=S/f'aevrynd-female-next-r0027-{LABEL}-fringe-guides.npz';CACHE=S/f'aevrynd-female-next-r0027-{LABEL}-fringe-data.npz'
def save(name,value):(E/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def selected(r):return (r[1]<-.075 and r[2]>1.525 and abs(r[0])<.055)
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def skin_loft(q,root,tree,individual=0.):
    out=q.copy();phase=math.floor((root[0]+.055)/.018)*2.39996323+math.floor((root[1]+.121)/.020)*.7
    for j in range(4,len(q)):
        u=(j-3)/(len(q)-4);hit,n,ti,d=tree.ray_cast(Vector((float(q[j,0]),-.4,float(q[j,2]))),Vector((0,1,0)),.5)
        if hit is None:continue
        loft=.0025+(.0015+.001*math.sin(phase))*math.sin(math.pi*u)+.00035*math.sin(individual)*math.sin(math.pi*u)
        surface=np.array(hit,np.float64)+np.array(n,np.float64)*loft;blend=float(smooth(u/.18));out[j]=q[j]*(1-blend)+surface*blend
    out[:4]=q[:4];return out
def fringe(p,tree,A,B):
    root=p[0];side=float(np.clip((root[0]+.055)/.11,0,1));back=float(np.clip((root[1]+.121)/.046,0,1));x=.040+.020*side;z=1.490+.008*side+.008*back
    hit,normal,ti,d=tree.ray_cast(Vector((x,-.4,z)),Vector((0,1,0)),.5);assert hit is not None
    end=np.array(hit,np.float64)+np.array(normal,np.float64)*.003
    start=p[3];tangent=p[4]-p[3];tangent/=np.linalg.norm(tangent);one=start+.012*tangent if SKIN_LOFT else start+.008*tangent+np.array((0.,-.022,.003));two=end+np.array((-.018,-.012,.018));phase=math.floor((root[0]+.055)/.018)*2.39996323+math.floor((root[1]+.121)/.020)*.7;extent=.78+.20*(.5+.5*math.sin(phase)) if SKIN_LOFT else 1.;u=np.linspace(0,extent,61)[1:];curve=(1-u[:,None])**3*start+3*(1-u[:,None])**2*u[:,None]*one+3*(1-u[:,None])*u[:,None]**2*two+u[:,None]**3*end
    q=np.vstack((p[:4],curve));assert len(q)==64
    if SKIN_LOFT:q=skin_loft(q,root,tree)
    else:
        arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))];ramp=smooth(arc/.020);q[4:]=old.route.shell_batch(q[4:],A,B,.00015+.00185*ramp[4:],.00005+.00095*ramp[4:])
    q[:4]=p[:4]
    return q.astype(np.float32)
def guides():
    started=time.time();manifest=json.loads((S.parent/'female-next.asset.json').read_text(encoding='utf8'));assert old.base.sha(SRC)==manifest['workingReviewSha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC));old.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');body=bpy.data.objects['AFN_R0008_Body'];V,T,tree=old.solid.data(body);v=np.array(V,np.float64);tri=v[np.array(T)];source=np.load(S/'aevrynd-female-next-r0017-c-volume-guides.npz');G=source['guides'].copy();A=source['planeNormals'];B=source['planeOffsets'];ids=np.array([i for i,p in enumerate(G) if selected(p[0])],np.int32);assert 30<=len(ids)<=100
    save('iteration-contract.json',{'previousGoalTurnClassification':'progress: r26 bounded actual soft-tissue studies rejected, new evidence stops oral CSG work and changes priority back to complete-head appearance.','stage':'B_COMPLETE_HEAD_IN_PROGRESS','source':str(SRC),'sourceSha256':old.base.sha(SRC),'visibleDefectsRanked':['Continuous centre-part cap and exposed artificial frontal hairline, stiff side-only flow.','Very pale sparse brows and low facial surface definition.','Stiff neutral mouth/empty oral anatomy in retained head, separate failed oral branches.'],'primaryDefect':'Frontal hair has no natural overlapping sweep; it reads as a parted cap.','hypothesis':'An authored diagonal fringe flow across the forehead, with layered end placement, changes the complete hairstyle and breaks the rigid frontal cap. Use existing scalp roots and materials; do not add fibres or alter skin/exposure.','design':'64 existing front guides selected by root domain. Preserve four original root CVs exactly, cubic sweep to actual forehead/temple landmarks, conservative outer routing of free lengths. Child authoring binds only selected frontal fibres to those guides.','reference':'Official Daniel Bystedt Hair Styles: scalp part domains and separately controlled flows as learning only. Exact CC-BY-SA version unresolved; no third-party geometry, node code, textures or author prose copied into our asset.','rejectIf':['Any complete guide/body capsule failure before child expansion.','Any moved root, changed unrelated head/skin/material/light state.','A new solid fringe slab, harsh shelf or obvious whole-head silhouette regression.','Any changed child/body/eye/brow/lash segment cannot be qualified in the saved static scope.'],'budget':{'candidatesMaximum':3,'candidate':'a','threads':4,'selectedGuides':len(ids),'guideCVs':64,'sourceFibres':21086,'noAddedFibres':True,'diagnosticMinutes':10,'roundCheckpointMinutes':45},'scope':'Static hairstyle appearance study; no self/dynamics or engine acceptance.'})
    for i in ids:G[i]=fringe(G[i].astype(np.float64),tree,A,B)
    if SKIN_LOFT:
        contract=json.loads((E/'iteration-contract.json').read_text(encoding='utf8'));contract.update({'candidate':'b','candidateARejected':'Neutral contact passes, but complete-head images show a bright flattened fringe plate and an abrupt cut edge.','hypothesis':'Replace the shared global-envelope surface by actual forehead ray-authored loft with independently layered lock lengths. Preserve root tangent and source radii/material/light.','reasonForAlternative':'A envelope projection collapses many strands to common planar facets; B changes the free-length authoring surface/volume, not a density, tip-only or material sweep.'});save('b-iteration-contract.json',contract)
    audit=old.route.check_paths(list(G[ids].astype(np.float64)),[np.full(64,.00006) for i in ids],tree,tri);np.savez_compressed(GUIDES,guides=G,oldGuides=source['guides'],selectedGuideIds=ids,planeNormals=A,planeOffsets=B)
    save(LABEL+'-guide-verification.json',{'source':str(SRC),'sourceSha256':old.base.sha(SRC),'guideData':str(GUIDES),'guideDataSha256':old.base.sha(GUIDES),'selectedGuideIds':ids.tolist(),'selectedGuides':len(ids),'bodyCapsules':audit,'childrenAllowed':audit['status']=='PASS_TESTED_BODY_CAPSULES','rootPrefixesExact':bool(np.array_equal(G[:,:4],source['guides'][:,:4])),'wallSeconds':time.time()-started});print('R0027_GUIDES',LABEL,audit['status'],'GUIDES',len(ids),'FAILURES',audit['unqualifiedSegments'],flush=True)
def children():
    start=time.time();proof=json.loads((E/(LABEL+'-guide-verification.json')).read_text(encoding='utf8'));assert proof['childrenAllowed'] and old.base.sha(GUIDES)==proof['guideDataSha256'] and old.base.sha(SRC)==proof['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC));old.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');before=old.base.snapshot();body=bpy.data.objects['AFN_R0008_Body'];V,T,tree=old.solid.data(body);data=np.load(GUIDES);G=data['guides'].astype(np.float64);ids=data['selectedGuideIds'];roots=G[ids,0];A=data['planeNormals'];B=data['planeOffsets'];bindings=json.loads((S/'aevrynd-female-next-r0014-root-bindings.json').read_text(encoding='utf8'));lookup={(r['layer'],r['curve']):r for r in bindings};positions=[];radii=[];offsets=[0];layers=[];changed=[];rows=[]
    for li,name in enumerate(old.base.NAMES):
        obj=bpy.data.objects['AFN14_'+name];P,rr,off=old.base.arrays(obj);Q=P.copy();local_changed=[];signature=old.v14.strand_signature(obj)
        for ci,(a,z) in enumerate(zip(off[:-1],off[1:])):
            p=P[a:z].astype(np.float64)
            if li in (0,1) and len(p)==64 and selected(p[0]):
                distance=np.linalg.norm(roots-p[0],axis=1);local=np.argsort(distance)[:3];guideids=ids[local];w=1/np.maximum(distance[local],.0006)**2;w/=w.sum();u=np.linspace(0,1,64);clump=(.20 if li==0 else .65)*u**1.8;one=np.eye(3)[np.argmax(w)];weights=(1-clump[:,None])*w+clump[:,None]*one;q=np.einsum('ji,ijk->jk',weights,G[guideids]);q+=(p[0]-w@G[guideids,0])[None,:]*(1-u[:,None])**2;q[:4]=p[:4]
                if SKIN_LOFT:
                    extent=.91+.09*(.5+.5*math.sin(ci*2.39996323+li));t=np.arange(3,64);sample=np.linspace(3,3+60*extent,61);q[3:]=np.column_stack([np.interp(sample,t,q[3:,axis]) for axis in range(3)]);q[:4]=p[:4];q=skin_loft(q,p[0],tree,ci*2.39996323+li)
                else:
                    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))];ramp=smooth(arc/.020);q[4:]=old.route.shell_batch(q[4:],A,B,.00015+.00185*ramp[4:],.00005+.00095*ramp[4:])
                q[:4]=p[:4];Q[a:z]=q.astype(np.float32);local_changed.append(ci);changed.append([li,ci]);row=lookup[(li,ci)];row['guides']=guideids.tolist();row['weights']=w.tolist();row['authoringFlow']='AFN27_DIAGONAL_FRINGE_'+LABEL.upper()
            positions.append(Q[a:z].copy());radii.append(rr[a:z].copy());layers.append(li);offsets.append(offsets[-1]+z-a)
        obj.data.position_data.foreach_set('vector',Q.ravel());assert old.v14.strand_signature(obj)==signature;assert np.array_equal(Q[off[:-1]],P[off[:-1]])
        rows.append({'object':obj.name,'changedCurves':len(local_changed),'changedCurveIds':local_changed,'allOtherCurvePointsExact':True})
    guideobj=bpy.data.objects['AFN14_GUIDES']
    for spline,p in zip(guideobj.data.splines,G):spline.points.foreach_set('co',np.column_stack((p,np.ones(len(p)))).astype(np.float32).ravel())
    assert old.base.snapshot()==before;bpy.context.scene['aevrynd_revision']='female-next-r0027-'+LABEL;bpy.context.scene['aevrynd_release_state']='OWN_SWEPT_FRINGE_CONTACT_VISUAL_PENDING';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST),compress=True)
    np.savez_compressed(CACHE,positions=np.concatenate(positions),radii=np.concatenate(radii),offsets=np.array(offsets,np.int64),layers=np.array(layers,np.int8),changedCurves=np.array(changed,np.int32));bindingpath=S/f'aevrynd-female-next-r0027-{LABEL}-root-bindings.json';bindingpath.write_text(json.dumps(bindings,indent=2)+'\n',encoding='utf8')
    save(LABEL+'-build-verification.json',{'source':str(SRC),'sourceSha256':old.base.sha(SRC),'output':str(DST),'outputSha256':old.base.sha(DST),'cache':str(CACHE),'cacheSha256':old.base.sha(CACHE),'bindingData':str(bindingpath),'bindingSha256':old.base.sha(bindingpath),'selectedGuideData':str(GUIDES),'selectedGuideDataSha256':old.base.sha(GUIDES),'changedCurves':len(changed),'layers':rows,'sourceHeadSkinRigMaterialLightUnchanged':True,'sourceCountsRadiiMaterialsAndRootsExact':True,'status':'BUILT_REQUIRES_REOPEN_CONTACT_VISUAL_GATES','wallSeconds':time.time()-start});print('R0027_CHILDREN',LABEL,len(changed),flush=True)
if __name__=='__main__':
    if '--children' in sys.argv:children()
    else:guides()
