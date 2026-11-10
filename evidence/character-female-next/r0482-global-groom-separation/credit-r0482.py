from pathlib import Path
from runpy import run_path
import numpy as np
import bpy

ROOT=Path(__file__).resolve().parent
a=run_path(str(ROOT/'author-r0482.py'))
old,groom=a['old'],a['groom']
DEST=ROOT/'female-next-r0482-global-groom-UNACCEPTED.blend'


def main():
    proof=old.read(ROOT/'bound-source-receipt.json')
    assert old.file_sha(Path(proof['source']['path']))==proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=proof['source']['path'],load_ui=False)
    credits=old.read(ROOT/'licenses'/'origin.json')
    for name,entry in credits.items():
        file=ROOT/'licenses'/name;assert old.file_sha(file)==entry['sha256']
        text=bpy.data.texts.new(name);text.write(file.read_text(encoding='utf8'))
    note=bpy.data.texts.new('Aevrynd_R482_Source_Provenance')
    note.write('Aevrynd r482 neutral full-groom research source.\n'
        'Body/head data retain their inherited authors and licenses in the attached original source notices.\n'
        'R482 modifications include scalp root spacing, complete shaft capsule projection, local skin clearance correction and scalp binding reconstruction.\n'
        'A and B are rejected rest studies because hair self-contact remains. Motion, full rig, expression and engine acceptance remain pending.\n'
        'Root binding uses AFN409_SKIN_TRIANGLE_ID, AFN409_SKIN_BARYCENTRIC and AEVRYND_ROOT_OFFSET_LOCAL.\n'
        'The local basis U follows triangle vertex 0 to 1, N is its outward geometric normal, and V is N cross U. Offset units are metres.\n')
    assert not DEST.exists()
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    bpy.ops.wm.open_mainfile(filepath=str(DEST),load_ui=False)
    for tag,row in proof['branches'].items():
        data=bpy.data.objects[row['object']].data
        q=np.empty((len(data.points),3),dtype='f4');data.position_data.foreach_get('vector',q.ravel());assert groom.arr_sha(q)==row['positionHash']
        for name,dtype,count,key,channel in (('radius','f4',len(q),'radiusHash','value'),('AFN409_CURVE_ID','i4',len(data.curves),'curveIdHash','value'),
                ('AFN409_POINT_ID','i4',len(q),'pointIdHash','value'),('AFN409_SKIN_TRIANGLE_ID','i4',len(data.curves),'faceHash','value'),
                ('AFN409_SKIN_BARYCENTRIC','f4',len(data.curves)*3,'baryHash','vector'),('AEVRYND_ROOT_OFFSET_LOCAL','f4',len(data.curves)*3,'localOffsetHash','vector'),
                ('AEVRYND_ROOT_NORMAL_OFFSET','f4',len(data.curves),'offsetHash','value')):
            values=np.empty(count,dtype=dtype);data.attributes[name].data.foreach_get(channel,values);assert groom.arr_sha(values)==row[key]
    for name in credits:
        assert bpy.data.texts[name].as_string()==(ROOT/'licenses'/name).read_text(encoding='utf8')
    external=[]
    for lib in bpy.data.libraries:external.append(lib.filepath)
    for image in bpy.data.images:
        if image.source=='FILE' and not image.packed_file:external.append(image.filepath)
    assert not external,external
    old.save(ROOT/'final-source-receipt.json',proof|dict(source=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=old.file_sha(DEST)),
        uncreditedParent=proof['source'],licenseOrigins=credits,externalDependencies=external,
        changesAfterPreview='Source notices and provenance text only. All rendered geometry, root-binding arrays and materials are hash-identical to the verified bound source.'))
    print('R482_FINAL_SOURCE',DEST,DEST.stat().st_size,flush=True)


if __name__=='__main__':
    main()