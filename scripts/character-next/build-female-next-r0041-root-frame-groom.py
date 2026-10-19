"""Private r41 A: complete guide paths transported by real follicle frames.
No original generated-child residual, positional averaging, random noise,
density/radius/material changes. Static whole-groom feasibility, not dynamics.
"""
import bpy,importlib.util,json,time
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('ch40r41',Path(__file__).with_name('build-female-next-r0040-guided-children.py'));ch=importlib.util.module_from_spec(sp);sp.loader.exec_module(ch)
ad=ch.ad;rt=ch.rt;rod=ch.rod;f=ch.f;b=ch.b;v=ch.v;S=rod.S
E=f.R/'Evidence/character-female-next/r0041-complete-path-groom';E.mkdir(exist_ok=True);PVT=E/'private';PVT.mkdir(exist_ok=True)
OUT=PVT/'aevrynd-female-next-r0041-a-root-frame-groom.blend'

def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def rotation(n1,n2):
    c=float(np.clip(n1@n2,-1,1));assert c>-.99
    u=np.cross(n1,n2);K=np.array(((0,-u[2],u[1]),(u[2],0,-u[0]),(-u[1],u[0],0)))
    return np.eye(3)+K+(K@K)/(1+c)

def main():
    start=time.time();assert b.sha(rod.SRC)=='0f8707b92196bc58e158b997a9170f22708d5ddeb2c2e0d95856cbfd00bb4c04'
    source=rod.c.PRIVATE/'aevrynd-female-next-r0039-c1-surface-transfer-study.blend';proof=json.loads((rod.E/'c-reopened-verification.json').read_text());assert proof['all376SavedNativeGuideBody']['status']=='PASS_TESTED_STATIC_CAPSULES'
    save('round-contract.json',{'revision':'female-next-r0041','workingSource':str(rod.SRC),'workingSha256':b.sha(rod.SRC),'previousGoalTurnClassification':'progress: r40 complete native guide/body proof and actual child delta-transfer failure, no accepted appearance gain; pushed08f8c6d','mainDefect':'Cap/sheet owned hair and frizzy/translucent private transfer; implausible late ear crossings','method':'A: one nearest complete guide, rigid real root-normal frame transport, real original child follicle retained; no original generated-child residual or averaging of unrelated complete curves','expectedVisibleChange':'Less frizzy shape, coherent full paths with individually rooted fibres and readable flowing locks','smallTest':'256 actual saved native child curves; all finite-segment capsules and root containment against actual closed target body before expansion','held':['11223 private-reference child follicles','Original physical radius profiles and material','Complete owned body/eye/skin/brow/lash layers','Camera/light/exposure/pose/color management'],'reject':['Any representative full capsule/root failure stops expansion','Cap/sheets/ropes, shared free shafts or no meaningful full-head improvement','Root or original non-hair state changes'],'resource':{'startUTC':'2026-10-19 13:25:07 UTC','checkpointUTC':'2026-10-19 14:10:07 UTC','blenderThreads':4,'heavyJobsAtOnce':1},'rights':'Daniel Bystedt original guides; unresolved upstream CC BY-SA version, private derivatives only','scope':'Static authoring; not calibrated motion, all-layer/self/continuous/engine acceptance'})
    guides,params=rt.unpack(rod.PVT/'c-refined-surface-guide-paths.npz');lineage=np.load(rod.PVT/'c-child-guide-lineage.npz');indices=lineage['indices'];weights=lineage['weights'];nearest=indices[np.arange(len(indices)),weights.argmax(1)]
    bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;old=bpy.data.objects['AFN39_C1_PRIVATE_SURFACE_TRANSFER'];base,rad=ad.read_native(old);old.hide_render=True;retained=f.state();old.hide_render=False
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tri=V[T];tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    bind=np.load(rod.c.PRIVATE/'c1-private-surface-transfer.npz');guideBind=np.load(rod.PVT/'a-rebuilt-guide-paths.npz');foot=tri[bind['rootTriangles']];childN=np.cross(foot[:,1]-foot[:,0],foot[:,2]-foot[:,0]);childN/=np.linalg.norm(childN,axis=1)[:,None];guideN=guideBind['rootNormals']
    def child(ci):
        gi=nearest[ci];t=params[gi];Q=guides[gi];R=rotation(guideN[gi],childN[ci]);P=base[ci][0]+(Q-Q[0])@R.T;P[0]=base[ci][0];rr=np.interp(t,np.linspace(0,1,len(rad[ci])),rad[ci]);return P,rr
    ids=np.linspace(0,len(base)-1,256,dtype='i4');paths=[];radii=[]
    for ci in ids:P,rr=child(ci);paths.append(P);radii.append(rr)
    old.hide_render=True;old.hide_set(True);pilotObj=ad.make_native(old,paths,radii,'AFN41_A_PRIVATE_ACTUAL_PILOT');actual,rr=ad.read_native(pilotObj);f.flowcheck.cap.math_controls();pilot=f.flowcheck.check(actual,rr,tree,tri)
    (PVT/'a-pilot-body-contact.json').write_text(json.dumps({'actualChildIds':ids.tolist(),'proof':pilot},indent=2)+'\n')
    pilotObj.hide_render=True;pilotObj.hide_set(True);assert f.state()==retained
    if pilot['status']!='PASS_TESTED_STATIC_CAPSULES':
        save('a-build-summary.json',{'status':'STOP_REPRESENTATIVE_CHILD_BODY_FAILURE','pilot':{k:pilot[k] for k in ('status','curves','segments','unqualifiedSegments','minimumCertifiedClearanceLowerBoundM','minimumSampledCVSurfaceGapM')},'fullGroomExpanded':False,'originalNonHairStateExact':True,'seconds':time.time()-start});print('R41_A_STOP',pilot['unqualifiedSegments'],time.time()-start,flush=True);return
    paths=[];radii=[]
    for ci in range(len(base)):P,rr=child(ci);paths.append(P);radii.append(rr)
    obj=ad.make_native(old,paths,radii,'AFN41_A_PRIVATE_ROOT_FRAME_FIBRES');actual,rr=ad.read_native(obj);obj.hide_render=True;assert f.state()==retained
    old.hide_render=False;old.hide_set(False);f.E=PVT;f.render('a-before');before=ch.review.extras('a-before',PVT);old.hide_render=True;old.hide_set(True);obj.hide_render=False;obj.hide_set(False);f.render('a-after');after=ch.review.extras('a-after',PVT);assert before==after
    for o in s.objects:
        if o.type=='CURVES' and o!=obj and o.name not in ('AFN36_L_BrowFibres','AFN36_R_BrowFibres'):o.hide_set(True)
    b.camera('face');s.camera.data.lens=85;s['AFN41_status']='PRIVATE_COMPLETE_PATH_GROOM_NOT_ADOPTED';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    np.savez_compressed(PVT/'a-lineage.npz',nearestGuide=nearest,childRootTriangles=bind['rootTriangles'],childRootBarycentric=bind['rootBarycentric'])
    save('a-build-summary.json',{'status':'COMPLETE_PRIVATE_GROOM_VISUAL_REVIEW_REQUIRED','output':str(OUT),'sha256':b.sha(OUT),'count':len(actual),'points':sum(map(len,actual)),'pilot':{k:pilot[k] for k in ('status','curves','segments','unqualifiedSegments','minimumCertifiedClearanceLowerBoundM','minimumSampledCVSurfaceGapM')},'fullGroomExpanded':True,'originalNonHairStateExact':True,'seconds':time.time()-start,'allChildSelfContinuousRuntime':'NOT_QUALIFIED'})
    print('R41_A_DONE',len(actual),time.time()-start,flush=True)

if __name__=='__main__':main()
