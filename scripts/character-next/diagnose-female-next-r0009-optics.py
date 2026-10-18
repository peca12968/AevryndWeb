"""Isolate the lower-iris crescent with fixed geometry, camera, exposure and lights."""
import bpy,json,hashlib,importlib.util
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0009-optics';E.mkdir(parents=True,exist_ok=True)
SRC=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0008-a-tight-study.blend'
spec=importlib.util.spec_from_file_location('afn_optics_stage',Path(__file__).with_name('build-female-next-r0007-socket-clearance.py'));stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage);stage.eyes.E=E
records=[]
for label in ('baseline','no-cornea','unit-ior','no-screen-refraction'):
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;rig=bpy.data.objects['AFN_R0005_Rig'];stage.set_pose(rig,'neutral');fits=stage.eyes.helper_centres();m=bpy.data.materials['AFN6_Cornea'];bsdf=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
    if label=='no-cornea':
        for side in ('L','R'):bpy.data.objects['AFN6_'+side+'_Cornea'].hide_render=True
    if label=='unit-ior':bsdf.inputs['IOR'].default_value=1.
    if label=='no-screen-refraction' and hasattr(m,'use_raytrace_refraction'):m.use_raytrace_refraction=False
    path=stage.eyes.render(label,'eyes',fits,'neutral')
    records.append({'label':label,'image':path,'ior':bsdf.inputs['IOR'].default_value,'corneaHidden':label=='no-cornea','useRaytraceRefraction':getattr(m,'use_raytrace_refraction',None),'engine':s.render.engine,'exposure':s.view_settings.exposure,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'lights':[{'name':o.name,'position':list(o.location),'energy':o.data.energy,'size':getattr(o.data,'size',None),'colour':list(o.data.color)} for o in bpy.data.objects if o.type=='LIGHT']})
(E/'optical-isolation.json').write_text(json.dumps({'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'purpose':'Diagnostics only. Unit IOR and hidden cornea are not adoption candidates.','records':records},indent=2)+'\n');print('AFN_R0009_ISOLATION_DONE')
