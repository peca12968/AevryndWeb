"""Reconstruct remaining actual upper anterior Skin bands, preserving qualified paths."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0183-upper-anterior-root-bands';OUT=C/'assets-source/aevrynd-character/female-next/r0183-source/aevrynd-female-next-r0183-a-upper-anterior-root-bands.blend'
sp=importlib.util.spec_from_file_location('r183base',C/'scripts/character-next/build-female-next-r0180-anatomical-lash-rows.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def unit(v):return v/max(np.linalg.norm(v),1e-15)
def main():
 tick=time.time();t=json.loads((E/'before.json').read_text());assert not OUT.exists() and a.a.sha(Path(t['source']))==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];lash=bpy.data.objects['AFN182_ACTUAL_ANTERIOR_SKIN_ROOTED_LASHES'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(skin);actual0,off=m.m.curveworld(lash);P=h.arr(lash.data.position_data,'vector',len(lash.data.position_data),3).reshape(436,17,3).copy();line=np.load(E.parent/'r0182-anterior-surface-root-band/corrected-anterior-root-band-lineage.npz');rootT=line['rootTriangles'].copy();BC=line['rootBC'].copy();preserve=set(map(int,line['changedCurveIDs']));records=json.loads((E.parent/'r0180-anatomical-lash-rows/direct-anatomical-lash-authoring.json').read_text())['actualRootAndGrowthRecords'];domains=json.loads((R/'Evidence/character-female-next/r0139-native-lid-follow/native-lid-follow-construction.json').read_text('utf-8-sig'))['actualSourceNativeDomains'];centres=json.loads((R/'Evidence/character-female-next/r0138-native-current-gaze/native-current-gaze-construction.json').read_text('utf-8-sig'))['centersWorld'];skinTree=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True);eyeTrees=[]
 for name in a.MOVING:
  V,F=a.geometry(bpy.data.objects[name]);eyeTrees.append(BVHTree.FromPolygons(V.tolist(),F.tolist(),all_triangles=True))
 def hit(tree,x,z):return tree.ray_cast(Vector((float(x),-.20,float(z))),Vector((0,1,0)),.30)
 def section(x,z):
  sk=hit(skinTree,x,z);eyes=[hit(tree,x,z) for tree in eyeTrees];yy=[r[0][1] for r in eyes if r[0] is not None];eye=min(yy) if yy else None;visible=eye is not None and (sk[0] is None or sk[0][1]>eye+2e-6);return sk,eye,visible
 roots={i:line['rootWorld'][i].copy() for i in range(436)};newFace={};newBC={};boundaries=[];target=[r for r in records if r['lid']=='UPPER' and r['id'] not in preserve]
 for side,sign in [('L',1),('R',-1)]:
  ids=domains[side+'_UPPER']['actualSkinSeedIds'];lo,hi=abs(W[ids,0]).min(),abs(W[ids,0]).max();eye=np.array(centres[side])
  for rec in [r for r in target if r['side']==side]:
   cid=rec['id'];x=float(sign*(lo+rec['u']*(hi-lo)));zg=np.linspace(eye[2]-.006,eye[2]+.010,161);visible=np.array([section(x,z)[2] for z in zg]);vv=np.flatnonzero(visible);assert len(vv),('No actual Eye-visible section',cid,side,x);j=int(vv[-1]);assert j<len(zg)-1;low,high=float(zg[j]),float(zg[j+1])
   for _ in range(16):
    mid=(low+high)*.5
    if section(x,mid)[2]:low=mid
    else:high=mid
   trace=[]
   for z in np.linspace(high+.00001,high+.0035,71):
    sk,ey,vis=section(x,z)
    if sk[0] is not None and not vis:trace.append(np.array(sk[0]))
   assert len(trace)>2;trace=np.array(trace);arc=np.r_[0,np.linalg.norm(np.diff(trace,axis=0),axis=1).cumsum()];distance=.00050+.00025*rec['row'];assert arc[-1]>distance;z=float(np.interp(distance,arc,trace[:,2]));sk,ey,vis=section(x,z);assert sk[0] is not None and not vis;fi=int(sk[2]);B=W[T[fi]];v=np.linalg.lstsq(np.column_stack((B[1]-B[0],B[2]-B[0])),np.array(sk[0])-B[0],rcond=None)[0];bc=np.clip(np.array([1-v.sum(),*v]),0,1);bc/=bc.sum();root=bc@B;roots[cid]=root;newFace[cid]=fi;newBC[cid]=bc;boundaries.append({'id':cid,'side':side,'row':rec['row'],'u':rec['u'],'actualIntendedX':x,'actualUpperEyeVisibleTransitionZ':high,'surfaceArcDistanceM':distance,'actualSkinTriangle':fi,'rootWorld':root.tolist(),'eyeFirstHitYAtRoot':ey,'skinBeforeEyeDistanceM':float(ey-root[1]) if ey is not None else None,'actualFirstAnteriorSkinHit':True,'notRenderVisibilityOrClinicalFollicleProof':True})
 changes=[]
 for side in ['L','R']:
  eye=np.array(centres[side])
  for row in range(4):
   members=sorted([r for r in records if r['side']==side and r['lid']=='UPPER' and r['row']==row],key=lambda r:r['u']);positions=np.array([roots[r['id']] for r in members]);tangents=np.gradient(positions,axis=0)
   for j,rec in enumerate(members):
    cid=rec['id']
    if cid in preserve:continue
    root=roots[cid];fi=newFace[cid];B=W[T[fi]];normal=unit(np.cross(B[1]-B[0],B[2]-B[0]));initial=unit(.75*normal+.25*unit(root-eye)+(.12+.22*rec['u'])*unit(tangents[j]));curl=unit(np.array([0,0,1])-initial*initial[2]);length=rec['arcLengthM'];angle=rec['totalCurlAngleRadians'];k=angle/length;arc=np.linspace(0,length,17);P[cid]=root+normal*.000032+np.sin(k*arc)[:,None]/k*initial+(1-np.cos(k*arc))[:,None]/k*curl;rootT[cid]=T[fi];BC[cid]=newBC[cid];changes.append({'id':cid,'side':side,'row':row,'oldRoot':line['rootWorld'][cid].tolist(),'newRoot':root.tolist(),'rootMovementM':float(np.linalg.norm(root-line['rootWorld'][cid])),'newSkinTriangle':fi,'wholePathReauthored':True,'lengthAndCurlUnchanged':True})
 changed=np.array(sorted(newFace),'i4');unchanged=np.setdiff1d(np.arange(436),changed);assert len(changed)==241 and len(preserve)==39;B=W[rootT];root=(B*BC[:,:,None]).sum(1);ax=B[:,1]-B[:,0];ax/=np.linalg.norm(ax,axis=1,keepdims=True);az=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);az/=np.linalg.norm(az,axis=1,keepdims=True);basis=np.stack((ax,np.cross(az,ax),az),axis=2);local=np.einsum('bni,bij->bnj',P-root[:,None],basis);oldData=lash.data;d=oldData.copy();d.name='AFN183_COMPLETE_UPPER_ANTERIOR_ROOT_BANDS_DATA';lash.data=d;lash.name='AFN183_ACTUAL_UPPER_ANTERIOR_ROOTED_LASHES';d.position_data.foreach_set('vector',P.ravel());d.attributes['AFN182_FOLLICLE_ID'].name='AFN183_FOLLICLE_ID'
 for j in range(3):
  vals=h.arr(oldData.attributes['AFN149_SkinVertex'+str(j)].data,'value',436*17,dtype='i4').reshape(436,17);vals[changed]=rootT[changed,j,None];d.attributes['AFN149_SkinVertex'+str(j)].data.foreach_set('value',vals.ravel())
 for name,new in [('AFN149_RootBarycentric',np.repeat(BC[:,None],17,axis=1)),('AFN149_RootLocal',local),('AFN149_RestWorld',P)]:
  vals=h.arr(oldData.attributes[name].data,'vector',436*17,3).reshape(436,17,3);vals[changed]=new[changed];d.attributes[name].data.foreach_set('vector',vals.ravel())
 d.update_tag();lash.update_tag();bpy.context.view_layer.update();actual,oo=m.m.curveworld(lash);newError=float(np.linalg.norm(actual.reshape(436,17,3)[changed]-P[changed],axis=2).max());unchangedError=float(np.linalg.norm(actual.reshape(436,17,3)[unchanged]-actual0.reshape(436,17,3)[unchanged],axis=2).max());assert newError<3e-6 and unchangedError==0;assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected};s.camera.data.type='PERSP';a.b.u.v.E=E;views=[a.b.u.v.image('a-upper-anterior-root-bands','face')]
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);save('a-build-summary.json',{'source':t['source'],'output':str(OUT),'engineAlias':str(R/'engine/assets/characters/female-next/source/r0183-source'/OUT.name),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':'AFN138_ACTUAL_CURRENT_GAZE_RIG','actualHair':lash.name,'originalLashesRetainedHiddenRollback':a.FIXED[2],'retainedSourceHair':a.FIXED[1],'nativeStrands':436,'points':len(actual),'completeWomanCandidates':1,'changedCompleteFibrePaths':len(changed),'preservedQualifiedInnerPaths':39,'preservedLowerPaths':156,'savedCameraType':'PERSP','unaccepted':True,'secondsBeforeOtherViews':time.time()-tick})
 np.savez_compressed(E/'upper-anterior-band-lineage.npz',rootTriangles=rootT,rootBC=BC,rootWorld=root,rootCentre=P[:,0],curveWorld=P,changedCurveIDs=changed,preservedInnerCurveIDs=np.array(sorted(preserve),'i4'));save('direct-upper-band-authoring.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':t['startedUTC'],'changedFailedPremise':'Actual independently located left/right anterior Skin/Eye section bands replace remaining unqualified front-nearest/crease root placements. Source u maps to each real skin margin span, not mirrored coordinates or collapsed rootWorld.241 full paths rebuilt,39 previously reconstructed innerL and156 lower complete paths/fields/evaluated geometry preserved exactly. No scalar sweep or change of optics/count/radius/gaze.','actualSurfaceSectionRecords':boundaries,'actualFullPathChanges':changes,'newPathMaximumConstructionErrorM':newError,'unchanged195EvaluatedPathsMaximumM':unchangedError,'allOriginalSevenRawMeshUVSignaturesRetained':True,'anatomicalConstructionNotFullFiniteContactAcceptance':True})
 for v in ['body-face','profile','back','oblique']:views.append(a.b.u.v.image('a-upper-anterior-root-bands',v));save('upper-band-preview-controls.json',views)
 m.E=E;save('upper-band-eye-capture-controls.json',m.eye_image('a-upper-anterior-root-bands-eyes',str(OUT)));print('R183_ACTUAL_REMAINING_UPPER_BANDS_COMPLETE_WOMAN_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
