from pathlib import Path
import bpy,json
E=Path('D:/Download/Aevrynd/Evidence/character-female-next/r0151-native-parent-groom');g=bpy.data.node_groups.new('AFN151_NATIVE_INTERPOLATE_CAPABILITY','GeometryNodeTree')
try:
 n=g.nodes.new('GeometryNodeInterpolateCurves');r={'available':True,'bl_idname':n.bl_idname,'inputs':[{'name':s.name,'identifier':s.identifier,'type':s.bl_rna.identifier,'default':str(getattr(s,'default_value',None))} for s in n.inputs],'outputs':[{'name':s.name,'type':s.bl_rna.identifier} for s in n.outputs]}
except Exception as e:r={'available':False,'error':str(e)}
(E/'native-interpolate-curves-capability-rna.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('R151_NATIVE_INTERPOLATE_CURVES_CAPABILITY',json.dumps(r))
