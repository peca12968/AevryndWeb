"""Actual native follicle deformation from current Skin bone weights; one candidate."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,datetime,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0184-native-follicle-deformation';OUT=C/'assets-source/aevrynd-character/female-next/r0184-source/aevrynd-female-next-r0184-a-native-follicle-deformation.blend'
sp=importlib.util.spec_from_file_location('native169',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
NAMES=['AFN139_STATIC_REST','AFN139_L_UPPER_LID','AFN139_L_LOWER_LID','AFN139_R_UPPER_LID','AFN139_R_LOWER_LID']
def save(name,value):(E/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def rotation(A):
 u,ss,v=np.linalg.svd(A);Q=u@v;assert np.linalg.det(Q)>0;return Q
def weights(skin,tri,bc):
 ids=np.unique(tri);W=np.zeros((len(skin.data.vertices),5));lookup={skin.vertex_groups[n].index:i for i,n in enumerate(NAMES)}
 for vi in ids:
  for gr in skin.data.vertices[int(vi)].groups:
   if gr.group in lookup:W[vi,lookup[gr.group]]=gr.weight
 rw=np.einsum('bn,bnk->bk',bc,W[tri]);assert np.max(abs(rw.sum(1)-1))<2e-7;return rw/rw.sum(1,keepdims=True)
def transforms(rig):
 return np.array([np.array(rig.matrix_world@rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()@rig.matrix_world.inverted()) for n in NAMES])
def main():
 tick=time.time();t=json.loads((E/'before.json').read_text());assert not OUT.exists();assert a.a.sha(Path(t['source']))==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];lash=bpy.data.objects['AFN183_ACTUAL_UPPER_ANTERIOR_ROOTED_LASHES'];raw={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};P,off=m.curveworld(lash);P=P.reshape(436,17,3);d=lash.data;tri=np.stack([h.arr(d.attributes['AFN149_SkinVertex'+str(j)].data,'value',7412,dtype='i4').reshape(436,17)[:,0] for j in range(3)],1);bc=h.arr(d.attributes['AFN149_RootBarycentric'].data,'vector',7412,3).reshape(436,17,3)[:,0];rw=weights(skin,tri,bc);W,T=a.geometry(skin);B=W[tri];root=(B*bc[:,:,None]).sum(1);ex=B[:,1]-B[:,0];ex/=np.linalg.norm(ex,axis=1,keepdims=True);ez=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);ez/=np.linalg.norm(ez,axis=1,keepdims=True);F0=np.stack([ex,np.cross(ez,ex),ez],2);M0=transforms(rig);reports=[]
 for frame in [1,13,37]:
  s.frame_set(frame);bpy.context.view_layer.update();V,_=a.geometry(skin);B=V[tri];x=B[:,1]-B[:,0];x/=np.linalg.norm(x,axis=1,keepdims=True);z=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);z/=np.linalg.norm(z,axis=1,keepdims=True);F=np.stack([x,np.cross(z,x),z],2);oldR=F@np.swapaxes(F0,1,2);MM=transforms(rig);delta=MM@np.linalg.inv(M0);blend=np.einsum('bk,kij->bij',rw,delta[:,:3,:3]);rot=rotation(blend);rel=oldR@np.swapaxes(rot,1,2);degrees=np.degrees(np.arccos(np.clip((np.trace(rel,axis1=1,axis2=2)-1)/2,-1,1)));old,_=m.curveworld(lash);centre=(B*bc[:,:,None]).sum(1)+z*.000032;native=centre[:,None]+np.einsum('bij,bnj->bni',rot,P-P[:,:1]);reports.append({'frame':frame,'triangleVersusBonePolarRotationDegreesQuantiles':np.quantile(degrees,[0,.5,.9,1]).tolist(),'largestMismatchCurveID':int(np.argmax(degrees)),'failed183Curve82MismatchDegrees':float(degrees[82]),'failed183Curve118MismatchDegrees':float(degrees[118]),'nativeVersusOldDisplayedMaximumM':float(np.linalg.norm(native-old.reshape(436,17,3),axis=2).max()),'actualBoneWorldMatrices':MM.tolist()})
 save('measured-native-follicle-premise.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':t['source'],'actualSkinVertexGroups':NAMES,'all436RootWeightsSumMaximumError':float(abs(rw.sum(1)-1).max()),'actualFrameComparisons':reports,'measuredMismatchNotProofOfFailureCause':True,'proposedChange':'Replace arbitrary triangle-edge rotation of full free paths with actual root skinning-weight blend of native lid-bone deformation. Keep current Skin barycentric root and actual normal-radius centre. No new root placement, rest path, count, radius, optics or gaze reduction.'})
 assert reports[-1]['triangleVersusBonePolarRotationDegreesQuantiles'][-1]>.01,'No measured changed premise'
 s.frame_set(1);bpy.context.view_layer.update();d=lash.data.copy();d.name='AFN184_NATIVE_BONE_WEIGHTED_FOLLICLE_DATA';lash.data=d;lash.name='AFN184_ACTUAL_NATIVE_DEFORMED_LASHES';d.attributes['AFN183_FOLLICLE_ID'].name='AFN184_FOLLICLE_ID';d.position_data.foreach_set('vector',P.astype('f4').ravel());d.attributes['AFN149_RestWorld'].data.foreach_set('vector',P.astype('f4').ravel())
 # The native rig has four X-only lid channels with the same rest orientation.
 # Verify that these are pure world-X rotations before implementing the exact
 # weighted sine/cosine polar rotation as a native Geometry Nodes field.
 axisProof=[]
 for frame in [1,13,37]:
  s.frame_set(frame);bpy.context.view_layer.update();delta=transforms(rig)@np.linalg.inv(M0)
  for k,n in enumerate(NAMES):
   theta=float(np.arctan2(delta[k,2,1],delta[k,1,1]));co,si=np.cos(theta),np.sin(theta);target=np.array([[1,0,0],[0,co,-si],[0,si,co]]);err=float(abs(delta[k,:3,:3]-target).max());axisProof.append({'frame':frame,'bone':n,'worldXAngle':theta,'maximumMatrixError':err});assert err<2e-6,(n,err)
 save('native-bone-axis-capability.json',axisProof);s.frame_set(1);bpy.context.view_layer.update()
 for k,n in enumerate(NAMES[1:],1):d.attributes.new('AFN184_RootWeight'+str(k),'FLOAT','POINT').data.foreach_set('value',np.repeat(rw[:,k],17).astype('f4'))
 for name,values in [('AFN184_RestRootCentre',np.repeat(P[:,:1],17,axis=1))]:d.attributes.new(name,'FLOAT_VECTOR','POINT').data.foreach_set('vector',values.astype('f4').ravel())
 # Copy existing sampled Skin/root graph, replacing only the free-path offset.
 mod=next(q for q in lash.modifiers if q.type=='NODES');g=mod.node_group.copy();g.name='AFN184_NATIVE_SKIN_BONE_FOLLICLE_DEFORMATION';mod.node_group=g;n=g.nodes;L=g.links
 def attr(name,kind='FLOAT_VECTOR'):
  node=n.new('GeometryNodeInputNamedAttribute');node.data_type=kind;node.inputs['Name'].default_value=name;return node.outputs['Attribute']
 def math(op,*values):
  node=n.new('ShaderNodeMath');node.operation=op
  for j,v in enumerate(values):
   if isinstance(v,(float,int)):node.inputs[j].default_value=v
   else:L.new(v,node.inputs[j])
  return node.outputs[0]
 def vec(op,*values):
  node=n.new('ShaderNodeVectorMath');node.operation=op
  for j,v in enumerate(values):L.new(v,node.inputs[j])
  return node.outputs[0]
 inp=next(q for q in n if q.bl_idname=='NodeGroupInput');out=next(q for q in n if q.bl_idname=='NodeGroupOutput');oldSet=next(q for q in n if q.bl_idname=='GeometryNodeSetPosition');oldAdd=oldSet.inputs['Position'].links[0].from_node;rootOffset=oldAdd.inputs[0].links[0].from_node;rootSocket=rootOffset.inputs[0].links[0].from_socket;offsetSocket=rootOffset.inputs[1].links[0].from_socket;normalScale=vec('SCALE',offsetSocket) if False else None
 # Recover actual root-normal from the existing normalized cross-product node.
 normals=[q for q in n if q.bl_idname=='ShaderNodeVectorMath' and q.operation=='NORMALIZE' and q.inputs[0].is_linked and q.inputs[0].links[0].from_node.bl_idname=='ShaderNodeVectorMath' and q.inputs[0].links[0].from_node.operation=='CROSS_PRODUCT'];assert len(normals)==1
 sc=n.new('ShaderNodeVectorMath');sc.operation='SCALE';L.new(normals[0].outputs[0],sc.inputs[0]);sc.inputs['Scale'].default_value=.000032;centre=vec('ADD',rootSocket,sc.outputs[0]);sumSin=0.;sumCos=attr('AFN184_RootWeight1','FLOAT')
 weightsAll=[attr('AFN184_RootWeight'+str(k),'FLOAT') for k in range(1,5)];sumWeights=math('ADD',math('ADD',weightsAll[0],weightsAll[1]),math('ADD',weightsAll[2],weightsAll[3]));sumCos=math('SUBTRACT',1.,sumWeights)
 for k,name in enumerate(NAMES[1:],1):
  val=n.new('ShaderNodeValue');val.label=name;fc=val.outputs[0].driver_add('default_value');dr=fc.driver;dr.type='SCRIPTED';v=dr.variables.new();v.name='lid_angle';v.type='SINGLE_PROP';v.targets[0].id=rig;v.targets[0].data_path='pose.bones["'+name+'"].rotation_euler[0]';dr.expression='lid_angle';wt=weightsAll[k-1];sn=math('MULTIPLY',wt,math('SINE',val.outputs[0]));cs=math('MULTIPLY',wt,math('COSINE',val.outputs[0]));sumSin=math('ADD',sumSin,sn);sumCos=math('ADD',sumCos,cs)
 angle=math('ARCTAN2',sumSin,sumCos);rotate=n.new('ShaderNodeVectorRotate');rotate.rotation_type='AXIS_ANGLE';rotate.inputs['Axis'].default_value=(1,0,0);L.new(vec('SUBTRACT',attr('AFN149_RestWorld'),attr('AFN184_RestRootCentre')),rotate.inputs['Vector']);L.new(angle,rotate.inputs['Angle']);pos=n.new('GeometryNodeInputPosition');newPos=vec('ADD',vec('ADD',centre,rotate.outputs[0]),vec('SUBTRACT',pos.outputs[0],attr('AFN149_RestWorld')));L.new(newPos,oldSet.inputs['Position']);d.update_tag();lash.update_tag();bpy.context.view_layer.update();now,_=m.curveworld(lash);restError=float(np.linalg.norm(now-P.reshape(-1,3),axis=1).max());assert restError<3e-6;assert raw=={name:a.rawsig(bpy.data.objects[name]) for name in raw}
 np.savez_compressed(E/'native-follicle-deformation-lineage.npz',rootTriangles=tri,rootBC=bc,rootBoneWeights=rw,restCurveWorld=P,neutralBoneWorldMatrices=M0)
 lash['scope']='Unaccepted complete native lash gaze deformation. Actual current Skin anchors plus root-weighted native lid-bone polar rotation; same436 full rest paths/IDs/material/radius/action. Not natural hair dynamics, finite/self/continuous contact or runtime acceptance.'
 s.camera.data.type='PERSP';a.b.u.v.E=E;views=[a.b.u.v.image('a-native-follicle-deformation','face')];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);save('a-build-summary.json',{'source':t['source'],'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualHair':lash.name,'actualSkin':skin.name,'actualRig':rig.name,'nativeStrands':436,'points':7412,'completeWomanCandidates':1,'neutralEvaluatedRestMaximumChangeM':restError,'restGeometryMaterialRadiusActionPreserved':True,'secondsBeforeOtherViews':time.time()-tick,'unaccepted':True})
 for view in ['body-face','profile','back','oblique']:views.append(a.b.u.v.image('a-native-follicle-deformation',view))
 save('native-follicle-preview-controls.json',views)
 sp2=importlib.util.spec_from_file_location('eyes180',C/'scripts/character-next/build-female-next-r0180-anatomical-lash-rows.py');eye=importlib.util.module_from_spec(sp2);sp2.loader.exec_module(eye);eye.E=E;captures=[]
 for frame in [1,13,37,49]:
  s.frame_set(frame);bpy.context.view_layer.update();captures.append(eye.eye_image('a-native-follicle-eyes-%03d'%frame,str(OUT)))
 save('native-follicle-eye-motion-controls.json',captures);s.frame_set(1);bpy.context.view_layer.update();print('R184_COMPLETE_NATIVE_FOLLICLE_DEFORMATION_PREVIEWS_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
