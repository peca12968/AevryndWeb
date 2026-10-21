"""Original native eye topology/UV and documented MHCLO fitting, no radius fitting or addon code."""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,gzip,hashlib,os
from PIL import Image
from mathutils import Vector
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0116-native-compatible-eyes';D=R/'Reference/character/makehuman-core-cc0/system-eyes';CORE=D.parent/'src/mpfb/data'
def save(n,o):(E/n).write_text(json.dumps(o,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8',newline='\n')
def main():
    tick=time.time();save('eye-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Directly author the actual source high-poly cornea/inner surfaces with original UV/material and native documented MHCLO correspondences on the same adult native morphology; no helper-radius fitting or program/addon copy.'});V=[]
    for line in (CORE/'3dobjs/base.obj').read_text(encoding='utf-8').splitlines():
        if line.startswith('v '):V.append(list(map(float,line.split()[1:4])))
    V=np.array(V);target=np.loadtxt(gzip.decompress((CORE/'targets/macrodetails/caucasian-female-young.target.gz').read_bytes()).decode().splitlines());V[target[:,0].astype(int)]+=target[:,1:];original=[];uv=[];faces=[];uvfaces=[]
    for l in (D/'high-poly.obj').read_text(encoding='utf-8').splitlines():
        a=l.split()
        if not a:continue
        if a[0]=='v':original.append(list(map(float,a[1:4])))
        elif a[0]=='vt':uv.append(list(map(float,a[1:3])))
        elif a[0]=='f':parts=[p.split('/') for p in a[1:]];faces.append([int(p[0])-1 for p in parts]);uvfaces.append([int(p[1])-1 for p in parts])
    original=np.array(original);uv=np.array(uv);rows=[];scales=np.ones(3);active=False;scaleDefs={}
    for l in (D/'high-poly.mhclo').read_text(encoding='utf-8').splitlines():
        a=l.split()
        if not a or a[0].startswith('#'):continue
        if a[0] in ['x_scale','y_scale','z_scale']:
            axis='xyz'.index(a[0][0]);i,j=int(a[1]),int(a[2]);scales[axis]=abs(V[i,axis]-V[j,axis])/float(a[3]);scaleDefs[a[0]]={'sourceIndices':[i,j],'sourceReferenceDistance':float(a[3]),'actualAxisDistance':float(abs(V[i,axis]-V[j,axis])),'nativeOffsetScale':scales[axis]}
        if a[0]=='verts':active=True;continue
        if active:
            if len(a)==9:
                try:rows.append(list(map(float,a)))
                except ValueError:active=False
            else:active=False
    rows=np.array(rows);assert len(rows)==len(original)==1064;ids=rows[:,:3].astype('i4');weights=rows[:,3:6];offsets=rows[:,6:];native=(V[ids]*weights[:,:,None]).sum(1)+offsets*scales;info=json.loads((E.parent/'r0113-coherent-head-foundation/coherent-native-head-b.json').read_text(encoding='utf-8'));world=native[:,[0,2,1]]*[1,-1,1]*info['uniformScale']+info['translation'];assert np.isfinite(world).all()
    parent=list(range(len(world)))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for f in faces:
        for j in f[1:]:parent[root(j)]=root(f[0])
    comps={}
    for i in range(len(world)):comps.setdefault(root(i),[]).append(i)
    texture=S/'makehuman-native-eye-textures/brown_eye.png';texture.parent.mkdir(exist_ok=True)
    if not texture.exists():os.link(D/'brown_eye.png',texture)
    assert hashlib.sha256(texture.read_bytes()).digest()==hashlib.sha256((D/'brown_eye.png').read_bytes()).digest();pixels=np.array(Image.open(texture).convert('RGBA'))
    bpy.ops.wm.read_factory_settings(use_empty=True);image=bpy.data.images.load(str(texture));image.colorspace_settings.name='sRGB';inner=bpy.data.materials.new('AFN116_NATIVE_BROWN_INNER_SURFACE');inner.use_nodes=True;p=inner.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.35;p.inputs['IOR'].default_value=1.376;tex=inner.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;uvnode=inner.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='MakeHumanEyeUV';inner.node_tree.links.new(uvnode.outputs['UV'],tex.inputs['Vector']);inner.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
    outer=bpy.data.materials.new('AFN116_NATIVE_CLEAR_CORNEAL_SURFACE');outer.use_nodes=True;p=outer.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(1,1,1,1);p.inputs['Roughness'].default_value=.02;p.inputs['IOR'].default_value=1.376;p.inputs['Transmission Weight'].default_value=1.;parts=[]
    for k,vertices in comps.items():
        selected=[i for i,f in enumerate(faces) if root(f[0])==k];uvsamples=uv[np.concatenate([uvfaces[i] for i in selected])];xx=np.clip((uvsamples[:,0]*1023).astype(int),0,1023);yy=np.clip(((1-uvsamples[:,1])*1023).astype(int),0,1023);alpha=pixels[yy,xx,3];isOuter=bool(np.max(alpha)==0);side='L' if world[vertices,0].mean()>0 else 'R';role='CORNEAL_SURFACE' if isOuter else 'SCLERA_IRIS_PUPIL_SURFACE';name='AFN116_'+side+'_'+role;mapping={v:j for j,v in enumerate(vertices)};C=np.array(info['nativeEyeCentresWorld'][0 if side=='L' else 1]);mesh=bpy.data.meshes.new(name);mesh.from_pydata((world[vertices]-C).tolist(),[],[[mapping[v] for v in faces[i]] for i in selected]);mesh.update();mesh.polygons.foreach_set('use_smooth',np.ones(len(mesh.polygons),bool));mesh.uv_layers.new(name='MakeHumanEyeUV').data.foreach_set('uv',uv[np.concatenate([uvfaces[i] for i in selected])].astype('f4').ravel());mesh.materials.append(outer if isOuter else inner);ob=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(ob);ob.location=C;parts.append({'name':name,'side':side,'role':role,'sourceVertexIDs':vertices,'sourceFaceIDs':selected,'vertices':len(vertices),'faces':len(selected),'originalTextureAlphaRange':[int(alpha.min()),int(alpha.max())],'worldBounds':[world[vertices].min(0),world[vertices].max(0)],'materialMapping':'Clear PBR transmission for authored alpha0 outer surface; original opaque native texture on inner. Fixed initial approximation, not source litsphere shader or calibrated finite anatomical eye.'})
    for name,position,power,size in [('NativeEye Key',(-.3,-.6,1.9),250.,.5),('NativeEye Fill',(.35,-.4,1.65),100.,.4)]:
        light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size;ob=bpy.data.objects.new(name,light);bpy.context.scene.collection.objects.link(ob);ob.location=position;ob.rotation_euler=(Vector((0,-.115,1.463))-ob.location).to_track_quat('-Z','Y').to_euler()
    cam=bpy.data.objects.new('NativeEye Source Camera',bpy.data.cameras.new('NativeEye Source Camera'));bpy.context.scene.collection.objects.link(cam);bpy.context.scene.camera=cam;cam.location=(.12,-.42,1.49);cam.rotation_euler=(Vector((0,-.115,1.463))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=85.;scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.world=bpy.data.worlds.new('NativeEye Black World');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.015,.015,.015,1);scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.5
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(E/'native-eye-source-authoring.blend'),compress=True);scene.render.filepath=str(E/'reference-native-eye-structure-oblique.png');bpy.ops.render.render(write_still=True)
    np.savez_compressed(E/'native-eye-source-lineage.npz',originalOBJ=original,actualNativeMorphologyEye=native,actualWorld=world,sourceBodyVertexIDs=ids,sourceWeights=weights,sourceOffsets=offsets,sourceOffsetScales=scales,uniformScale=np.array(info['uniformScale']),translation=np.array(info['translation']))
    save('native-eye-source-authoring.json',{'source':'MakeHuman system high-poly eyes / original CC0 OBJ, MHCLO and brown texture','actualSourceParts':parts,'nativeOffsetScaleDefinitions':scaleDefs,'nativeWorldBounds':[world.min(0),world.max(0)],'sourceOBJAndCurrentBasemeshHaveDifferentOriginsDoNotFitOBJByEye':'OBJ supplies original topology/UV; documented MHCLO supplies adapted coordinates. No helper-sphere radius or extra eye scale is fitted.','documentedDataFormula':'sum(w_i * currentAdultNativeBase[v_i]) + sourceOffset * nativeAxisScale','documentation':'https://static.makehumancommunity.org/oldsite/documentation/file_formats_and_extensions.html','sourceNativeUniformTransformUnchanged':True,'actualEyeFiniteThicknessIrisPupilGeometrySeparationGazeControlsAndContactUnaccepted':True,'GPLProgramLogicNotInstalledExecutedOrCopied':True,'independentSourceInspectionOnlyNotCompleteCharacter':True,'seconds':time.time()-tick});print('R116_ACTUAL_NATIVE_EYE_SOURCE_AUTHORED',len(parts),time.time()-tick,flush=True)
if __name__=='__main__':main()
