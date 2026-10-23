"""New explicitly authored rest-guide basis, soft neighbours and full birth bed.
Not the retired150 hard owner/taper or151 same33 resting-guide geometry.
All guide/free paths are new current-space strokes; no old free path is kept.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util
from mathutils import Matrix
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0193-soft-guide-hierarchy';OUT=C/'assets-source/aevrynd-character/female-next/r0193-source/aevrynd-female-next-r0193-coarse-soft-guide-groom.blend'
sp=importlib.util.spec_from_file_location('r193base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def library():
 return [
 [[.008,-.085,1.562],[.022,-.096,1.578],[.060,-.110,1.570],[.090,-.113,1.540],[.119,-.110,1.500],[.132,-.085,1.465],[.110,-.060,1.430],[.100,-.055,1.390],[.115,-.065,1.355]],
 [[.020,-.065,1.564],[.040,-.076,1.582],[.080,-.094,1.560],[.112,-.095,1.520],[.130,-.073,1.480],[.125,-.040,1.440],[.105,-.025,1.405],[.108,-.040,1.365],[.120,-.045,1.345]],
 [[.012,-.040,1.570],[.030,-.050,1.585],[.065,-.057,1.575],[.100,-.068,1.540],[.125,-.040,1.500],[.137,-.016,1.465],[.125,.010,1.425],[.110,.005,1.390],[.117,.018,1.350]],
 [[.020,-.015,1.566],[.040,-.020,1.585],[.080,-.025,1.565],[.120,-.020,1.520],[.140,.000,1.480],[.133,.030,1.440],[.112,.040,1.400],[.110,.030,1.360],[.120,.030,1.340]],
 [[.045,-.060,1.548],[.065,-.075,1.565],[.092,-.085,1.545],[.115,-.080,1.510],[.131,-.050,1.480],[.118,-.020,1.440],[.102,-.025,1.402],[.110,-.036,1.360]],
 [[.064,-.040,1.515],[.084,-.053,1.535],[.110,-.050,1.515],[.130,-.025,1.480],[.134,.005,1.440],[.113,.022,1.405],[.102,.020,1.365],[.112,.018,1.342]],
 [[.067,-.010,1.495],[.084,.004,1.520],[.112,.027,1.505],[.133,.040,1.470],[.124,.060,1.430],[.108,.062,1.390],[.108,.045,1.350]],
 [[.055,.018,1.510],[.070,.040,1.535],[.095,.071,1.520],[.120,.085,1.480],[.119,.090,1.440],[.100,.078,1.400],[.088,.080,1.365],[.098,.095,1.340]],
 [[.015,.030,1.555],[.030,.050,1.575],[.055,.080,1.550],[.080,.110,1.515],[.090,.120,1.480],[.078,.100,1.440],[.065,.085,1.400],[.065,.100,1.360],[.078,.108,1.340]],
 [[.008,.048,1.520],[.015,.065,1.542],[.020,.095,1.520],[.028,.125,1.485],[.026,.125,1.445],[.015,.102,1.410],[.018,.090,1.370],[.030,.103,1.340]],
 [[.038,.045,1.495],[.050,.065,1.515],[.065,.100,1.490],[.080,.115,1.450],[.068,.110,1.410],[.055,.095,1.370],[.060,.100,1.335]],
 [[.045,.032,1.460],[.060,.055,1.480],[.080,.090,1.460],[.091,.110,1.425],[.080,.105,1.390],[.065,.085,1.355],[.073,.095,1.330]]]
def curve(points,K):
 p=np.vstack([points[0],points,points[-1]]);out=[]
 for f in np.linspace(0,len(points)-1,201):
  j=min(int(f),len(points)-2);u=f-j;A,B,D,F=p[j:j+4];out.append(.5*((2*B)+(-A+D)*u+(2*A-5*B+4*D-F)*u*u+(-A+3*B-3*D+F)*u*u*u))
 out=np.array(out);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(out,axis=0),axis=1))];return np.column_stack([np.interp(np.linspace(0,arc[-1],K),arc,out[:,j]) for j in range(3)])
def attr(d,n,typ,values,prop):z=d.attributes.new(n,typ,'POINT');z.data.foreach_set(prop,np.asarray(values).ravel())
def main():
 tick=time.time();t=json.loads((E/'before.json').read_text());assert not OUT.exists() and sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);s.camera.data.type='PERSP';hair=bpy.data.objects['AFN191_ACTUAL_NATIVE_VOLUME_DRIVEN_GROWTH'];before,offset=m.curveworld(hair);N=len(offset);K=49;birth=before[offset].copy();protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};guides=[];rootids=[];branches=[];anchorErrors=[];used=set();strokes=[]
 for side in [-1,1]:
  for poly in library():
   poly=np.array(poly);poly[:,0]*=side;eligible=np.flatnonzero((birth[:,0]>=0)==(side>0));order=eligible[np.argsort(np.linalg.norm(birth[eligible]-poly[0],axis=1))];rid=next(int(x) for x in order if int(x) not in used);used.add(rid);anchorErrors.append(float(np.linalg.norm(poly[0]-birth[rid])));poly[0]=birth[rid];g=curve(poly,K);g[0]=birth[rid];guides.append(g);rootids.append(rid);branches.append(side);strokes.append(poly.tolist())
 guides=np.array(guides,'f4');M=len(guides);rootids=np.array(rootids,'i4');branches=np.array(branches);nei=np.empty((N,4),'i4');weights=np.empty((N,K,4),'f4');offs=np.zeros((N,K,3),'f4');P=np.zeros((N,K,3),'f4');u=np.linspace(0,1,K);distances=[]
 for i,r in enumerate(birth):
  candidates=np.flatnonzero((branches>0)==(r[0]>=0));dd=np.linalg.norm(guides[candidates,0]-r,axis=1);chosen=candidates[np.argsort(dd)[:4]];nei[i]=chosen;d=np.linalg.norm(guides[chosen,0]-r,axis=1);distances.append(d.tolist());base=1/(d+.005)**2;base/=base.sum();w=np.tile(base,(K,1));bias=.25*np.sin(u*np.pi/2)**2;w[:,0]+=bias;w/=w.sum(1)[:,None];weights[i]=w
  for j,gid in enumerate(chosen):
   g=guides[gid];tan=np.gradient(g.astype('f8'),axis=0);tan/=np.maximum(np.linalg.norm(tan,axis=1)[:,None],1e-20);t0=tan[0];axis=np.cross(np.tile(t0,(K,1)),tan);cos=tan@t0;delta=r-g[0];rot=delta+np.cross(axis,delta)+np.cross(axis,np.cross(axis,delta))/np.maximum(1+cos[:,None],1e-6);offs[i]+=w[:,j,None]*rot;P[i]+=w[:,j,None]*g
  P[i]+=offs[i];P[i,0]=r
 hair.modifiers.clear();hair.name='AFN193_ACTUAL_SOFT_NEIGHBOUR_REST_GROOM';cu=hair.data;cu.position_data.foreach_set('vector',P.ravel());gc=bpy.data.hair_curves.new('AFN193_NEW_CURRENT_SPACE_REST_GUIDES');gc.add_curves([K]*M);gc.position_data.foreach_set('vector',guides.ravel());guide=bpy.data.objects.new('AFN193_ACTUAL_EDITABLE_REST_GUIDES',gc);s.collection.objects.link(guide);guide.hide_render=True;guide.hide_set(True)
 for j in range(4):attr(cu,f'AFN193_GUIDE_I{j}','INT',nei[:,j,None]*K+np.arange(K)[None],'value');attr(cu,f'AFN193_GUIDE_W{j}','FLOAT',weights[:,:,j],'value')
 attr(cu,'AFN193_FULL_ROOT_SECTION_OFFSET','FLOAT_VECTOR',offs,'vector');attr(cu,'AFN193_FIXED_BIRTH','FLOAT_VECTOR',np.repeat(birth[:,None],K,axis=1),'vector');attr(cu,'AFN193_ROOT_PIN','BOOLEAN',np.tile(np.arange(K)==0,N),'value')
 gn=bpy.data.node_groups.new('AFN193_ACTUAL_SOFT_GUIDE_DRIVER','GeometryNodeTree');gn.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');gn.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');nodes=gn.nodes;links=gn.links;ni=nodes.new('NodeGroupInput');no=nodes.new('NodeGroupOutput');obj=nodes.new('GeometryNodeObjectInfo');obj.transform_space='ORIGINAL';obj.inputs['Object'].default_value=guide;position=nodes.new('GeometryNodeInputPosition');terms=[]
 def named(n,typ):a=nodes.new('GeometryNodeInputNamedAttribute');a.data_type=typ;a.inputs['Name'].default_value=n;return a.outputs['Attribute']
 for j in range(4):
  sample=nodes.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';links.new(obj.outputs['Geometry'],sample.inputs['Geometry']);links.new(position.outputs['Position'],sample.inputs['Value']);links.new(named(f'AFN193_GUIDE_I{j}','INT'),sample.inputs['Index']);scale=nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';links.new(sample.outputs['Value'],scale.inputs[0]);links.new(named(f'AFN193_GUIDE_W{j}','FLOAT'),scale.inputs['Scale']);terms.append(scale.outputs['Vector'])
 result=named('AFN193_FULL_ROOT_SECTION_OFFSET','FLOAT_VECTOR')
 for term in terms:add=nodes.new('ShaderNodeVectorMath');add.operation='ADD';links.new(result,add.inputs[0]);links.new(term,add.inputs[1]);result=add.outputs['Vector']
 sw=nodes.new('GeometryNodeSwitch');sw.input_type='VECTOR';links.new(named('AFN193_ROOT_PIN','BOOLEAN'),sw.inputs['Switch']);links.new(named('AFN193_FIXED_BIRTH','FLOAT_VECTOR'),sw.inputs['True']);links.new(result,sw.inputs['False']);setpos=nodes.new('GeometryNodeSetPosition');links.new(ni.outputs[0],setpos.inputs['Geometry']);links.new(sw.outputs[0],setpos.inputs['Position']);links.new(setpos.outputs[0],no.inputs[0]);hair.modifiers.new('AFN193_ACTUAL_NEIGHBOUR_GUIDE_GEOMETRY','NODES').node_group=gn;cu.update_tag();guide.update_tag();hair.update_tag();bpy.context.view_layer.update();actual,ao=m.curveworld(hair);err=float(np.linalg.norm(actual-P.reshape(-1,3),axis=1).max());rooterr=float(np.linalg.norm(actual[ao]-birth,axis=1).max());assert err<3e-6 and rooterr<3e-6 and np.array_equal(ao,offset);assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
 np.savez_compressed(E/'soft-guide-ownership.npz',guideBirthRootIDs=rootids,guideNeighbourIDs=nei,rootWorld=birth,guideBranches=branches,guideBirthAnchorDistance=np.array(anchorErrors),newRestGuidePositions=guides)
 save('coarse-construction-summary.json',{'UTC':stamp(),'actualHair':hair.name,'actualGuides':guide.name,'curves':N,'pointsPerCurve':K,'newRestGuides':M,'actualNativeExpectedMaximumErrorM':err,'actualBirthErrorMaximumM':rooterr,'all4096CurrentBirthsIDsRadiusAndMaterialRetained':True,'allNewGuideFreePathsNoOld33Or191192PathsReused':True,'soft4NeighbourWeightsNoHardOwnerAndNoRootOffsetTaper':True,'guideRootAnchorDistancesM':anchorErrors,'neighbourRootDistancesMQuantiles':np.quantile(distances,[.5,.9,1],axis=0).tolist(),'newCurrentSpaceRestStrokeControls':strokes,'notBiologicalFollicleOrFiniteContactAcceptance':True,'restOffsetTransportFrozenDuringGuideEditNotDynamicFrameCalibration':True,'protectedRawMeshUVSignatures':protected,'secondsBeforePreview':time.time()-tick,'officialDocsScope':'Official search excerpts on guide maps/clumping read; full pages returned402, not claimed read. No bundled asset/code imported.'})
 captures=[]
 def capture(scene):
  captures.append({'UTC':stamp(),'loadedSource':bpy.data.filepath,'plannedCandidate':str(OUT),'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(v) for v in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'exposure':scene.view_settings.exposure,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'samples':scene.cycles.samples,'seed':scene.cycles.seed,'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'viewportExpectedGeometryCheckedNotRenderDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
 bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=E
 for view in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('coarse-soft-guide-hierarchy',view)
 bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[0]['cameraMatrixWorld']);s.camera.data.lens=captures[0]['lens'];s.camera.data.type=captures[0]['cameraType'];OUT.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save('a-build-summary.json',{'UTC':stamp(),'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'actualHair':hair.name,'actualGuides':guide.name,'coarseOnly':True,'completeFineCandidates':0,'oneNewRestGuideConstruction':True,'elapsedJobSeconds':time.time()-tick,'appearanceCompleteOperationContactRuntimeUnaccepted':True});print('R193_ONE_COMPLETE_NEW_SOFT_GUIDE_GROOM_SAVED',flush=True)
if __name__=='__main__':main()
