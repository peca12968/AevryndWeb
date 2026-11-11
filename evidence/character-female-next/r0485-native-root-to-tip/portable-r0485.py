"""Localize native editor brush dependencies after exact branch sealing."""
from pathlib import Path
from hashlib import file_digest,sha256
import json
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'female-next-r0485-native-groom-review-UNACCEPTED.blend'
DEST=ROOT/'female-next-r0485-native-groom-portable-UNACCEPTED.blend'
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
    assert SOURCE.exists() and not DEST.exists()
    receipts={t:read(ROOT/f'native-{t}-receipt.json') for t in ('A','B')}
    control=np.load(ROOT/'before-native.npz',allow_pickle=False)['position']
    hashes={'control':sha256(control.tobytes()).hexdigest()}|{t:r['positionHash'] for t,r in receipts.items()}
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False,use_scripts=False)
    linked=[dict(name=i.name,type=i.bl_rna.identifier,library=i.library.filepath) for i in bpy.data.user_map() if i.library]
    (ROOT/'native-editor-dependencies-before-localization.json').write_bytes(json.dumps(linked,indent=2).encode('utf8'))
    bpy.ops.object.make_local(type='ALL');bpy.ops.file.pack_all()
    bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
    note=bpy.data.texts.new('Aevrynd_R485_Editor_Dependency_Note')
    note.write('Native Comb editing brush data came from the existing Blender essential brush library and was localized for portable authoring. It is editing-tool data, not an Aevrynd runtime dependency or exclusively owned source artwork. Native checkpoint geometry remains unchanged; all source notices retained.\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    bpy.ops.wm.open_mainfile(filepath=str(DEST),load_ui=False,use_scripts=False)
    modes={}
    for tag in ('control','A','B'):
        d=bpy.data.objects[f'R485 complete hair | {tag}'].data;p=np.empty((len(d.points),3),dtype='f4');d.position_data.foreach_get('vector',p.ravel())
        assert sha256(p.tobytes()).hexdigest()==hashes[tag]
        modes[tag]=dict(object=f'R485 complete hair | {tag}',positionHash=hashes[tag],curves=len(d.curves),points=len(d.points),materials=[m.name for m in d.materials])
    external=[i.filepath for i in bpy.data.libraries]+[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file]
    assert not external,external
    record=dict(source=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=sha(DEST)),nativeCheckpointReceipts=receipts,
        modes=modes,externalDependencies=external,localizedEditorDependencies=linked,
        supersededLinkedSeal=dict(path=str(SOURCE),sha256=sha(SOURCE),bytes=SOURCE.stat().st_size),
        nativeOperationPerformed=True,geometryUnchangedFromCheckpoints=True,appearanceDecision='PENDING_MATCHED_RENDER_REVIEW',contactOrMotionAccepted=False)
    (ROOT/'sealed-source-receipt.json').write_bytes(json.dumps(record,indent=2).encode('utf8'))
    print(json.dumps(record['source']|dict(externalDependencies=external,localizedEditorDependencies=linked),indent=2),flush=True)
if __name__=='__main__':main()
