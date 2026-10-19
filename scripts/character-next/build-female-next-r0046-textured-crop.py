"""Complete short textured crop from absolute independent scalp-root paths.

New cut/length/layer construction on the same person, not offsets of the old
bob or transfer of an artist groom. Each native strand gets an independent
surface track and three-dimensional lift/free-tip section. No simulation claim.
"""
import bpy,importlib.util,json,time,sys,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('crop46source',Path(__file__).with_name('inspect-female-next-r0043-ocular-junction.py'));i=importlib.util.module_from_spec(sp);sp.loader.exec_module(i)
b=i.b;f=i.f;v=i.v;R=b.R;S=b.S;E=R/'Evidence/character-female-next/r0046-textured-crop';E.mkdir(exist_ok=True)
SRC=S/'aevrynd-female-next-r0042-b-shadow-quality-review.blend';OUT=S/'aevrynd-female-next-r0046-a-textured-short-crop.blend';PILOT='--pilot' in sys.argv
old=f.flowcheck.module('contacts37r46','verify-female-next-r0037-eye-margin.py');live=f.flowcheck.module('guides38r46','build-female-next-r0038-live-groom.py')
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def norm(v):return v/max(np.linalg.norm(v),1e-30)
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def path(root,index,part,tree,V,T):
    hit,n,tid,d=tree.find_nearest(Vector(root));foot=np.array(hit);N=np.array(n);h0=float(np.linalg.norm(root-foot));tri=V[T[tid]];co=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),foot-tri[0],rcond=None)[0];bc=np.array((1-co.sum(),co[0],co[1]));assert bc.min()>-1e-3
    crown=float(smooth((root[2]-1.520)/.045));front=float(smooth((-root[1]-.027)/.065));nape=float(1-smooth((root[2]-1.465)/.035));wave=np.sin(root[0]*173+root[1]*211)+.5*np.sin(root[2]*431+root[0]*127);rnd=np.random.default_rng(index+460000);fine=float(rnd.uniform(-1,1));length=(.010+.030*crown+.012*front*(1-nape)+.005*(1-crown)*(1-nape))*(1+.105*wave+.025*fine);lift=(.0020+.0045*crown)*(1+.16*wave);tip=(.0008+.0016*crown)*(1+.15*fine);phase=float(rnd.uniform(0,2*np.pi));positions=[root.copy()];q=foot.copy();ds=length/32;lastN=N.copy()
    for step in range(1,33):
        t=step/32
        # Planned growth zones: parted crown to side/back, divided front fringe,
        # short temple/ear contour and tapered nape. Absolute rest paths only.
        direction=np.array((part*(.35+.55*front),.65*(1-front)+.25,-.65*(1-crown)-.18*front));direction-=lastN*(direction@lastN)
        if np.linalg.norm(direction)<1e-6:direction=np.cross(lastN,(0,1,0))
        direction=norm(direction);qh,qn,_,_=tree.find_nearest(Vector(q+direction*ds));q=np.array(qh);lastN=norm(np.array(qn));side=norm(np.cross(lastN,direction));height=h0+lift*np.sin(np.pi*t)*np.sqrt(t)+tip*t*t;lateral=(.00012*np.sin(phase+3*np.pi*t)+.00005*fine)*t*t
        if index%137==0:height+=.0008*t**3
        positions.append(q+lastN*height+side*lateral)
    # Piecewise-linear resampling preserves the actual authored path geometry.
    # It also matches retained native128-point guide-control indexing.
    P=np.array(positions);s=np.linspace(0,1,len(P));out=np.column_stack([np.interp(np.linspace(0,1,128),s,P[:,j]) for j in range(3)]);out[0]=root
    region=0 if front>.6 and crown>.3 else 1 if crown>.5 else 4 if nape>.5 else 2 if abs(root[0])>.045 else 3
    return out,{'bodyTriangle':int(tid),'barycentric':bc.tolist(),'surfaceM':foot.tolist(),'rootOffsetWorldM':(root-foot).tolist(),'normal':N.tolist(),'targetCutLengthM':length,'region':region,'outerLayer':bool(wave>0),'maximumPlannedLiftM':lift+tip}
def main():
    tick=time.time();assert b.sha(SRC)=='d62c180a5af61f6f8d800926b101738c89a8fbe7785fe1054fd655fd018824da';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4;before=f.state();hair=bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'];local,rr=v.hair_arrays(hair);mx=np.array(hair.matrix_world);P=local.astype('f8')@mx[:3,:3].T+mx[:3,3];rad=rr.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2);V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=i.i.tree(V,T);parts=np.load(S/'aevrynd-female-next-r0033-c-bob-fibres.npz')['parts'];bind=np.load(S/'aevrynd-female-next-r0038-b-live-guide-bindings.npz');ids=bind['guideRootIds'];which=ids if PILOT else np.arange(len(P));paths=[];records=[]
    save('round-contract.json',{'revision':'female-next-r0046-a','previousGoalTurnClassification':'r44/r45 eye production produced verified rejection evidence and no whole-character appearance improvement; r45 history pushed38dd883','source':str(SRC),'sourceSha256':b.sha(SRC),'majorDefects':['Cap/sheet bob silhouette and uniform cut','Staring eyes with no accepted expressive motion','Flat skin response'],'chosenDefect':'Complete hairstyle silhouette and strand hierarchy','hypothesis':'A deliberately different short textured crop with independent crown/front/temple/ear/nape lengths and absolute3D paths can remove the current long hanging curtains and expose a readable layered silhouette on the same complete head','styleChangeExplicit':'New short-hair alternative. Does not fix/validate old bob, anatomy or hair dynamics. No hair-length requirement was specified; retain old source for comparison.','method':'Independent actual-scalp surface tracks, region-planned variable cut lengths,3D lift and free tips, complete own12000fibres and retained256live native guide controls. No old-curtain delta strokes, artist-groom transfer or radial loft funnel.','cheapTest':'256actual guide-root strands with full finite segment/body capsules, followed by actual complete12000strand full-head/multiple-angle visual preview before expensive whole-groom gates','reject':['Fur/helmet/cap,sheets,spikes,bulges/wings or unconvincing complete haircut','Pilot body contact','Any root/radius/skin/lighting drift','Unqualified full displayed geometry body/optics/brow/lash/tissue/self contacts prevents corresponding adoption'],'candidateCount':1,'resources':{'startUTC':'2026-10-19 15:28:33 UTC','cumulativeResourceCheckpointUTC':'2026-10-19 15:43:35 UTC','threads':4,'heavyJobsAtOnce':1,'newNodeServers':0,'memoryPolicy':'One foreground-free Blender process, bounded12000x128native fibres; do not start unbounded contact hash or concurrent heavy jobs'},'reference':'Visual short-cut silhouettes only; no remote pixels/groom data imported. Existing own scalp/body and CC0 skin only.','scope':'Static neutral haircut authoring; no head binding in motion,wind/dynamics/continuous contacts or engine acceptance'})
    if not PILOT:
        proof=json.loads((E/'pilot-body-contact.json').read_text());assert proof['status']=='PASS_TESTED_STATIC_CAPSULES'
    for count,ci in enumerate(which):
        pp,record=path(P[ci,0],int(ci),int(parts[ci]),tree,V,T);paths.append(pp);record['curve']=int(ci);records.append(record)
        if count%1000==0:print('R46_PATHS',count,len(which),time.time()-tick,flush=True)
    W=np.array(paths);rads=rad[which];save('pilot-root-bindings.json' if PILOT else 'a-root-bindings.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'bodyTriangleCount':len(T),'roots':records,'scope':'Current actual static body triangle/barycentric root offset, not deforming-skin binding or physics'});np.savez_compressed(E/('pilot-paths.npz' if PILOT else 'a-complete-paths.npz'),positionsWorld=W,radiiWorld=rads,curveIds=which)
    if PILOT:
        proof=old.v.g.check(W,rads,tree,V[T]);save('pilot-body-contact.json',proof);print('R46_PILOT_CONTACT',proof['status'],proof['unqualifiedSegments'],time.time()-tick,flush=True);return
    newlocal=((W-mx[:3,3])@np.linalg.inv(mx[:3,:3]).T).astype('f4');newlocal[:,0]=local[:,0];hair.data.position_data.foreach_set('vector',newlocal.ravel());regions=np.array([r['region'] for r in records],dtype='i4');outer=np.array([r['outerLayer'] for r in records],dtype='i4')
    for name,values in [('AFN46_Region',regions),('AFN46_OuterLayer',outer)]:
        att=hair.data.attributes.get(name) or hair.data.attributes.new(name,'INT','CURVE');att.data.foreach_set('value',values)
    hair['AFN46_style']='Own complete short textured crop, static authoring candidate';hair['AFN46_regions']='0front fringe,1crown,2temple,3ear/back transition,4nape; inner/outer attributes are authoring labels, not simulation/rig'
    for name in [live.GUIDE,live.REST]:
        o=bpy.data.objects[name];gm=np.array(o.matrix_world);gp=((W[ids]-gm[:3,3])@np.linalg.inv(gm[:3,:3]).T).astype('f4');o.data.position_data.foreach_set('vector',gp.ravel());o['AFN46_scope']='Current crop rest controls; same native3neighbor delta authoring. Edits require revalidation; no dynamics.'
    bpy.context.view_layer.update();ev,er=live.eval_arrays(hair);assert np.array_equal(ev,newlocal) and np.array_equal(er,rr);after=f.state();assert after['meshes']==before['meshes'] and after['materials']==before['materials'] and after['skinFields']==before['skinFields'] and after['stage']==before['stage'];assert all(after['curves'][n]==x for n,x in before['curves'].items() if n!=hair.name);assert np.array_equal(ev[:,0],local[:,0]);s['AFN46_status']='COMPLETE_SHORT_GROOM_CANDIDATE_REQUIRES_VISUAL_AND_CONTACT_REVIEW';b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'originalUnrelatedMeshSkinMaterialsStageExact':True,'all12000RootPositionsAndNativeRadiiExact':True,'nativeCurves':len(W),'nativePointsPerCurve':128,'guideCount':len(ids),'guideRestReadbackExact':True,'regionCounts':{str(k):int((regions==k).sum())for k in np.unique(regions)},'newLengthsM':{'min':float(np.linalg.norm(np.diff(W,axis=1),axis=2).sum(1).min()),'max':float(np.linalg.norm(np.diff(W,axis=1),axis=2).sum(1).max())},'staticOnly':True,'seconds':time.time()-tick})
    f.E=E;f.render('a-after',('face','oblique','profile'));i.ch.review.extras('a-after',E);print('R46_COMPLETE_PREVIEW',time.time()-tick,flush=True)
if __name__=='__main__':main()
