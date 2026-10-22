"""Reopen actual archived compact .blend with mirror-relative textures."""
from pathlib import Path
import bpy,json,numpy as np,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0152-layered-groom';M=R/'sites-engine-journey/assets-source/aevrynd-character/female-next'
sp=importlib.util.spec_from_file_location('r152mirror',Path(__file__).with_name('build-female-next-r0152-layered-current-source.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
def main():
 b=json.loads((E/'b-build-summary.json').read_text());file=M/'r0152-source'/Path(b['output']).name;assert a.a.sha(file)==b['sha256'];bpy.ops.wm.open_mainfile(filepath=str(file));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();hair=bpy.data.objects[b['actualHair']];assert a.a.hasharray(a.q.hair(hair))==b['actualGeometryHash'];textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   p=Path(bpy.path.abspath(im.filepath)).resolve();assert p.is_file() and p.is_relative_to(M.resolve());textures.append({'relative':im.filepath,'mirrorAbsolute':str(p),'sha256':a.a.sha(p),'bytes':p.stat().st_size})
 rig=bpy.data.objects[b['actualRig']];assert rig.animation_data.action.name==b['originalGazeAction'];scene.frame_set(9);bpy.context.view_layer.update();assert abs(a.angles(rig)['L'][2]+20)<1e-4;scene.frame_set(1);bpy.context.view_layer.update();assert a.a.hasharray(a.q.hair(hair))==b['actualGeometryHash'];h.save('independent-mirror-current-only-reopen.json',{'source':str(file),'sha256':b['sha256'],'actualArchivedBlendIndependentlyReopened':True,'actualNativeGeometryMatchesSourceHash':True,'actualExistingGazeOperatedFrame9AndRestored':True,'allExternalTexturesResolveInsideArchiveMirror':True,'textures':textures,'externalHistoricalRollbackOnlyMetadataNotCurrentGeometryDependency':True,'noAppearanceMotionContactRuntimeAcceptance':True});print('R152_MIRROR_COMPACT_SOURCE_REOPEN_RELATIVE_TEXTURES_DONE',len(textures),flush=True)
if __name__=='__main__':main()
