"""Bounded actual source/rig/annulus inspection for native optical construction."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,hashlib
R=Path(r'D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0087-eye-solids';S=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0081-b-stable-frame-curly-study.blend'
sp=importlib.util.spec_from_file_location('r87data',R/'scripts/character-next/build-female-next-r0081-editable-curly.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
assert hashlib.sha256(S.read_bytes()).hexdigest()=='dfcc38df12c6bd93c9659b90f8b665e973b7a90f3828b134297bd6f2365898c0';bpy.ops.wm.open_mainfile(filepath=str(S));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rows=[]
for n in m.rig.native_names()[:4]:
 o=bpy.data.objects[n];weights={}
 for vert in o.data.vertices:
  for g in vert.groups:
   name=o.vertex_groups[g.group].name;weights.setdefault(name,[]).append(g.weight)
 rows.append({'object':n,'matrix':np.array(o.matrix_world).tolist(),'modifiers':[{'name':md.name,'type':md.type,'object':getattr(getattr(md,'object',None),'name',None)} for md in o.modifiers],'weights':{n:[len(a),min(a),max(a)] for n,a in weights.items()},'parent':getattr(o.parent,'name',None)})
tree=bpy.data.materials['AFN57_COMBINED_SCLERA_CORNEA_APPROXIMATION'].node_tree
out={'source':str(S),'eyes':rows,'rigMatrix':np.array(bpy.data.objects['AFN69_BODY_CONTROLS'].matrix_world).tolist(),'headRest':np.array(bpy.data.objects['AFN69_BODY_CONTROLS'].pose.bones['Head'].matrix_basis).tolist(),'outerTextureCoordinates':[{'node':n.name,'type':n.bl_idname,'image':getattr(getattr(n,'image',None),'name',None),'links':[[s.name,[(a.from_node.name,a.from_socket.name) for a in s.links]] for s in n.inputs if s.is_linked]} for n in tree.nodes if n.bl_idname in ('ShaderNodeTexImage','ShaderNodeUVMap','ShaderNodeVectorMath','ShaderNodeTexCoord') ]}
(E/'actual-eye-source-and-rig.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
