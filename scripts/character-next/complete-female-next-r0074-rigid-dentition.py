"""Correct the independently detected upper dental/soft-gum subdivision coupling."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
from mathutils import Matrix
sp=importlib.util.spec_from_file_location('oral74b',Path(__file__).with_name('build-female-next-r0074-rigid-jaw.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
E=m.E;OUT=m.S/'aevrynd-female-next-r0074-c-rigid-dentition-controls-study.blend'
def main():
    tick=time.time();ref=json.loads((E/'b-build-summary.json').read_text());assert not OUT.exists() and m.m.sha(Path(ref['output']))==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();old=bpy.data.objects['AFN74_UPPER_TEETH'];rest=m.geometry(old);pivot=rest.mean(0)
    mesh=bpy.data.meshes.new_from_object(old.evaluated_get(bpy.context.evaluated_depsgraph_get()),preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());mesh.name='AFN74_UPPER_TEETH_RIGID_REST';mesh.transform(Matrix.Translation((-pivot).tolist())@old.matrix_world)
    rig=bpy.data.objects['AFN69_BODY_CONTROLS'];anchor=bpy.data.objects.new('AFN74_HEAD_DENTAL_FRAME',None);s.collection.objects.link(anchor);anchor.location=pivot.tolist();anchor.empty_display_size=.02;con=anchor.constraints.new('CHILD_OF');con.target=rig;con.subtarget='Head';con.inverse_matrix=(rig.matrix_world@rig.pose.bones['Head'].matrix).inverted()
    new=bpy.data.objects.new('AFN74_UPPER_TEETH_RIGID',mesh);bpy.data.collections['AFN74_10_DISPLAY_LAYERS'].objects.link(new);new.parent=anchor;new.matrix_parent_inverse=Matrix.Identity(4);new['editing']='Independent rest upper dental mesh, rigid Head attachment. Does not inherit moving gum subdivision.';old.name='AFN74_UPPER_TEETH_SOFT_SOURCE_REFERENCE';old.hide_render=True;old.hide_set(True);bpy.context.view_layer.update();neutral=float(np.linalg.norm(m.geometry(new)-rest,axis=1).max());assert neutral<1e-6
    rows=[]
    for frame in (7,13,31,37):
        s.frame_set(frame);bpy.context.view_layer.update();err=float(np.linalg.norm(m.geometry(new)-rest,axis=1).max());assert err<1e-6;rows.append({'frame':frame,'maximumUpperDentalWorldDeltaM':err})
    s.frame_set(1);bpy.context.view_layer.update();ctrl=bpy.data.objects['AFN74_ORAL_CONTROLS']
    ctrl['layer_scope']='Two independently editable actual dental arch meshes,16 tooth UV charts each; rigid upper Head attachment and lower jaw arc. Soft display layers share native source; upper gum/cavity combined.'
    s['AFN74_scope']='Complete woman: native soft-tissue mouth expression, two actual rigid dental arch meshes and generated oral display layers. Limited operation, not calibrated jaw anatomy or full contact/natural dynamics/engine acceptance.'
    m.m.m.k.b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    m.m.save('c-build-summary.json',{'source':ref['output'],'sourceSha256':ref['outputSha256'],'output':str(OUT),'outputSha256':m.m.sha(OUT),'outputBytes':OUT.stat().st_size,'method':'Both dental arches use actual rigid rest meshes. Lower uses source-fitted jaw arc; upper follows Head independently of soft gums.','rigidFit':ref['rigidFit'],'correctionReason':'Independent B readback found22.008micrometre upper dental movement caused by subdividing connected soft gums, despite zero native upper-tooth offsets. Fixed construction, not relaxed checker.','neutralUpperMaximumWorldErrorM':neutral,'upperDentalChecks':rows,'independentEditableDentalArchMeshes':2,'toothUVChartsPerArch':16,'softLayersStillSharedMaster':True,'upperGumCavityCombined':True,'contactNaturalDynamicsAndRuntimeAccepted':False,'secondsBeforePilot':time.time()-tick})
    s.frame_set(13);bpy.context.view_layer.update();m.m.save('c-open-pilot-controls.json',[m.m.render('c-open','face'),m.m.render('c-open','body-face')]);print('R74_RIGID_DENTITION_COMPLETE',time.time()-tick,flush=True)
if __name__=='__main__':main()
