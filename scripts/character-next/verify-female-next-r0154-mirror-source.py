from pathlib import Path
import bpy,json,numpy as np,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0154-native-scalp-rest';M=R/'sites-engine-journey/assets-source/aevrynd-character/female-next'
sp=importlib.util.spec_from_file_location('r154mirror',Path(__file__).with_name('build-female-next-r0149-native-physical-groom.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
b=json.loads((E/'rejected-component-source.json').read_text());p=M/'r0154-source'/Path(b['source']).name;assert a.a.sha(p)==b['sha256'];bpy.ops.wm.open_mainfile(filepath=str(p));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();ob=bpy.data.objects[b['rejectedActualGuideObject']];P=a.q.hair(ob).reshape(252,16,3);assert ob.hide_render and np.linalg.norm(P-np.load(E/'native-scalp-mapping-attempt3-diagnostic.npz')['mappedArtist'],axis=2).max()<3e-7;libs=[]
for lib in bpy.data.libraries:
 path=Path(bpy.path.abspath(lib.filepath)).resolve();assert path.is_relative_to(M.resolve()) and a.a.sha(path)==b['dependencyLibrary']['sha256'];libs.append(str(path))
textures=[]
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file and im.filepath:
  path=Path(bpy.path.abspath(im.filepath,library=im.library)).resolve();assert path.is_relative_to(M.resolve()) and path.is_file();textures.append({'file':str(path),'sha256':a.a.sha(path)})
assert len(textures)==16;eye=bpy.data.objects[a.MOVING[0]];neutral=a.geometry(eye)[0].copy();s.frame_set(9);bpy.context.view_layer.update();move=float(np.linalg.norm(a.geometry(eye)[0]-neutral,axis=1).max());assert move>.001;s.frame_set(1);bpy.context.view_layer.update();assert np.array_equal(a.geometry(eye)[0],neutral)
(E/'independent-mirror-source-readback.json').write_bytes((json.dumps({'mirrorSource':str(p),'sha256':a.a.sha(p),'failedGuidesRetained':252,'failedPointsRetained':4032,'failedSnapshotNotLiveMapperOrCandidate':True,'relativeLibrariesWithinArchive':libs,'relativeTexturesWithinArchive':textures,'retainedCurrentGazeFrame9MovementM':move,'retainedCurrentGazeRestored':True},indent=2)+'\n').encode());print('R154_MIRROR_FAILED_SNAPSHOT_RETAINED_WOMAN_16_TEXTURES_REOPEN_DONE',flush=True)
