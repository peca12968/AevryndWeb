"""Keep mandibular oral support on the jaw arc, preserving authored endpoint shapes."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0075-occlusion-authoring';OUT=S/'aevrynd-female-next-r0075-c-coordinated-oral-arc-study.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def points(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;a=np.empty((len(d.vertices),3),'f4');d.vertices.foreach_get('co',a.ravel());return a
def main():
    ref=json.loads((E/'b-build-summary.json').read_text());assert not OUT.exists() and sha(Path(ref['output']))==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];old={}
    for frame in (1,13):s.frame_set(frame);bpy.context.view_layer.update();old[frame]=points(body).copy()
    s.frame_set(1);bpy.context.view_layer.update();field=np.load(E/'b-authored-oral-field.npz',allow_pickle=False);t=np.array(ref['perToothWorldRestShiftsM'][0]);weight=np.clip(field['worldRestField']@t/(t@t),0,1);assert weight.max()>.999 and np.all(weight[field['frozenSkinBoundary']]==0)
    d=body.data;base=np.array([v.co[:] for v in d.shape_keys.key_blocks[0].data]);rest=base.copy()
    for key in d.shape_keys.key_blocks[1:]:
        if not key.name.startswith('AFN75_'):rest+=(np.array([p.co[:] for p in key.data])-base)*key.value
    a=np.array(body.matrix_world);rest=rest@a[:3,:3].T+a[:3,3];fit=json.loads((E.parent/'r0074-oral-controls/c-build-summary.json').read_text())['rigidFit'];pivot=np.array(fit['pivotWorldM']);axis=np.array(fit['axis']);axis/=np.linalg.norm(axis);theta=float(fit['angleRadians']);r=rest-pivot;parallel=(r@axis)[:,None]*axis;perp=r-parallel;cross=np.cross(axis,r);inverse=np.linalg.inv(a[:3,:3]);ctrl=bpy.data.objects['AFN74_ORAL_CONTROLS']
    expressions={'RADIAL':'cos('+repr(theta)+'*jaw)-1-jaw*('+repr(float(np.cos(theta)-1))+')','TANGENT':'sin('+repr(theta)+'*jaw)-jaw*('+repr(float(np.sin(theta)))+')'}
    for name,v in [('RADIAL',perp),('TANGENT',cross)]:
        delta=weight[:,None]*v@inverse.T;k=body.shape_key_add(name='AFN75_MANDIBULAR_ARC_'+name,from_mix=False);k.relative_key=d.shape_keys.key_blocks[0];k.slider_min=-1;k.slider_max=1;k.data.foreach_set('co',(base+delta).astype('f4').ravel());dr=k.driver_add('value').driver;dr.type='SCRIPTED';dr.expression=expressions[name];var=dr.variables.new();var.name='jaw';var.type='SINGLE_PROP';var.targets[0].id=ctrl;var.targets[0].data_path='["jaw_open"]'
    errors={}
    for frame in (1,13):s.frame_set(frame);bpy.context.view_layer.update();err=float(np.linalg.norm(points(body)-old[frame],axis=1).max());assert err<1e-6;errors[frame]=err
    s.frame_set(1);bpy.context.view_layer.update();ctrl['AFN75_scope']='One coherent lower-arch rest placement, shared lower gum/tongue support and endpoint-preserving mandibular arc compensation. Teeth unchanged in size, full jaw opening unchanged. Complete contacts/runtime still require qualification.';s['AFN75_scope']=ctrl['AFN75_scope'];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    result={'source':ref['output'],'sourceSha256':ref['outputSha256'],'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'wholeArchShiftWorldM':t.tolist(),'openingAngleRadiansUnchanged':theta,'endpointMaximumBodyLocalErrorsM':errors,'newKeys':list(expressions),'weightRange':[float(weight.min()),float(weight.max())],'formula':'w*(rigidJawArc(q)-q*rigidJawArc(1)); zero at both endpoints, corrects linear-blend chord shrink of oral support. Original native endpoint residual remains.','assumptions':'Source-derived jaw affinity from constrained support field, not calibrated clinical biomechanics. Upper gum/cavity still combined.','contactNaturalDynamicsAndRuntimeAccepted':False};(E/'c-build-summary.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('R75_ORAL_ARC_CORRECTION_SAVED',errors,flush=True)
if __name__=='__main__':main()
