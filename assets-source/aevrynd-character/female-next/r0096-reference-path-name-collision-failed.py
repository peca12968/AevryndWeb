"""Portable source reference repair only, then the paired affected views.
The target candidate already independently reopened; no model correction.
"""
from pathlib import Path
import bpy,json,hashlib,runpy
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0096-artist-bob-foundation';S=R/'engine/assets/characters/female-next/source';original=E/'original-canonical-Bob-reference.blend';failed=S/'aevrynd-female-next-r0096-reference-original-Bob.blend';fixed=S/'aevrynd-female-next-r0096-reference-original-Bob-portable.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not fixed.exists();rows=json.loads((E/'minimum-saved-readback.json').read_text('utf8'))['a']['externalTextures'];byName={Path(row['relative']).name:row for row in rows};assert len(byName)==15
bpy.ops.wm.open_mainfile(filepath=str(original));files=[]
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file:
  row=byName[Path(im.filepath).name];path=S/row['relative'].removeprefix('//');assert sha(path)==row['sha256'];im.filepath=str(path);files.append(row)
assert len(files)==15;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(fixed),compress=True);bpy.ops.wm.open_mainfile(filepath=str(fixed))
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file:assert im.filepath.startswith('//') and sha(Path(bpy.path.abspath(im.filepath)))==byName[Path(im.filepath).name]['sha256']
record={'originalLocalReference':str(original),'originalLocalReferenceSha256':sha(original),'failedRelativePathReference':str(failed),'failedRelativePathReferenceSha256':sha(failed),'failedScope':'Derived original-canonical source reference saved with missing relative images. Preserved explicitly failed; target woman and her independent readback unaffected.','portableReference':str(fixed),'portableReferenceSha256':sha(fixed),'bytes':fixed.stat().st_size,'changes':'Assign verified original texture paths absolutely before save; Blender remaps them relative to the new source folder. No geometry/shape/shader repair or model round.','independentlyReopened':True,'externalTextures':files,'formalRuntimeOrCompleteCharacterCandidate':False}
(E/'source-reference-portability.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');print('R96_REFERENCE_PATH_REPAIR_VERIFIED',flush=True)
runpy.run_path(str(Path(__file__).with_name('render-female-next-r0096-affected-views.py')),run_name='__main__')
