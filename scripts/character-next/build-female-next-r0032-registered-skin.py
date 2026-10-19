"""One registered CC0 pigment/material baseline; fixed new-head geometry.

Native UV remains intact. Registered source UV coordinates use an additional
point-vector field in B (an extra UV layer in rejected A). Actual facial profile
landmarks sample old skin surface UVs, avoiding the old open-mouth ray hole.
Photo scalp/brow hair is explicitly masked from the pigment transfer.
"""
import bpy,importlib.util,json,math,time,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('inspect32',Path(__file__).with_name('inspect-female-next-r0032-skin-registration.py'));i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
b=i.b;c=i.c;R=i.R;S=i.S;ROOT_E=i.E;CHART='--chart-uv' in sys.argv;E=ROOT_E/'b' if CHART else ROOT_E;E.mkdir(exist_ok=True);SRC=i.NEW;OUT=S/('aevrynd-female-next-r0032-b-chart-registered-skin.blend' if CHART else 'aevrynd-female-next-r0032-a-registered-skin.blend')
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def face_chart(v,t,uv):
    n=len(t);edges=np.concatenate((t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]));euv=np.concatenate((uv[:,[0,1]],uv[:,[1,2]],uv[:,[2,0]]));flip=edges[:,0]>edges[:,1];euv[flip]=euv[flip,::-1];edges=np.sort(edges,axis=1);keys=edges[:,0].astype('i8')*len(v)+edges[:,1];order=np.argsort(keys);faces=np.tile(np.arange(n),3);parents=list(range(n))
    def find(x):
        while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
        return x
    adjacent=(keys[order[:-1]]==keys[order[1:]])&(np.max(np.abs(euv[order[:-1]]-euv[order[1:]]),axis=(1,2))<1e-6)
    for pos in np.flatnonzero(adjacent):a=find(int(faces[order[pos]]));c=find(int(faces[order[pos+1]]));parents[a]=c
    labels=np.array([find(x) for x in range(n)]);bt=BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True);_,_,seed,_=bt.find_nearest(Vector((.025,-.135,1.435)));label=labels[seed];keep=labels==label;counts=np.unique(labels,return_counts=True)[1];save('source-uv-chart-inspection.json',{'sourceTriangles':n,'UVCharts':len(counts),'largestChartSizes':sorted(counts.tolist(),reverse=True)[:10],'selectedSeedWorldM':[.025,-.135,1.435],'selectedChartFaces':int(keep.sum()),'method':'Connected geometry edges only if their two source-UV endpoints also match. Source cheek seed selects one continuous external head photo chart; separate mouth/body/lining islands are excluded.'});return keep
def smooth(a,z,x):
    t=np.clip((x-a)/(z-a),0,1);return t*t*(3-2*t)
def mesh_state():
    return {o.name:{'geometrySha256':b.mesh_signature(o.data)['geometrySha256'],'UV':b.mesh_signature(o.data)['uv'],'parent':o.parent.name if o.parent else None,'basis':b.matrix(o.matrix_basis),'parentInverse':b.matrix(o.matrix_parent_inverse)} for o in bpy.data.objects if o.type=='MESH'}
def main():
    start=time.time();inspection=json.loads((ROOT_E/'source-registration-inspection.json').read_text(encoding='utf8'));assert b.sha(SRC)==inspection['new']['sha256']=='7e0137afbac302c3233e2558fcf450453723b0e2d7ed11bb75abf87543678bf6';assert b.sha(i.TEXTURE)==inspection['textureSha256']=='1d82f782b7d2da732229633bd2d14754d873fff53cdb1d088977bcf67ae19dde'
    save('round-contract.json',{'previousGoalTurn':'progress: r31 two brow styles rejected with real static surface/root evidence; same local brow schemes stopped.','source':str(SRC),'sourceSha256':b.sha(SRC),'defect':'Retained new head is uniformly gray clay; no calibrated anatomical pigment, roughness or skin response.','hypothesis':'An explicitly registered existing CC0 pigment map, regional roughness, micron-scale bump and controlled subsurface response improve skin readability on the same unchanged head without old-UV mismatch.','candidateCount':1,'held':['All body/optical geometry and transforms','Native UV','Lighting,camera,exposure,color management and pose','No brows/lashes/hair added'],'registration':'Profile extrema measured in actual old/new heads; eye horizontal scale from existing verified centers. Nearest old head surface UV samples after landmark warp; no direct old material/UV assignment.','reject':['Visible lip/nose/eye pigment misregistration or UV seam artifacts.','Photo scalp/brow hair presented as actual new groom.','No visible whole-head skin benefit or excessive orange/waxy/noisy result.','Any original geometry/nativeUV/eye/stage state changes.'],'resources':'One Blender,four threads,45-minute checkpoint; additional native UV/point fields,no topology changes or new geometry.','limits':'Reflectance targets inherited from r11 reference-site calibration, not measured skin of this subject. Material-only reference baseline, not a completed photoreal skin or character.'})
    with np.load(ROOT_E/'old-body-sampling.npz') as cache:v=cache['vertices'];t=cache['triangles'];uv=cache['triangleUV']
    keep=np.all(v[t,2]>1.32,axis=1);tt=t[keep];tu=uv[keep];unique,inv=np.unique(tt,return_inverse=True);hv=v[unique];ht=inv.reshape(-1,3)
    if CHART:chart=face_chart(hv,ht,tu);ht=ht[chart];tu=tu[chart]
    source_cache=S/('aevrynd-female-next-r0032-b-source-head-uv.npz' if CHART else 'aevrynd-female-next-r0032-source-head-uv.npz');np.savez_compressed(source_cache,vertices=hv,triangles=ht,triangleUV=tu);tree=BVHTree.FromPolygons(hv.tolist(),ht.tolist(),all_triangles=True)
    # All z anchors below come from recorded actual front-profile extrema;
    # this warp changes sampling coordinates only, never the new geometry.
    newz=np.array([1.3400,1.3716,1.3880,1.3952,1.4030,1.4128,1.4304,1.459491,1.5050,1.5650]);oldz=np.array([1.3400,1.3770,1.3924,1.3980,1.4054,1.4142,1.4270,1.459975,1.5050,1.5650]);xscale=.02825532481/.03127725
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;b.E=E;c.a.q.b.E=E;c.a.E=E;b.setup(s,b.config(s));original_state=mesh_state();cfg=b.config(s);light_state=[(o.name,list(o.location),list(o.rotation_euler),list(o.scale),o.data.energy) for o in s.objects if o.type=='LIGHT'];c.a.q.render('before');c.a.closeup('before');body=bpy.data.objects[b.BODY];m=body.data;P=np.array([list(body.matrix_world@v.co) for v in m.vertices],dtype='f8');normalmatrix=body.matrix_world.to_3x3().inverted().transposed();N=np.array([list(normalmatrix@n.vector) for n in m.vertex_normals]);N/=np.linalg.norm(N,axis=1)[:,None]
    mapped=np.zeros((len(P),2),dtype='f4');weights=[];roughness=[];failures=[];rows=[]
    for vi,(p,n) in enumerate(zip(P,N)):
        x,y,z=p;weight=float(smooth(1.344,1.371,z)*(1-smooth(1.495,1.516,z))*smooth(.025,.080,-y));brow_x=(abs(x)-.0142)/.0453;brow_center=1.4774+.008*math.sin(math.pi*np.clip(brow_x,0,1))
        # Existing photo brow/scalp features are not accepted 3D hair. Exclude
        # their region from transferred pigment, with a soft material blend.
        brow_mask=(1-smooth(.003,.006,abs(z-brow_center)))*smooth(.010,.017,abs(x))*(1-smooth(.058,.064,abs(x)));weight*=1-brow_mask
        if CHART:weight*=1-smooth(.046,.066,abs(x))*smooth(1.460,1.485,z)
        # UV coordinates must remain defined across zero-weight vertices too;
        # otherwise subdivision interpolates from face UV into default(0,0).
        if (z>1.30 if CHART else weight>1e-6):
            zs=float(np.interp(z,newz,oldz));xm=x*(1-(1-xscale)*smooth(1.35,1.415,z));sample=np.array([xm,y,zs]);hit,nn,ti,d=tree.find_nearest(Vector(sample.tolist()));tri=hv[ht[ti]];co=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),np.array(hit)-tri[0],rcond=None)[0];bc=np.maximum(0,np.array([1-co.sum(),co[0],co[1]]));bc/=bc.sum();mapped[vi]=bc@tu[ti];alignment=float(n@np.array(nn));valid=d<.020 and alignment>-.05
            if not valid:failures.append({'vertex':vi,'distanceM':d,'normalDot':alignment,'weight':weight});weight=0
            rows.append({'vertex':vi,'newWorld':p.tolist(),'sampleOldWorld':sample.tolist(),'nearestOldWorld':list(hit),'oldHeadTriangle':int(ti),'barycentric':bc.tolist(),'sourceUV':mapped[vi].tolist(),'distanceM':float(d),'normalDot':alignment,'weight':weight})
        weights.append(weight);nose=math.exp(-((x/.013)**2+((z-1.432)/.018)**2));forehead=math.exp(-((x/.045)**2+((z-1.504)/.018)**2));lips=math.exp(-((x/.022)**2+((z-1.3952)/.0060)**2));roughness.append(.54-.10*nose-.04*forehead-.09*lips)
    newuv=None;mapping_attr=None
    if CHART:
        # Multires evaluation in this Blender build changes when a second UV
        # coordinate set is assigned. Store the same continuous coordinates as
        # a point-vector field instead; leave all native face-varying UV data
        # untouched. The shader reads this named field directly.
        mapping_attr=m.attributes.new('AFN32_RegisteredCC0UVW','FLOAT_VECTOR','POINT');mapping_attr.data.foreach_set('vector',np.column_stack((mapped,np.zeros(len(mapped),dtype='f4'))).astype('f4').ravel())
    else:
        newuv=m.uv_layers.new(name='AFN32_RegisteredCC0UV');loop_verts=np.empty(len(m.loops),dtype='i4');m.loops.foreach_get('vertex_index',loop_verts);newuv.data.foreach_set('uv',mapped[loop_verts].ravel());m.uv_layers.active_index=0
    for name,values in [('AFN32_PigmentWeight',weights),('AFN32_Roughness',roughness)]:attr=m.attributes.new(name,'FLOAT','POINT');attr.data.foreach_set('value',values)
    mat=bpy.data.materials.new('AFN32_RegisteredCalibratedSkin');mat.use_nodes=True;nt=mat.node_tree;shader=nt.nodes.get('Principled BSDF');image=bpy.data.images.load(str(i.TEXTURE),check_existing=True);image.colorspace_settings.name='sRGB';image.pack()
    if CHART:uvnode=nt.nodes.new('ShaderNodeAttribute');uvnode.attribute_name=mapping_attr.name;coordinate_output=uvnode.outputs['Vector']
    else:uvnode=nt.nodes.new('ShaderNodeUVMap');uvnode.uv_map=newuv.name;coordinate_output=uvnode.outputs['UV']
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Linear';nt.links.new(coordinate_output,tex.inputs['Vector']);gain=nt.nodes.new('ShaderNodeMixRGB');gain.blend_type='MULTIPLY';gain.inputs[0].default_value=1;gain.inputs[2].default_value=(*inspection['calibration']['perChannelReflectanceGain'],1);nt.links.new(tex.outputs['Color'],gain.inputs[1]);weight=nt.nodes.new('ShaderNodeAttribute');weight.attribute_name='AFN32_PigmentWeight';mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[1].default_value=(.32,.23,.18,1);nt.links.new(weight.outputs['Fac'],mix.inputs[0]);nt.links.new(gain.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],shader.inputs['Base Color']);rough=nt.nodes.new('ShaderNodeAttribute');rough.attribute_name='AFN32_Roughness';nt.links.new(rough.outputs['Fac'],shader.inputs['Roughness'])
    coords=nt.nodes.new('ShaderNodeTexCoord');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3500*float(body.matrix_world.to_scale().x);noise.inputs['Detail'].default_value=2;nt.links.new(coords.outputs['Object'],noise.inputs['Vector']);bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.000012;nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],shader.inputs['Normal']);shader.inputs['IOR'].default_value=1.4;shader.inputs['Specular IOR Level'].default_value=.30;shader.inputs['Subsurface Weight'].default_value=.09;shader.inputs['Subsurface Scale'].default_value=.0012;shader.inputs['Subsurface Radius'].default_value=(1,.48,.25);m.materials.clear();m.materials.append(mat)
    after=mesh_state()
    for name,state in original_state.items():
        assert after[name]['geometrySha256']==state['geometrySha256'];assert after[name]['parent']==state['parent'] and after[name]['basis']==state['basis'] and after[name]['parentInverse']==state['parentInverse'];assert all(u in after[name]['UV'] for u in state['UV'])
    assert b.config(s)==cfg;assert [(o.name,list(o.location),list(o.rotation_euler),list(o.scale),o.data.energy) for o in s.objects if o.type=='LIGHT']==light_state;b.camera('face');s['AFN32_status']='REGISTERED_SKIN_MATERIAL_BASELINE_STATIC_REVIEW';s['AFN32_calibration']='Inherited six-site albedo target, not subject-measured reflectance';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('registration-data.json',{'zAnchorsNewM':newz.tolist(),'zAnchorsOldM':oldz.tolist(),'eyeXScale':xscale,'oldSource':str(i.OLD),'oldSourceSha256':inspection['old']['sha256'],'newSource':str(SRC),'newSourceSha256':b.sha(SRC),'nativeVertexSamples':rows,'guardFailures':failures,'photoHairMask':'Upper scalp z1.495..1.516, brow region and (B) lateral temple masked to base skin. No scalp/brow geometry generated or claimed.','description':('Continuous source coordinate point-vector field on native cage, within one proven external head UV chart; native UV layers unchanged.' if CHART else 'Additional UV layer on native cage; rejected discontinuities where unmapped coordinates interpolate into visible regions.')+' Nearest source head surface after measured profile sampling warp; bounded approximate pigment registration, not exact biometric correspondence.'})
    save('build-verification.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'originalMeshState':original_state,'material':mat.name,'newUVLayer':newuv.name if newuv else None,'newMappingAttribute':mapping_attr.name if mapping_attr else None,'nativeUVPreserved':True,'originalGeometryTransformsExact':True,'stageOriginalConfig':cfg,'stageOriginalLights':light_state,'texture':{'source':str(i.TEXTURE),'sha256':b.sha(i.TEXTURE),'packed':bool(image.packed_file),'author':'MakeHuman Community','license':'CC0-1.0','calibration':inspection['calibration']},'registrationSamples':len(rows),'registrationGuardFailures':len(failures),'materialInputs':{'baseFallbackLinearRGB':[.32,.23,.18],'roughnessRange':[min(roughness),max(roughness)],'subsurfaceWeight':.09,'subsurfaceScale':.0012,'subsurfaceRadius':[1,.48,.25],'bumpDistance':.000012,'bumpStrength':.12,'geometryDisplacement':False},'seconds':time.time()-start,'limits':['Approximate facial registration from a different subject/base, no exact skin capture.','Body outside registered head uses reference base reflectance only; no full body pigment detail claim.','Photographic source may contain baked shading, not a measured albedo scan.','Procedural microbump and coordinate-field sampling need engine-compatible baking.','No geometry/motion/contact/runtime changes or full-character acceptance.']});c.a.q.render('after');c.a.closeup('after');print('R0032_BUILD_DONE',json.dumps({'samples':len(rows),'failures':len(failures),'output':str(OUT)}),flush=True)
if __name__=='__main__':main()
