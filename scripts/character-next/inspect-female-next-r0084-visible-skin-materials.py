"""Read actual evaluated visible-skin materials, not its empty carrier mesh slots."""
from pathlib import Path
import bpy,json,hashlib,importlib.util
R=Path(r"D:/Download/Aevrynd");E=R/"Evidence/character-female-next/r0084-physical-brown-hair";SRC=R/"engine/assets/characters/female-next/source/aevrynd-female-next-r0081-b-stable-frame-curly-study.blend";assert hashlib.sha256(SRC.read_bytes()).hexdigest()=="dfcc38df12c6bd93c9659b90f8b665e973b7a90f3828b134297bd6f2365898c0"
bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rows=[];seen=set();trees=[]
def val(s):
 if not hasattr(s,"default_value"):return None
 x=s.default_value
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 if hasattr(x,"name"):return x.name
 return list(x)
def walk(t,depth=0):
 if t.as_pointer() in seen or depth>4:return
 seen.add(t.as_pointer());ns=[]
 for n in t.nodes:
  if n.bl_idname=="ShaderNodeBsdfPrincipled":ns.append({"name":n.name,"type":n.bl_idname,"inputs":[[s.name,val(s),[[l.from_node.name,l.from_socket.name] for l in s.links]] for s in n.inputs]})
  if n.bl_idname=="ShaderNodeTexImage" and n.image:ns.append({"name":n.name,"image":n.image.name,"path":n.image.filepath,"size":list(n.image.size),"colourSpace":n.image.colorspace_settings.name})
  if n.type=="GROUP":walk(n.node_tree,depth+1)
 if ns:trees.append({"tree":t.name,"ownerMaterial":mat.name,"nodes":ns})
for name in ("AFN60_BODY_ORAL_AND_OCULAR_LINING","AFN74_SKIN_AND_EXISTING_OCULAR_LINING"):
 o=bpy.data.objects[name];d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;rows.append({"object":name,"hideRender":o.hide_render,"authoringMaterialSlots":[x.name for x in o.data.materials],"evaluatedMaterialSlots":[x.name for x in d.materials],"evaluatedFaces":len(d.polygons),"materialIndices":list(sorted(set(p.material_index for p in d.polygons)))})
 for mat in d.materials:
  if mat and mat.use_nodes:walk(mat.node_tree)
(E/"actual-evaluated-skin-material-context.json").write_text(json.dumps({"source":str(SRC),"objects":rows,"trees":trees,"authoringCarrierSlotsNotEvidenceOfActualRenderedShading":True},indent=2)+"\n");print("ACTUAL_SKIN_MATERIALS",json.dumps(rows),flush=True)
