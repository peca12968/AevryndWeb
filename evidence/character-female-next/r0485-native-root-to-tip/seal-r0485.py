"""Preserve the native checkpoints as explicit branches without changing their shapes."""
from pathlib import Path
from hashlib import file_digest,sha256
import json
import bpy
import numpy as np
from mathutils import Matrix
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'female-next-r0485-native-groom-review-UNACCEPTED.blend'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def main():
    assert not DEST.exists()
    receipts={tag:read(ROOT/f'native-{tag}-receipt.json') for tag in ('A','B')}
    for row in receipts.values():assert sha(Path(row['source']['path']))==row['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=receipts['B']['source']['path'],load_ui=False,use_scripts=False)
    if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    original=bpy.data.objects['R485 Native complete root-to-tip hair'];original.name='R485 complete hair | B'
    current=np.empty((24831,80,3),dtype='f4');original.data.position_data.foreach_get('vector',current.ravel())
    assert sha256(current.tobytes()).hexdigest()==receipts['B']['positionHash']
    modes={'B':original};hashes={'B':receipts['B']['positionHash']}
    for tag,path in (('control','before-native.npz'),('A','native-A-capture.npz')):
        p=np.load(ROOT/path,allow_pickle=False)['position']
        obj=original.copy();obj.data=original.data.copy();obj.name=f'R485 complete hair | {tag}';obj.data.name=f'R485 preserved native data | {tag}'
        bpy.context.scene.collection.objects.link(obj);obj.data.position_data.foreach_set('vector',p.ravel());obj.data.update_tag();obj.update_tag()
        obj.hide_render=True;obj.hide_set(True);modes[tag]=obj;hashes[tag]=sha256(p.tobytes()).hexdigest()
        if tag=='A':assert hashes[tag]==receipts['A']['positionHash']
    # Restore the known fixed portrait camera; this affects every study identically.
    shot=read(ROOT.parent/'r0470-independent-posterior-locks/shot-A-face.json')['shot']
    scene=bpy.context.scene;scene.camera.matrix_world=Matrix(shot['camera']);scene.camera.data.type=shot['cameraType'];scene.camera.data.lens=shot['lens']
    bpy.ops.object.select_all(action='DESELECT');original.select_set(True);bpy.context.view_layer.objects.active=original
    note=bpy.data.texts.new('Aevrynd_R485_Actual_Native_Operation')
    note.write((ROOT/'native-actions.json').read_text(encoding='utf8'))
    scene['R485_Status']='Unaccepted native complete-groom sculpt studies. Surface collision during authoring is not independent contact verification.'
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    bpy.ops.wm.open_mainfile(filepath=str(DEST),load_ui=False,use_scripts=False)
    after={}
    for tag in ('control','A','B'):
        d=bpy.data.objects[f'R485 complete hair | {tag}'].data;p=np.empty((len(d.points),3),dtype='f4');d.position_data.foreach_get('vector',p.ravel())
        assert sha256(p.tobytes()).hexdigest()==hashes[tag]
        after[tag]=dict(object=f'R485 complete hair | {tag}',positionHash=hashes[tag],curves=len(d.curves),points=len(d.points),materials=[m.name for m in d.materials])
    external=[l.filepath for l in bpy.data.libraries]+[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file]
    assert not external
    record=dict(source=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=sha(DEST)),nativeCheckpointReceipts=receipts,
        modes=after,externalDependencies=external,scope='Exact native checkpoint branch preservation. No extra shape, radius or shader changes in sealing.',
        appearanceDecision='PENDING_MATCHED_RENDER_REVIEW',nativeOperationPerformed=True,contactOrMotionAccepted=False)
    (ROOT/'sealed-source-receipt.json').write_bytes(json.dumps(record,indent=2).encode('utf8'))
    print(json.dumps(record['source']|dict(modes=after,externalDependencies=external),indent=2),flush=True)
if __name__=='__main__':main()
