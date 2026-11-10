from pathlib import Path
from runpy import run_path
from hashlib import file_digest,sha256
from time import perf_counter
import json
import bpy
import numpy as np
from mathutils import Matrix
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()

def main():
    proof=read(ROOT/'authored-source-receipt.json');assert sha(Path(proof['source']['path']))==proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=proof['source']['path'],load_ui=False,use_scripts=False)
    scene=bpy.context.scene;scene.render.use_persistent_data=False
    a=run_path(str(ROOT.parent/'r0480-lock-clearance-projection/author-r0480.py'))
    skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD']
    skin_stamp=[a['groom'].arr_sha(x) for x in a['probe']['u'].evaluated(skin)]
    assert skin_stamp==read(ROOT/'assembled-source-receipt.json')['completeSkinHashesExactlyMatchR480']
    reference=read(ROOT.parent/'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform=reference['transform'];scene.view_settings.look=reference['look'];scene.view_settings.exposure=reference['exposure']
    for key,value in reference['cycles'].items():setattr(scene.cycles,key,value)
    assert bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].hide_render
    assert bpy.data.objects['R482 archived complete neutral skin'].hide_render
    hashes={}
    for tag in ('control','A'):
        data=bpy.data.objects[f'R484 complete hair | {tag}'].data
        p=np.empty((len(data.points),3),dtype='f4');data.position_data.foreach_get('vector',p.ravel())
        hashes[tag]=sha256(p.tobytes()).hexdigest();assert hashes[tag]==proof['positionHashes'][tag]
    renders={}
    for view in ('rear-oblique','face','posterior-detail','opposite-profile','full-body'):
        shot=read(ROOT.parent/f'r0470-independent-posterior-locks/shot-A-{view}.json')['shot']
        assert shot['frame']==1
        scene.camera.matrix_world=Matrix(shot['camera']);scene.camera.data.lens=shot['lens'];scene.camera.data.type=shot['cameraType']
        scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage=shot['resolution']
        scene.cycles.samples=shot['samples'];scene.cycles.seed=shot['seed'];scene.cycles.use_denoising=shot['denoising']
        assert scene.view_settings.exposure==shot['exposure']
        for tag in ('control','A'):
            for name in ('control','A'):
                obj=bpy.data.objects[f'R484 complete hair | {name}'];obj.hide_render=name!=tag;obj.hide_set(name!=tag)
            bpy.context.view_layer.update()
            output=ROOT/f'{tag}-{view}.png';assert not output.exists()
            scene.render.filepath=str(output);started=perf_counter();bpy.ops.render.render(write_still=True)
            renders[f'{tag}:{view}']=dict(path=str(output),sha256=sha(output),camera=shot['camera'],lens=shot['lens'],
                exposure=scene.view_settings.exposure,frame=1,blink=0.,cameraReferenceBlink=shot['blink'],samples=scene.cycles.samples,seed=scene.cycles.seed,
                skinHashes=skin_stamp,geometryHash=hashes[tag],seconds=perf_counter()-started)
            (ROOT/'preview-progress.json').write_bytes(json.dumps(dict(source=proof['source'],renders=renders),indent=2).encode('utf8'))
            print('R484_PREVIEW',tag,view,flush=True)
    (ROOT/'preview-receipt.json').write_bytes(json.dumps(dict(source=proof['source'],renders=renders,
        completeCurrentWomanComponents=True,originalMeshReferenceHidden=True,contactOrMotionAccepted=False,
        libraries=[lib.filepath for lib in bpy.data.libraries],linkedIDs=[dict(name=i.name,type=i.bl_rna.identifier,library=i.library.filepath) for i in bpy.data.user_map() if i.library]),indent=2).encode('utf8'))

if __name__=='__main__':main()
