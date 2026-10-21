"""One coherent editable craniofacial volume-cage rest-shape construction.
Fixed hand-authored malar/submalar/orbital volumes, not nasal-handle retuning.
"""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0125-craniofacial-rest-shape';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend';OUT=S/'r0125-source/aevrynd-female-next-r0125-a-craniofacial-volume-cage.blend'
sp=importlib.util.spec_from_file_location('r125base',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8',newline='\n')
def set_control(value):
 c=bpy.data.objects['AFN125_CRANIOFACIAL_CONTROL'];c['rest_shape']=value;c.update_tag();bpy.data.objects['AFN125_EDITABLE_NATIVE_REST_SOURCE'].update_tag();bpy.context.view_layer.update()
def main():
 tick=time.time();assert not OUT.exists()
 if not (E/'craniofacial-authoring-start.json').exists():save('craniofacial-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct editable volumetric cage for coherent lower-orbital/malar/submalar native rest shape, actual skin live subdivision correspondence.'})
 bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0.);skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];ref=bpy.data.objects['AFN115_EDITABLE_CONNECTED_NATIVE_ADULT_SOURCE'];ref.hide_set(False);bpy.context.view_layer.update();protected=a.protected();_,baseline,BT=b.u.b.geom(skin);baseline=baseline.copy();_,original,_=b.u.b.geom(ref);assert np.array_equal(original,baseline);A=np.array(ref.matrix_world);co=q.arr(ref.data.vertices,'co',len(ref.data.vertices),3);world=co@A[:3,:3].T+A[:3,3]
 edit=ref.copy();edit.data=ref.data.copy();edit.name='AFN125_EDITABLE_NATIVE_REST_SOURCE';bpy.context.scene.collection.objects.link(edit);edit.hide_render=True;edit.hide_set(False);edit.display_type='WIRE'
 lat=bpy.data.lattices.new('AFN125_ORBITAL_MALAR_SUBMALAR_CAGE');lat.points_u=7;lat.points_v=3;lat.points_w=9;lat.interpolation_type_u='KEY_BSPLINE';lat.interpolation_type_v='KEY_BSPLINE';lat.interpolation_type_w='KEY_BSPLINE';cage=bpy.data.objects.new('AFN125_EDITABLE_FACE_VOLUME_CAGE',lat);bpy.context.scene.collection.objects.link(cage);cage.location=(0.,-.12,1.445);cage.scale=(.14,.10,.14);cage.hide_render=True;cage.show_in_front=True
 # Positive Y = into the head, negative Y = forward. Rows are ordered from
 # lower cheek through malar shelf to lower orbit/brow, in millimetres.
 forwardY=np.array([[0,0,0,0,0,0,0],[0,.6,.2,0,.2,.6,0],[0,3.,.8,0,.8,3.,0],[0,1.,-1.2,-.4,-1.2,1.,0],[0,-4.,-2.2,-.8,-2.2,-4.,0],[0,-2.2,.6,-1.2,.6,-2.2,0],[0,-.5,-.8,-.4,-.8,-.5,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0]])
 lateral=np.array([[0,0,0,0,0,0,0],[0,-.4,0,0,0,-.4,0],[0,-1.5,-.3,0,-.3,-1.5,0],[0,-.3,.1,0,.1,-.3,0],[0,1.,.3,0,.3,1.,0],[0,.6,0,0,0,.6,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0]])
 points=[]
 for k in range(9):
  for j in range(3):
   for i in range(7):
    ix=i+7*j+21*k;p=lat.points[ix];base=p.co_deform.copy();side=np.sign(i-3);depth=[1.,1.,0.][j];delta=np.array([side*lateral[k,i],forwardY[k,i],0.])*.001*depth;p.co_deform=base+__import__('mathutils').Vector(delta/np.array(cage.scale));points.append({'index':ix,'u':i,'v':j,'w':k,'originalLocal':list(base),'worldDeltaM':delta.tolist()})
 # Protect exact native eye aperture and oral boundary with topology rings.
 edgefaces={}
 for poly in ref.data.polygons:
  vs=list(poly.vertices)
  for u,v in zip(vs,vs[1:]+vs[:1]):edgefaces.setdefault(tuple(sorted((u,v))),0);edgefaces[tuple(sorted((u,v)))]+=1
 adjacency=[set() for _ in co]
 for u,v in edgefaces:adjacency[u].add(v);adjacency[v].add(u)
 boundary={v for edge,count in edgefaces.items() if count==1 for v in edge};eye={i for i in boundary if world[i,1]<-.085 and 1.45<world[i,2]<1.48};mouth={i for i in boundary if world[i,1]<-.10 and 1.385<world[i,2]<1.422};fixed=eye|mouth;ring=set(fixed)
 for _ in range(2):ring|={j for i in list(ring) for j in adjacency[i]}
 # Include anatomical oral/periocular masks even when source topology closes
 # an opening: these are protected vertices, not excluded collision witnesses.
 x=np.abs(world[:,0]);z=world[:,2];y=world[:,1];eyeMask=(((x-.030)/.019)**2+((z-1.463)/.009)**2<1.)&(y<-.09);oralMask=(x<.027)&(z>1.387)&(z<1.418)&(y<-.112);fixed|=set(map(int,np.flatnonzero(eyeMask|oralMask)));ring|=fixed
 weights=np.ones(len(co));weights[(x>=.07)|(z<=1.375)|(z>=1.515)|(y>=-.075)]=0.;weights[list(ring)]=0.;transition={j for i in ring for j in adjacency[i]}-ring
 for i in transition:weights[i]*=.5
 group=edit.vertex_groups.new(name='AFN125_NATIVE_FACE_VOLUME_DOMAIN')
 for value in [0.5,1.]:
  ids=np.flatnonzero(weights==value).tolist()
  if ids:group.add(ids,value,'REPLACE')
 lm=edit.modifiers.new('AFN125_CRANIOFACIAL_VOLUME_CONSTRUCTION','LATTICE');lm.object=cage;lm.vertex_group=group.name;bpy.context.view_layer.objects.active=edit;bpy.ops.object.modifier_move_to_index(modifier=lm.name,index=0)
 ctrl=bpy.data.objects.new('AFN125_CRANIOFACIAL_CONTROL',None);bpy.context.scene.collection.objects.link(ctrl);ctrl['rest_shape']=1.;ctrl.id_properties_ui('rest_shape').update(min=0.,max=1.,description='Own coherent craniofacial volume-cage rest shape, original0/candidate1; not anatomy/contact/runtime approval.');drv=lm.driver_add('strength').driver;drv.expression='v';v=drv.variables.new();v.name='v';v.targets[0].id=ctrl;v.targets[0].data_path='["rest_shape"]'
 ng=bpy.data.node_groups.new('AFN125_NATIVE_REST_LIVE_SUBDIVISION','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');N=ng.nodes;L=ng.links;inp=N.new('NodeGroupInput');out=N.new('NodeGroupOutput');pos=N.new('GeometryNodeInputPosition');ix=N.new('GeometryNodeInputIndex');samples=[]
 for ob in [edit,ref]:
  info=N.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=ob;sample=N.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';L.new(info.outputs['Geometry'],sample.inputs['Geometry']);L.new(pos.outputs['Position'],sample.inputs['Value']);L.new(ix.outputs['Index'],sample.inputs['Index']);samples.append(sample.outputs['Value'])
 sub=N.new('ShaderNodeVectorMath');sub.operation='SUBTRACT';L.new(samples[0],sub.inputs[0]);L.new(samples[1],sub.inputs[1]);setpos=N.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);L.new(sub.outputs['Vector'],setpos.inputs['Offset']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=skin.modifiers.new('AFN125_ACTUAL_LIVE_CRANIOFACIAL_REST','NODES');md.node_group=ng
 set_control(0.);assert a.protected()==protected;set_control(1.);_,W,_=b.u.b.geom(skin);W=W.copy();_,C,_=b.u.b.geom(edit);error=float(abs(W-C).max());move=np.linalg.norm(W-baseline,axis=1);save('same-index-numeric-readback.json',{'maximumWorldDifferenceM':error,'exactFloatEquality':bool(np.array_equal(C,W)),'maximumMovementM':float(move.max()),'scope':'Geometry-node delta arithmetic readback, not a contact clearance tolerance or appearance pass.'});assert error<2e-6;assert np.isfinite(W).all() and move.max()>1e-5 and move.max()<.006;after=a.protected();assert after['rawAllShapeKeys']==protected['rawAllShapeKeys'];ref.hide_set(True);edit.hide_set(True);cage.hide_set(True);set_control(1.);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
 np.savez_compressed(E/'craniofacial-volume-lineage.npz',coarseOriginalWorld=world,displayOriginalWorld=baseline,displayAuthoredWorld=W,displayDeltaWorld=(W-baseline).astype('f4'),protectedNativeIDs=np.array(sorted(ring)),domainWeights=weights,matrix=A)
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':a.sha(SRC),'output':str(OUT),'sha256':a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkinObject':skin.name,'coarseSculptObject':edit.name,'originalCoarseReference':ref.name,'cageObject':cage.name,'controlObject':ctrl.name,'controlProperty':'rest_shape','method':'One authored7x3x9 B-spline volumetric rest-shape cage across orbital/malar/submalar structure, actual native coarse before subdivision; exact index delta on same complete displayed woman. No nearest-surface projection, nasal-only handles, UV/shader/pigment replacement or parameter sweep.','cageControls':points,'protectedNativeBoundaryAndOralPeriocularVertices':len(ring),'sourceBoundaryEyeVertices':len(eye),'sourceBoundaryMouthVertices':len(mouth),'beforeProtected':protected,'afterProtected':after,'originalAtControl0ExactlyRecovered':True,'originalRawSkinClosureKeysUnchanged':True,'allOriginalFibreGeometryAndRadiusHashesStillExact':after['allOriginalFibres']==protected['allOriginalFibres'],'actualDisplayedVerticesMovedAbove0P1Micrometre':int((move>1e-7).sum()),'maximumActualDisplayMovementM':float(move.max()),'sameIndexEditedCoarseDisplayMaximumErrorM':float(abs(W-C).max()),'originalUVPigmentMaterialsExposureAndBodySourcePreserved':True,'fullAnatomyFunctionFiniteContactAndRuntimeNotAccepted':True,'secondsBeforePreview':time.time()-tick})
 rows=[]
 for view in ['face','body-face','profile','oblique','back']:
  rows.append(b.u.v.image('a-craniofacial-volume-cage',view));save('a-view-controls.json',rows)
 for label,value in [('half',.5),('closed',1.),('restored',0.)]:
  b.deliver(value);rows.append(b.u.v.image('a-craniofacial-volume-cage-'+label,'face'));save('a-view-controls.json',rows)
 print('R125_COMPLETE_CRANIOFACIAL_VOLUME_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
