"""One complete source-corresponding eye-layer workflow, not an added shell.
Partition evaluated source faces into eight disjoint layers, retain source
corner normals/UV and deformation. Existing optical approximation is explicit.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r"D:/Download/Aevrynd");S=R/"engine/assets/characters/female-next/source";E=R/"Evidence/character-female-next/r0086-eye-layers";SRC=S/"aevrynd-female-next-r0081-b-stable-frame-curly-study.blend";OUT=S/"aevrynd-female-next-r0086-a-source-corresponding-eye-layers.blend"
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module("r86source","build-female-next-r0081-editable-curly.py");m.E=E;m.m.E=E;m.rig.E=E;m.rig.shade.g.E=E;v=module("r86views","render-female-next-r0081-retained-study.py");v.E=E

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
def material(old):
 name="AFN86_SOURCE_NORMAL_"+old.name
 if name in bpy.data.materials:return bpy.data.materials[name]
 mat=old.copy();mat.name=name;n=mat.node_tree.nodes;l=mat.node_tree.links;attr=n.new("ShaderNodeAttribute");attr.attribute_name="AFN86_SourceCornerNormal";trans=n.new("ShaderNodeVectorTransform");trans.vector_type="NORMAL";trans.convert_from="OBJECT";trans.convert_to="WORLD";l.new(attr.outputs["Vector"],trans.inputs["Vector"])
 for node in n:
  if node.bl_idname.startswith("ShaderNodeBsdf") and "Normal" in node.inputs:
   assert not node.inputs["Normal"].is_linked,"Do not overwrite an existing bump/normal chain";l.new(trans.outputs["Vector"],node.inputs["Normal"])
 return mat

def layer(source,label,role,ctrl,collection):
 data=bpy.data.meshes.new("AFN86_"+label+"_CARRIER");o=bpy.data.objects.new("AFN86_"+label,data);collection.objects.link(o);o.matrix_world=source.matrix_world.copy();ng=bpy.data.node_groups.new(o.name+"_SOURCE_PARTITION","GeometryNodeTree");ng.interface.new_socket(name="Geometry",in_out="INPUT",socket_type="NodeSocketGeometry");ng.interface.new_socket(name="Geometry",in_out="OUTPUT",socket_type="NodeSocketGeometry");n=ng.nodes;l=ng.links;inp=n.new("NodeGroupInput");out=n.new("NodeGroupOutput");info=n.new("GeometryNodeObjectInfo");info.transform_space="RELATIVE";info.inputs["Object"].default_value=source;info.inputs["As Instance"].default_value=False;geo=info.outputs["Geometry"]
 for attrName,domain,kind,nodeType,socket in [("AFN86_SourcePointID","POINT","INT","GeometryNodeInputIndex","Index"),("AFN86_SourceFaceID","FACE","INT","GeometryNodeInputIndex","Index"),("AFN86_SourceCornerID","CORNER","INT","GeometryNodeInputIndex","Index"),("AFN86_SourceCornerNormal","CORNER","FLOAT_VECTOR","GeometryNodeInputNormal","Normal")]:
  field=n.new(nodeType);store=n.new("GeometryNodeStoreNamedAttribute");store.domain=domain;store.data_type=kind;store.inputs["Name"].default_value=attrName;l.new(geo,store.inputs["Geometry"]);l.new(field.outputs[socket],store.inputs["Value"]);geo=store.outputs["Geometry"]
 if role in ("CORNEAL_REGION","SCLERA_REGION"):
  attr=n.new("GeometryNodeInputNamedAttribute");attr.data_type="INT";attr.inputs["Name"].default_value="AFN86_SourceOpticalRegion";value=attr.outputs["Attribute"];target=1 if role=="CORNEAL_REGION" else 0;mat=source.data.materials[3]
 else:
  index=n.new("GeometryNodeInputMaterialIndex");value=index.outputs["Material Index"];target=0 if role=="IRIS" else 2;mat=source.data.materials[target]
 compare=n.new("FunctionNodeCompare");compare.data_type="INT";compare.operation="EQUAL";l.new(value,compare.inputs["A"]);compare.inputs["B"].default_value=target;split=n.new("GeometryNodeSeparateGeometry");split.domain="FACE";l.new(geo,split.inputs["Geometry"]);l.new(compare.outputs["Result"],split.inputs["Selection"]);setmat=n.new("GeometryNodeSetMaterial");setmat.inputs["Material"].default_value=material(mat);l.new(split.outputs["Selection"],setmat.inputs["Geometry"]);switch=n.new("GeometryNodeSwitch");switch.input_type="GEOMETRY";l.new(setmat.outputs["Geometry"],switch.inputs["True"]);l.new(switch.outputs["Output"],out.inputs["Geometry"]);md=o.modifiers.new("AFN86_LIVE_SOURCE_LAYER","NODES");md.node_group=ng;prop=label.lower()+"_visible";ctrl[prop]=True;fc=switch.inputs["Switch"].driver_add("default_value");fc.driver.type="SCRIPTED";fc.driver.expression="visible";var=fc.driver.variables.new();var.name="visible";var.type="SINGLE_PROP";var.targets[0].id=ctrl;var.targets[0].data_path='["'+prop+'"]';o["sourceObject"]=source.name;o["role"]=role;o["scope"]="Real disjoint evaluated source-face layer with source point/face/corner IDs, original UV and preserved source corner normals. Editable source correspondence, not independently retopologized solid tissue.";return {"object":o.name,"source":source.name,"role":role,"visibilityProperty":prop,"material":setmat.inputs["Material"].default_value.name}

def validate(source,rows):
 q=m.q;d,P=q.geom(source);sourceNormals=q.arr(d.corner_normals,"vector",len(d.loops),3);uv=q.arr(d.uv_layers["VitruvianUV.UDIM"].data,"uv",len(d.loops),2);seen=[];result=[]
 for row in rows:
  o=bpy.data.objects[row["object"]];ed,W=q.geom(o);pi=q.arr(ed.attributes["AFN86_SourcePointID"].data,"value",len(W),dtype="i4");fi=q.arr(ed.attributes["AFN86_SourceFaceID"].data,"value",len(ed.polygons),dtype="i4");ci=q.arr(ed.attributes["AFN86_SourceCornerID"].data,"value",len(ed.loops),dtype="i4");normal=q.arr(ed.attributes["AFN86_SourceCornerNormal"].data,"vector",len(ed.loops),3);posError=float(np.linalg.norm(W-P[pi],axis=1).max());normalError=float(np.linalg.norm(normal-sourceNormals[ci],axis=1).max());assert posError<2e-6 and normalError<2e-5,(row["object"],posError,normalError);assert np.array_equal(q.arr(ed.uv_layers["VitruvianUV.UDIM"].data,"uv",len(ed.loops),2),uv[ci]);seen.extend(fi.tolist());result.append(dict(row,vertices=len(W),faces=len(fi),maximumSourcePositionErrorM=posError,maximumCapturedSourceCornerNormalError=normalError))
 assert sorted(seen)==list(range(len(d.polygons))),"Source faces missing or duplicated";return {"source":source.name,"sourceFaces":len(d.polygons),"eachSourceFaceExactlyOnce":True,"layers":result}

def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=="dfcc38df12c6bd93c9659b90f8b665e973b7a90f3828b134297bd6f2365898c0";bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();coll=bpy.data.collections.new("AFN86_SOURCE_CORRESPONDING_EYE_LAYERS");s.collection.children.link(coll);ctrl=bpy.data.objects.new("AFN86_EYE_LAYER_CONTROLS",None);coll.objects.link(ctrl);ctrl.empty_display_size=.02;ctrl.location=(0,-.2,1.47);ctrl["scope"]="Eight independent layer visibility controls with exact restoration. Cornea/sclera regions retain original one-interface optics; no new corneal solid or full optical/contact qualification.";im=bpy.data.images["Sclera_Color.1005.exr"];pixels=np.empty(len(im.pixels),"f4");im.pixels.foreach_get(pixels);alpha=pixels.reshape(im.size[1],im.size[0],4)[:,:,3];parts=[];sources=[];region=[]
 for side in ("L","R"):
  outer=bpy.data.objects["AFN60_"+side+"_EYE_OUTER_SHELL_APPROX"];inner=bpy.data.objects["AFN60_"+side+"_IRIS_PUPIL_SURFACE"];sources.extend([outer,inner]);uv=m.q.arr(outer.data.uv_layers["VitruvianUV.UDIM"].data,"uv",len(outer.data.loops),2);values=[]
  for f in outer.data.polygons:
   coord=uv[f.loop_start:f.loop_start+f.loop_total].mean(0);u=(coord[0]-4)%1;vcoord=coord[1]%1;values.append(int(alpha[int(vcoord*(alpha.shape[0]-1)),int(u*(alpha.shape[1]-1))]<.5))
  at=outer.data.attributes.new("AFN86_SourceOpticalRegion","INT","FACE");at.data.foreach_set("value",values);region.append({"source":outer.name,"nativeFaces":len(values),"cornealRegionNativeFaces":int(sum(values)),"definition":"Source Sclera_Color alpha<.5 at native-face centroid. Editing partition only, not exact anatomical limbus or opacity replacement; original continuous source alpha shader retained."})
  for src in (outer,inner):
   for md in src.modifiers:
    if md.type=="SUBSURF":md.levels=md.render_levels
  for src,roles in [(outer,("SCLERA_REGION","CORNEAL_REGION")),(inner,("IRIS","PUPIL"))]:
   for role in roles:parts.append(layer(src,side+"_"+role,role,ctrl,coll))
 bpy.context.view_layer.update();guards=[validate(src,[r for r in parts if r["source"]==src.name]) for src in sources];save("a-partition-guard.json",{"sources":guards,"noAddedOrDuplicatedSourceFaces":True,"noNewLayerContactGeometry":True,"notAFiniteThicknessCornealVolumeOrGlobalContactCertificate":True})
 for src in sources:src.hide_render=True;src.hide_set(True)
 m.rig.shade.settings();s.render.hair_subdiv=3;m.rig.k.b.camera("face");s.camera.data.lens=85;s["AFN86_scope"]=ctrl["scope"];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save("a-build-summary.json",{"source":str(SRC),"sourceSha256":sha(SRC),"output":str(OUT),"outputSha256":sha(OUT),"outputBytes":OUT.stat().st_size,"controls":ctrl.name,"layers":parts,"sourceRegionDefinitions":region,"guard":"a-partition-guard.json","existingDepthRetainedNotExtraShell":True,"opticalSolidsAnatomicalThicknessNaturalMotionRuntimeAccepted":False,"secondsBeforePreview":time.time()-tick});rows=[]
 for view in ("face","body-face","oblique"):rows.append(v.image("a-layers",view));save("a-pilot-controls.json",rows)
 print("R86_SOURCE_EYE_LAYERS_PILOT_COMPLETE",time.time()-tick,flush=True)
if __name__=="__main__":main()
