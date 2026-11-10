from pathlib import Path
from runpy import run_path
from hashlib import sha256
import json
import numpy as np
import bpy
from mathutils import Matrix
from time import perf_counter

ROOT=Path(__file__).resolve().parent
a=run_path(str(ROOT/'author-r0483.py'))
DEST=ROOT/'female-next-r0483-layered-bob-drafts-UNACCEPTED.blend'


def main():
    previous=a['read'](ROOT/'shape-receipt.json');assert a['sha'](Path(previous['source']['path']))==previous['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=previous['source']['path'],load_ui=False,use_scripts=False)
    baseobj=bpy.data.objects['R483 complete groom | base'];data=baseobj.data
    coords=np.empty((len(data.points),3),dtype='f4');data.position_data.foreach_get('vector',coords.ravel());base=coords.reshape(-1,80,3)
    ids=np.empty(len(data.curves),dtype='i4');data.attributes['AFN409_CURVE_ID'].data.foreach_get('value',ids)
    stats={};stamps={'base':sha256(base.tobytes()).hexdigest()}
    for tag in ('A','B'):
        q,stats[tag]=a['strand_shape'](base,ids,tag)
        obj=bpy.data.objects[f'R483 complete groom | {tag}'];obj.data.position_data.foreach_set('vector',q.ravel());obj.data.update_tag();obj.update_tag()
        assert np.array_equal(q[:,0],base[:,0]);stamps[tag]=sha256(q.tobytes()).hexdigest()
        np.savez_compressed(ROOT/f'prepared-shape-{tag}.npz',position=q,curveIDs=ids)
    assert not DEST.exists();bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    bpy.ops.wm.open_mainfile(filepath=str(DEST),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    for tag,digest in stamps.items():
        obj=bpy.data.objects[f'R483 complete groom | {tag}'];q=np.empty((len(obj.data.points),3),dtype='f4');obj.data.position_data.foreach_get('vector',q.ravel())
        assert sha256(q.tobytes()).hexdigest()==digest
        assert obj.data.surface.name=='R483 complete neutral skin' and obj.data.surface_uv_map==a['UV_NAME']
        assert obj.data.attributes['surface_uv_coordinate'].data_type=='FLOAT2'
    r470=ROOT.parent/'r0470-independent-posterior-locks'
    shots={}
    for view in ('posterior-detail','rear-oblique','face','opposite-profile','full-body'):
        shot=a['read'](r470/f'shot-A-{view}.json')['shot']
        scene.camera.matrix_world=Matrix(shot['camera']);scene.camera.data.lens=shot['lens'];bpy.context.view_layer.update()
        for tag in ('base','A','B'):
            for name in ('base','A','B'):
                obj=bpy.data.objects[f'R483 complete groom | {name}'];obj.hide_render=name!=tag;obj.hide_set(name!=tag)
            file=ROOT/f'{tag}-{view}.png';assert not file.exists();scene.render.filepath=str(file)
            started=perf_counter();bpy.ops.render.render(write_still=True)
            shots[f'{tag}:{view}']=dict(file=str(file),sha256=a['sha'](file),camera=shot['camera'],lens=shot['lens'],exposure=scene.view_settings.exposure,seconds=perf_counter()-started)
            print('R483_PREVIEW',tag,view,flush=True)
    proof=previous|dict(source=dict(path=str(DEST),sha256=a['sha'](DEST),bytes=DEST.stat().st_size),
        neutralPositionHash=stamps,variants=stats,renders=shots,nativeSculptAction='Not performed; Windows permission dialog awaiting user handling.')
    (ROOT/'draft-receipt.json').write_bytes(json.dumps(proof,indent=2).encode('utf8'))
    print('R483_DRAFTS',stats,flush=True)


if __name__=='__main__':
    main()