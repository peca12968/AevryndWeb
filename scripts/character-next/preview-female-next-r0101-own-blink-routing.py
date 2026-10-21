"""Prove and remove the legacy body blink from the new lid boundary.
Unsaved routing preview first; preserve the complete current A2 file intact.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0101-articulated-eyelid-topology';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r101route',Path(__file__).with_name('build-female-next-r0098-native-head.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);q=m.q;v=m.v;v.E=E
def save(x):(E/'own-blink-routing-preview.json').write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def route():
 face=bpy.data.objects['AFN59_FACE_CONTROLS'];body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];freeze=bpy.data.objects.new('AFN101_LEGACY_SKIN_NEUTRAL_BLINK_INPUT',None);bpy.context.scene.collection.objects.link(freeze);freeze['blink_left']=freeze['blink_right']=0.;freeze['scope']='Only legacy original body skin blink inputs are held at their neutral0. Original keys/driver formulas remain; FaceControls continue to drive the new anatomical lids and attached lashes. Original immutable source is unchanged.';rows=[]
 for fc in body.data.shape_keys.animation_data.drivers:
  for var in fc.driver.variables:
   for target in var.targets:
    if target.id==face and target.data_path in ['["blink_left"]','["blink_right"]']:
     rows.append({'driverPath':fc.data_path,'variable':var.name,'originalObject':face.name,'replacementObject':freeze.name,'dataPath':target.data_path});target.id=freeze
 assert rows,'No legacy blink driver targets found';body.data.shape_keys.update_tag();body.update_tag();freeze.update_tag();return rows
def inputs(blink):
 face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS'];face['blink_left']=face['blink_right']=blink;oral['jaw_open']=0
 for ob in [face,oral]:ob.update_tag()
 for name in m.m.rig.native_names():ob=bpy.data.objects[name];ob.update_tag();ob.data.shape_keys.update_tag()
 bpy.data.objects['AFN101_EDITABLE_LID_AND_SOCKET_COMPONENT'].data.shape_keys.update_tag();bpy.context.view_layer.update()
def main():
 tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0101-a2-lash-attachment.blend'));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS']
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 control=bpy.data.objects['AFN99_ORIGINAL_CONTINUOUS_ARTIST_SKIN'];inputs(0);P0=q.geom(control)[1].copy();inputs(1);P1=q.geom(control)[1].copy();rows=route();inputs(1);P2=q.geom(control)[1].copy();err=float(np.linalg.norm(P2-P0,axis=1).max());assert err<4e-6,err;meta={'source':'aevrynd-female-next-r0101-a2-lash-attachment.blend','redirectedDriverTargets':rows,'legacyWholeSkinBlinkMaximumWorldMoveM':float(np.linalg.norm(P1-P0,axis=1).max()),'routedLegacySkinMaximumDifferenceFromNeutralM':err,'newLidActualEvaluatedBlinkLeft':float(face.evaluated_get(bpy.context.evaluated_depsgraph_get())['blink_left']),'originalSourcesAndKeysNotDeleted':True,'newSourceSaved':False,'scope':'Own new lid component receives blink; neutral legacy C outer boundary still receives head/body/oral controls. Not complete operation/contact acceptance.'};save(meta);meta['render']=v.image('a3-routing-preview-closed','face');meta['seconds']=time.time()-tick;save(meta);print('R101_OWN_BLINK_ROUTING_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
