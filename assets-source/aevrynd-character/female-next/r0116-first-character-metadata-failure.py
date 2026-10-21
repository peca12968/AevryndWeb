"""Replace helper-sized old optics by the inspected actual source-native eye layers on the same woman."""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,datetime,importlib.util
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0116-native-compatible-eyes';SRC=S/'r0115-source/aevrynd-female-next-r0115-b-continuous-native-neutral.blend';OUT=S/'r0116-source/aevrynd-female-next-r0116-a-native-paired-eyes.blend'
sp=importlib.util.spec_from_file_location('r116main',Path(__file__).with_name('build-female-next-r0113-native-neck-character.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);q=b.q;b.u.v.E=E
def save(n,o):(E/n).write_text(json.dumps(o,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8',newline='\n')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def hasharray(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def protected():
    ob=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];d,V,T=b.u.b.geom(ob);return {'actualSkinWorld':hasharray(V),'actualTriangles':hasharray(T),'rawAllShapeKeys':{k.name:hasharray(q.arr(k.data,'co',len(k.data),3)) for k in ob.data.shape_keys.key_blocks},'allOriginalFibres':{n:{'curves':len(bpy.data.objects[n].data.curves),'world':hasharray(q.hair(bpy.data.objects[n])),'radii':hasharray(q.arr(bpy.data.objects[n].data.attributes['radius'].data,'value',len(bpy.data.objects[n].data.attributes['radius'].data)))} for n in ['AFN97_TUCKED_ARTIST_BOB_CHILDREN','AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES']}}
def main():
    tick=time.time();assert not OUT.exists();save('complete-eye-character-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Append inspected real native eye layers into unchanged r115 B; hide/preserve old helper-sized optics, fixed original native mapping/UV and one initial PBR approximation, no fitting/material sweep.'});digest=sha(SRC);bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0);before=protected();oldImages={im:im.filepath for im in bpy.data.images};source=readSource=json.loads((E/'native-eye-source-authoring.json').read_text(encoding='utf-8'));names=[p['name'] for p in source['actualSourceParts']]
    with bpy.data.libraries.load(str(E/'native-eye-source-authoring.blend'),link=False) as (aa,bb):bb.objects=names
    for ob in bb.objects:
        bpy.context.scene.collection.objects.link(ob);ob.hide_render=False;ob.hide_set(False)
        for mat in ob.data.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.bl_idname=='ShaderNodeTexImage' and node.image:
                        if node.image in oldImages:node.image=node.image.copy()
                        node.image.name='AFN116_NATIVE_BROWN_TEXTURE';node.image.filepath='//../makehuman-native-eye-textures/brown_eye.png'
        ob['scope']='Actual source-native eye surface, original native MHCLO/UV. Static PBR approximation; finite thickness, independent iris/pupil, gaze controls and full contacts unaccepted.'
    oldNames=['AFN113_'+side+'_'+part for side in ['L','R'] for part in ['SCLERA','IRIS']]
    for n in oldNames:ob=bpy.data.objects[n];ob.hide_render=True;ob.hide_set(True)
    for im,path in oldImages.items():assert im.filepath==path,(im.name,path,im.filepath)
    bpy.context.view_layer.update();after=protected();assert before==after
    b.deliver(0);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);assert sha(SRC)==digest
    save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'bytes':OUT.stat().st_size,'sha256':sha(OUT),'newActualSourceEyeObjects':names,'oldOpticsPreservedHidden':oldNames,'actualSourceReference':'reference-native-eye-structure-oblique.png','originalNativeEyeTopologyAndUVPreserved':True,'nativeMorphologyMapping':'Documented MHCLO IDs/weights/source offsets with original native axis-scale definitions and same adult morphology/world transform as complete body. No helper-radius or extra eye scale fit.','originalBodyAllKeysAndHairBrowLashPointsRadiiHashesBefore':before,'originalBodyAllKeysAndHairBrowLashPointsRadiiHashesAfter':after,'allProtectedGeometryByteExact':True,'oldImagePathsUnchanged':True,'materialScope':'Original native brown texture opaque inner surface, fixed initial clear PBR outer surface. Not a copied litsphere runtime, not anatomy/physical calibration or a parameter sweep.','irisPupilIndependentGeometryFiniteCornealWallNaturalGazeAndContactUnaccepted':True,'secondsBeforePreview':time.time()-tick})
    views=[]
    for view in ['face','body-face','profile','oblique','back']:
        views.append(b.u.v.image('a-native-paired-eyes',view));save('a-view-controls.json',views)
    for label,value in [('half',.5),('closed',1.),('restored',0.)]:
        b.deliver(value);views.append(b.u.v.image('a-native-paired-eyes-'+label,'face'));save('a-view-controls.json',views)
    print('R116_COMPLETE_SOURCE_NATIVE_EYES_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
