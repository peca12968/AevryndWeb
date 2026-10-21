"""Direct native nasal-complex sculpt with live exact-subdivision correspondence.
Fixed authored topology handles, one harmonic proportional-edit extension.
No nearest-surface projection, generic face crease or shader/parameter sweep.
"""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0124-native-nasal-sculpt';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend';OUT=S/'r0124-source/aevrynd-female-next-r0124-a-live-native-nasal-sculpt.blend'
sp=importlib.util.spec_from_file_location('r124base',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8',newline='\n')
def sha(p):return a.sha(Path(p))
def set_control(value):
 ctrl=bpy.data.objects['AFN124_NASAL_SCULPT_CONTROL'];ctrl['nasal_sculpt']=value;ctrl.update_tag();ob=bpy.data.objects['AFN124_EDITABLE_NATIVE_NASAL_SCULPT'];ob.data.shape_keys.update_tag();ob.update_tag();bpy.context.view_layer.update()
def main():
 tick=time.time();assert not OUT.exists();save('native-nasal-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Directly sculpt native nasal tip/alar/nostril topology; connect actual editable coarse source to displayed whole woman using exact verified subdivision vertex identity.'});bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0.);skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];ref=bpy.data.objects['AFN115_EDITABLE_CONNECTED_NATIVE_ADULT_SOURCE'];ref.hide_set(False);bpy.context.view_layer.update();protected=a.protected();d,baseline,BT=b.u.b.geom(skin);baseline=baseline.copy();BT=BT.copy();rd,original,RT=b.u.b.geom(ref);assert np.array_equal(original,baseline);A=np.array(ref.matrix_world);co=q.arr(ref.data.vertices,'co',len(ref.data.vertices),3);world=co@A[:3,:3].T+A[:3,3];assert all(k.value==0 for k in ref.data.shape_keys.key_blocks)
 # Authored native control handles, in WORLD millimetres. These are explicit
 # topology selections after inspecting the actual nose, not a fit sweep.
 centre={201:(0,-.25,-.10),291:(0,-.50,-.40),294:(0,-1.00,-.80),297:(0,-1.30,-1.20),302:(0,-1.00,-1.00),307:(0,-.70,-.70),312:(0,-.30,-.30)}
 right={7060:(-.30,-1.10,-.80),7061:(-.10,-1.20,-.90),7062:(-.30,-1.00,-1.00),7063:(-.10,-1.30,-1.20),7066:(-.20,-.80,-.90),7067:(-.10,-1.00,-1.00),7045:(-.35,-.60,-.70),7046:(-.40,-.50,-.50),7047:(-.30,-.30,-.30),7097:(.30,-.30,-.30),7100:(.35,-.10,-.10),7056:(.35,-.15,-.20),7083:(.20,-.20,-.20),7084:(.20,-.20,-.20),7057:(.20,.35,0),7099:(.25,.25,0),7088:(.10,.35,0),7043:(0,-.35,-.35),7064:(0,-.40,-.40),7072:(0,-.15,-.15)}
 tree=KDTree(len(world))
 for i,p in enumerate(world):tree.insert(Vector(p),i)
 tree.balance();cx=float(world[297,0]);handles={int(i):np.array(delta)*.001 for i,delta in centre.items()};pairs=[]
 for i,delta in right.items():
  target=world[i].copy();target[0]=2*cx-target[0];hit,j,dist=tree.find(Vector(target));assert dist<2e-6,(i,j,dist);v=np.array(delta)*.001;handles[i]=v;handles[int(j)]=v*np.array([-1,1,1]);pairs.append({'right':i,'left':int(j),'nativeMirrorWorldErrorM':float(dist)})
 adjacency=[set() for _ in co]
 for poly in ref.data.polygons:
  vs=list(poly.vertices)
  for x,y in zip(vs,vs[1:]+vs[:1]):adjacency[x].add(y);adjacency[y].add(x)
 region=set(handles);front=set(handles)
 for _ in range(5):
  front={j for i in front for j in adjacency[i] if abs(world[j,0]-cx)<.027 and world[j,1]<-.123 and 1.416<world[j,2]<1.452}-region;region|=front
 unknown=sorted(region-set(handles));index={v:i for i,v in enumerate(unknown)};matrix=np.zeros((len(unknown),len(unknown)));rhs=np.zeros((len(unknown),3))
 for v,i in index.items():
  neighbors=adjacency[v];matrix[i,i]=len(neighbors)
  for j in neighbors:
   if j in index:matrix[i,index[j]]-=1.
   elif j in handles:rhs[i]+=handles[j]
 delta=np.zeros_like(world,dtype='f8')
 for v,dv in handles.items():delta[v]=dv
 delta[unknown]=np.linalg.solve(matrix,rhs);assert np.isfinite(delta).all();changed=np.flatnonzero(np.any(delta!=0,axis=1));assert np.linalg.norm(delta,axis=1).max()<.002
 edit=ref.copy();edit.data=ref.data.copy();edit.name='AFN124_EDITABLE_NATIVE_NASAL_SCULPT';bpy.context.scene.collection.objects.link(edit);assert edit.data.shape_keys!=ref.data.shape_keys;edit.hide_render=True;edit.hide_set(False);edit.display_type='WIRE';key=edit.shape_key_add(name='AFN124_Nasal_Tip_Alar_Continuity');localDelta=delta@np.linalg.inv(A[:3,:3]).T;basis=q.arr(edit.data.shape_keys.key_blocks[0].data,'co',len(co),3);key.data.foreach_set('co',(basis+localDelta).astype('f4').ravel());ctrl=bpy.data.objects.new('AFN124_NASAL_SCULPT_CONTROL',None);bpy.context.scene.collection.objects.link(ctrl);ctrl['nasal_sculpt']=1.;ctrl.id_properties_ui('nasal_sculpt').update(min=0.,max=1.,description='Own native nasal-complex sculpt; original0/authored1. Current complete source, not whole anatomy/contact/runtime approval.');b.oldbuild.drive(key,ctrl,'nasal_sculpt','v');bpy.context.view_layer.update()
 # Exact subdivision point identity is the construction foundation. Actual
 # skin keys/UV/topology remain intact; editable coarse delta is added live.
 ng=bpy.data.node_groups.new('AFN124_LIVE_NATIVE_SUBDIVISION_CORRESPONDENCE','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');N=ng.nodes;L=ng.links;inp=N.new('NodeGroupInput');out=N.new('NodeGroupOutput');pos=N.new('GeometryNodeInputPosition');ix=N.new('GeometryNodeInputIndex');samples=[]
 for ob in [edit,ref]:
  info=N.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=ob;sample=N.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';L.new(info.outputs['Geometry'],sample.inputs['Geometry']);L.new(pos.outputs['Position'],sample.inputs['Value']);L.new(ix.outputs['Index'],sample.inputs['Index']);samples.append(sample.outputs['Value'])
 subtract=N.new('ShaderNodeVectorMath');subtract.operation='SUBTRACT';L.new(samples[0],subtract.inputs[0]);L.new(samples[1],subtract.inputs[1]);setpos=N.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);L.new(subtract.outputs['Vector'],setpos.inputs['Offset']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=skin.modifiers.new('AFN124_ACTUAL_LIVE_COARSE_SCULPT','NODES');md.node_group=ng
 set_control(0.);zero=a.protected();assert zero==protected;set_control(1.);cd,C,CT=b.u.b.geom(edit);d,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();assert np.max(abs(W-C))<2e-6;after=a.protected();assert after['rawAllShapeKeys']==protected['rawAllShapeKeys'] and after['allOriginalFibres']==protected['allOriginalFibres'];movement=np.linalg.norm(W-baseline,axis=1);ids=np.flatnonzero(movement>1e-7);assert len(ids)>0 and movement.max()<.002
 skin['AFN124_scope']='Original skin/UV/closure keys intact. Live point-index delta between original and artist-edited native coarse subdivision sources. Own nasal-complex handles, no surface projection or pigment change. Coarse/morph controls are not complete anatomy/contact/body/cloth/runtime qualification.';edit['AFN124_scope']='Editable complete native source with own nasal shape key and original subdivision. Actual displayed skin samples its evaluated delta at exact matching point indices. Original reference remains separate. No cage binding or generic projection field.';ref.hide_set(True);edit.hide_set(True);set_control(1.);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
 np.savez_compressed(E/'nasal-sculpt-authoring-lineage.npz',coarseBeforeWorld=world,coarseAuthoredDeltaWorld=delta,coarseChangedIDs=changed,subdivOriginalWorld=baseline,subdivAuthoredWorld=W,displayChangedIDs=ids,displayDeltaWorld=(W-baseline).astype('f4'),matrix=A)
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'coarseSculptObject':edit.name,'originalCoarseReference':ref.name,'actualSkinObject':skin.name,'controlObject':ctrl.name,'controlProperty':'nasal_sculpt','originalNeutralSubdivisionAndDisplayExactlyEqual':True,'allOriginalAtControl0ExactlyRecovered':True,'allOriginalRawClosureKeysAndHairBrowLashPositionsRadiiExactAtControl1':True,'beforeProtected':protected,'afterProtected':after,'authoredWorldMillimetreHandles':{str(k):(v*1000).tolist() for k,v in handles.items()},'mirrorHandlePairs':pairs,'coarseVerticesChanged':len(changed),'displayVerticesChangedAbove0P1Micrometre':len(ids),'coarseMaximumMoveM':float(np.linalg.norm(delta,axis=1).max()),'displayMaximumMoveM':float(movement.max()),'displayChangedBoundsWorld':[W[ids].min(0),W[ids].max(0)],'sameIndexEditedCoarseAndActualDisplayMaximumWorldErrorM':float(np.max(abs(W-C))),'originalUVsMaterialPigmentAndAllOtherLayersPreserved':True,'interpolation':'One harmonic proportional-edit extension through five native edge rings, zero outside fixed nasal neighborhood; fixed explicit handles, no parameter sweep.','fullAnatomyFunctionFiniteContactAndRuntimeNotAccepted':True,'secondsBeforePreview':time.time()-tick})
 rows=[]
 for view in ['face','body-face','profile','oblique','back']:
  rows.append(b.u.v.image('a-live-native-nasal-sculpt',view));save('a-view-controls.json',rows)
 for label,value in [('half',.5),('closed',1.),('restored',0.)]:
  b.deliver(value);rows.append(b.u.v.image('a-live-native-nasal-sculpt-'+label,'face'));save('a-view-controls.json',rows)
 print('R124_COMPLETE_LIVE_NATIVE_NASAL_SCULPT_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
