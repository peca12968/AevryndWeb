"""Native finite optical-envelope/iris construction on the same complete woman.
Art-directed approximation, not a captured/anatomically certified individual eye.
"""
from pathlib import Path
from collections import defaultdict
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r'D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0087-eye-solids';SRC=S/'aevrynd-female-next-r0081-b-stable-frame-curly-study.blend';OUT=S/'aevrynd-female-next-r0087-a-finite-optical-envelope.blend'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('r87source','build-female-next-r0081-editable-curly.py');q=m.q;v=module('r87views','render-female-next-r0081-retained-study.py');v.E=E
THICKNESS=.00055;IRIS_THICKNESS=.00015;IRIS_RELIEF=.00012;CAVITY_DEPTH=.002;CORNEA_IOR=1.376;AQUEOUS_IOR=1.336
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def actual(o):
 for md in o.modifiers:
  if md.type=='SUBSURF':md.levels=md.render_levels
 bpy.context.view_layer.update();d,P=q.geom(o);F=[list(f.vertices) for f in d.polygons];uv=q.arr(d.uv_layers['VitruvianUV.UDIM'].data,'uv',len(d.loops),2);norm=q.arr(d.corner_normals,'vector',len(d.loops),3);weights=[[(g.group,g.weight) for g in vert.groups] for vert in d.vertices];assert all(len(w)>0 for w in weights),'Do not invent missing evaluated skin weights'
 return {'P':P.copy(),'F':F,'UV':uv.copy(),'N':norm.copy(),'MI':q.arr(d.polygons,'material_index',len(d.polygons),dtype='i4'),'weights':weights,'starts':np.r_[0,np.cumsum([len(f) for f in F])]}
def native(source,name,P,F,uv,matIndices,weights,materials,customNormals=None):
 # Use native mesh coordinates/UV/deform groups, not shader attribute normals.
 A=np.array(source.matrix_world);local=(P-A[:3,3])@np.linalg.inv(A[:3,:3]).T;d=bpy.data.meshes.new(name+'_MESH');d.from_pydata(local.tolist(),[],F);d.update();u=d.uv_layers.new(name='VitruvianUV.UDIM');u.data.foreach_set('uv',np.asarray(uv,'f4').ravel())
 for mat in materials:d.materials.append(mat)
 d.polygons.foreach_set('material_index',np.asarray(matIndices,'i4'))
 for f in d.polygons:f.use_smooth=True
 if customNormals is not None:d.normals_split_custom_set(np.asarray(customNormals).tolist())
 o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.matrix_world=source.matrix_world.copy()
 for group in source.vertex_groups:o.vertex_groups.new(name=group.name)
 for i,row in enumerate(weights):
  for g,w in row:o.vertex_groups[g].add([i],float(w),'REPLACE')
 md=o.modifiers.new('AFN87_INHERITED_INTERPOLATED_SOURCE_SKIN','ARMATURE');md.object=bpy.data.objects['AFN69_BODY_CONTROLS'];md.use_deform_preserve_volume=False;o['scope']='Native optical study; source-interpolated Neck/Head skin weights. No independent eye rotation or full dynamic/contact qualification.';return o
def selected(raw,mask):
 fi=np.flatnonzero(mask);ids=np.unique(np.concatenate([raw['F'][i] for i in fi]));lookup=np.full(len(raw['P']),-1,'i4');lookup[ids]=np.arange(len(ids));F=[lookup[raw['F'][i]].tolist() for i in fi];loops=np.concatenate([np.arange(raw['starts'][i],raw['starts'][i+1]) for i in fi]);return ids,F,raw['UV'][loops].copy(),loops
def boundary(F):
 edges=defaultdict(list)
 for f in F:
  for a,b in zip(f,f[1:]+f[:1]):edges[tuple(sorted((a,b)))].append((a,b))
 assert all(len(x)<=2 for x in edges.values());return [x[0] for x in edges.values() if len(x)==1]
def annular_coordinate(rad,theta,edges):
 # Follow the two actual irregular source rims, rather than assume circles.
 adj=defaultdict(set)
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 remaining=set(adj);rings=[]
 while remaining:
  todo=[remaining.pop()];ring=[]
  while todo:
   a=todo.pop();ring.append(a)
   for b in adj[a]:
    if b in remaining:remaining.remove(b);todo.append(b)
  rings.append(np.array(ring,'i4'))
 assert len(rings)==2 and all(len(x)==128 for x in rings)
 rings.sort(key=lambda ids:float(rad[ids].mean()));profiles=[]
 for ids in rings:
  order=np.argsort(theta[ids]);profiles.append(np.interp(theta,theta[ids][order],rad[ids][order],period=2*np.pi))
 return np.clip((rad-profiles[0])/(profiles[1]-profiles[0]),0,1)
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=='dfcc38df12c6bd93c9659b90f8b665e973b7a90f3828b134297bd6f2365898c0';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();rig=bpy.data.objects['AFN69_BODY_CONTROLS'];assert all(np.max(np.abs(np.array(b.matrix_basis)-np.eye(4)))<1e-6 for b in rig.pose.bones),'Baking requires neutral FK source';rows=[];lineage={}
 innerMat=bpy.data.materials.new('AFN87_CORNEA_TO_AQUEOUS_RELATIVE_INTERFACE');innerMat.use_nodes=True;bs=innerMat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(1,1,1,1);bs.inputs['Transmission Weight'].default_value=1;bs.inputs['IOR'].default_value=CORNEA_IOR/AQUEOUS_IOR;bs.inputs['Roughness'].default_value=.025
 for side in ('L','R'):
  outer=bpy.data.objects['AFN60_'+side+'_EYE_OUTER_SHELL_APPROX'];iris=bpy.data.objects['AFN60_'+side+'_IRIS_PUPIL_SURFACE'];a=actual(outer);ir=actual(iris);assert not boundary(a['F']),'Source outer must be closed';P=a['P'];C=(P.min(0)+P.max(0))*.5;normal=np.zeros_like(P)
  for f in a['F']:
   n=np.cross(P[f[1]]-P[f[0]],P[f[2]]-P[f[0]])
   for i in f:normal[i]+=n
  normal/=np.linalg.norm(normal,axis=1)[:,None];assert np.min(np.sum((P-C)*normal,axis=1))>0,'Source orientation must point outward';inner=P-THICKNESS*normal;assert np.isfinite(inner).all();outerObj=outer;innerF=[list(reversed(f)) for f in a['F']];innerUV=np.concatenate([a['UV'][a['starts'][i]:a['starts'][i+1]][::-1] for i in range(len(a['F']))]);innerObj=native(outer,'AFN87_'+side+'_CORNEOSCLERAL_INNER',inner,innerF,innerUV,np.zeros(len(innerF),'i4'),a['weights'],[innerMat]);outerObj['scope']='Original native cage, shape keys, interpolated rig weights, subdivision and limit normals remain live; material alpha still models continuous clear/opaque limbus. Paired inner envelope is an art-directed constant-normal thickness approximation, not measured corneal layers.';innerObj['scope']='Closed inward-facing inner envelope at0.55mm corresponding-vertex normal offset; front cornea-to-aqueous relative IOR1.376/1.336. Opaque sclera hides the simplified posterior representation. No fluid absorption/lens/retina simulation.'
  ids,F,uv,loops=selected(ir,ir['MI']==0);front=ir['P'][ids].copy();centre=(ir['P'].min(0)+ir['P'].max(0))*.5;dx=front[:,0]-centre[0];dz=front[:,2]-centre[2];rad=np.hypot(dx,dz);theta=np.arctan2(dz,dx);edges=boundary(F);assert len(edges)==256,'Expected two128-vertex native iris boundary rings';t=annular_coordinate(rad,theta,edges);envelope=np.sin(np.pi*t)**2;fold=(.55*np.sin(37*theta+3.5*t)+.30*np.sin(61*theta-5*t)+.15*np.cos(23*theta+t));relief=IRIS_RELIEF*envelope*fold;front[:,1]-=relief;assert max(abs(relief[[i for e in edges for i in e]]))<1e-7;back=front.copy();back[:,1]+=IRIS_THICKNESS;N=len(front);solidP=np.r_[front,back];solidF=F+[[i+N for i in reversed(f)] for f in F]+[[b,a,a+N,b+N] for a,b in edges];frontUV=uv.copy();backUV=np.concatenate([uv[sum(map(len,F[:i])):sum(map(len,F[:i+1]))][::-1] for i in range(len(F))]);uvByVertex={}
  at=0
  for f in F:
   for i in f:uvByVertex.setdefault(i,uv[at].copy());at+=1
  wallUV=np.array([uvByVertex[i%N] for f in solidF[len(F)*2:] for i in f]);solidUV=np.r_[frontUV,backUV,wallUV];solidW=[ir['weights'][i] for i in ids]*2;assert not boundary(solidF);irisObj=native(iris,'AFN87_'+side+'_IRIS_STROMA',solidP,solidF,solidUV,np.zeros(len(solidF),'i4'),solidW,[iris.data.materials[0]]);irisObj['scope']='Source UV annulus with authored radial-fold relief<=0.12mm and0.15mm posterior thickness; closed mesh. These are procedural art-directed folds, not captured crypt geometry or inferred texture-to-depth.'
  pid,pf,puv,ploops=selected(ir,ir['MI']==2);well=ir['P'][pid].copy();pr=np.hypot(well[:,0]-centre[0],well[:,2]-centre[2]);pu=np.clip(pr/pr.max(),0,1);depth=CAVITY_DEPTH*(1-pu**2)**2;well[:,1]+=depth;pupil=native(iris,'AFN87_'+side+'_PUPIL_DARK_CAVITY',well,pf,puv,np.zeros(len(pf),'i4'),[ir['weights'][i] for i in pid],[iris.data.materials[2]]);pupil['scope']='Source pupil cap recessed into a dark well, preserving aperture rim. Approximate absorbing cavity terminator, not a simulated lens/retina or a fully open anatomical pupil.'
  iris.hide_render=True;iris.hide_set(True)
  bpy.context.view_layer.update();_,actualOuter=q.geom(outerObj);error=float(np.linalg.norm(actualOuter-P,axis=1).max());assert error<2e-6;sourceCorner=q.arr(q.geom(outerObj)[0].corner_normals,'vector',len(a['N']),3);cornerError=float(np.linalg.norm(sourceCorner-a['N'],axis=1).max());assert cornerError<2e-5
  lineage.update({side+'_outerSourceWorld':P,side+'_innerWorld':inner,side+'_irisSourceIds':ids,side+'_irisSourceWorld':ir['P'][ids],side+'_irisFrontWorld':front,side+'_irisReliefM':relief,side+'_pupilSourceIds':pid,side+'_pupilSourceWorld':ir['P'][pid],side+'_pupilWellWorld':well})
  rows.append({'side':side,'objects':[o.name for o in (outerObj,innerObj,irisObj,pupil)],'outerWorldPositionReadbackMaximumErrorM':error,'outerNativeCornerNormalReadbackMaximumError':cornerError,'outerFaces':len(a['F']),'innerFaces':len(innerF),'irisClosedFaces':len(solidF),'pupilWellFaces':len(pf),'normalCorrespondenceThicknessM':THICKNESS,'notGlobalMinimumThickness':True,'irisThicknessAlongWorldYM':IRIS_THICKNESS,'maximumAbsoluteAuthoredIrisReliefM':float(abs(relief).max()),'maximumPupilPosteriorShiftM':float(depth.max()),'originalOuterRetainedLiveVisible':True,'originalIrisRetainedHidden':True})
 np.savez_compressed(E/'a-native-optical-lineage.npz',**lineage);m.rig.shade.settings();s.render.hair_subdiv=3;m.rig.k.b.camera('face');s.camera.data.lens=85;s['AFN87_scope']='One native finite optical-envelope and iris-relief study; not anatomical/complete contact, natural dynamics or engine acceptance.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'construction':rows,'outerSurfacePreservedNoAdditionalCoincidentShell':True,'cornealNormalOffsetM':THICKNESS,'corneaIOR':CORNEA_IOR,'aqueousIOR':AQUEOUS_IOR,'innerInterfaceRelativeIOR':CORNEA_IOR/AQUEOUS_IOR,'noCapturedIndividualEyeOrAnatomicalGlobalContactOrNaturalMotionRuntimeQualification':True,'secondsBeforePreview':time.time()-tick});renders=[]
 for view in ('face','body-face','oblique'):renders.append(v.image('a-solids',view));save('a-pilot-controls.json',renders)
 print('R87_NATIVE_FINITE_EYE_PILOT_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
