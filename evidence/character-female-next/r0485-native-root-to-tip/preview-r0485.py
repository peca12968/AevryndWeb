"""Render all position banks through one persistent native curve object."""
from pathlib import Path
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
    proof=read(ROOT/'sealed-source-receipt.json');assert sha(Path(proof['source']['path']))==proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=proof['source']['path'],load_ui=False,use_scripts=False)
    scene=bpy.context.scene;scene.render.use_persistent_data=False
    if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    banks={}
    for tag,row in proof['modes'].items():
        obj=bpy.data.objects[row['object']];d=obj.data;p=np.empty((24831,80,3),dtype='f4');d.position_data.foreach_get('vector',p.ravel())
        assert sha256(p.tobytes()).hexdigest()==row['positionHash'];banks[tag]=p
        obj.hide_render=True;obj.hide_set(True)
    carrier=bpy.data.objects['R485 complete hair | B'];carrier.hide_render=False;carrier.hide_set(False)
    reference=read(ROOT.parent/'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform=reference['transform'];scene.view_settings.look=reference['look'];scene.view_settings.exposure=reference['exposure']
    for key,value in reference['cycles'].items():setattr(scene.cycles,key,value)
    assert bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].hide_render
    renders={}
    for view in ('face','rear-oblique','posterior-detail','opposite-profile','full-body'):
        shot=read(ROOT.parent/f'r0470-independent-posterior-locks/shot-A-{view}.json')['shot']
        scene.camera.matrix_world=Matrix(shot['camera']);scene.camera.data.type=shot['cameraType'];scene.camera.data.lens=shot['lens']
        scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage=shot['resolution']
        scene.cycles.samples=shot['samples'];scene.cycles.seed=shot['seed'];scene.cycles.use_denoising=shot['denoising']
        for tag in ('control','A','B'):
            carrier.data.position_data.foreach_set('vector',banks[tag].ravel());carrier.data.update_tag();carrier.update_tag();bpy.context.view_layer.update()
            output=ROOT/f'{tag}-{view}.png';assert not output.exists()
            scene.render.filepath=str(output);start=perf_counter();bpy.ops.render.render(write_still=True)
            renders[f'{tag}:{view}']=dict(path=str(output),sha256=sha(output),camera=shot['camera'],lens=shot['lens'],exposure=scene.view_settings.exposure,
                frame=scene.frame_current,blink='source neutral state',samples=scene.cycles.samples,seed=scene.cycles.seed,
                carrierObject=carrier.name,carrierData=carrier.data.name,geometryHash=proof['modes'][tag]['positionHash'],seconds=perf_counter()-start)
            (ROOT/'preview-progress.json').write_bytes(json.dumps(dict(source=proof['source'],renders=renders),indent=2).encode('utf8'))
            print('R485_PREVIEW',tag,view,flush=True)
    assert sha(Path(proof['source']['path']))==proof['source']['sha256']
    (ROOT/'preview-receipt.json').write_bytes(json.dumps(dict(source=proof['source'],renders=renders,sameObjectAndDataForAllModes=True,
        storedSourceUnchanged=True,onlyPositionBankSwitched=True),indent=2).encode('utf8'))
if __name__=='__main__':main()
