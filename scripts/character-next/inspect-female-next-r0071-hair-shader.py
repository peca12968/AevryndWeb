import bpy,json
from pathlib import Path
r=Path(r'D:\Download\Aevrynd'); e=r/'Evidence/character-female-next/r0071-hair-scattering';e.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(r/'engine/assets/characters/female-next/source/aevrynd-female-next-r0069-a-complete-controls-study.blend'))
def value(s):
 if not hasattr(s,'default_value'):return None
 v=s.default_value
 if isinstance(v,(str,int,float,bool)):return v
 try:return list(v)
 except:return str(v)
def tree(t,seen):
 if t.name in seen:return
 seen.add(t.name)
 row={'tree':t.name,'nodes':[{'name':n.name,'type':n.bl_idname,'model':getattr(n,'model',None),'parametrization':getattr(n,'parametrization',None),'operation':getattr(n,'operation',None),'inputs':[(s.name,value(s),s.is_linked) for s in n.inputs],'outputs':[s.name for s in n.outputs]} for n in t.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in t.links]}
 result.append(row)
 for n in t.nodes:
  if n.type=='GROUP' and n.node_tree:tree(n.node_tree,seen)
result=[];tree(bpy.data.materials['Brown hair'].node_tree,set())
(e/'source-hair-shader.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
