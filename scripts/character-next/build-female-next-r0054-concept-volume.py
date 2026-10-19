"""Actual Blender visual-hull mass from an explicitly authored concept.

Only a volume-design proxy. The image is not presented as the model result,
the actual body is unchanged, and projected cavity intervals are not CCD/SDF.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time,sys
sp=importlib.util.spec_from_file_location('hull54',Path(__file__).with_name('build-female-next-r0054-clump-volume.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E;SRC=k.SRC;OUT=b.S/'aevrynd-female-next-r0054-d-concept-volume-proxy.blend'
CLEAN='--clean-masks' in sys.argv;PREFIX='e' if CLEAN else 'd';TAG='clean-' if CLEAN else ''
if CLEAN:OUT=b.S/'aevrynd-female-next-r0054-e-clean-concept-volume-proxy.blend'

def main():
    tick=time.time();assert b.sha(SRC)=='c293976b2745e372565eb990f2e844a8255f2cdaad8e004563643d0f51c9f537'
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state();a=np.load(E/(TAG+'concept-hull-mesh.npz'))
    mesh=bpy.data.meshes.new('AFN54_D_AUTHORED_VOLUME_PROXY');mesh.from_pydata(a['vertices'].tolist(),[],a['quads'].tolist());mesh.update()
    ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob)
    for obj in bpy.context.view_layer.objects:obj.select_set(False)
    ob.select_set(True);bpy.context.view_layer.objects.active=ob
    mesh.remesh_voxel_size=.0012
    if hasattr(mesh,'use_remesh_preserve_volume'):mesh.use_remesh_preserve_volume=True
    bpy.ops.object.voxel_remesh()
    smooth=ob.modifiers.new('AFN54_DesignMassSmoothing','SMOOTH');smooth.factor=.65;smooth.iterations=6
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    for face in ob.data.polygons:face.use_smooth=True
    ob.data.materials.append(k.material());ob['aevrynd_layer']='AUTHORED_VISUAL_HULL_PROXY_NOT_HAIR'
    ob['scope']='Actual mesh built from own labelled concept silhouettes and source-head visibility depth. Not a scan, final hair, physical root map or qualified collision geometry.'
    old=bpy.data.objects[k.k.OLD];old.hide_render=True;old.hide_set(True)
    after=f.state()
    assert all(after['meshes'][name]==row for name,row in before['meshes'].items())
    assert all(after['materials'][name]==row for name,row in before['materials'].items())
    assert all(after[key]==before[key] for key in ('skinFields','curves','stage'))
    X,T=b.evaluated(ob,True);b.camera('face');bpy.context.scene.camera.data.lens=85
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    k.save(PREFIX+'-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'coarseSilhouetteCleanup':CLEAN,
        'object':ob.name,'nativeVertices':len(ob.data.vertices),'nativeFaces':len(ob.data.polygons),'evaluatedTriangles':len(T),
        'boundsM':[X.min(0).tolist(),X.max(0).tolist()],
        'originalBodySkinOpticsMaterialsHairAndStageUnchanged':True,'reference':'design-concept-reference-only.png',
        'method':'Occlusion-aware concept visual hull; native Blender voxel remesh and mesh smoothing. No old guide route, clump loft or strand interpolation.',
        'status':'ACTUAL_3D_VOLUME_PROXY_PENDING_VISUAL_REVIEW','physicalHairContact':'NOT_TESTED_NOT_FINAL_HAIR',
        'seconds':time.time()-tick})
    label=PREFIX+'-proxy';f.E=E;f.render(label,('face','oblique','profile'));k.k.k.k.a.i.ch.review.extras(label,E);k.orthographic(label)
    print('R54_CONCEPT_VOLUME_READY',len(X),len(T),time.time()-tick,flush=True)

if __name__=='__main__':main()
