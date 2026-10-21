"""Inspect one original native hair shape and explicit forehead parent correspondences."""
from pathlib import Path
import bpy,numpy as np,json,gzip,datetime,time
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0118-native-bob-construction';D=R/'Reference/character/makehuman-core-cc0/system-bob01-geometry-first';CORE=D.parent/'src/mpfb/data'
def obj(path):
    V=[];UV=[];F=[];FU=[]
    for l in path.read_text(encoding='utf-8').splitlines():
        a=l.split()
        if not a:continue
        if a[0]=='v':V.append(list(map(float,a[1:4])))
        elif a[0]=='vt':UV.append(list(map(float,a[1:3])))
        elif a[0]=='f':p=[x.split('/') for x in a[1:]];F.append([int(x[0])-1 for x in p]);FU.append([int(x[1])-1 for x in p])
    return np.array(V),np.array(UV),np.array(F,dtype='i4'),np.array(FU,dtype='i4')
def main():
    tick=time.time();(E/'hair-authoring-start.json').write_text(json.dumps({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct authoring of original bob01 shape/UV/native body correspondences before same-character hair-fibre reconstruction. No generic head-mask or nearest fallback.'},indent=2)+'\n',encoding='utf-8')
    base=[]
    for l in (CORE/'3dobjs/base.obj').read_text(encoding='utf-8').splitlines():
        if l.startswith('v '):base.append(list(map(float,l.split()[1:4])))
    base=np.array(base);delta=np.loadtxt(gzip.decompress((CORE/'targets/macrodetails/caucasian-female-young.target.gz').read_bytes()).decode().splitlines());base[delta[:,0].astype(int)]+=delta[:,1:];V,UV,F,FU=obj(D/'bob01.obj');rows=[];scale=np.ones(3);active=False
    for l in (D/'bob01.mhclo').read_text(encoding='utf-8').splitlines():
        a=l.split()
        if not a or a[0].startswith('#'):continue
        if a[0] in ['x_scale','y_scale','z_scale']:axis='xyz'.index(a[0][0]);scale[axis]=abs(base[int(a[1]),axis]-base[int(a[2]),axis])/float(a[3])
        if a[0]=='verts':active=True;continue
        if active:
            if len(a)==9:
                try:rows.append(list(map(float,a)))
                except ValueError:pass
            else:pass
    rows=np.array(rows);assert len(rows)==len(V);ids=rows[:,:3].astype('i4');weights=rows[:,3:6];assert ids.max()<len(base);native=(base[ids]*weights[:,:,None]).sum(1)+rows[:,6:]*scale;info=json.loads((E.parent/'r0113-coherent-head-foundation/coherent-native-head-b.json').read_text(encoding='utf-8'));world=native[:,[0,2,1]]*[1,-1,1]*info['uniformScale']+info['translation'];assert np.isfinite(world).all()
    bpy.ops.wm.read_factory_settings(use_empty=True);mesh=bpy.data.meshes.new('AFN118_NATIVE_BOB_SHAPE_REFERENCE');mesh.from_pydata(world.tolist(),[],F.tolist());mesh.update();mesh.polygons.foreach_set('use_smooth',np.ones(len(F),bool));mesh.uv_layers.new(name='NativeBobUV').data.foreach_set('uv',UV[FU.ravel()].astype('f4').ravel());ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob);mat=bpy.data.materials.new('AFN118_PUBLISHER_BOB_REFERENCE_ALPHA');mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.6;p.inputs['Base Color'].default_value=(.06,.045,.035,1);p.inputs['Roughness'].default_value=.6;mesh.materials.append(mat)
    light=bpy.data.lights.new('Bob Source Key','AREA');light.energy=300.;light.size=.5;lo=bpy.data.objects.new(light.name,light);bpy.context.scene.collection.objects.link(lo);lo.location=(-.2,-.6,1.9);target=Vector(world.mean(0));lo.rotation_euler=(target-lo.location).to_track_quat('-Z','Y').to_euler();cam=bpy.data.objects.new('Bob Source Camera',bpy.data.cameras.new('Bob Source Camera'));bpy.context.scene.collection.objects.link(cam);cam.location=target+Vector((.25,-.65,.10));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=85;scene=bpy.context.scene;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.world=bpy.data.worlds.new('Bob Source Grey World');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.3,.3,1);scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.5
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(E/'native-bob-source-authoring.blend'),compress=True);scene.render.filepath=str(E/'reference-native-bob-source-3d.png');bpy.ops.render.render(write_still=True)
    np.savez_compressed(E/'native-bob-source-lineage.npz',originalOBJ=V,sourceUV=UV,sourceFaces=F,sourceFaceUV=FU,actualNativeWorld=world,nativeBodyParentVertexIDs=ids,nativeBodyParentWeights=weights,nativeSourceOffsets=rows[:,6:],nativeOffsetScales=scale)
    result={'originalSource':'MakeHuman bob01 / CC0, original MHCLO/OBJ/PNG/MHMAT/thumbnail','nativeVertices':len(V),'nativeFaces':len(F),'nativeBodyParentIndexRange':[int(ids.min()),int(ids.max())],'nativeWorldBounds':[world.min(0).tolist(),world.max(0).tolist()],'sameAdultNativeMorphologyAndWorldTransform':True,'sourceIsNativeHairSurfaceReferenceNotFinalRenderedFibres':True,'material':'Diagnostic brown mesh only, original texture pending full asset fetch; publisher thumb preserved separately','actualForeheadAncestryAndFiberContactStillRequireValidation':True,'seconds':time.time()-tick};(E/'native-bob-source-authoring.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('R118_NATIVE_BOB_REFERENCE_AUTHORED',len(V),len(F),time.time()-tick,flush=True)
if __name__=='__main__':main()
