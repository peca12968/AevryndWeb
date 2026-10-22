"""Actual native rest-surface corrective, baked into the same woman's shape keys.
Replaces local angular-only surface deformation by a bound differential rest
correction. No colour/UV/clearance edits; same exact source root anchors follow.
"""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0147-outer-lid-surface';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0146-source/aevrynd-female-next-r0146-a-connected-palpebral-lining.blend';OUT=S/'r0147-source/aevrynd-female-next-r0147-a-native-tarsal-corrective.blend'
sp=importlib.util.spec_from_file_location('r147restbase',Path(__file__).with_name('build-female-next-r0146-connected-lining.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;a.b.u.v.E=E
def save(n,x):h.E=E;h.save(n,x)
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[h.c.h.SKIN];rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];protected=a.a.protected();oldRaw={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};base=a.geometry(skin)[0];demo=rig.animation_data.action;slot=rig.animation_data.action_slot;rig.animation_data.action=None
 for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(0,0,0)
 for p in h.PROPS.values():rig[p]=0.
 rig.update_tag();bpy.context.view_layer.update();N=len(skin.data.vertices);left=h.values(skin.data.attributes['AFN146_BlinkAngle_L'].data,'value',N);right=h.values(skin.data.attributes['AFN146_BlinkAngle_R'].data,'value',N);mapping=h.values(skin.data.attributes['AFN146_ORIGINAL_VERTEX_ID'].data,'value',N,dtype='i4');weight=np.clip((abs(left)+abs(right))/.06,0,1);weight[mapping<0]=0;active=np.flatnonzero(weight>0);assert len(active)>100
 save('direct-native-tarsal-surface-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T02:52:50+00:00','action':'Create and bind native differential rest-surface corrective on actual outer eyelid Skin, then bake all16 side poses and transfer exact original triangle/barycentric anchor deltas to actual lash/wet islands. Keep source texture makeup rather than recolour it.','failedUVBindingPremiseRetired':'Normal map already names AngelicaOriginalUV; no candidate from that hypothesis.'})
 group=skin.vertex_groups.new(name='AFN147_NATIVE_OUTER_TARSAL_CORRECTION')
 for i in active:group.add([int(i)],float(weight[i]),'REPLACE')
 md=skin.modifiers.new('AFN147_BOUND_REST_TARSAL_SURFACE','CORRECTIVE_SMOOTH');md.vertex_group=group.name;md.rest_source='BIND';md.smooth_type='LENGTH_WEIGHTED';md.factor=1.;md.iterations=8;md.use_only_smooth=False;md.use_pin_boundary=True;bpy.context.view_layer.objects.active=skin;skin.select_set(True);bpy.ops.object.correctivesmooth_bind(modifier=md.name);assert md.is_bind
 construction=json.loads((E.parent/'r0146-connected-palpebral-lining/connected-palpebral-lining-construction.json').read_text('utf-8'));attachments=construction['actualAttachments'];records=[];deltas={};raws={}
 for side in ['L','R']:
  for k in range(1,9):
   for s,p in h.PROPS.items():rig[p]=k/8 if s==side else 0.
   rig.update_tag();md.show_viewport=False;bpy.context.view_layer.update();old=a.geometry(skin)[0];md.show_viewport=True;bpy.context.view_layer.update();new=a.geometry(skin)[0];delta=new-old;assert np.isfinite(new).all();key='AFN146_'+side+'_LAMELLAR_%02d'%k;raws[key]=h.values(skin.data.shape_keys.key_blocks[key].data,'co',N,3);B=np.array(skin.matrix_world);inv=np.linalg.inv(B);local=(np.c_[new,np.ones(N)]@inv.T)[:,:3];md.show_viewport=False;skin.data.shape_keys.key_blocks[key].data.foreach_set('co',local.astype('f4').ravel());skin.data.update();attachmentReports={}
   for name,report in attachments.items():
    ob=bpy.data.objects[name];block=ob.data.shape_keys.key_blocks[key];P=h.values(block.data,'co',len(block.data),3).astype('f8');Ai=np.linalg.inv(np.array(ob.matrix_world)[:3,:3]);maxShift=0
    for anchor in report['anchors']:
     ids=anchor['vertices'];tri=anchor['actualNewSkinTriangleVertices'];bc=np.array(anchor['barycentric']);shift=bc@delta[tri];P[ids]+=shift@Ai.T;maxShift=max(maxShift,float(np.linalg.norm(shift)))
    block.data.foreach_set('co',P.astype('f4').ravel());ob.data.update();attachmentReports[name]={'sameOriginalAnchors':len(report['anchors']),'maximumIslandTranslationM':maxShift}
   deltas[key]=delta[active].astype('f4');records.append({'side':side,'alpha':k/8,'actualSkinMaximumCorrectiveM':float(np.linalg.norm(delta,axis=1).max()),'outerActiveMaximumCorrectiveM':float(np.linalg.norm(delta[active],axis=1).max()),'sameOriginalAttachmentAnchorTransfer':attachmentReports})
 skin.modifiers.remove(md);skin.vertex_groups.remove(group)
 for p in h.PROPS.values():rig[p]=0.
 rig.animation_data.action=demo;rig.animation_data.action_slot=slot;scene.frame_set(1);rig.update_tag();bpy.context.view_layer.update();assert np.linalg.norm(a.geometry(skin)[0]-base,axis=1).max()<2e-6
 checks=[]
 for f in range(1,18):
  scene.frame_set(f);bpy.context.view_layer.update();W,T=a.geometry(skin);area=np.linalg.norm(np.cross(W[T[:,1]]-W[T[:,0]],W[T[:,2]]-W[T[:,0]]),axis=1);row={'frame':f,'actualSkinZeroAreaTriangles':int(np.count_nonzero(area==0)),'minimumTwiceAreaM2':float(area.min()),'allFinite':bool(np.isfinite(W).all())};checks.append(row);save('actual-before-save-corrective-poses.json',checks);assert row['allFinite'] and row['actualSkinZeroAreaTriangles']==0,row
 scene.frame_set(1);bpy.context.view_layer.update();assert oldRaw=={n:a.rawsig(bpy.data.objects[n]) for n in oldRaw} and a.a.protected()==protected;assert max(r['actualSkinMaximumCorrectiveM'] for r in records)>1e-6
 np.savez_compressed(E/'native-tarsal-corrective-deltas.npz',activeOuterSkinIds=active,**deltas);save('native-tarsal-corrective-construction.json',{'source':str(SRC),'method':'Native Blender bound rest differential Corrective Smooth, length-weighted, factor1,8iterations; baked actual evaluated surface into existing16 native relative keys, no modifier remains. Single structural method, no sweep.','activeOuterSkinVertices':len(active),'newLiningIntentionallyExcludedFromCorrectionGroup':True,'actualCorrectionPoses':records,'preSave17ActualSkinChecks':checks,'rawGeometryUVOriginalMaterialAndTexturesUntouched':True,'attachmentAnchors':'Exact r146 stored original triangle IDs/barycentrics/islands; per-island corrective translations added to existing native key, not re-guessed roots.','scope':'Engineering rest-surface correction, not full anatomical muscle/skin simulation, finite-thickness or contact acceptance. Existing original finite/self/continuous failures/unaccepted scope remain.'})
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);save('a-build-summary.json',{'source':str(SRC),'comparisonBaseline':str(S/'r0139-source/aevrynd-female-next-r0139-a-native-lid-follow.blend'),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':rig.name,'actualControllers':h.PROPS,'originalGazeAction':'AFN138_NATIVE_CURRENT_GAZE_DEMO','newBlinkDemoAction':'AFN144_ACTUAL_CURRENT_SKIN_BLINK_DEMO','oneCompleteCandidate':True,'completeAppearanceOperationContactRuntimeUnaccepted':True,'secondsBeforePreview':time.time()-tick})
 views=[]
 for v in ['face','body-face','profile','oblique','back']:views.append(a.b.u.v.image('a-native-tarsal-corrective',v));save('a-view-controls.json',views)
 motion=[]
 for f in [5,9,13,17]:
  scene.frame_set(f);bpy.context.view_layer.update()
  for v in ['face','body-face']:
   row=a.b.u.v.image('blink-%03d'%f,v);row['actualBlink']={s:float(rig[p]) for s,p in h.PROPS.items()};motion.append(row);save('actual-blink-motion-controls.json',motion)
 scene.frame_set(9);bpy.context.view_layer.update();save('actual-closed-profile-control.json',a.b.u.v.image('closed-blink','profile'));scene.frame_set(1);bpy.context.view_layer.update();print('R147_ACTUAL_NATIVE_TARSAL_CORRECTIVE_COMPLETE_HEAD_BODY_BLINK_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
