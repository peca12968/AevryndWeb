from pathlib import Path
from runpy import run_path
from time import perf_counter
import numpy as np
import bpy
from mathutils import Matrix

ROOT=Path(__file__).resolve().parent
a=run_path(str(ROOT/'author-r0482.py'))
old,groom=a['old'],a['groom']
DEST=ROOT/'female-next-r0482-global-groom-surface-UNACCEPTED.blend'


def main():
    source=old.read(ROOT/'source-receipt.json')
    surface=old.read(ROOT/'surface-receipt.json')
    assert old.file_sha(Path(source['source']['path']))==source['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=source['source']['path'],load_ui=False)
    banks={}; rows=source['branches'].copy()
    for tag,item in surface['variants'].items():
        file=ROOT/item['file']; assert old.file_sha(file)==item['sha256']
        with np.load(file,allow_pickle=False) as f:
            q=f['position']; banks[tag]=q
        obj=bpy.data.objects[rows[tag]['object']]
        obj.data.position_data.foreach_set('vector',q.ravel()); obj.data.update_tag(); obj.update_tag()
        rows[tag]=rows[tag]|dict(positionHash=groom.arr_sha(q))
    for tag,row in rows.items():
        obj=bpy.data.objects[row['object']]; obj.hide_render=tag!='B'; obj.hide_set(tag!='B')
    assert not DEST.exists()
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    bpy.ops.wm.open_mainfile(filepath=str(DEST),load_ui=False)
    scene=bpy.context.scene
    for tag,row in rows.items():
        data=bpy.data.objects[row['object']].data
        q=np.empty((len(data.points),3),dtype='f4'); data.position_data.foreach_get('vector',q.ravel()); assert groom.arr_sha(q)==row['positionHash']
        for name,dtype,count,key in (('radius','f4',len(q),'radiusHash'),('AFN409_CURVE_ID','i4',len(data.curves),'curveIdHash'),
                ('AFN409_POINT_ID','i4',len(q),'pointIdHash'),('AFN409_SKIN_TRIANGLE_ID','i4',len(data.curves),'faceHash')):
            values=np.empty(count,dtype=dtype); data.attributes[name].data.foreach_get('value',values); assert groom.arr_sha(values)==row[key]
        values=np.empty((len(data.curves),3),dtype='f4'); data.attributes['AFN409_SKIN_BARYCENTRIC'].data.foreach_get('vector',values.ravel()); assert groom.arr_sha(values)==row['baryHash']
        assert data.surface.name=='R482 archived complete neutral skin'
    renders={f'base:{view}':source['renders'][f'base:{view}'] for view in a['VIEWS']}
    for view in a['VIEWS']:
        shot=old.read(a['R470']/f'shot-A-{view}.json')['shot']
        scene.camera.matrix_world=Matrix(shot['camera']); scene.camera.data.lens=shot['lens']; bpy.context.view_layer.update()
        assert scene.view_settings.exposure==source['renders'][f'base:{view}']['exposure']
        for tag in ('A','B'):
            for mode,row in rows.items():
                obj=bpy.data.objects[row['object']]; obj.hide_render=mode!=tag; obj.hide_set(mode!=tag)
            file=ROOT/f'surface-{tag}-{view}.png'; assert not file.exists()
            scene.render.filepath=str(file); start=perf_counter(); bpy.ops.render.render(write_still=True)
            renders[f'{tag}:{view}']=dict(file=str(file),sha256=old.file_sha(file),camera=shot['camera'],lens=shot['lens'],
                exposure=scene.view_settings.exposure,view=view,tag=tag,seconds=perf_counter()-start)
            print('R482_SURFACE_RENDER',tag,view,flush=True)
    old.save(ROOT/'surface-source-receipt.json',dict(source=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=old.file_sha(DEST)),
        parent=source['source'],surfaceReceiptSha256=old.file_sha(ROOT/'surface-receipt.json'),branches=rows,renders=renders,
        hairMaterial=source['hairMaterial'],bodyMaterial=source['bodyMaterial'],default='B',scope=source['scope']))


if __name__=='__main__':
    main()