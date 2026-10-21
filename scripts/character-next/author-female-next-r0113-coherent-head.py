"""Original CC0 adult whole-head topology and its own native closure targets."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,gzip,time,datetime,importlib.util
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0113-coherent-head-foundation';INPUT=R/'Reference/character/makehuman-core-cc0/src/mpfb/data'
sp=importlib.util.spec_from_file_location('r113u',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q;u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf8',newline='\n')
def load_mesh():
 V=[];UV=[];faces=[];uvfaces=[];groups=[];group=''
 for l in (INPUT/'3dobjs/base.obj').read_text('utf8').splitlines():
  if l.startswith('v '):V.append(list(map(float,l.split()[1:4])))
  elif l.startswith('vt '):UV.append(list(map(float,l.split()[1:3])))
  elif l.startswith('g '):group=l[2:]
  elif l.startswith('f '):row=[p.split('/') for p in l.split()[1:]];faces.append([int(p[0])-1 for p in row]);uvfaces.append([int(p[1])-1 for p in row]);groups.append(group)
 return np.array(V),np.array(UV),faces,uvfaces,np.array(groups)
def target(name,n):
 a=np.loadtxt(gzip.decompress((INPUT/'targets'/name).read_bytes()).decode().splitlines());d=np.zeros((n,3));d[a[:,0].astype(int)]=a[:,1:4];return d
def main():
 tick=time.time();save('coherent-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Directly construct CC0 adult female whole-head surface and native same-topology blink, not a local eye graft or pose-field transfer.'});V,UV,F,FUV,groups=load_mesh();V+=target('macrodetails/caucasian-female-young.target.gz',len(V));raw=V.copy();convert=lambda p:p[:,[0,2,1]]*np.array([1,-1,1]);getids=lambda group:np.unique(np.concatenate([f for f,g in zip(F,groups) if g==group]));centres=np.array([convert(V[getids('joint-'+s+'-eye')]).mean(0) for s in ['l','r']]);eyes=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text('utf8'))['eyes'];C=np.array([eyes[s]['posteriorSphereFitCentreWorld'] for s in ['L','R']]);scale=np.linalg.norm(C[0]-C[1])/np.linalg.norm(centres[0]-centres[1]);translation=C.mean(0)-centres.mean(0)*scale;world=convert(V)*scale+translation
 bpy.ops.wm.read_factory_settings(use_empty=True);bodyFaces=[f for f,g in zip(F,groups) if g=='body'];bodyUV=[f for f,g in zip(FUV,groups) if g=='body'];used,inv=np.unique(np.concatenate(bodyFaces),return_inverse=True);mesh=bpy.data.meshes.new('AFN113_NATIVE_ADULT_FULL_HEAD_SOURCE');mesh.from_pydata(world[used].tolist(),[],np.array(bodyFaces).tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob)
 # body indices are source0..13379; assert instead of silently assuming helpers.
 assert np.array_equal(used,np.arange(len(used)))
 layer=mesh.uv_layers.new(name='MakeHumanOriginalUV');layer.data.foreach_set('uv',UV[np.concatenate(bodyUV)].astype('f4').ravel());basis=ob.shape_key_add(name='Basis',from_mix=False)
 for side,label in [('L','left'),('R','right')]:
  delta=convert(target('expression/units/caucasian/eye-'+label+'-closure.target.gz',len(raw)))*scale;k=ob.shape_key_add(name='AFN113_NATIVE_CLOSED_'+side,from_mix=False);k.relative_key=basis;k.value=0.;k.data.foreach_set('co',(world[used]+delta[used]).astype('f4').ravel())
 # Cut the full native body at neck only. All facial topology stays coherent.
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,1.31),plane_no=(0,0,1),clear_inner=True,clear_outer=False,dist=1e-7);bm.to_mesh(mesh);bm.free();mesh.update()
 for p in mesh.polygons:p.use_smooth=True
 sub=ob.modifiers.new('AFN113_NATIVE_HEAD_SUBDIVISION','SUBSURF');sub.levels=sub.render_levels=2
 clay=bpy.data.materials.new('AFN113_SOURCE_REFERENCE_CLAY');clay.diffuse_color=(.55,.55,.55,1);mesh.materials.append(clay);bpy.context.view_layer.update();d,N,T=u.b.geom(ob);N=N.copy();T=T.copy();arrays={'neutralWorld':N,'triangles':T};pose=[]
 for value,label in [(0.,'neutral'),(.5,'half'),(1.,'closed'),(0.,'restored')]:
  for side in ['L','R']:ob.data.shape_keys.key_blocks['AFN113_NATIVE_CLOSED_'+side].value=value
  ob.data.shape_keys.update_tag();ob.update_tag();bpy.context.view_layer.update();dd,P,PT=u.b.geom(ob);P=P.copy();arrays[label+'World']=P;pose.append({'state':label,'maxMotionM':float(np.linalg.norm(P-N,axis=1).max())})
 np.savez_compressed(E/'coherent-native-head.npz',**arrays);save('coherent-native-head.json',{'source':'MakeHuman/MPFB core assets CC0','input':'caucasian-female-young (adult25 reference), neutral average build; no child/baby targets','uniformScale':scale,'translation':translation,'nativeEyeCentresWorld':C,'rawBodyVisibleOnlyNoHelpers':True,'actualHeadVertices':len(N),'actualHeadTriangles':len(T),'actualSameTopologyClosure':pose,'modifier':'Subsurf2, no pose field applied to old head','noAnatomyContactOrCompleteCharacterAcceptance':True})
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(E/'coherent-native-head-authoring.blend'),compress=True);print('R113_COHERENT_WHOLE_HEAD_AND_NATIVE_TARGET_AUTHORED',time.time()-tick,flush=True)
if __name__=='__main__':main()
