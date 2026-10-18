"""Verify all source meshes and unrelated scene controls in both saved styles."""
import bpy,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('b27',Path(__file__).with_name('build-female-next-r0027-swept-fringe.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def main():
    bpy.ops.wm.open_mainfile(filepath=str(b.SRC));b.old.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');meshes={o.name:b.old.solid.geom(o) for o in bpy.data.objects if o.type=='MESH'};state=b.old.base.snapshot();rows=[]
    for label in ('a','b'):
        report=json.loads((b.E/(label+'-build-verification.json')).read_text(encoding='utf8'));path=Path(report['output']);assert b.old.base.sha(path)==report['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(path));b.old.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');assert meshes=={n:b.old.solid.geom(bpy.data.objects[n]) for n in meshes} and b.old.base.snapshot()==state;images=[{'name':i.name,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'];assert all(i['packed'] for i in images) and not bpy.data.libraries;rows.append({'label':label,'asset':str(path),'sha256':report['outputSha256'],'allSourceMeshGeometryExact':True,'headSkinRigWeightsUVMaterialsLightsSnapshotExact':True,'images':images,'linkedLibraries':0})
    b.save('saved-controls-verification.json',{'source':str(b.SRC),'sourceSha256':b.old.base.sha(b.SRC),'sourceMeshGeometry':meshes,'candidates':rows,'status':'PASS_UNRELATED_STATE_AND_REOPEN_ONLY_NOT_REALISM'});print('R0027_ALL_MESH_CONTROL_PASS',flush=True)
if __name__=='__main__':main()
