from pathlib import Path
import bpy,numpy as np,json,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0155-native-blink'
sp=importlib.util.spec_from_file_location('r155inspect',Path(__file__).with_name('build-female-next-r0155-margin-blink.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;b=json.loads((E/'b-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;rig=bpy.data.objects[b['actualRig']];skin=bpy.data.objects[b['actualSkin']];s.frame_set(1);bpy.context.view_layer.update();P=a.geometry(skin)[0];s.frame_set(11);bpy.context.view_layer.update();Q=a.geometry(skin)[0];rows=[]
for ob in [skin]+[bpy.data.objects[n] for n in h.h.ATTACH]:
 mod=next(m for m in ob.modifiers if m.type=='NODES' and m.name.startswith('AFN155'));g=mod.node_group;values=[]
 for n in g.nodes:
  if n.bl_idname=='ShaderNodeValue':values.append({'name':n.name,'value':float(n.outputs[0].default_value)})
 rows.append({'object':ob.name,'nodes':len(g.nodes),'valuesAtClosed':values,'drivers':[{'path':fc.data_path,'valid':fc.driver.is_valid,'expression':fc.driver.expression,'variables':[(v.name,str(v.targets[0].id),v.targets[0].data_path) for v in fc.driver.variables]} for fc in g.animation_data.drivers] if g.animation_data else []})
manual=[]
for ob in [skin]+[bpy.data.objects[n] for n in h.h.ATTACH]:
 mod=next(m for m in ob.modifiers if m.type=='NODES' and m.name.startswith('AFN155'));g=mod.node_group
 if g.animation_data:
  for fc in g.animation_data.drivers:fc.mute=True
 for n in g.nodes:
  if n.bl_idname=='ShaderNodeValue':n.outputs[0].default_value=1.
 g.update_tag();ob.update_tag()
bpy.context.view_layer.update();M=a.geometry(skin)[0];table=bpy.data.objects['AFN155_CURRENT_SKIN_BLINK_FIELD'];attrs={}
for name in ['AFN155_ANGLE','AFN155_ACTIVE']:
 d=table.data.attributes[name];v=np.empty(len(d.data),'f4');d.data.foreach_get('value',v);attrs[name]={'min':float(v.min()),'max':float(v.max()),'nonzero':int(np.count_nonzero(v))}
h.save('field-driving-inspection.json',{'rigClosedProperties':{k:float(rig[k]) for k in ['blink_L','blink_R']},'actualAnimatedClosedSkinMovementM':float(np.linalg.norm(Q-P,axis=1).max()),'actualManualScalarOneSkinMovementM':float(np.linalg.norm(M-P,axis=1).max()),'actualNativeFieldAttributes':attrs,'nodeDriverState':rows,'noSourceFileSavedOrChanged':True});print('R155_ACTUAL_FIELD_DRIVING_INSPECTION_DONE',float(np.linalg.norm(Q-P,axis=1).max()),float(np.linalg.norm(M-P,axis=1).max()),flush=True)
