"""Save exact rejected pilots alongside untouched complete working source."""
import bpy,importlib.util,time,json
from pathlib import Path
import numpy as np
sp=importlib.util.spec_from_file_location('r45review',Path(__file__).with_name('build-female-next-r0045-closed-lids.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
b=a.b;i=a.i;f=a.f;E=a.E;S=a.S;SRC=a.SRC;OUT=S/'aevrynd-female-next-r0045-rejected-closed-structure-studies.blend'
def main():
    tick=time.time();assert b.sha(SRC)=='d62c180a5af61f6f8d800926b101738c89a8fbe7785fe1054fd655fd018824da';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;original=f.state();body=bpy.data.objects[b.BODY];col=bpy.data.collections.new('AFN45_REJECTED_TECHNICAL_STUDIES_NOT_PRODUCTION');s.collection.children.link(col);objects=[];records=[]
    mat=bpy.data.materials.new('AFN45_DIAGNOSTIC_CLAY_NOT_SKIN_COMPARISON');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.38,.32,.29,1);bs.inputs['Roughness'].default_value=.65
    for label,file,pk,tk in [('A_CSG_CLOSED_REJECTED','a-native-closed-body.npz','positionsWorld','triangles'),('B_AUTHORED_HALF_REJECTED','b-authored-native-shapes.npz','pose0.5','triangles')]:
        d=np.load(E/file);P=d[pk];T=d[tk];mesh=bpy.data.meshes.new('AFN45_'+label);mesh.from_pydata(P.tolist(),[],T.tolist());mesh.update();o=bpy.data.objects.new(mesh.name,mesh);col.objects.link(o);mesh.materials.append(mat)
        for p in mesh.polygons:p.use_smooth=True
        o['aevrynd_status']='REJECTED_NATIVE_PILOT_NOT_ANIMATION_OR_WORKING_MODEL';o['warning']='Diagnostic clay/native resolution. Original neutral attachments are not updated or qualified. Not matched appearance A/B. See independent actual geometry evidence.';o.hide_render=True;o.hide_set(True);objects.append(o);records.append({'object':o.name,'cache':str(E/file),'vertices':len(P),'triangles':len(T)})
    text=bpy.data.texts.new('AFN45_README_REJECTIONS');text.write('Default view is unchanged complete r42B working character, not a new quality improvement.\nAFN45_REJECTED collection contains two exact native geometry failures for inspection.\nHide original GEO-body_female_realistic and show one diagnostic object at a time.\nA has nonmanifold/body-eye/self failures; B fails at half closure. Neutral lash/wet tissues are NOT moved.\nCC0 MakeHuman pose-unit data is a motion reference, not an accepted morph for this topology.\n');s['AFN45_status']='REJECTED_TECHNICAL_STUDIES_WORKING_SOURCE_R42B_UNCHANGED';b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    body.hide_render=True;body.hide_set(True);f.E=E
    for o,record in zip(objects,records):
        o.hide_render=False;o.hide_set(False);f.render(record['object'],('face',));o.hide_render=True;o.hide_set(True)
    bpy.ops.wm.open_mainfile(filepath=str(OUT));assert f.state()==original
    for record in records:
        o=bpy.data.objects[record['object']];P,T=b.evaluated(o,True);d=np.load(record['cache']);pk='positionsWorld' if 'positionsWorld' in d else 'pose0.5';assert np.array_equal(T,d['triangles']);assert np.linalg.norm(P-d[pk],axis=1).max()<2e-7
    a.save('rejected-studies-reopen-verification.json',{'source':str(OUT),'sourceSha256':b.sha(OUT),'sourceBytes':OUT.stat().st_size,'status':'PASS_EXACT_REOPENED_REJECTED_PILOTS_ONLY','defaultCompleteR42BVisibleStateExact':True,'sourceWorkingFileUntouched':True,'records':records,'renderScope':'Actual native diagnostic clay with unchanged neutral attachments, not new production appearance A/B','seconds':time.time()-tick});print('R45_REJECTED_STUDIES_SAVED',str(OUT),time.time()-tick,flush=True)
if __name__=='__main__':main()
