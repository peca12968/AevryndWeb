"""One scoped diagnosis of saved neutral/source correspondence; no new shape candidate."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0115-native-continuous-neck';P=R/'engine/assets/characters/female-next/source/r0115-source/aevrynd-female-next-r0115-a-continuous-native-woman.blend'
sp=importlib.util.spec_from_file_location('r115state',Path(__file__).with_name('build-female-next-r0113-native-neck-character.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);q=b.q
bpy.ops.wm.open_mainfile(filepath=str(P));skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];raw=bpy.data.objects['AFN115_EDITABLE_CONNECTED_NATIVE_ADULT_SOURCE'];face=bpy.data.objects['AFN59_FACE_CONTROLS'];rows=[]
for name,ob in [('displayed',skin),('raw',raw)]:
    rows.append({'object':name,'shapeKeyValues':{k.name:k.value for k in ob.data.shape_keys.key_blocks},'showOnlyShapeKey':ob.show_only_shape_key,'activeShapeKeyIndex':ob.active_shape_key_index,'basisFirst':list(ob.data.shape_keys.key_blocks[0].data[0].co),'drivers':[{'path':x.data_path,'valid':x.driver.is_valid,'expression':x.driver.expression,'targets':[{'id':getattr(v.targets[0].id,'name',''),'path':v.targets[0].data_path} for v in x.driver.variables]} for x in ob.data.shape_keys.animation_data.drivers] if ob.data.shape_keys.animation_data else []})
samples=[];arrays={}
for label,value in [('neutral',0.),('half',.5),('closed',1.),('restored',0.)]:
    b.deliver(value);d,V,T=b.u.b.geom(skin);V=V.copy();arrays[label]=V
    samples.append({'state':label,'assigned':value,'actualKeys':{k.name:k.value for k in skin.data.shape_keys.key_blocks},'sourceKeys':{k.name:k.value for k in raw.data.shape_keys.key_blocks}})
for k in raw.data.shape_keys.key_blocks:k.value=0.
raw.data.shape_keys.update_tag();raw.update_tag();bpy.context.view_layer.update();d,V,T=b.u.b.geom(raw);V=V.copy();arrays['actualOriginalRawNeutral']=V
result={'objects':rows,'faceProps':{p:face[p] for p in ['blink_left','blink_right']},'samples':samples,'displayedNeutralAgainstActualOriginalSourceMaxM':float(np.linalg.norm(arrays['neutral']-V,axis=1).max()),'displayedHalfMotionMaxM':float(np.linalg.norm(arrays['half']-arrays['neutral'],axis=1).max()),'displayedClosedMotionMaxM':float(np.linalg.norm(arrays['closed']-arrays['neutral'],axis=1).max())}
(E/'saved-neutral-state-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');np.savez_compressed(E/'saved-neutral-state-diagnosis.npz',**arrays);print('R115_SAVED_NEUTRAL_SOURCE_DIAGNOSIS_DONE',json.dumps(result),flush=True)
