from pathlib import Path
from runpy import run_path
from time import perf_counter
import numpy as np
import bpy
from mathutils import Matrix

ROOT=Path(__file__).resolve().parent
a=run_path(str(ROOT/'author-r0482.py'))
old,groom=a['old'],a['groom']


def main():
    proof,banks,_,_=a['read_data']()
    rows={tag:dict(object=f'R482 complete groom | {tag}',positionHash=groom.arr_sha(bank['position']),radiusHash=groom.arr_sha(bank['radius']),
        curveIdHash=groom.arr_sha(bank['curveIDs']),pointIdHash=groom.arr_sha(bank['pointIDs']),
        faceHash=groom.arr_sha(bank['skinTriangle']),baryHash=groom.arr_sha(bank['barycentric'])) for tag,bank in banks.items()}
    bpy.ops.wm.open_mainfile(filepath=str(a['DEST']),load_ui=False)
    scene=bpy.context.scene
    for tag,row in rows.items():
        data=bpy.data.objects[row['object']].data
        q=np.empty((len(data.points),3),dtype='f4'); data.position_data.foreach_get('vector',q.ravel()); assert groom.arr_sha(q)==row['positionHash']
        for name,dtype,count,key in (('radius','f4',len(q),'radiusHash'),('AFN409_CURVE_ID','i4',len(data.curves),'curveIdHash'),
            ('AFN409_POINT_ID','i4',len(q),'pointIdHash'),('AFN409_SKIN_TRIANGLE_ID','i4',len(data.curves),'faceHash')):
            values=np.empty(count,dtype=dtype); data.attributes[name].data.foreach_get('value',values); assert groom.arr_sha(values)==row[key]
        values=np.empty((len(data.curves),3),dtype='f4'); data.attributes['AFN409_SKIN_BARYCENTRIC'].data.foreach_get('vector',values.ravel()); assert groom.arr_sha(values)==row['baryHash']
        assert data.surface.name=='R482 archived complete neutral skin' and [m.name for m in data.materials]==[a['MATERIAL']]
    renders={}
    for view in a['VIEWS']:
        shot=old.read(a['R470']/f'shot-A-{view}.json')['shot']
        scene.camera.matrix_world=Matrix(shot['camera']); scene.camera.data.lens=shot['lens']; bpy.context.view_layer.update()
        for tag,row in rows.items():
            for mode,entry in rows.items():
                obj=bpy.data.objects[entry['object']]; obj.hide_render=mode!=tag; obj.hide_set(mode!=tag)
            file=ROOT/f'{tag}-{view}.png'; assert not file.exists()
            scene.render.filepath=str(file); started=perf_counter(); bpy.ops.render.render(write_still=True)
            renders[f'{tag}:{view}']=dict(file=str(file),sha256=old.file_sha(file),camera=shot['camera'],lens=shot['lens'],
                exposure=scene.view_settings.exposure,view=view,tag=tag,seconds=perf_counter()-started)
            print('R482_RENDER',tag,view,flush=True)
    source=a['DEST']
    old.save(ROOT/'source-receipt.json',dict(source=dict(path=str(source),bytes=source.stat().st_size,sha256=old.file_sha(source)),
        globalReceiptSha256=old.file_sha(ROOT/'global-receipt.json'),branches=rows,renders=renders,
        hairMaterial=a['MATERIAL'],bodyMaterial='R482 neutral diagnostic skin',default='B',
        scope='Standalone neutral full-groom Blender source with persistent identities, explicit scalp triangle and barycentric attributes, owned keratin shader and archived complete skin. The fixture has no rig, expression morphs or motion acceptance.'))


if __name__=='__main__':
    main()