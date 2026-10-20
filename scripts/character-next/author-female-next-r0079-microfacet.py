"""Controlled microfacet-fibre model comparison; same B geometry/palette/light.
No component suppression, pigment/roughness sweep or claimed engine port.
"""
from pathlib import Path
import bpy,json,hashlib,importlib.util,time
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0079-physical-filaments';OUT=S/'aevrynd-female-next-r0079-c-microfacet-filaments-study.blend';sp=importlib.util.spec_from_file_location('micro79render',Path(__file__).with_name('build-female-next-r0074-oral-controls.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.E=E;m.m.shade.g.E=E
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
 tick=time.time();b=json.loads((E/'b-build-summary.json').read_text());src=Path(b['output']);assert not OUT.exists() and sha(src)==b['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(src));bpy.context.scene.frame_set(1);o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];old=o.data.materials[0];mat=old.copy();mat.name='AFN79_HUANG_CIRCULAR_MICROFACET_FILAMENT';node=mat.node_tree.nodes['AFN79_DIELECTRIC_PIGMENT_CHIANG'];node.name='AFN79_DIELECTRIC_PIGMENT_HUANG';node.model='HUANG';node.parametrization='COLOR';node.inputs['Aspect Ratio'].default_value=1.;node.inputs['Roughness'].default_value=.30
 for n in ('Reflection','Transmission','Secondary Reflection'):node.inputs[n].default_value=1.
 o.data.materials[0]=mat;mat['scope']='Controlled Huang microfacet reflection/transmission on the unchanged B circular fibres and bounded source palette. Aspect1 matches actual circular world representation. No measured scattering fit, component suppression or engine acceptance.';bpy.context.scene['AFN79_C_scope']='Same B physical fibre geometry/guide lineage, palette and lights; Huang circular microfacet optical model only. No contact/dynamics/runtime promotion.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 save('c-build-summary.json',{'source':str(src),'sourceSha256':b['outputSha256'],'originalCompleteGuideSource':b['source'],'originalCompleteGuideSha256':b['sourceSha256'],'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'geometryAndRadiiAndPaletteIdenticalToB':True,'hairBSDF':'HUANG/COLOR','aspectRatio':1.,'microfacetRoughness':.30,'reflectionTransmissionSecondaryReflection':[1.,1.,1.],'modelRoughnessIsNotMeasuredOrNumericallyEquivalentToChiangBeta':True,'sourceReference':'https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/hair_principled.html','secondsBeforePilot':time.time()-tick});rows=[]
 for view in ('face','body-face'):rows.append(m.render('c-pilot',view));save('c-pilot-controls.json',rows)
 print('R79_CONTROLLED_MICROFACET_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
