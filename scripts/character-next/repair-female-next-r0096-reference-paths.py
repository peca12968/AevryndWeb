"""Read back the local absolute-path reference without another save, then paired views.
The target candidate already independently reopened; no model correction.
"""
from pathlib import Path
import bpy,json,hashlib,runpy
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0096-artist-bob-foundation';S=R/'engine/assets/characters/female-next/source';original=E/'original-canonical-Bob-reference.blend';failed=S/'aevrynd-female-next-r0096-reference-original-Bob.blend';fixed=S/'aevrynd-female-next-r0096-reference-original-Bob-portable.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert fixed.exists();rows=json.loads((E/'minimum-saved-readback.json').read_text('utf8'))['a']['externalTextures'];byAbsolute={(S/row['relative'].removeprefix('//')).resolve():row for row in rows};bpy.ops.wm.open_mainfile(filepath=str(fixed));files=[]
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file:
  path=Path(bpy.path.abspath(im.filepath)).resolve();row=byAbsolute[path];assert sha(path)==row['sha256'];files.append({'storedPath':im.filepath,'expectedSourceTexture':row})
assert len(files)==15
record={'originalLocalReference':str(original),'originalLocalReferenceSha256':sha(original),'failedRelativePathReference':str(failed),'failedRelativePathReferenceSha256':sha(failed),'failedScope':'Derived original-canonical source reference saved with missing relative images. Preserved explicitly failed; target woman and her independent readback unaffected.','localAbsoluteReference':str(fixed),'localAbsoluteReferenceSha256':sha(fixed),'portable':False,'status':'LOCAL_SOURCE_REFERENCE_ONLY_ABSOLUTE_TEXTURES_NOT_PORTABLE','bytes':fixed.stat().st_size,'changes':'Second reference stores absolute verified texture paths. Independently reopens locally but is NOT PORTABLE despite its historical filename; both reference save failures preserved. No target geometry, shape or shader correction.','independentlyReopened':True,'externalTextures':files,'formalRuntimeOrCompleteCharacterCandidate':False}
(E/'source-reference-portability.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');print('R96_LOCAL_ABSOLUTE_REFERENCE_ONLY_NOT_PORTABLE',flush=True)
runpy.run_path(str(Path(__file__).with_name('render-female-next-r0096-affected-views.py')),run_name='__main__')
