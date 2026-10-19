"""Own complete ocular-junction rest layer on exact retained full character.
Actual-globe front-gap contraction preserves x/z and iris aperture. Native
Multires/source cage retained; explicit post-Multires point delta GN layer.
Wet tissue bases and lash follicles rebuild from original exact body lineage.
Static neutral only; no blink or calibrated tear-fluid/optical claim.
"""
import bpy,importlib.util,time,json,hashlib,sys
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
sp=importlib.util.spec_from_file_location('ocular43i',Path(__file__).with_name('inspect-female-next-r0043-ocular-junction.py'));i=importlib.util.module_from_spec(sp);sp.loader.exec_module(i)
f=i.f;b=i.b;v=i.v;E=i.E;S=i.S;SRC=i.SRC
CONSISTENT='--consistent-attachments' in sys.argv;LABEL='b' if CONSISTENT else 'a'
OUT=S/('aevrynd-female-next-r0043-b-consistent-ocular-junction.blend' if CONSISTENT else 'aevrynd-female-next-r0043-a-lid-apposition.blend')
def save(n,x):
    if CONSISTENT:n='b-'+n[2:] if n.startswith('a-') else ('b-round-contract.json' if n=='round-contract.json' else n)
    i.save(n,x)
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def rotation(a,z):
    c=float(np.clip(a@z,-1,1));assert c>-.99;u=np.cross(a,z);K=np.array(((0,-u[2],u[1]),(u[2],0,-u[0]),(-u[1],u[0],0)));return np.eye(3)+K+K@K/(1+c)

def delta_layer(body,D,T):
    matrix=np.array(body.matrix_world);local=D@np.linalg.inv(matrix[:3,:3]).T
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());source=ev.to_mesh();source.calc_loop_triangles();loops=np.array([t.loops[:] for t in source.loop_triangles],dtype='i4');assert np.array_equal(np.array([t.vertices[:] for t in source.loop_triangles]),T)
    old=np.empty(len(source.vertices)*3,dtype='f4');source.vertices.foreach_get('co',old);old=old.reshape(-1,3);new=(old+local.astype('f4')).astype('f4')
    def geometric_normals(P):
        Q=P.astype('f8')[T];F=np.cross(Q[:,1]-Q[:,0],Q[:,2]-Q[:,0]);N=np.zeros((len(P),3))
        for k in range(3):np.add.at(N,T[:,k],F)
        N/=np.maximum(np.linalg.norm(N,axis=1)[:,None],1e-30);return N
    N0=geometric_normals(old);N1=geometric_normals(new);axis=np.cross(N0,N1);sn=np.linalg.norm(axis,axis=1);angle=np.arctan2(sn,np.einsum('ij,ij->i',N0,N1));axis/=np.maximum(sn[:,None],1e-30);axis[sn<1e-14]=(0.,1.,0.);angle[sn<1e-14]=0.
    mesh=bpy.data.meshes.new('AFN43_NEUTRAL_LID_REST_DATA');mesh.vertices.add(len(old));mesh.vertices.foreach_set('co',old.ravel());mesh.loops.add(len(T)*3);mesh.loops.foreach_set('vertex_index',T.astype('i4').ravel());mesh.polygons.add(len(T));mesh.polygons.foreach_set('loop_start',np.arange(len(T),dtype='i4')*3);mesh.polygons.foreach_set('loop_total',np.full(len(T),3,dtype='i4'));mesh.polygons.foreach_set('use_smooth',np.ones(len(T),dtype=bool));mesh.update(calc_edges=True)
    for mat in source.materials:mesh.materials.append(mat)
    for uv in source.uv_layers:
        a=np.empty(len(uv.data)*2,dtype='f4');uv.data.foreach_get('uv',a);dest=mesh.uv_layers.new(name=uv.name);dest.data.foreach_set('uv',a.reshape(-1,2)[loops].ravel())
    for name in ('AFN32_RegisteredCC0UVW','AFN32_PigmentWeight','AFN32_Roughness'):
        ar=source.attributes[name];n=3 if ar.data_type=='FLOAT_VECTOR' else 1;data=np.empty(len(ar.data)*n,dtype='f4');ar.data.foreach_get('vector' if n==3 else 'value',data);dest=mesh.attributes.new(name,ar.data_type,'POINT');dest.data.foreach_set('vector' if n==3 else 'value',data)
    for name,values,domain,dtype,field in [('AFN43_RestDelta',local,'POINT','FLOAT_VECTOR','vector'),('AFN43_NormalAxis',axis,'POINT','FLOAT_VECTOR','vector'),('AFN43_NormalAngle',angle,'POINT','FLOAT','value'),('AFN43_SourceCorner',loops.ravel(),'CORNER','INT','value')]:
        ar=mesh.attributes.new(name,dtype,domain);ar.data.foreach_set(field,np.asarray(values,dtype='i4' if dtype=='INT' else 'f4').ravel())
    ev.to_mesh_clear();o=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(o);o.matrix_world=Matrix.Identity(4);o.hide_render=True;o.hide_set(True);o['aevrynd_layer']='NEUTRAL_REST_TOPOLOGY_AND_DELTA_DATA';o['expected_evaluated_body_vertices']=len(D);o['scope']='Exact source tessellation and static neutral rest data. Input cage/Multires remain editable. Rebuild if source topology/order/UV/fields change. Not rig or physics.'
    ng=bpy.data.node_groups.new('AFN43_LidRestApposition','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');nodes=ng.nodes;links=ng.links
    inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput');info=nodes.new('GeometryNodeObjectInfo');info.transform_space='ORIGINAL';info.inputs['Object'].default_value=o;info.inputs['As Instance'].default_value=False
    def attr(name,dtype='FLOAT_VECTOR'):
        n=nodes.new('GeometryNodeInputNamedAttribute');n.data_type=dtype;n.inputs['Name'].default_value=name;return n.outputs['Attribute']
    sample=nodes.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';sample.clamp=False;pos=nodes.new('GeometryNodeInputPosition');idx=nodes.new('GeometryNodeInputIndex');setpos=nodes.new('GeometryNodeSetPosition');size=nodes.new('GeometryNodeAttributeDomainSize');compare=nodes.new('ShaderNodeMath');compare.operation='COMPARE';compare.inputs[1].default_value=float(len(D));compare.inputs[2].default_value=.5
    links.new(inp.outputs[0],sample.inputs['Geometry']);links.new(pos.outputs[0],sample.inputs['Value']);links.new(idx.outputs[0],sample.inputs['Index']);links.new(info.outputs['Geometry'],setpos.inputs['Geometry']);links.new(sample.outputs[0],setpos.inputs['Position']);links.new(attr('AFN43_RestDelta'),setpos.inputs['Offset']);links.new(inp.outputs[0],size.inputs['Geometry']);links.new(size.outputs['Point Count'],compare.inputs[0])
    normal=nodes.new('GeometryNodeInputNormal');snorm=nodes.new('GeometryNodeSampleIndex');snorm.data_type='FLOAT_VECTOR';snorm.domain='CORNER';snorm.clamp=False;links.new(inp.outputs[0],snorm.inputs['Geometry']);links.new(normal.outputs[0],snorm.inputs['Value']);links.new(attr('AFN43_SourceCorner','INT'),snorm.inputs['Index']);rotate=nodes.new('ShaderNodeVectorRotate');rotate.rotation_type='AXIS_ANGLE';links.new(snorm.outputs[0],rotate.inputs['Vector']);links.new(attr('AFN43_NormalAxis'),rotate.inputs['Axis']);links.new(attr('AFN43_NormalAngle','FLOAT'),rotate.inputs['Angle']);setnormal=nodes.new('GeometryNodeSetMeshNormal');setnormal.mode='FREE';setnormal.domain='CORNER';links.new(setpos.outputs[0],setnormal.inputs['Mesh']);links.new(rotate.outputs[0],setnormal.inputs['Custom Normal']);switch=nodes.new('GeometryNodeSwitch');switch.input_type='GEOMETRY';links.new(compare.outputs[0],switch.inputs['Switch']);links.new(inp.outputs[0],switch.inputs['False']);links.new(setnormal.outputs[0],switch.inputs['True']);links.new(switch.outputs[0],out.inputs[0]);mod=body.modifiers.new('AFN43_NeutralLidRest','NODES');mod.node_group=ng
    return o,ng

def main():
    start=time.time();assert b.sha(SRC)=='d62c180a5af61f6f8d800926b101738c89a8fbe7785fe1054fd655fd018824da';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;body=bpy.data.objects[b.BODY];before=f.state();native=b.mesh_signature(body.data);V,T=b.evaluated(body,True);measure=json.loads((E/'source-ocular-measurements.json').read_text());D=np.zeros_like(V);rows=[]
    save('round-contract.json',{'revision':'female-next-r0043-a','source':str(SRC),'sourceSha256':b.sha(SRC),'previousGoalTurnClassification':'progress: ownedr42B reduces false shadow bands; exact geometry/materials/liveguide proof and actual full views, pushed0e8871f','primaryDefect':'Detached body-lid/globe junction; staring/artificial eye presentation','sourceEvidence':'Actual upperiris occlusion1.19..1.30mm already in reference range, so keep aperture and globe size; nearest visible lid/globe gaps0.46..1.61mm remain.','hypothesis':'Bring both upper/lower lid tissues toward actual globe while preserving frontal opening; rebuild attached wet margins and220actual lash roots in one complete model.','method':'Source-rim reference target80percent of actual front-eye excess gap above120um normal clearance, normalized0.7mm Gaussian interpolation, compact4mm XZ and8mm depth support, fixed canthal taper and actual-globe normal mask. PositiveY shift capped at90percent of local allowed gap; measured depth Jacobian lower bound retained. Exact source triangle/cornerUV template with relative normal transport after original native Multires. Neutral rest only.','reject':['Body/eye or changed-self/tissue/lash intersections','Lost exact skin attachment or significant visible distortion','Unexpected topology/order,field or unrelated source changes','No multiangle full-head improvement'],'held':['Native source control cage,UV andskin attributes','All8optical meshes/poses/materials','Brow/scalp geometry,widths,live guide functions','r42jitter/renderquality and fixed lighting,exposure,color management'],'references':[{'url':'https://www.uclahealth.org/sites/default/files/documents/1_11_12_tajudeen_bleph_ch176.pdf','use':'Adult lid/limbus relationship modeling reference only, not universal aesthetic or medical prescription.'},{'url':'https://studios.disneyresearch.com/2014/11/19/high-quality-capture-of-eyes/','use':'Model dependent ocular structures together; own implementation, no paper code/assets.'}],'resources':{'startUTC':'2026-10-19 13:56:24 UTC','checkpointUTC':'2026-10-19 14:41:24 UTC','threads':4,'heavyJobsAtOnce':1},'scope':'Neutral anatomical rest authoring only. No blink,gaze,continuous dynamics,complete physiology or engine acceptance.'})
    for side in ('L','R'):
        eyeV,eyeT=i.i.outer(side);eye=i.i.tree(eyeV,eyeT);c=np.array(i.i.FITS[side]['centerM']);Q=np.array(measure['rim'][side]['upper']['points']+measure['rim'][side]['lower']['points']);inside=(abs(V[:,0]-c[0])<.0165)&(V[:,1]<-.095)&(V[:,2]>Q[:,2].min()-.004)&(V[:,2]<Q[:,2].max()+.004);ids=np.flatnonzero(inside);xz=V[ids][:,[0,2]];dist=np.sqrt(np.min(np.sum((xz[:,None]-Q[None,:,[0,2]])**2,axis=2),axis=1));weight=np.maximum(0,1-(dist/.004)**2)**3*(1-smooth((abs(V[ids,0]-c[0])-.008)/.004))
        target=[]
        for qp in Q:
            h,n,_,_=eye.ray_cast(Vector((qp[0],-.25,qp[2])),Vector((0,1,0)),.3)
            target.append(.80*max(0.,float(h.y-qp[1])-.00012/max(abs(n.y),.15)) if h is not None else 0.)
        target=np.array(target);d2=np.sum((xz[:,None]-Q[None,:,[0,2]])**2,axis=2);K=np.exp(-d2/(.0007**2));den=np.maximum(K.sum(1),1e-30);rimDelta=K@target/den;rimY=K@Q[:,1]/den
        #Reference-rim displacement, not all anterior tissue gap. Compact depth
        #falloff keeps derivative bound positive; safety map is monotone too.
        bound=1-float(rimDelta.max())*1.718/.008;assert bound>.1,('Non-monotone depth support bound',bound)
        depthWeight=np.maximum(0,1-((V[ids,1]-rimY)/.008)**2)**3
        used=0;maximum=0.
        for vi,w,delta0,depth in zip(ids,weight,rimDelta,depthWeight):
            if w<1e-6:continue
            p=V[vi];hit,n,tid,d=eye.ray_cast(Vector((p[0],-.25,p[2])),Vector((0,1,0)),.3)
            if hit is None:continue
            ny=abs(n.y);w*=float(smooth((ny-.15)/.35));gap=float(hit.y-p[1]);g0=.00012/max(ny,.15)
            if gap<=g0 or w<=0:continue
            u=gap-g0;delta=min(float(delta0*w*depth),.90*w*u);D[vi,1]=delta;used+=1;maximum=max(maximum,delta)
        rows.append({'side':side,'candidateVertices':len(ids),'movingVertices':used,'maximumDepthShiftM':maximum,'depthSupportJacobianLowerBound':bound,'maximumReferenceRimDepthShiftM':float(rimDelta.max())})
    assert np.isfinite(D).all() and (D[:,1]>=0).all()
    if D.max()>=.002:
        k=int(np.argmax(D[:,1]));save('a-initial-field-rejection.json',{'status':'STOP_OVER2MM_GUARD_NO_MODEL_SAVED','maximumRequestedMovementM':float(D[k,1]),'point':V[k].tolist(),'rows':rows,'reason':'XZ-only gap contraction also affects protruding front orbital tissue; constrain displacement to source rim depth band before production.'});print('R43_A_STOP_INITIAL_FIELD',D[k,1],V[k],flush=True);return
    helper,ng=delta_layer(body,D,T);bpy.context.view_layer.update();NV,NT=b.evaluated(body,True);changed=np.flatnonzero(np.linalg.norm(NV-V,axis=1)>1e-10);error=float(np.linalg.norm(NV-(V+D),axis=1).max());sameT=np.array_equal(T,NT)
    save('a-rest-layer-feasibility.json',{'changedVertices':len(changed),'maximumMovementM':float(np.linalg.norm(NV-V,axis=1).max()),'requestedDeltaReadbackErrorM':error,'triangleOrderExact':sameT,'oldTriangleHash':hashlib.sha256(T.tobytes()).hexdigest(),'newTriangleHash':hashlib.sha256(NT.tobytes()).hexdigest(),'rows':rows,'originalNativeMeshUVExact':b.mesh_signature(body.data)==native,'seconds':time.time()-start})
    if error>1.5e-7 or not sameT:print('R43_A_STOP_REPRESENTATION',error,sameT,flush=True);return
    np.savez_compressed(S/f'aevrynd-female-next-r0043-{LABEL}-rest-delta.npz',bodyDeltaWorld=D.astype('f4'),changedVertexIndices=changed)
    #Cheap actual globe/body gate before rebuilding attached structures.
    bt=i.i.tree(NV,NT);contacts={}
    for side in ('L','R'):
        for part in ('Sclera','Cornea','Iris','Pupil'):
            name=f'AFN30_{side}_{part}';ev,et=b.evaluated(bpy.data.objects[name],True);pairs=bt.overlap(i.i.tree(ev,et));contacts[name]=len(pairs)
    save('a-body-optical-feasibility.json',{'contacts':contacts,'status':'PASS_ACTUAL_NEUTRAL_BODY_OPTICS' if not any(contacts.values()) else 'REJECT_BODY_OPTICS','seconds':time.time()-start})
    if any(contacts.values()):print('R43_A_STOP_BODY_OPTICS',contacts,flush=True);return
    #Exact existing skin triangle/barycentric tissue lineage; no new exceptions.
    tb=json.loads((b.R/'Evidence/character-female-next/r0037-eye-margin/c-review-tissue-bindings.json').read_text());localNew=(NV-np.array(body.matrix_world)[:3,3])@np.linalg.inv(np.array(body.matrix_world)[:3,:3]).T
    normals=np.zeros_like(NV);tri=NV[NT];fn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    for j in range(3):np.add.at(normals,NT[:,j],fn)
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-20);oldnormals=np.zeros_like(V);oldt=V[T];oldfn=np.cross(oldt[:,1]-oldt[:,0],oldt[:,2]-oldt[:,0])
    for j in range(3):np.add.at(oldnormals,T[:,j],oldfn)
    oldnormals/=np.maximum(np.linalg.norm(oldnormals,axis=1)[:,None],1e-20);inverse=np.linalg.inv(np.array(body.matrix_world));patches=[]
    for record in tb['patches']:
        o=bpy.data.objects[record['object']];Pold,TT=b.evaluated(o,True);n=len(record['nodes']);baseNew=np.array([np.array(x['weights'])@NV[x['indices']] for x in record['nodes']]);baseOld=np.array([np.array(x['weights'])@V[x['indices']] for x in record['nodes']]);normalNew=np.array([np.array(x['weights'])@normals[x['indices']] for x in record['nodes']]);normalNew/=np.linalg.norm(normalNew,axis=1)[:,None];Pnew=[]
        for vi,(source,role) in enumerate(zip(record['vertexBaseNode'],record['vertexRole'])):
            h=0. if role=='base' else float(np.linalg.norm(Pold[vi]-baseOld[source]))
            if CONSISTENT:
                node=record['nodes'][source];n0=np.array(node['weights'])@oldnormals[node['indices']];n0/=np.linalg.norm(n0);R=rotation(n0,normalNew[source]);Pnew.append(baseNew[source]+R@(Pold[vi]-baseOld[source]))
            else:Pnew.append(baseNew[source]+normalNew[source]*h)
        Pnew=np.array(Pnew);mx=np.array(o.matrix_world);loc=(Pnew-mx[:3,3])@np.linalg.inv(mx[:3,:3]).T;o.data.vertices.foreach_set('co',loc.astype('f4').ravel());o.data.update();patches.append({'object':o.name,'baseNodes':n,'maximumMovementM':float(np.linalg.norm(Pnew-Pold,axis=1).max())})
    #Closed display lash meshes and their actual authoring controls move together.
    bindings=json.loads((b.R/'Evidence/character-female-next/r0037-eye-margin/c-final-lash-bindings.json').read_text());roots=bindings['roots'];byName={}
    for row in roots:byName.setdefault(row['object'],[]).append(row)
    lashRows=[]
    for name,records in byName.items():
        o=bpy.data.objects[name];Pold,TT=b.evaluated(o,True);assert len(Pold)==len(records)*258;Pnew=Pold.copy();control=bpy.data.objects[name.replace('_Lashes','_LashControls')];gp,gr=v.hair_arrays(control);gm=np.array(control.matrix_world);gw=gp.astype('f8')@gm[:3,:3].T+gm[:3,3];newg=gw.copy()
        for ci,row in enumerate(records):
            bc=np.array(row['barycentric']);tid=int(row['bodyTriangle']);oldFoot=bc@V[T[tid]];newFoot=bc@NV[T[tid]];oldN=np.array(row['normal'])
            if CONSISTENT:
                t0=V[T[tid]];t1=NV[T[tid]];n0=np.cross(t0[1]-t0[0],t0[2]-t0[0]);n0/=np.linalg.norm(n0);n1=np.cross(t1[1]-t1[0],t1[2]-t1[0]);n1/=np.linalg.norm(n1);R=rotation(n0,n1);newN=R@oldN
            else:newN=bc@normals[T[tid]];newN/=np.linalg.norm(newN);R=rotation(oldN,newN)
            stand=float(row['standOffM']);oldRoot=oldFoot+oldN*stand;newRoot=newFoot+newN*stand;sl=slice(ci*258,(ci+1)*258);Pnew[sl]=newRoot+(Pold[sl]-oldRoot)@R.T;newg[ci]=newRoot+(gw[ci]-oldRoot)@R.T
        mx=np.array(o.matrix_world);o.data.vertices.foreach_set('co',((Pnew-mx[:3,3])@np.linalg.inv(mx[:3,:3]).T).astype('f4').ravel());o.data.update();control.data.position_data.foreach_set('vector',((newg-gm[:3,3])@np.linalg.inv(gm[:3,:3]).T).astype('f4').ravel());lashRows.append({'object':name,'fibres':len(records),'maximumMovementM':float(np.linalg.norm(Pnew-Pold,axis=1).max())})
    b.camera('face');s.camera.data.lens=85;s['AFN43_status']='NEUTRAL_OCULAR_APPOSITION_CANDIDATE_UNQUALIFIED';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'bodyDeltaHelper':helper.name,'nodes':len(ng.nodes),'nativeControlCageMultiresUVRetained':True,'bodyTriangleOrderExact':True,'patches':patches,'lashes':lashRows,'changedBodyVertices':len(changed),'bodyMovementBoundsM':{'min':NV[changed].min(0).tolist(),'max':NV[changed].max(0).tolist()},'sourceState':before,'status':'FULL_VISUAL_AND_SAVED_CONTACT_REVIEW_REQUIRED','seconds':time.time()-start})
    f.E=E;f.render(LABEL+'-after');i.ch.review.extras(LABEL+'-after',E);f.g.E=E;f.g.closeup(LABEL+'-after');print('R43_DONE',LABEL,len(changed),time.time()-start,flush=True)
if __name__=='__main__':main()
