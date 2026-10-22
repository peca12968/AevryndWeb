from pathlib import Path
import bpy,json,numpy as np,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0153-current-hairline';M=R/'sites-engine-journey/assets-source/aevrynd-character/female-next'
sp=importlib.util.spec_from_file_location('r153mirror',Path(__file__).with_name('build-female-next-r0153-current-hairline.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
b=json.loads((E/'a-build-summary.json').read_text());p=M/'r0153-source'/Path(b['output']).name;assert a.a.sha(p)==b['sha256'];bpy.ops.wm.open_mainfile(filepath=str(p));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();hair=bpy.data.objects[b['actualHair']];P=a.q.hair(hair);assert len(P)==16900 and np.isfinite(P).all();rest=a.a.hasharray(P);libraries=[]
for lib in bpy.data.libraries:
 path=Path(bpy.path.abspath(lib.filepath)).resolve();assert path.is_relative_to(M.resolve()) and a.a.sha(path)==b['sourceSha256'];libraries.append(str(path))
textures=[]
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file and im.filepath:
  path=Path(bpy.path.abspath(im.filepath,library=im.library)).resolve();assert path.is_relative_to(M.resolve()) and path.is_file();textures.append({'file':str(path),'sha256':a.a.sha(path)})
assert len(textures)==16;eye=bpy.data.objects[a.MOVING[0]];neutral=a.geometry(eye)[0].copy();s.frame_set(9);bpy.context.view_layer.update();motion=float(np.linalg.norm(a.geometry(eye)[0]-neutral,axis=1).max());assert motion>.001;s.frame_set(1);bpy.context.view_layer.update();assert np.array_equal(a.geometry(eye)[0],neutral) and a.a.hasharray(a.q.hair(hair))==rest
h.save('independent-mirror-source-readback.json',{'mirrorSource':str(p),'sha256':a.a.sha(p),'actualCurves':len(hair.data.curves),'actualPoints':len(P),'actualGazeFrame9EyeMovementM':motion,'actualGazeAndHairNeutralRestorationExact':True,'relativeLibrariesWithinArchive':libraries,'relativeTexturesWithinArchive':textures,'librariesAndTexturesRequiredNotClaimedAsSingleStandaloneBlob':True,'sourceConstructionOnlyNotAppearanceCompleteOperationContactOrRuntimeAdoption':True});print('R153_MIRROR_SHARED_WOMAN_REOPEN_16_TEXTURES_GAZE_RESTORE_DONE',flush=True)
