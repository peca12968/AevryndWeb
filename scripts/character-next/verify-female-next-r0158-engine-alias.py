"""Finish only unresolved alias readback; avoid stale RNA after file reopen."""
from pathlib import Path
import bpy,json,importlib.util,numpy as np,time
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0158-shared-native-skin'
sp=importlib.util.spec_from_file_location('r158alias',C/'scripts/character-next/build-female-next-r0158-shared-native-skin.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
def deps():
 out=[]
 for lib in bpy.data.libraries:
  p=Path(bpy.path.abspath(lib.filepath)).resolve();assert p.is_file();out.append({'kind':'library','file':str(p),'sha256':a.a.sha(p)})
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   p=Path(bpy.path.abspath(im.filepath,library=im.library)).resolve();assert p.is_file();out.append({'kind':'texture','file':str(p),'sha256':a.a.sha(p)})
 assert len(out)==17;return out
tick=time.time();b=json.loads((E/'b-build-summary.json').read_text());q=json.loads((E/'independent-native-source-readback.json').read_text());before=[]
for path in [b['output'],b['engineAlias']]:
 assert a.a.sha(Path(path))==b['sha256'];bpy.ops.wm.open_mainfile(filepath=path);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();ob=bpy.data.objects[b['actualSkin']];V,T=a.geometry(ob);d=deps();before.append({'path':path,'geometryHashes':[a.a.hasharray(V),a.a.hasharray(T)],'materialSlots':[m.name if m else None for m in ob.data.materials],'dependencies':d})
assert before[0]['geometryHashes']==before[1]['geometryHashes'];assert before[0]['materialSlots']==before[1]['materialSlots']==q['effectiveMaterialSlotsPersisted'];assert sorted(x['sha256'] for x in before[0]['dependencies'])==sorted(x['sha256'] for x in before[1]['dependencies']);h.save('independent-engine-alias-readback.json',{'physicalAndAliasReopened':before,'sourceSha256':b['sha256'],'sameActualNeutralSkinAndTriangles':True,'sameEffectiveMaterials':True,'sameAll17DependencyHashes':True,'filesNotModified':True,'originalReadbackFailure':'Original93012 completed physical operations and contact evidence, then failed only at removed old Skin RNA reference after alias reopen. Original script/log retained. This script resolves only that alias comparison.','elapsedSeconds':time.time()-tick});print('R158_INDEPENDENT_PHYSICAL_AND_ENGINE_ALIAS_REOPEN_DONE',time.time()-tick,flush=True)
