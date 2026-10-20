from pathlib import Path
import bpy,numpy as np,json,hashlib
R=Path(r"D:/Download/Aevrynd");E=R/"Evidence/character-female-next/r0083-posterior-guide-authoring";E.mkdir(exist_ok=True);S=R/"engine/assets/characters/female-next/source/aevrynd-female-next-r0081-b-stable-frame-curly-study.blend"
assert hashlib.sha256(S.read_bytes()).hexdigest()=="dfcc38df12c6bd93c9659b90f8b665e973b7a90f3828b134297bd6f2365898c0"
bpy.ops.wm.open_mainfile(filepath=str(S));o=bpy.data.objects["AFN81_EDITABLE_CURLY_GUIDES"];d=o.data;p=np.empty(len(d.position_data)*3,"f4");d.position_data.foreach_get("vector",p);p=p.reshape(-1,3);A=np.array(o.matrix_world);W=p@A[:3,:3].T+A[:3,3];counts=np.array([c.points_length for c in d.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];rows=[]
for i,(st,n) in enumerate(zip(starts,counts)):
 q=W[st:st+n];rows.append({"guide":i,"root":q[0].tolist(),"control2":q[2].tolist(),"tip":q[-1].tolist(),"bounds":[q.min(axis=0).tolist(),q.max(axis=0).tolist()]})
mods=[]
for md in o.modifiers:
 row={"name":md.name,"enabled":[md.show_viewport,md.show_render]}
 if md.type=="NODES":
  row["nodes"]=[{"name":n.name,"type":n.bl_idname,"group":n.node_tree.name if n.type=="GROUP" else None,"inputs":[[s.name,str(s.default_value)] for s in n.inputs if hasattr(s,"default_value") and not s.is_linked]} for n in md.node_group.nodes]
 mods.append(row)
(E/"posterior-guide-inspection.json").write_text(json.dumps({"source":str(S),"guides":rows,"modifiers":mods},indent=2));np.savez_compressed(E/"before-native-guides.npz",P=p,A=A,W=W,counts=counts)
print("GUIDE_BOUNDS",W.min(0),W.max(0));print("POSTERIOR_GUIDES",json.dumps([x for x in rows if x["root"][1]>.025 and x["root"][2]>1.43]));print("R83_INSPECT_COMPLETE",flush=True)

import importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location("r83build",R/"scripts/character-next/build-female-next-r0081-editable-curly.py");m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);body=m.rig.k.mesh(bpy.data.objects["AFN60_BODY_ORAL_AND_OCULAR_LINING"]);tree=BVHTree.FromPolygons(body["V"].tolist(),body["T"].tolist(),all_triangles=True);rows=[]
for z in [1.46,1.47,1.48,1.49,1.50,1.51,1.52,1.53]:
 row={"z":z,"rearSurfaceY":[]}
 for x in [-.03,-.015,0,.015,.03]:
  co,_,_,_=tree.ray_cast(Vector((x,.2,z)),Vector((0,-1,0)),.4);row["rearSurfaceY"].append([x,co.y if co else None])
 rows.append(row)
(E/"posterior-body-profile.json").write_text(json.dumps(rows,indent=2));print("BODY_REAR_PROFILE",json.dumps(rows),flush=True)
