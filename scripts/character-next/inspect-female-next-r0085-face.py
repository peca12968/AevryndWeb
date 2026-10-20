"""Bounded current head views and native-coordinate anatomical authoring basis."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util
R=Path(r"D:/Download/Aevrynd");E=R/"Evidence/character-female-next/r0085-orbital-fold";SRC=R/"engine/assets/characters/female-next/source/aevrynd-female-next-r0081-b-stable-frame-curly-study.blend";assert hashlib.sha256(SRC.read_bytes()).hexdigest()=="dfcc38df12c6bd93c9659b90f8b665e973b7a90f3828b134297bd6f2365898c0"
sp=importlib.util.spec_from_file_location("r85base",R/"scripts/character-next/build-female-next-r0081-editable-curly.py");m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);sp=importlib.util.spec_from_file_location("r85views",R/"scripts/character-next/render-female-next-r0081-retained-study.py");v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);v.E=E
bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();V=np.zeros((37436,3));rows=[]
for name in m.rig.native_names():
 o=bpy.data.objects[name];ids=m.q.arr(o.data.attributes["AFN60_NativeVertexID"].data,"value",len(o.data.vertices),dtype="i4");basis=np.array([p.co[:] for p in o.data.shape_keys.key_blocks[0].data]);local=basis.copy()
 for key in o.data.shape_keys.key_blocks[1:]:local+=(np.array([p.co[:] for p in key.data])-basis)*key.value
 A=np.array(o.matrix_world);V[ids]=local@A[:3,:3].T+A[:3,3]
np.savez_compressed(E/"baseline-native-world.npz",world=V);rows=[]
for view in ("face","body-face","profile","oblique"):
 rows.append(v.image("baseline-r81",view));(E/"baseline-view-controls.json").write_text(json.dumps(rows,indent=2)+"\n")
print("R85_COMPLETE_HEAD_ANATOMY_VIEWS_DONE",flush=True)
