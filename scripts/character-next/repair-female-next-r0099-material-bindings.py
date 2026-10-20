"""Repair persisted material identity, not a new artistic construction.
Evaluated material IDs were not valid saved original IDs; bind canonical IDs
explicitly and restore the ineffective1.2% globe experiment to exact r98 data.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0099-continuous-head-neck';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0099-a-continuous-head-neck.blend';OUT=S/'aevrynd-female-next-r0099-a2-continuous-head-neck-materials.blend'
sp=importlib.util.spec_from_file_location('r99repair',Path(__file__).with_name('build-female-next-r0099-continuous-skin.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);q=m.q;v=m.v;v.E=E
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0098-b-native-artist-head.blend'));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();eyes={}
 for name in m.m.rig.native_names():
  if name=='AFN60_BODY_ORAL_AND_OCULAR_LINING':continue
  ob=bpy.data.objects[name];eyes[name]={'vertices':q.arr(ob.data.vertices,'co',len(ob.data.vertices),3).copy(),'keys':{k.name:q.arr(k.data,'co',len(k.data),3).copy() for k in ob.data.shape_keys.key_blocks}}
 body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];canonical=[x.name if x else None for x in body.data.materials];assert canonical[4]==canonical[5]=='AFN57_CANONICAL_SKIN'
 bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();ob=bpy.data.objects['AFN99_CONTINUOUS_RENDER_SKIN'];head=bpy.data.objects['AFN98_ORIGINAL_ARTIST_HEAD_AND_NECK_COLLAR'];z=np.load(E/'actual-interface-input.npz');material=np.r_[z['skinMaterial'],z['headMaterial']];assert len(material)==len(ob.data.polygons)
 for target in [ob,head]:
  target.data.materials.clear()
  for name in canonical:target.data.materials.append(bpy.data.materials[name] if name else None)
 ob.data.polygons.foreach_set('material_index',material);ob.data.update()
 for name,row in eyes.items():
  part=bpy.data.objects[name];part.data.vertices.foreach_set('co',row['vertices'].ravel())
  for key in part.data.shape_keys.key_blocks:key.data.foreach_set('co',row['keys'][key.name].ravel())
  part.data.update()
 bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);summary={'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'renderSkin':ob.name,'sameArtConstructionAsA':True,'repair':'Original canonical material IDs from retained master, not evaluated-ID references; explicitly correct both joined skin and hidden source-head saved slots. Original world shapes/weld/UV/pose inputs unchanged.','canonicalSavedMaterialSlots':canonical,'originalOpticalNativeAndAllShapeKeyDataRestoredExactly':True,'ineffectiveSourceGlobeScaleExperimentWithdrawn':True,'originalAWhiteFixturePreserved':True,'appearanceFunctionContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick};(E/'a2-build-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8');rows=[]
 for view in ['face','profile','oblique','body-face']:
  rows.append(v.image('a2-material-repair',view));(E/'a2-view-controls.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
 print('R99_MATERIAL_ID_REPAIR_COMPLETE_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
