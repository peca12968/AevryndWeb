from pathlib import Path
import bpy,json
R=Path(r"D:/Download/Aevrynd");E=R/"Evidence/character-female-next/r0083-posterior-guide-authoring";bpy.ops.wm.open_mainfile(filepath=str(R/"engine/assets/characters/female-next/source/aevrynd-female-next-r0081-b-stable-frame-curly-study.blend"));visited=set();rows=[]
def walk(tree):
 if tree.name in visited:return
 visited.add(tree.name);nodes=[]
 for n in tree.nodes:
  inputs=[]
  for s in n.inputs:
   v=s.default_value if hasattr(s,"default_value") else None
   try:v=list(v)
   except TypeError:v=str(v)
   inputs.append({"name":s.name,"value":v,"links":[[l.from_node.name,l.from_socket.name] for l in s.links]})
  nodes.append({"name":n.name,"type":n.bl_idname,"inputs":inputs,"group":n.node_tree.name if n.type=="GROUP" else None})
  if n.type=="GROUP":walk(n.node_tree)
 rows.append({"tree":tree.name,"nodes":nodes})
walk(bpy.data.materials["Brown hair"].node_tree);(E/"brown-hair-full-shader-tree.json").write_text(json.dumps(rows,indent=2));print("HAIR_SHADER_TREES",[(r["tree"],len(r["nodes"])) for r in rows]);print("SURFACE_SHADERS",[(r["tree"],n) for r in rows for n in r["nodes"] if any(x in n["type"] for x in ["Bsdf","OutputMaterial","Holdout"])] ,flush=True)
