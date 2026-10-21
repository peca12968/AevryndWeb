"""Independent actual complete groom layer/joint/frame operations and restoration."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0137-complete-studio-groom';S=R/'engine/assets/characters/female-next/source'
def module(n,f):sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
a=module('r137verifybase','build-female-next-r0116-native-eye-character.py');b=a.b;q=a.q;sign=module('r137sign','build-female-next-r0131-native-hair-material.py')
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def geom(o):return q.hair(o).copy() if o.type=='CURVES' else b.u.b.geom(o)[1].copy()
def snapshot(objects):return {o.name:geom(o) for o in objects}
def hashes(rows):return {n:a.hasharray(P) for n,P in rows.items()}
def main():
 tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend'));protected=a.protected();mats={m.name:sign.signature(m) for m in bpy.data.materials};result={}
 for tag in ['a','b']:
  s=json.loads((E/(tag+'-build-summary.json')).read_text('utf-8'));src=Path(s['output']);assert a.sha(src)==s['sha256'];bpy.ops.wm.open_mainfile(filepath=str(src));assert a.protected()==protected;assert {m.name:sign.signature(m) for m in bpy.data.materials if m.name in mats}==mats;skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];_,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();assert [a.hasharray(W),a.hasharray(T)]==s['currentSkinHashes'];objects=[bpy.data.objects[n] for n in s['renderObjects']];assert all(not o.hide_render for o in objects);base=snapshot(objects);before=hashes(base);hinge=bpy.data.objects[s['actualPonyControl']];frame=bpy.data.objects[s['actualWholeHairFrame']];old=hinge.rotation_euler.copy();hinge.rotation_euler.x+=.12;bpy.context.view_layer.update();moved=snapshot(objects);op={};ponyNames={'AFN137_CORE_PONY','AFN137_NATIVE_PONY_FIBRES','AFN137_OWN_FINITE_PONY_TIE'}
  for name,P in moved.items():
   delta=float(np.linalg.norm(P-base[name],axis=1).max());op[name]=delta
   if name in ponyNames:assert delta>1e-6
   else:assert np.array_equal(P,base[name])
  hinge.rotation_euler=old;bpy.context.view_layer.update();assert hashes(snapshot(objects))==before
  old=frame.location.copy();frame.location.x+=.001;bpy.context.view_layer.update();moved=snapshot(objects);frameDelta={n:float(np.linalg.norm(P-base[n],axis=1).max()) for n,P in moved.items()};assert all(.00099<x<.00101 for x in frameDelta.values());frame.location=old;bpy.context.view_layer.update();assert hashes(snapshot(objects))==before
  raw=q.arr(skin.data.vertices,'co',len(skin.data.vertices),3);edit=raw.copy();j=int(W[:,2].argmax());edit[j,2]+=.0002;skin.data.vertices.foreach_set('co',edit.ravel());skin.data.update();bpy.context.view_layer.update();coupling={n:float(np.linalg.norm(P-base[n],axis=1).max()) for n,P in snapshot(objects).items()};skin.data.vertices.foreach_set('co',raw.ravel());skin.data.update();bpy.context.view_layer.update();assert hashes(snapshot(objects))==before;_,WW,TT=b.u.b.geom(skin);assert np.array_equal(WW,W) and np.array_equal(TT,T) and protected==a.protected();assert all(x==0 for x in coupling.values())
  b.u.v.image.__globals__['m'].rig.shade.settings();b.u.v.image.__globals__['m'].rig.k.b.camera('profile');assert bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].hide_render
  if tag=='b':assert bpy.data.objects['AFN137_NATIVE_FRONT_BACK_LOOSE_FIBRES'].hide_render
  textures=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file and im.filepath:
    p=Path(bpy.path.abspath(im.filepath));assert p.is_file();textures.append({'relative':im.filepath,'absolute':str(p),'bytes':p.stat().st_size,'sha256':a.sha(p)})
  assert a.sha(src)==s['sha256'];result[tag]={'source':str(src),'sha256':s['sha256'],'bytes':src.stat().st_size,'independentlyReopened':True,'actualLayerGeometryHashes':before,'actualPonyJointRotationRadians':.12,'actualPonyJointLayerMaxMovementM':op,'protectedNonPonyLayerUnchangedDuringJoint':True,'actualWholeHairFrameTranslationM':.001,'actualWholeHairFrameLayerMaxMovementM':frameDelta,'currentVisibleSkinVertex':j,'currentVisibleSkinVertexEditM':.0002,'currentSkinDeformCouplingMaxM':coupling,'currentHeadDeformAttachmentAbsent':True,'actualSkinLayersControlsAndHiddenRollbackRestoredExactly':True,'allOriginalMaterialGraphsExact':True,'originalHairAndFailedAFrontRemainHiddenAfterRenderSetup':True,'allReferencedExternalTextures':textures,'newCompleteUsableOperationAccepted':False,'naturalMotionFiniteSelfContinuousContactRuntimeAccepted':False};save('minimum-saved-complete-groom-readback.json',{'sources':result,'scope':'Actual current complete groom layer rigid joint and frame editing/restoration only, not native source rig, body/head deformation attachment or natural motion/finite contact/runtime. Source-cache sampling not exact original renderer occupancy.','seconds':time.time()-tick})
 print('R137_BOTH_COMPLETE_GROOM_SOURCES_REOPEN_ACTUAL_JOINT_FRAME_RESTORE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
