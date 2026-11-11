from pathlib import Path
from runpy import run_path
from hashlib import file_digest,sha256
import json
import bpy
import numpy as np
from mathutils import Matrix
ROOT=Path(__file__).resolve().parent
PREVIOUS=ROOT.parent/'r0484-root-to-tip-construction'
DEST=ROOT/'female-next-r0485-native-work-UNACCEPTED.blend'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def main():
    proof=read(PREVIOUS/'volume-source-receipt.json');assert sha(Path(proof['source']['path']))==proof['source']['sha256']
    assert not DEST.exists()
    bpy.ops.wm.open_mainfile(filepath=proof['source']['path'],load_ui=False,use_scripts=False)
    original=bpy.data.objects['R484 complete hair | B']
    work=original.copy();work.data=original.data.copy();work.name='R485 Native complete root-to-tip hair';work.data.name='R485 Native sculpt editable curves'
    bpy.context.scene.collection.objects.link(work)
    methods=run_path(str(ROOT.parent/'r0483-layered-bob-rest/author-r0483.py'))
    atlas=methods['attachment_atlas'];atlas.__globals__['UV_NAME']='R485 Neutral scalp attachment atlas'
    body=bpy.data.objects['R482 archived complete neutral skin']
    uv=atlas(body,{'work':work})
    for tag in ('control','A','B'):
        obj=bpy.data.objects[f'R484 complete hair | {tag}'];obj.hide_render=True;obj.hide_set(True)
    work.hide_render=False;work.hide_set(False)
    bpy.ops.object.select_all(action='DESELECT');work.select_set(True);bpy.context.view_layer.objects.active=work
    shot=read(ROOT.parent/'r0470-independent-posterior-locks/shot-A-face.json')['shot']
    scene=bpy.context.scene;scene.camera.matrix_world=Matrix(shot['camera']);scene.camera.data.lens=shot['lens']
    scene.render.threads_mode='FIXED';scene.render.threads=4
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.region_3d.view_perspective='CAMERA';space.region_3d.view_camera_zoom=15.
                space.shading.type='SOLID';space.shading.color_type='MATERIAL'
    text=bpy.data.texts.new('Aevrynd_R485_Native_Operation_Note')
    text.write('Unaccepted independent native Curve Sculpt work copy. Surface UV atlas is attached to the verified neutral skin fixture. Original follicles, identity and binding fields remain unchanged. Native viewport operation, final shape, finite contact, hair motion and runtime acceptance are pending. Keep all inherited author and license notices.\n')
    p=np.empty((24831,80,3),dtype='f4');work.data.position_data.foreach_get('vector',p.ravel())
    assert sha256(p.tobytes()).hexdigest()==proof['positionHashes']['B']
    np.savez_compressed(ROOT/'before-native.npz',position=p)
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    record=dict(source=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=sha(DEST)),parent=proof['source'],
        object=work.name,positionHash=sha256(p.tobytes()).hexdigest(),uvHash=uv,curveCount=24831,pointsPerCurve=80,
        nativeOperationPerformed=False,rootUVSurface=body.name,contactStatus='NOT_EVALUATED')
    (ROOT/'prepared-source-receipt.json').write_bytes(json.dumps(record,indent=2).encode('utf8'))
    print(json.dumps(record,indent=2),flush=True)
if __name__=='__main__':main()
