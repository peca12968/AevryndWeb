"""One complete posed-artist-path reconstruction with actual 3D scalp ownership.
Independent root-frame transport, not UV/carrier-tangent or decorative-card flow.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime
from mathutils import Vector
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0177-anatomical-guide-paths';OUT=C/'assets-source/aevrynd-character/female-next/r0177-source/aevrynd-female-next-r0177-a-anatomical-guide-paths.blend'
sp=importlib.util.spec_from_file_location('r177base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+'\n','utf-8')
def attr(d,n,t,dom,p,v):d.attributes.new(n,t,dom).data.foreach_set(p,np.asarray(v).ravel())
def basis(W,T):
 B=W[T];ax=B[:,1]-B[:,0];ax/=np.linalg.norm(ax,axis=1,keepdims=True);az=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);az/=np.linalg.norm(az,axis=1,keepdims=True);return np.stack((ax,np.cross(az,ax),az),axis=2)
def normals(W,T):
 n=np.zeros_like(W);v=np.cross(W[T[:,1]]-W[T[:,0]],W[T[:,2]]-W[T[:,0]])
 for k in range(3):np.add.at(n,T[:,k],v)
 n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-15);return n
def rotate(P,src,dst):
 axis=np.cross(src,dst);co=float(np.dot(src,dst));assert co>-.99
 # Rodrigues minimal rotation preserves each independently owned full path.
 return P+np.cross(axis,P)+np.cross(axis,np.cross(axis,P))/(1+co)
def main():
 tick=time.time();timing=json.loads((E/'before.json').read_text());assert not OUT.exists();assert a.a.sha(Path(timing['source']))==timing['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=timing['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];old.material_slots[0].link='DATA';protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(skin)
 cor=np.load(E/'anatomical-source-current-root-correspondence.npz');assert np.array_equal(W,cor['currentWorld']) and np.array_equal(T,cor['currentTriangles']);src=np.load(E.parent/'r0169-native-carrier-groom/coherent-native-carrier-lineage.npz');line=np.load(E.parent/'r0171-actual-scalp-chart/actual-scalp-groom-lineage.npz');SG=src['sourcePosedGuides'].reshape(252,16,3);gT=cor['guideTriangles'];gBC=cor['guideBC'];gRoot=(W[gT]*gBC[:,:,None]).sum(1);vn=normals(W,T);tn=(vn[gT]*gBC[:,:,None]).sum(1);tn/=np.linalg.norm(tn,axis=1,keepdims=True);sn=normals(src['sourceCarrierWorld'],src['sourceCarrierTriangles']);st=src['sourceGuideCarrierTriangles'];sb=src['sourceGuideCarrierBarycentric'];sn=(sn[st]*sb[:,:,None]).sum(1);sn/=np.linalg.norm(sn,axis=1,keepdims=True)
 G=[]
 for j in range(252):
  original=SG[j]-SG[j,0];rotated=rotate(original,sn[j],tn[j]);arc=np.r_[0,np.linalg.norm(np.diff(rotated,axis=0),axis=1).cumsum()];path=np.stack([np.interp(np.linspace(0,arc[-1],33),arc,rotated[:,k]) for k in range(3)],axis=1);G.append(path+gRoot[j]+tn[j]*.000035)
 G=np.asarray(G,'f4');gd=bpy.data.hair_curves.new('AFN177_ANATOMICAL_COMPLETE_ARTIST_GUIDE_PATHS_DATA');gd.add_curves([33]*252);gd.position_data.foreach_set('vector',G.ravel());attr(gd,'AFN177_GUIDE_ID','INT','CURVE','value',np.arange(252,dtype='i4'));go=bpy.data.objects.new('AFN177_EDITABLE_COMPLETE_ROOT_TO_TIP_GUIDES',gd);s.collection.objects.link(go);go.hide_render=True;go.hide_set(True);gb=basis(W,gT);glocal=np.einsum('bni,bij->bnj',G-gRoot[:,None],gb);h.bind(go,skin,gT,gBC,glocal,G)
 rootT=line['fixedRootTriangles'];rootBC=line['fixedRootBarycentric'];root=(W[rootT]*rootBC[:,:,None]).sum(1);N=len(root);assert N==10191;rb=basis(W,rootT);rootCentre=root+rb[:,:,2]*.000035;rm=bpy.data.meshes.new('AFN177_FIXED_CURRENT_SKIN_BIRTH_ROOTS_DATA');rm.from_pydata(rootCentre.tolist(),[],[]);ro=bpy.data.objects.new('AFN177_FIXED_CURRENT_SKIN_BIRTH_ROOTS',rm);s.collection.objects.link(ro);ro.hide_render=True;ro.hide_set(True);h.bind(ro,skin,rootT,rootBC,np.einsum('bni,bij->bnj',(rootCentre-root)[:,None],rb),rootCentre[:,None])
 distance=np.linalg.norm(root[:,None]-gRoot[None],axis=2);distance[(root[:,0]>=0)[:,None]!=(gRoot[:,0]>=0)[None]]=1e6;nearest=np.argsort(distance,axis=1)[:,:4];dist=np.take_along_axis(distance,nearest,axis=1);weights=1/np.maximum(dist,.0002)**2;weights/=weights.sum(1,keepdims=True);P=(rootCentre[:,None]+np.einsum('bi,bink->bnk',weights,(G-G[:,0,None])[nearest])).astype('f4');P[:,0]=rootCentre;assert np.isfinite(P).all()
 hd=bpy.data.hair_curves.new('AFN177_FIXED_BIRTH_ANATOMICAL_ARTIST_PATH_DISPLAY_DATA');hd.add_curves([33]*N);hd.position_data.foreach_set('vector',P.ravel());attr(hd,'radius','FLOAT','POINT','value',np.tile(.000035*(1-.98*np.linspace(0,1,33)**6),N).astype('f4'));attr(hd,'AFN177_BIRTH_ID','INT','CURVE','value',np.arange(N,dtype='i4'));attr(hd,'AFN177_ROOT_SAMPLE','INT','POINT','value',np.repeat(np.arange(N,dtype='i4'),33));attr(hd,'AFN177_REST_WORLD','FLOAT_VECTOR','POINT','vector',P.reshape(-1,3))
 for k in range(4):
  attr(hd,f'AFN177_GUIDE_POINT_{k}','INT','POINT','value',(nearest[:,k,None]*33+np.arange(33)[None]).astype('i4').ravel());attr(hd,f'AFN177_GUIDE_ROOT_{k}','INT','POINT','value',np.repeat(nearest[:,k]*33,33).astype('i4'));attr(hd,f'AFN177_GUIDE_WEIGHT_{k}','FLOAT','POINT','value',np.repeat(weights[:,k],33).astype('f4'))
 hair=bpy.data.objects.new('AFN177_ACTUAL_ANATOMICAL_ROOT_TO_TIP_GROOM',hd);s.collection.objects.link(hair);mat=bpy.data.materials.new('AFN177_FIXED_BROWN_FIBRE_IDENTICAL175_PARAMETERS');mat.use_nodes=True;ns=mat.node_tree.nodes;ns.clear();bs=ns.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='MELANIN';bs.inputs['Melanin'].default_value=.75;bs.inputs['Melanin Redness'].default_value=.15;bs.inputs['Roughness'].default_value=.35;bs.inputs['Radial Roughness'].default_value=.45;out=ns.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs[0],out.inputs[0]);hd.materials.append(mat)
 group=bpy.data.node_groups.new('AFN177_FIXED_BIRTH_EXPLICIT_FOUR_ARTIST_GUIDE_DEFORMATION','GeometryNodeTree');group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');n=group.nodes;L=group.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');pos=n.new('GeometryNodeInputPosition')
 def named(name,typ='FLOAT_VECTOR'):
  x=n.new('GeometryNodeInputNamedAttribute');x.data_type=typ;x.inputs['Name'].default_value=name;return x.outputs['Attribute']
 def info(ob):
  x=n.new('GeometryNodeObjectInfo');x.transform_space='RELATIVE';x.inputs['Object'].default_value=ob;return x.outputs['Geometry']
 def sample(geom,index):
  x=n.new('GeometryNodeSampleIndex');x.data_type='FLOAT_VECTOR';x.domain='POINT';x.clamp=False;L.new(geom,x.inputs['Geometry']);L.new(pos.outputs[0],x.inputs['Value']);L.new(index,x.inputs['Index']);return x.outputs['Value']
 def vec(op,*v):
  x=n.new('ShaderNodeVectorMath');x.operation=op
  for j,q in enumerate(v):L.new(q,x.inputs[j])
  return x.outputs[0]
 def scale(v,w):
  x=n.new('ShaderNodeVectorMath');x.operation='SCALE';L.new(v,x.inputs[0]);L.new(w,x.inputs['Scale']);return x.outputs[0]
 guideGeom=info(go);rootGeom=info(ro);position=sample(rootGeom,named('AFN177_ROOT_SAMPLE','INT'))
 for k in range(4):position=vec('ADD',position,scale(vec('SUBTRACT',sample(guideGeom,named(f'AFN177_GUIDE_POINT_{k}','INT')),sample(guideGeom,named(f'AFN177_GUIDE_ROOT_{k}','INT'))),named(f'AFN177_GUIDE_WEIGHT_{k}','FLOAT')))
 position=vec('ADD',position,vec('SUBTRACT',pos.outputs[0],named('AFN177_REST_WORLD')));setp=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setp.inputs['Geometry']);L.new(position,setp.inputs['Position']);L.new(setp.outputs['Geometry'],out.inputs['Geometry']);hair.modifiers.new('AFN177_ACTUAL_COMPLETE_GUIDE_PATH_NATIVE_DEFORMATION','NODES').node_group=group;old.hide_render=True;old.hide_set(True);s.render.hair_type='STRIP';bpy.context.view_layer.update();actual,offset=m.curveworld(hair);error=float(np.linalg.norm(actual-P.reshape(-1,3),axis=1).max());assert error<3e-6;assert protected=={name:a.rawsig(bpy.data.objects[name]) for name in protected}
 np.savez_compressed(E/'anatomical-guide-path-lineage.npz',guideTriangles=gT,guideBC=gBC,guideWorld=G,guideNormals=tn,sourceGuideNormals=sn,rootTriangles=rootT,rootBC=rootBC,rootWorld=root,rootCentre=rootCentre,nearestGuides=nearest,guideWeights=weights,scalpFaces=cor['scalpFaces'])
 save('direct-anatomical-guide-path-authoring.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':timing['startedUTC'],'changedFailedPremise':'Actual posed independent artist complete root-to-tip paths, direct 3D summit-seeded root-to-actual-scalp triangle mapping, per-guide source/target normal minimal rotation. No UV chart derivative, carrier deformation, whole-groom affine fitting, decorative card inverse flow or fixed failed mid/tips. Four-guide fixed-birth interpolation reused as construction only.','root0and61ActualCurrent':gRoot[[0,61]].tolist(),'root0and61CompleteAuthoredPaths':G[[0,61]].tolist(),'sourceTargetNormalAngleDegrees':np.degrees(np.arccos(np.clip((sn*tn).sum(1),-1,1))).tolist(),'nativeDisplayMaximumErrorM':error,'actualGuides':go.name,'actualRoots':ro.name,'actualHair':hair.name,'guideCurves':252,'displayCurves':N,'controlsPerCurve':33,'same175CountRadiusShaderParameters':True,'sourceRights':'Tomáš Klecer / MakeHuman Hair Editor functional CC0 package; official provenance retained, no new downloaded or BY-SA asset. Current woman retains DarkNik/NikZava284 CC-BY4 attribution and CC0 body.','noFullFiniteSelfContinuousNaturalMotionRuntimeClaim':True})
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);save('a-build-summary.json',{'source':timing['source'],'output':str(OUT),'engineAlias':str(R/'engine/assets/characters/female-next/source/r0177-source'/OUT.name),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':'AFN138_ACTUAL_CURRENT_GAZE_RIG','actualHair':hair.name,'actualGuides':go.name,'actualRoots':ro.name,'retainedSourceHair':old.name,'nativeStrands':N,'points':len(actual),'fullNativeGroomCandidate':True,'unaccepted':True,'secondsBeforePreview':time.time()-tick});assert OUT.stat().st_size<timing['sourceBudgetBytes'];a.b.u.v.E=E;views=[]
 for view in ['face','body-face','profile','back','oblique']:
  ctl=a.b.u.v.image('a-anatomical-guide-paths',view);ctl.update(frame=1,actualHair=hair.name,hairTypeAtActualCapture=s.render.hair_type,actualSamplesAtCapture=s.cycles.samples,actualResolutionAtCapture=[s.render.resolution_x,s.render.resolution_y]);views.append(ctl);save('anatomical-guide-preview-controls.json',views)
 print('R177_ANATOMICAL_COMPLETE_ROOT_TO_TIP_GROOM_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
