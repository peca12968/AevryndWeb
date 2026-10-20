"""One cheap full-character native-rod left-turn trial; stop before expansion."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def module(n,p):
    sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('trial70base',Path(__file__).with_name('build-female-next-r0069-complete-controls.py'));eng=module('trial70native',m.R/'engine/character/physics/groom_native_xpbd_reference.py');R=m.R;E=R/'Evidence/character-female-next/r0070-native-flexible';S=m.S;SRC=S/'aevrynd-female-next-r0069-a-complete-controls-study.blend';TAG='c' if '--uniform-material' in sys.argv else ('b' if '--inextensible' in sys.argv else 'a');OUT=S/('aevrynd-female-next-r0070-'+TAG+'-native-flexible-trial.blend');SHA='f358d3c5a4d00ee6ad94d324612b33bdcf5aa4dde0bb19382d72bc7afabbb667'
def save(n,v):(E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def world(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=m.base.array3(d.position_data,'vector').astype('f8');A=np.array(o.matrix_world);return P@A[:3,:3].T+A[:3,3]
def material_maps(rest,counts):
    starts=np.r_[0,np.cumsum(counts)[:-1]];forward=[];back=[]
    for start,count in zip(starts,counts):
        P=rest[start:start+count];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];u=np.linspace(0,arc[-1],count);assert np.all(np.diff(arc)>1e-7)
        j=np.clip(np.searchsorted(arc,u,side='right')-1,0,count-2);a=(u-arc[j])/(arc[j+1]-arc[j]);forward.extend(zip(start+j,start+j+1,a));v=arc/arc[-1]*(count-1);j2=np.minimum(np.floor(v).astype(int),count-2);b=v-j2;back.extend(zip(start+j2,start+j2+1,b))
    def mapping(rows):
        a=np.array(rows);return (a[:,0].astype('i4'),a[:,1].astype('i4'),a[:,2])
    return mapping(forward),mapping(back)
def mapped(P,indices):
    i,j,a=indices
    return P[i]*(1-a[:,None])+P[j]*a[:,None] if P.ndim==2 else P[i]*(1-a)+P[j]*a
def cache_modifier(o,states,frames):
    A=np.array(o.matrix_world);inv=np.linalg.inv(A[:3,:3]);local=[x@inv.T for x in states];d=bpy.data.meshes.new(o.name+'_AFN70_NATIVE_DISPLACEMENTS');d.from_pydata(local[0].tolist(),[],[]);d.update();helper=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(helper);helper.matrix_world=o.matrix_world.copy();helper.hide_render=True;helper.hide_set(True);helper.shape_key_add(name='Basis')
    for i,(frame,positions) in enumerate(zip(frames[1:],local[1:]),1):
        key=helper.shape_key_add(name='AFN70_Frame_'+str(frame));key.data.foreach_set('co',np.asarray(positions,'f4').ravel())
        for f,v in ((frames[i-1],0),(frame,1),(frames[i+1],0) if i+1<len(frames) else (frame+1,1)):key.value=v;key.keyframe_insert(data_path='value',frame=f)
    if helper.data.shape_keys.animation_data:
        action=helper.data.shape_keys.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for p in fc.keyframe_points:p.interpolation='LINEAR'
    ng=bpy.data.node_groups.new(o.name+'_AFN70_ADD_SIMULATED_OFFSET','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');nodes=ng.nodes;links=ng.links;inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput');info=nodes.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=helper;info.inputs['As Instance'].default_value=False;sample=nodes.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';sample.clamp=False;pos=nodes.new('GeometryNodeInputPosition');idx=nodes.new('GeometryNodeInputIndex');setpos=nodes.new('GeometryNodeSetPosition');links.new(info.outputs['Geometry'],sample.inputs['Geometry']);links.new(pos.outputs['Position'],sample.inputs['Value']);links.new(idx.outputs['Index'],sample.inputs['Index']);links.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);links.new(sample.outputs['Value'],setpos.inputs['Offset']);links.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=o.modifiers.new('AFN70_NATIVE_FLEXIBLE_TRIAL','NODES');md.node_group=ng;helper['scope']='Baked all-displayed-particle displacements, sampled frames only. Root offsets zero. No continuous/contact/runtime acceptance.'
def main():
    tick=time.time();E.mkdir(parents=True,exist_ok=True);assert not OUT.exists() and m.sha(SRC)==SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();objects=[bpy.data.objects[n] for n in ('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES')];pieces=[world(o) for o in objects];cuts=np.r_[0,np.cumsum([len(p) for p in pieces])];rest=np.concatenate(pieces);counts=np.concatenate([np.array([c.points_length for c in o.data.curves]) for o in objects]);radii=[]
    for o in objects:
        rr=np.empty(len(o.data.position_data),'f4');o.data.attributes['radius'].data.foreach_get('value',rr);radii.append(rr*np.linalg.norm(np.array(o.matrix_world)[:3,:3],ord=2))
    native_rest=rest.copy();native_radii=np.concatenate(radii);radii=native_radii.copy();forward=back=None
    if TAG=='c':forward,back=material_maps(rest,counts);rest=mapped(rest,forward);radii=mapped(radii,forward);np.savez_compressed(E/'c-material-parameterization.npz',forward0=forward[0],forward1=forward[1],forwardWeight=forward[2],back0=back[0],back1=back[1],backWeight=back[2],nativeRest=native_rest.astype('f4'),materialRest=rest.astype('f4'),nativeRadii=native_radii,counts=counts)
    solver=(eng.NativeInextensibleFTL if TAG in ('b','c') else eng.NativeRods)(rest,counts,radii)
    if TAG=='c':
        starts=solver.starts;length=np.array([np.linalg.norm(np.diff(rest[s:s+n],axis=0),axis=1).mean() for s,n in zip(starts,counts)]);mass=eng.DENSITY*np.pi*np.maximum(radii,1e-6)**2*np.repeat(length,counts);solver.w=1/mass;solver.w[starts]=0
    native_local=np.concatenate([np.arange(n) for n in counts]);native_edges=np.flatnonzero(native_local<np.repeat(counts,counts)-1);native_length=np.linalg.norm(native_rest[native_edges+1]-native_rest[native_edges],axis=1)
    previous=rest.copy();body=bpy.data.objects[m.native_names()[4]];oldbody=m.k.mesh(body);saved_frames=[1];offsets=[np.zeros_like(native_rest)];rows=[]
    for frame in range(2,14):
        s.frame_set(frame);bpy.context.view_layer.update();native_target=np.concatenate([world(o) for o in objects]);target=mapped(native_target,forward) if TAG=='c' else native_target;row=m.k.mesh(body);V,T=row['V'],row['T'];tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);N=len(rest);near=np.empty((N,3));normal=np.empty((N,3));face=np.empty(N,'i4')
        for i,q in enumerate(solver.x):
            p,n,f,distance=tree.find_nearest(Vector(q));near[i]=p;normal[i]=n;face[i]=f
        tri=V[T[face]];a=tri[:,1]-tri[:,0];b=tri[:,2]-tri[:,0];q=near-tri[:,0];aa=np.einsum('ij,ij->i',a,a);ab=np.einsum('ij,ij->i',a,b);bb=np.einsum('ij,ij->i',b,b);qa=np.einsum('ij,ij->i',q,a);qb=np.einsum('ij,ij->i',q,b);den=aa*bb-ab*ab;assert (den>1e-24).all();u=(bb*qa-ab*qb)/den;v=(aa*qb-ab*qa)/den;weights=np.column_stack((1-u-v,u,v));oldtri=oldbody['V'][T[face]];oldnear=np.einsum('ij,ijk->ik',weights,oldtri);oldnormal=np.cross(oldtri[:,1]-oldtri[:,0],oldtri[:,2]-oldtri[:,0]);oldnormal/=np.linalg.norm(oldnormal,axis=1)[:,None];report=solver.advance(previous,target,oldnear,near,oldnormal,normal,radii);report.update(frame=frame,seconds=time.time()-tick);rows.append(report);print('R70_ACTUAL_ALL_PARTICLES',report,flush=True)
        native_offset=mapped(solver.x-target,back) if TAG=='c' else solver.x-target;native_output=native_target+native_offset;native_strain=np.abs(np.linalg.norm(native_output[native_edges+1]-native_output[native_edges],axis=1)/native_length-1);report['maximumActualDisplayEdgeRelativeStrain']=float(native_strain.max());report['p99ActualDisplayEdgeRelativeStrain']=float(np.quantile(native_strain,.99));previous=target;oldbody=row
        if frame%4==1:saved_frames.append(frame);offsets.append(native_offset)
        # A large stretch failure falsifies this finite iteration/discrete-plane construction.
        if report['maximumRelativeEdgeStrain']>.10 or report.get('infeasibleCachedSpherePlaneConstraints',0)>0 or report['maximumActualDisplayEdgeRelativeStrain']>.10:
            if saved_frames[-1]!=frame:saved_frames.append(frame);offsets.append(native_offset)
            print('R70_CHEAP_STRAIN_FALSIFICATION',frame,flush=True);break
    last=rows[-1]['frame'];np.savez_compressed(E/(TAG+'-native-motion-raw.npz'),frames=np.array(saved_frames),offsets=np.array(offsets,dtype='f4'),rest=native_rest.astype('f4'),counts=counts,radii=native_radii,cuts=cuts)
    for j,o in enumerate(objects):cache_modifier(o,[x[cuts[j]:cuts[j+1]] for x in offsets],saved_frames)
    s.frame_start=1;s.frame_end=last;s.frame_set(1);bpy.context.view_layer.update();s['AFN70_scope']='All native display particle flexible trial through first original left turn only. Cached discrete closest-skin planes, co-rotated curvature/stretch/root tangent, gravity/drag. No self/torsion/friction/continuous or runtime acceptance.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    result={'revision':'female-next-r0070','source':str(SRC),'sourceSha256':SHA,'output':str(OUT),'outputSha256':m.sha(OUT),'actualCurves':len(counts),'actualParticles':len(rest),'simulatedSourceFrames':[1,last],'savedOffsetFrames':saved_frames,'rows':rows,'sourcePrimaryReference':('https://matthias-research.github.io/pages/publications/FTLHairFur.pdf' if TAG=='b' else 'https://github.com/GPUOpen-Effects/TressFX/blob/master/src/Shaders/TressFXSimulation.hlsl'),'method':('Own native variable-length dynamicFTL, co-rotated elastic local shape, exact length-sphere/contact-cap intersection, velocity correction1.0, gravity/drag; cached planes not full collision proof.' if TAG=='b' else 'Own all-native-particle co-rotated vector-curvature/stretch XPBD, root-tangent boundary, gravity and drag; per-frame discrete closest-plane contact response. No guide/follow deformation transfer.'),'parameters':{'youngPa':eng.YOUNG,'densityKgM3':eng.DENSITY,'dragRatePerS':eng.DRAG_RATE,'substeps':eng.SUBSTEPS,'iterations':eng.ITERATIONS,'decorativePhysicalRadiusFloorM':1e-6,'actualRenderCollisionRadiiUnchanged':True},'newPhysicsAccepted':False,'selfTorsionFrictionCalibrationAndContinuousNotImplemented':True,'firstCheapFalsificationRelativeStrainLimit':.10,'sourceNativeRestGeometrySkinMaterialsLightingUnchanged':True,'partialPilotNotFullOriginalAnimation':True,'secondsBeforePreview':time.time()-tick};save(TAG+'-build-summary.json',result)
    if TAG=='c':result['uniformMaterialParameterization']='Same number of particles per individual fibre, equal arc-length sampling and equal lumped mass along each constant-radius main strand. Render CVs/material/radius unchanged; simulation offsets transferred by explicit material-coordinate maps. Actual displayed edge strain is separately rejected, never inferred from solver lengths.';result['sourcePrimaryReference']='https://matthias-research.github.io/pages/publications/FTLHairFur.pdf';result['method']='Own equal-material-coordinate DFTL with geometric length/contact-cap solve and explicit original-render-CV deformation transfer; cached body planes and uncalibrated curvature response remain limitations.';save(TAG+'-build-summary.json',result)
    m.shade.settings();s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;controls=[]
    for f,view in ((last,'face'),(last,'body-face')):
        s.frame_set(f);m.k.b.camera(view);s.camera.data.lens=85;s.render.filepath=str(E/f'{TAG}-pilot-{f}-{view}.png');bpy.ops.render.render(write_still=True);controls.append({'frame':f,'view':view,'file':s.render.filepath,'resolution':640,'samples':16,'camera':np.array(s.camera.matrix_world).tolist()})
    save(TAG+'-pilot-controls.json',controls);print('R70_COMPLETE_HEAD_PILOT_DONE',last,time.time()-tick,flush=True)
if __name__=='__main__':main()
