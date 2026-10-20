"""Third construction: correct actual renderer-specific shader routing.
Use the source's existing Cycles Hair BSDF output, not an EEVEE surface shader.
No geometric coverage layer, density/radius/pigment/lighting/exposure change.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r"D:/Download/Aevrynd");E=R/"Evidence/character-female-next/r0083-posterior-guide-authoring";S=R/"engine/assets/characters/female-next/source";SRC=S/"aevrynd-female-next-r0081-b-stable-frame-curly-study.blend";SHA="dfcc38df12c6bd93c9659b90f8b665e973b7a90f3828b134297bd6f2365898c0";OUT=S/"aevrynd-female-next-r0083-c-cycles-hair-shader-route.blend"
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module("r83Cbase","build-female-next-r0081-editable-curly.py");m.E=E;m.m.E=E;m.rig.E=E;m.rig.shade.g.E=E
visual=module("r83Cview","render-female-next-r0081-retained-study.py");visual.E=E

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)==SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);m.rig.shade.settings();assert s.render.engine=="CYCLES";bpy.context.view_layer.update();o=bpy.data.objects["AFN81_EDITABLE_CURLY_GUIDES"];before=m.q.hair(o).copy();mat=bpy.data.materials["Brown hair"];tree=mat.node_tree;group=tree.nodes["Group"];route=tree.nodes["Reroute.001"];assert route.inputs[0].links[0].from_socket==group.outputs["EEVEE Shader"];oldInputs={i.name:str(i.default_value) for i in group.inputs};inner=group.node_tree;native=inner.nodes["Principled Hair BSDF.001"];tree.links.new(group.outputs["Cycles Shader"],route.inputs[0]);bpy.context.view_layer.update();after=m.q.hair(o);assert np.array_equal(before,after);assert oldInputs=={i.name:str(i.default_value) for i in group.inputs};o["AFN83_scope"]="Original303-guide r81B geometry/skin following unchanged; Brown material now uses its pre-existing Cycles Shader output in Cycles. R81 failed skin-frame target, contact and natural dynamics remain unaccepted.";s["AFN83_scope"]=o["AFN83_scope"];s.render.hair_subdiv=3;m.rig.k.b.camera("face");s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;save("c-build-summary.json",{"source":str(SRC),"sourceSha256":SHA,"output":str(OUT),"outputSha256":sha(OUT),"outputBytes":OUT.stat().st_size,"renderer":s.render.engine,"oldRoute":"Group.EEVEE Shader -> Reroute.001 -> Material Output.Surface","newRoute":"Group.Cycles Shader -> Reroute.001 -> Material Output.Surface","existingNativeHairShader":native.bl_idname,"nativeHairParametrization":native.parametrization,"nativeHairModel":native.model,"allExistingGroupInputsUnchanged":oldInputs,"evaluatedGeometryBeforeAfterExact":True,"nativeGuides":len(o.data.curves),"nativePoints":len(o.data.position_data),"actualEvaluatedCurves":len(d.curves),"actualEvaluatedPoints":len(d.position_data),"secondsBeforePreview":time.time()-tick,"noContactNaturalMotionRuntimePromotion":True});rows=[]
 for view in ("back","face","body-face"):rows.append(visual.image("c-cycles",view));save("c-pilot-controls.json",rows)
 print("R83_RENDERER_SHADER_ROUTE_PILOT_COMPLETE",time.time()-tick,flush=True)
if __name__=="__main__":main()
