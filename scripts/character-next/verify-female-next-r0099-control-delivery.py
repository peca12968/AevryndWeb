"""Prove control delivery before interpreting zero movement as model failure.
Temporarily detach control actions, tag driver inputs, inspect actual source
body/full-skin deformation, and render delivered blink/jaw. Never save edits.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0099-continuous-head-neck';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r99delivery',Path(__file__).with_name('verify-female-next-r0099-saved-motion.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);q=m.q
def save(x):(E/'evaluated-control-delivery.json').write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def main():
 tick=time.time();ref=json.loads((E/'c-build-summary.json').read_text('utf8'));m.h.open_file(Path(ref['output']));s=bpy.context.scene;face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS'];controls=[face,oral];actions={o.name:o.animation_data.action if o.animation_data else None for o in controls};props={o.name:{k:o[k] for k in (['blink_left','blink_right'] if o==face else ['jaw_open'])} for o in controls}
 for o in controls:
  if o.animation_data:o.animation_data.action=None
 skin=bpy.data.objects[ref['renderSkin']];body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];originalSkin=bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING'];cut=originalSkin.modifiers['AFN98_REPLACE_OUTER_HEAD_REGION_ONLY'];cutState=cut.show_viewport;cut.show_viewport=False;hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];base=None;rows=[]
 for i,(name,blink,jaw) in enumerate([('neutral',0.,0.),('blink-delivered',1.,0.),('jaw-delivered',0.,.35),('neutral-restore',0.,0.)]):
  face['blink_left']=face['blink_right']=blink;oral['jaw_open']=jaw
  for o in controls:o.update_tag()
  for name0 in m.m.rig.native_names():
   ob=bpy.data.objects[name0];ob.update_tag();ob.data.shape_keys.update_tag()
  bpy.context.view_layer.update();V,T=m.geom(skin);BV,_=m.geom(body);SV,_=m.geom(originalSkin);HP=q.hair(hair).reshape(24800,17,3)
  if base is None:base=(V.copy(),BV.copy(),SV.copy(),HP.copy())
  delta=lambda a,b:float(np.linalg.norm(a-b,axis=1).max()) if a.shape==b.shape else None
  row={'state':name,'assignedBlink':blink,'assignedJaw':jaw,'evaluatedBlinkLeft':float(face.evaluated_get(bpy.context.evaluated_depsgraph_get())['blink_left']),'evaluatedJaw':float(oral.evaluated_get(bpy.context.evaluated_depsgraph_get())['jaw_open']),'originalBodyMaximumWorldDisplacementM':delta(BV,base[1]),'originalFullDisplayedSkinMaximumWorldDisplacementM':delta(SV,base[2]),'newActualContinuousSkinMaximumWorldDisplacementM':delta(V,base[0]),'allActualRootsMaximumWorldErrorM':m.root_error(hair,V),'finite':bool(np.isfinite(V).all() and np.isfinite(HP).all()),'nativeDrivenNonzeroKeys':{n:{k.name:float(k.value) for k in bpy.data.objects[n].data.shape_keys.key_blocks if k.value!=0 and 'AFN74' in k.name} for n in m.m.rig.native_names()}}
  if i in [1,2]:
   m.m.rig.shade.settings();m.m.rig.k.b.camera('oblique');s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=320;s.cycles.samples=8;s.render.hair_subdiv=3;s.render.filepath=str(E/('delivered-control-%02d.png'%i));bpy.context.view_layer.update();bpy.ops.render.render(write_still=True);row['file']=s.render.filepath
  rows.append(row);save({'source':ref['output'],'sourceSha256':ref['outputSha256'],'priorPropertyOnlyProbeDidNotProveEvaluatedInputDelivery':True,'controlActionsDetachedOnlyInUnsavedVerificationScene':True,'states':rows,'completeOperationOrContactAccepted':False})
 cut.show_viewport=cutState
 for o in controls:
  for key,val in props[o.name].items():o[key]=val
  if o.animation_data:o.animation_data.action=actions[o.name]
  o.update_tag()
 s.frame_set(1);bpy.context.view_layer.update();save({'source':ref['output'],'sourceSha256':ref['outputSha256'],'priorPropertyOnlyProbeDidNotProveEvaluatedInputDelivery':True,'controlActionsDetachedOnlyInUnsavedVerificationScene':True,'states':rows,'temporaryControlsAndCutRestoredNoModelSaved':True,'originalControlActionsRestored':True,'seconds':time.time()-tick,'completeOperationOrContactAccepted':False});print('R99_EVALUATED_CONTROL_DELIVERY_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
