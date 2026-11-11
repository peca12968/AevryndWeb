from pathlib import Path
from hashlib import file_digest,sha256
import bpy,numpy as np,json
from mathutils import Matrix
from time import perf_counter
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def main():
    proof=read(R/'construction-receipt.json');src=Path(proof['source']['path']);assert sha(src)==proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False)
    scene=bpy.context.scene;scene.render.use_persistent_data=False
    control=bpy.data.objects[proof['controlObject']];candidate=bpy.data.objects[proof['candidateObject']]
    banks={};fields={}
    for tag,obj in [('control',control),('candidate',candidate)]:
        d=obj.data;p=np.empty((24831,80,3),dtype='f4');d.position_data.foreach_get('vector',p.ravel());banks[tag]=p
        fields[tag]={}
        for attr in control.data.attributes:
            if attr.name=='position':continue
            a=d.attributes[attr.name];width={'FLOAT_VECTOR':3,'FLOAT2':2}.get(a.data_type,1)
            out=np.empty((len(a.data),width),dtype='i4' if a.data_type=='INT' else 'f4');a.data.foreach_get('vector' if width>1 else 'value',out.ravel())
            fields[tag][a.name]=sha256(out.tobytes()).hexdigest()
    assert fields['control']==fields['candidate'];assert np.array_equal(banks['control'][:,0],banks['candidate'][:,0]);assert np.isfinite(banks['candidate']).all()
    assert sha256(banks['candidate'].tobytes()).hexdigest()==proof['positionHash']
    construction=np.load(R/'primary-guide-construction.npz',allow_pickle=False)
    guides=construction['guides'];owner=construction['ownerGuide'];weights=construction['ownerWeight'];roots=banks['candidate'][:,0]
    reconstructed=roots[:,None]+np.sum((guides[owner]-guides[owner][:,:,0,None,:])*weights[:,:,None,None],axis=1)
    reconstructed[:,0]=roots
    max_error=float(np.max(np.abs(reconstructed-banks['candidate'])))
    assert max_error<2e-7
    dependencies=dict(libraries=[l.filepath for l in bpy.data.libraries],images=[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file])
    assert not any(dependencies.values())
    stats=dict(sceneObjects=len(scene.objects),meshVertices=sum(len(o.data.vertices) for o in scene.objects if o.type=='MESH'),meshPolygons=sum(len(o.data.polygons) for o in scene.objects if o.type=='MESH'),armatureBones=sum(len(o.data.bones) for o in scene.objects if o.type=='ARMATURE'),shapeKeys=sum(max(0,len(o.data.shape_keys.key_blocks)-1) for o in scene.objects if o.type=='MESH' and o.data.shape_keys),materials=len(bpy.data.materials),images=len(bpy.data.images),hairCurves=24831,hairPoints=1986480,primaryGuides=len(guides))
    (R/'reopen-verification.json').write_text(json.dumps(dict(source=proof['source'],rootsBitIdentical=True,unchangedFields=fields,guideInterpolationMaxAbsErrorMetres=max_error,externalDependencies=dependencies,stats=stats,finitePoints=True,collisionCount=None,minimumSignedGapMetres=None,testedPose='neutral only; appearance review',dynamics='NOT_TESTED',engineTiming='NOT_TESTED'),indent=2),encoding='utf8')
    # Same carrier and data for both banks, keeping shading random identity fixed.
    for o in bpy.data.objects:
        if o.type=='CURVES':o.hide_render=True;o.hide_set(True)
    candidate.hide_render=False;candidate.hide_set(False)
    reference=read(R.parent/'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform=reference['transform'];scene.view_settings.look=reference['look'];scene.view_settings.exposure=reference['exposure']
    for key,value in reference['cycles'].items():setattr(scene.cycles,key,value)
    renders={}
    for view in ('face','rear-oblique','opposite-profile','posterior-detail','full-body'):
        shot=read(R.parent/f'r0470-independent-posterior-locks/shot-A-{view}.json')['shot']
        scene.camera.matrix_world=Matrix(shot['camera']);scene.camera.data.type=shot['cameraType'];scene.camera.data.lens=shot['lens']
        scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage=shot['resolution']
        scene.cycles.samples=shot['samples'];scene.cycles.seed=shot['seed'];scene.cycles.use_denoising=shot['denoising']
        for tag in ('control','candidate'):
            candidate.data.position_data.foreach_set('vector',banks[tag].ravel());candidate.data.update_tag();candidate.update_tag();bpy.context.view_layer.update()
            output=R/f'{tag}-{view}.png';assert not output.exists();scene.render.filepath=str(output);start=perf_counter();bpy.ops.render.render(write_still=True)
            renders[f'{tag}:{view}']=dict(path=str(output),sha256=sha(output),seconds=perf_counter()-start,camera=shot['camera'],lens=shot['lens'],exposure=scene.view_settings.exposure,samples=scene.cycles.samples,seed=scene.cycles.seed,carrier=candidate.name,positionHash=sha256(banks[tag].tobytes()).hexdigest())
            (R/'preview-progress.json').write_text(json.dumps(dict(source=proof['source'],renders=renders),indent=2),encoding='utf8');print('R486_PREVIEW',tag,view,flush=True)
    assert sha(src)==proof['source']['sha256']
    (R/'preview-receipt.json').write_text(json.dumps(dict(source=proof['source'],renders=renders,sourceUnchanged=True,onlyPositionBankSwitched=True),indent=2),encoding='utf8')
if __name__=='__main__':main()
