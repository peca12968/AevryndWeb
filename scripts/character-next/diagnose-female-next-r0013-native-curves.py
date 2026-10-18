"""Inspect the installed Blender API before authoring native strand data."""
import bpy,json
from pathlib import Path
E=Path(r'D:\Download\Aevrynd\Evidence\character-female-next\r0013-envelope-hair')
d=bpy.data.hair_curves.new('AFN13_API_PROBE');d.add_curves([3,3]);d.position_data.foreach_set('vector',[0.,0.,0.,0.,0.,.1,0.,0.,.2,.1,0.,0.,.1,0.,.1,.1,0.,.2])
radius=d.attributes.new('radius','FLOAT','POINT');radius.data.foreach_set('value',[.00004]*6)
t=d.attributes.get('curve_type') or d.attributes.new('curve_type','INT8','CURVE');t.data.foreach_set('value',[1,1])
m=bpy.data.materials.new('AFN13_HAIR_PROBE');m.use_nodes=True;n=m.node_tree.nodes.new('ShaderNodeBsdfHairPrincipled')
out={'version':bpy.app.version_string,'curves':len(d.curves),'attributes':[(a.name,a.domain,a.data_type) for a in d.attributes],'firstPoint':list(d.curves[0].points[0].position),'pointProperties':[(p.identifier,p.type) for p in d.curves[0].points[0].bl_rna.properties],'dataProperties':[(p.identifier,p.type) for p in d.bl_rna.properties],'hairNodeParameters':[(p.identifier,p.type,([x.identifier for x in p.enum_items] if p.type=='ENUM' else None)) for p in n.bl_rna.properties if p.identifier in ('model','parametrization')],'hairInputs':[(i.name,list(i.default_value) if hasattr(i.default_value,'__iter__') else i.default_value) for i in n.inputs]}
(E/'installed-native-curves-api.json').write_text(json.dumps(out,indent=2)+'\n');print('AFN13_API='+json.dumps(out))
