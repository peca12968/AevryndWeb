"""Open the copied source from its Git history location, not the workspace."""
from pathlib import Path
import bpy, json, hashlib, time
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0057-coherent-foundation'
M=R/'sites-engine-journey/assets-source/aevrynd-character/female-next'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    tick=time.time();manifest=json.loads((E/'history-file-manifest.json').read_text());verified=0
    for x in manifest['files']:
        p=R/'sites-engine-journey'/x['path'];assert sha(p)==x['sha256'];verified+=1
    source=M/'aevrynd-female-next-r0057-d-portable-native-foundation.blend'
    assert sha(source)=='318f0e2f18584be23ba1dc11c59e924c1719bb6768e40c3c3a65e66f1c81e34f'
    bpy.ops.wm.open_mainfile(filepath=str(source));images=[]
    for im in bpy.data.images:
        if im.source not in ('FILE','TILED'):continue
        p=Path(bpy.path.abspath(im.filepath)).resolve()
        assert im.source=='FILE' and im.filepath.startswith('//') and p.is_relative_to(M/'study-vitruvian-textures') and p.exists()
        assert im.size[0]>0 and im.size[1]>0 and len(im.pixels)>0
        images.append({'name':im.name,'path':str(p),'sha256':sha(p),'dimensions':list(im.size)})
    assert len(images)==15 and len(bpy.data.libraries)==0
    assert not any(o.particle_systems for o in bpy.context.scene.objects if o.type=='MESH')
    assert not any(m.type=='SURFACE_DEFORM' for o in bpy.context.scene.objects for m in o.modifiers)
    out={'source':str(source),'sourceSha256':sha(source),'openedFromHistoryLocation':True,'verifiedArchiveFiles':verified,'relativeResourcesResolvedAndLoaded':images,'externalLibraries':0,'legacyParticleSystems':0,'surfaceDeformModifiers':0,'notAnEngineOrCollisionPass':True,'seconds':time.time()-tick}
    (E/'history-bundle-reopened.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
    print('R57_HISTORY_BUNDLE_REOPENED',verified,len(images),time.time()-tick,flush=True)
if __name__=='__main__':main()
