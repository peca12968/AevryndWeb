"""Actual displayed skin response to the two new sculpt controls, not cage-only."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util
R=Path(r"D:/Download/Aevrynd");E=R/"Evidence/character-female-next/r0085-orbital-fold";sp=importlib.util.spec_from_file_location("r85check",R/"scripts/character-next/build-female-next-r0081-editable-curly.py");m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);rows=[]
for tag,keyName in [("a","AFN85_CC0_UPPER_LID_CREASE"),("b","AFN85_PRETARSAL_FOLD_SCULPT")]:
 ref=json.loads((E/(tag+"-build-summary.json")).read_text());assert hashlib.sha256(Path(ref["output"]).read_bytes()).hexdigest()==ref["outputSha256"];bpy.ops.wm.open_mainfile(filepath=ref["output"]);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects["AFN60_BODY_ORAL_AND_OCULAR_LINING"];skin=bpy.data.objects["AFN74_SKIN_AND_EXISTING_OCULAR_LINING"];key=body.data.shape_keys.key_blocks[keyName];before={o.name:m.rig.k.mesh(o)["V"].copy() for o in (body,skin)};key.value=0;bpy.context.view_layer.update();row={"tag":tag,"key":keyName,"showOnlyShapeKey":body.show_only_shape_key,"activeKeyIndex":body.active_shape_key_index,"actualGeometry":{}}
 for o in (body,skin):
  now=m.rig.k.mesh(o)["V"];diff=np.linalg.norm(now-before[o.name],axis=1);row["actualGeometry"][o.name]={"maximumWorldMoveM":float(diff.max()),"pointsChangedOver1Micrometre":int((diff>1e-6).sum()),"changedBoundsM":[before[o.name][diff>1e-6].min(0).tolist(),before[o.name][diff>1e-6].max(0).tolist()] if (diff>1e-6).any() else None}
 rows.append(row)
(E/"actual-visible-sculpt-response.json").write_text(json.dumps(rows,indent=2)+"\n");print("ACTUAL_SCULPT_RESPONSE",json.dumps(rows),flush=True)
