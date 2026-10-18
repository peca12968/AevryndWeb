"""A justified second geometry candidate: macro lock volume on unchanged roots."""
import bpy,json,math,importlib.util,time
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('flow',Path(__file__).with_name('build-female-next-r0014-scalp-flow.py'));flow=importlib.util.module_from_spec(spec);spec.loader.exec_module(flow)
E,S,C,solid=flow.E,flow.S,flow.C,flow.solid

def deform(P,A,b,scale=1.):
    root=P[0].copy();side=1 if root[0]>=0 else -1;band=int(np.clip((root[1]+.12)/.022,0,7));layer=int(root[2]<1.525);cid=(0 if side<0 else 16)+band*2+layer;phase=cid*1.817
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];u=arc/max(arc[-1],1e-9);fade=np.clip(arc/.025,0,1);fade=fade*fade*(3-2*fade)
    horizontal=P-C;horizontal[:,2]=0;horizontal/=np.maximum(np.linalg.norm(horizontal,axis=1,keepdims=True),1e-9)
    radial=(P-C)/np.array((.078,.095,.085))**2;radial/=np.maximum(np.linalg.norm(radial,axis=1,keepdims=True),1e-9);crown=np.clip((P[:,2]-1.485)/.035,0,1);normal=horizontal*(1-crown[:,None])+radial*crown[:,None];normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-9)
    tangent=np.column_stack((-horizontal[:,1],horizontal[:,0],np.zeros(len(P))))
    loft=(.0026+.0018*math.cos(phase))*np.sin(math.pi*u)**1.4;wave=(.0028+.0012*math.sin(phase*.7))*np.sin(2*math.pi*arc/.125+phase)*np.sin(math.pi*u)**.7
    Q=P+scale*fade[:,None]*(normal*loft[:,None]+tangent*wave[:,None]);curl=np.clip((u-.78)/.22,0,1);Q-=scale*horizontal*(.004*curl*curl)[:,None]
    ramp=np.clip(arc/.020,0,1);ramp=ramp*ramp*(3-2*ramp);Q[1:]=flow.route.shell_batch(Q[1:],A,b,.00015+.00185*ramp[1:],.00005+.00095*ramp[1:]);Q[0]=root
    return Q,cid

def main():
    start=time.time();src=S/'aevrynd-female-next-r0014-a-scalp-flow-study.blend';prior=json.loads((E/'saved-scalp-flow-verification.json').read_text());assert prior['status']=='PASS_TESTED_STATIC_SURFACE_SCOPE' and len(prior['poses'])==5 and flow.route.sha(src)==prior['candidateSha256']
    bpy.ops.wm.open_mainfile(filepath=str(src));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');V,T,tree=solid.data(bpy.data.objects['AFN_R0008_Body']);V=np.array(V,dtype=np.float64);tri=V[np.array(T,dtype=np.int32)];guideData=np.load(S/'aevrynd-female-next-r0014-a-scalp-guides.npz');A=guideData['planeNormals'];b=guideData['planeOffsets'];G=np.array([deform(g.astype(np.float64),A,b)[0] for g in guideData['guides']]);audit=flow.route.check_paths(list(G),[np.full(64,.00006) for g in G],tree,tri)
    go=bpy.data.objects['AFN14_GUIDES']
    for spline,p in zip(go.data.splines,G):spline.points.foreach_set('co',np.column_stack((p,np.ones(len(p)))).astype(np.float32).ravel())
    np.savez_compressed(S/'aevrynd-female-next-r0014-c-clump-guides.npz',guides=G.astype(np.float32),planeNormals=A,planeOffsets=b)
    (E/'c-clump-guide-verification.json').write_text(json.dumps({'sourceSha256':flow.route.sha(src),'guideBodyCheck':audit,'childGenerationAllowed':audit['status']=='PASS_TESTED_BODY_CAPSULES','reason':'A fixes root-domain gaps but remains a uniform sheet. C changes macro-lock volume and S-curvature, retaining A roots, counts, radii, materials and light.'},indent=2)+'\n')
    if audit['status']!='PASS_TESTED_BODY_CAPSULES':
        for o in bpy.data.objects:
            if o.type=='CURVES' and o.name.startswith('AFN14_'):o.hide_render=True
        bpy.context.scene['aevrynd_release_state']='REJECTED_CLUMP_GUIDE_DIAGNOSTIC';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(S/'aevrynd-female-next-r0014-c-rejected-clump-guides.blend'));print('AFN14_CLUMP_GUIDES_REJECTED');return
    d=np.load(S/'aevrynd-female-next-r0014-a-hair-data.npz');P=d['positions'];offsets=d['offsets'];layers=d['layers'];allP=[];clumps=[];descs=[]
    for li,name in enumerate(('PRIMARY_MASS','SECONDARY_CLUMPS','HAIRLINE_FINE','FLYAWAYS')):
        ids=np.flatnonzero(layers==li);paths=[]
        for i in ids:
            q,cid=deform(P[offsets[i]:offsets[i+1]].astype(np.float64),A,b,.4 if li==2 else (1.15 if li==3 else 1.));paths.append(q);clumps.append(cid)
        obj=bpy.data.objects['AFN14_'+name];obj.data.position_data.foreach_set('vector',np.concatenate(paths).astype(np.float32).ravel());obj['aevrynd_revision']='female-next-r0014-c-clump-volume';allP.extend(paths);descs.append({'object':obj.name,'curves':len(paths),'points':sum(len(p) for p in paths)})
    cache=S/'aevrynd-female-next-r0014-c-hair-data.npz';np.savez_compressed(cache,positions=np.concatenate(allP).astype(np.float32),radii=d['radii'],offsets=offsets,layers=layers,clumpIds=np.array(clumps,dtype=np.int16))
    scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0014-c-clump-volume';scene['aevrynd_release_state']='MACRO_LOCK_VOLUME_STUDY_PENDING_SAVED_CHECK';dest=S/'aevrynd-female-next-r0014-c-clump-volume-study.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    (E/'c-clump-volume-build.json').write_text(json.dumps({'source':str(src),'sourceSha256':flow.route.sha(src),'output':str(dest),'outputSha256':flow.route.sha(dest),'layers':descs,'hairCurves':len(allP),'hairPoints':len(P),'rootBindingsInheritedFrom':'root-bindings.json','rootBindingsSha256':flow.route.sha(E/'root-bindings.json'),'clumpCount':len(set(clumps)),'rootPositionsUnchanged':bool(np.array_equal(np.concatenate(allP).astype(np.float32)[offsets[:-1]],P[offsets[:-1]])),'materialsRadiiAndCountsUnchanged':True,'fileBytes':dest.stat().st_size,'wallSeconds':time.time()-start,'overallCharacterScore':None},indent=2)+'\n');print('AFN14_CLUMP_CHILDREN_DONE',flush=True)
if __name__=='__main__':main()
