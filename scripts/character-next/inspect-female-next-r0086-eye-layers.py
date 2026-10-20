"""Actual rendered eye geometry, source alpha and optical shader inventory."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util
R=Path(r"D:/Download/Aevrynd");E=R/"Evidence/character-female-next/r0086-eye-layers";SRC=R/"engine/assets/characters/female-next/source/aevrynd-female-next-r0081-b-stable-frame-curly-study.blend";assert hashlib.sha256(SRC.read_bytes()).hexdigest()=="dfcc38df12c6bd93c9659b90f8b665e973b7a90f3828b134297bd6f2365898c0"
sp=importlib.util.spec_from_file_location("r86base",R/"scripts/character-next/build-female-next-r0081-editable-curly.py");m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();names=m.rig.native_names()[:4];arrays={};rows=[];alphaImage=next(n.image for n in bpy.data.materials["AFN57_COMBINED_SCLERA_CORNEA_APPROXIMATION"].node_tree.nodes if n.name=="SuppliedScleraColour");pixels=np.empty(len(alphaImage.pixels),"f4");alphaImage.pixels.foreach_get(pixels);im=pixels.reshape(alphaImage.size[1],alphaImage.size[0],4)
for name in names:
 o=bpy.data.objects[name]
 for md in o.modifiers:
  if md.type=="SUBSURF":md.levels=md.render_levels
 bpy.context.view_layer.update();d,P=m.q.geom(o);d.calc_loop_triangles();T=np.array([t.vertices[:] for t in d.loop_triangles]);mi=m.q.arr(d.polygons,"material_index",len(d.polygons),dtype="i4");centres=np.array([P[list(f.vertices)].mean(0) for f in d.polygons]);uv=m.q.arr(d.uv_layers["VitruvianUV.UDIM"].data,"uv",len(d.loops),2);a=[]
 for f in d.polygons:
  coord=uv[f.loop_start:f.loop_start+f.loop_total].mean(0);u=(coord[0]-4)%1;v=coord[1]%1;a.append(float(im[int(v*(im.shape[0]-1)),int(u*(im.shape[1]-1)),3]))
 row={"object":name,"matrix":np.array(o.matrix_world).tolist(),"vertices":len(P),"faces":len(d.polygons),"boundsM":[P.min(0).tolist(),P.max(0).tolist()],"materials":[x.name for x in d.materials],"roles":{str(i):{"material":d.materials[i].name,"faces":int((mi==i).sum()),"centroidBoundsM":[centres[mi==i].min(0).tolist(),centres[mi==i].max(0).tolist()]} for i in np.unique(mi)},"alphaRange":[min(a),max(a)] if "OUTER" in name else None};rows.append(row);arrays[name+"_P"]=P;arrays[name+"_T"]=T;arrays[name+"_FaceCentre"]=centres;arrays[name+"_FaceMaterial"]=mi;arrays[name+"_FaceSourceAlpha"]=np.array(a);arrays[name+"_UV"]=uv
np.savez_compressed(E/"baseline-eye-geometry.npz",**arrays);tree=bpy.data.materials["AFN57_COMBINED_SCLERA_CORNEA_APPROXIMATION"].node_tree;nodes=[]
for n in tree.nodes:
 if any(x in n.bl_idname for x in ["Bsdf","MixShader","OutputMaterial"]):
  ins=[]
  for sock in n.inputs:
   if not hasattr(sock,"default_value"):value=None
   else:
    value=sock.default_value
    try:value=list(value)
    except TypeError:value=str(value)
   ins.append([sock.name,value,[[l.from_node.name,l.from_socket.name] for l in sock.links]])
  nodes.append({"name":n.name,"type":n.bl_idname,"inputs":ins})
(E/"actual-eye-inspection.json").write_text(json.dumps({"source":str(SRC),"eyes":rows,"outerEyeShaderNodes":nodes,"sourceScleraAlphaImage":alphaImage.filepath,"sourceAlphaImageRange":[float(im[:,:,3].min()),float(im[:,:,3].max())]},indent=2)+"\n");print("R86_ACTUAL_EYE_GEOMETRY",json.dumps(rows),flush=True)
