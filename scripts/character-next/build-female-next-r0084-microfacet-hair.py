"""Second construction: microfacet fibre scattering, fixed proven RGB field.
No palette/roughness/exposure/density sweep. Circular section explicitly assumed
for the rendered cylinder; not a measured human fibre cross-section certificate.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r"D:/Download/Aevrynd");E=R/"Evidence/character-female-next/r0084-physical-brown-hair";S=R/"engine/assets/characters/female-next/source";OUT=S/"aevrynd-female-next-r0084-b-microfacet-brown-hair-study.blend"
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module("r84Bsource","build-female-next-r0081-editable-curly.py");m.E=E;m.m.E=E;m.rig.E=E;m.rig.shade.g.E=E
visual=module("r84Bview","render-female-next-r0081-retained-study.py");visual.E=E

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
def main():
 tick=time.time();a=json.loads((E/"a-build-summary.json").read_text());assert not OUT.exists() and sha(Path(a["output"]))==a["outputSha256"];bpy.ops.wm.open_mainfile(filepath=a["output"]);s=bpy.context.scene;s.frame_set(1);m.rig.shade.settings();bpy.context.view_layer.update();o=bpy.data.objects["AFN81_EDITABLE_CURLY_GUIDES"];before=m.q.hair(o).copy();mat=bpy.data.materials["AFN84_BROWN_DIELECTRIC_HAIR"];mat.name="AFN84_MICROFACET_BROWN_HAIR";hair=mat.node_tree.nodes["AFN84_HAIR_SCATTERING"];assert hair.model=="CHIANG" and hair.parametrization=="COLOR";rough=float(hair.inputs["Roughness"].default_value);hair.model="HUANG";hair.inputs["Aspect Ratio"].default_value=1
 for name in ("Reflection","Transmission","Secondary Reflection"):hair.inputs[name].default_value=1
 assert float(hair.inputs["Roughness"].default_value)==rough;bpy.context.view_layer.update();assert np.array_equal(before,m.q.hair(o));o["AFN84_scope"]="Same original303-guide r81B woman and explicit Brown RGB field; Huang microfacet fibre scattering with assumed circular section, all reflection/transmission factors1. No arbitrary pigment/roughness/density changes. Not full contact/natural dynamics/engine acceptance.";s["AFN84_scope"]=o["AFN84_scope"];m.rig.k.b.camera("face");s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;descriptor=json.loads((E/"a-material-descriptor.json").read_text());descriptor.update(material=mat.name,model="HUANG",crossSectionAspectRatio=1,circularSectionAssumedNotMeasured=True,reflectionTransmissionSecondaryFactors=[1,1,1],sameProvenRGBFieldAndRoughness=True);save("b-material-descriptor.json",descriptor);save("b-build-summary.json",{"source":a["output"],"sourceSha256":a["outputSha256"],"completeBaselineSource":a["source"],"completeBaselineSha256":a["sourceSha256"],"output":str(OUT),"outputSha256":sha(OUT),"outputBytes":OUT.stat().st_size,"materialDescriptor":"b-material-descriptor.json","evaluatedGeometryBeforeAfterExact":True,"nativeGuides":303,"nativePoints":3636,"actualEvaluatedCurves":len(d.curves),"actualEvaluatedPoints":len(d.position_data),"secondsBeforePreview":time.time()-tick,"fullContactNaturalMotionRuntimeAccepted":False});rows=[]
 for view in ("face","body-face","back"):rows.append(visual.image("b-microfacet",view));save("b-pilot-controls.json",rows)
 print("R84_MICROFACET_HAIR_PILOT_COMPLETE",time.time()-tick,flush=True)
if __name__=="__main__":main()
