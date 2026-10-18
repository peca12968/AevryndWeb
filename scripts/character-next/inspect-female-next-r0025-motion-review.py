"""Reopened actual playback must retain the verified dental/skin endpoints."""
import bpy,importlib.util,json,math
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('b25',Path(__file__).with_name('build-female-next-r0025-dental-contact.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def main():
    report=json.loads((b.E/'a-motion-render.json').read_text(encoding='utf8'));path=Path(report['source']);assert b.sha(path)==report['sha256'];bpy.ops.wm.open_mainfile(filepath=str(path))
    cache=np.load(b.S/'aevrynd-female-next-r0024-oral-fit-data.npz');body=bpy.data.objects['AFN_R0008_Body'];rows=[]
    for frame,w in ((1,0.),(13,.2),(25,0.)):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();actual=b.prior.evaluate(body);error=float(np.linalg.norm(actual-(cache['bodyNeutral']+cache['bodyDeltaOpen']*w),axis=1).max());assert error<5.e-7
        rows.append({'frame':frame,'weight':float(bpy.data.objects['AFN24_MouthControl']['open']),'bodyErrorM':error,'lowerAngle':float(bpy.data.objects['AFN24_LowerRigidControl'].rotation_axis_angle[0])})
    images=[{'name':i.name,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'];assert all(i['packed'] for i in images) and not bpy.data.libraries
    for o in bpy.data.objects:
        for target in [o]+([o.data.shape_keys] if o.type=='MESH' and o.data.shape_keys else []):
            if target.animation_data:assert all(c.driver.is_valid for c in target.animation_data.drivers)
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    geometry={o.name:{'geometrySha256':b.prior.solid.geom(o),'parent':o.parent.name,'matrixBasis':[v for row in o.matrix_basis for v in row]} for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN25_')}
    controls={}
    for name in ('AFN24_UpperRigidControl','AFN24_LowerRigidControl'):
        o=bpy.data.objects[name];controls[name]={'parent':o.parent.name,'parentType':o.parent_type,'parentBone':o.parent_bone,'matrixParentInverse':[v for row in o.matrix_parent_inverse for v in row],'location':list(o.location),'scale':list(o.scale),'rotationAxisAngle':list(o.rotation_axis_angle),'drivers':[{'path':c.data_path,'index':c.array_index,'expression':c.driver.expression,'targets':[(var.name,var.targets[0].id.name,var.targets[0].data_path) for var in c.driver.variables]} for c in o.animation_data.drivers]}
    b.save('a-saved-motion-verification.json',{'asset':str(path),'sha256':b.sha(path),'status':'PASS_REOPEN_AND_SAMPLED_PLAYBACK_ONLY','frames':rows,'images':images,'externalLibraries':len(bpy.data.libraries),'safeModeAutoexecFail':bpy.app.autoexec_fail,'teethGeometry':geometry,'jawControls':controls,'limits':'Playback correctness only; dental sweep is separately scoped, other mouth contacts remain unresolved. Geometry/control fingerprints allow reuse only while the exact mesh and motion contract remain unchanged.'});print('R0025_MOTION_REOPEN_PASS',flush=True)
if __name__=='__main__':main()
