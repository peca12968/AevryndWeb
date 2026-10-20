"""Two tiny emission diagnostics: named curve color vs explicit source palette.
Not a character candidate or beauty result; no source saved/modified.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0079-physical-filaments';sp=importlib.util.spec_from_file_location('diag79render',Path(__file__).with_name('build-female-next-r0074-oral-controls.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.E=E;m.m.shade.g.E=E
ref=json.loads((E/'b-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=ref['output']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];actual=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;at=actual.attributes['AFN79_PigmentReflectance'];colors=np.empty(len(at.data)*4,'f4');at.data.foreach_get('color',colors);colors=colors.reshape(-1,4);palette=bpy.data.materials['Brown hair'].node_tree.nodes['Group'];average=(np.array(palette.inputs['Color 1'].default_value)+np.array(palette.inputs['Color 2'].default_value))*.5
row={'source':ref['output'],'notACharacterCandidate':True,'actualColorDomain':at.domain,'actualColorDataType':at.data_type,'colorRange':[colors.min(0).tolist(),colors.max(0).tolist()],'sourcePaletteMean':average.tolist(),'objectSlots':[{'link':s.link,'material':s.material.name if s.material else None} for s in o.material_slots],'bsdf':{'model':o.active_material.node_tree.nodes['AFN79_DIELECTRIC_PIGMENT_CHIANG'].model,'parametrization':o.active_material.node_tree.nodes['AFN79_DIELECTRIC_PIGMENT_CHIANG'].parametrization,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in o.active_material.node_tree.nodes['AFN79_DIELECTRIC_PIGMENT_CHIANG'].inputs if hasattr(i,'default_value')}}}
mat=bpy.data.materials.new('AFN79_DIAGNOSTIC_EMISSION_ONLY');mat.use_nodes=True;t=mat.node_tree;t.nodes.clear();em=t.nodes.new('ShaderNodeEmission');em.inputs['Strength'].default_value=1.;att=t.nodes.new('ShaderNodeAttribute');att.attribute_name='AFN79_PigmentReflectance';out=t.nodes.new('ShaderNodeOutputMaterial');t.links.new(em.outputs[0],out.inputs['Surface']);o.data.materials[0]=mat
for tag in ('attribute','constant'):
 for link in list(t.links):
  if link.to_socket==em.inputs['Color']:t.links.remove(link)
 if tag=='attribute':t.links.new(att.outputs['Color'],em.inputs['Color'])
 else:em.inputs['Color'].default_value=average
 m.render('b-'+tag+'-emission-diagnostic','face',256,4)
(E/'b-color-diagnosis.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8');print('R79_COLOR_DIAGNOSTIC_DONE',row['actualColorDomain'],row['colorRange'],row['objectSlots'],flush=True)
