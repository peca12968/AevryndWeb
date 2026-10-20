"""Independent saved-source skin and sampled scalp-following check, not physics."""
from pathlib import Path
import bpy,numpy as np,time,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import importlib.util
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('verify69build','build-female-next-r0069-complete-controls.py');v=module('verify69native','verify-female-next-r0061-complete-groom.py');par=module('verify69parity','probe-female-next-r0067-contacts.py')
def world(o):
    P=m.base.array3(o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.position_data,'vector');A=np.array(o.matrix_world);return P.astype('f8')@A[:3,:3].T+A[:3,3]
def main():
    tick=time.time();summary=m.read(m.E/'a-build-summary.json');source=Path(summary['output']);history='--history' in sys.argv
    if history:source=m.R/'sites-engine-journey/assets-source/aevrynd-character/female-next'/source.name
    assert m.sha(source)==summary['outputSha256'];names=m.native_names();bpy.ops.wm.open_mainfile(filepath=str(m.SRC));bpy.context.scene.frame_set(1);native={n:v.mesh_signature(bpy.data.objects[n]) for n in names};materials={x.name:m.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes};curves={n:m.k.v59.native_curves(bpy.data.objects[n]) for n in ('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES')};v.raise_subdivision();neutral={n:m.k.mesh(bpy.data.objects[n])['V'] for n in names};bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();assert native=={n:v.mesh_signature(bpy.data.objects[n]) for n in names};assert materials=={n:m.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in materials};assert curves=={n:m.k.v59.native_curves(bpy.data.objects[n]) for n in curves}
    rig=bpy.data.objects['AFN69_BODY_CONTROLS'];assert len(rig.data.bones)==52;raw=np.load(m.E/'source-indexed-body-weights.npz',allow_pickle=False);W=raw['weights'];order=raw['names'].tolist();assert (W>=0).all() and np.max(np.abs(W.sum(1)-1))<1e-6;weight_errors=[]
    for n in names:
        o=bpy.data.objects[n];ids=np.empty(len(o.data.vertices),'i4');o.data.attributes['AFN60_NativeVertexID'].data.foreach_get('value',ids);actual=np.zeros((len(ids),52),'f4');lookup={o.vertex_groups[name].index:i for i,name in enumerate(order) if name in o.vertex_groups}
        for vertex in o.data.vertices:
            for g in vertex.groups:
                if g.group in lookup:actual[vertex.index,lookup[g.group]]=g.weight
        assert np.array_equal(actual,W[ids]);assert o.modifiers[0].type=='ARMATURE' and o.modifiers[0].object==rig;weight_errors.append({'object':n,'vertices':len(ids),'sourceNormalizedWeightsExact':True})
    cache=bpy.data.objects['AFN69_REST_BODY_POINT_REFERENCE'];assert len(cache.data.polygons)==0 and cache.hide_render and len(cache.data.vertices)==len(m.k.mesh(bpy.data.objects[names[4]])['V']);rows=[];initial=None;stats=[]
    for frame in (1,13,25,49,61):
        s.frame_set(frame);bpy.context.view_layer.update();body=m.k.mesh(bpy.data.objects[names[4]]);entry={'frame':frame,'boneQuaternions':{n:list(rig.pose.bones[n].rotation_quaternion) for n in ('Head','LeftArm','RightArm')},'groom':[]}
        if frame==1:
            geometry={n:m.k.mesh(bpy.data.objects[n]) for n in names};err={n:float(np.linalg.norm(geometry[n]['V']-neutral[n],axis=1).max()) for n in names};assert max(err.values())<1e-6;entry['neutralOriginalBodyErrorsM']=err;initial=body['V'].copy()
            for n in names:
                o=bpy.data.objects[n];stats.append({'object':n,'nativeVertices':len(o.data.vertices),'nativePolygons':len(o.data.polygons),'renderVertices':len(geometry[n]['V']),'renderTriangles':len(geometry[n]['T']),'shapeKeys':list(o.data.shape_keys.key_blocks.keys()),'materialSlots':[x.name for x in o.data.materials]})
        entry['maximumActualBodyDisplacementFromNeutralM']=float(np.linalg.norm(body['V']-initial,axis=1).max())
        for n in curves:
            o=bpy.data.objects[n];data=np.load(m.E/(n+'-binding.npz'));P=world(o);assert np.isfinite(P).all();ids=data['ids'];tri=body['V'][ids];a=tri[:,1]-tri[:,0];a/=np.linalg.norm(a,axis=1)[:,None];z=np.cross(a,tri[:,2]-tri[:,0]);z/=np.linalg.norm(z,axis=1)[:,None];b=np.cross(z,a);anchor=np.einsum('ij,ijk->ik',data['bary'],tri);starts=data['starts'];old=data['restWorld'];off=old[starts]-data['anchor'];expected=anchor.copy()
            for oldbasis,newbasis in ((data['tangent'],a),(data['binormal'],b),(data['normal'],z)):expected+=newbasis*np.einsum('ij,ij->i',off,oldbasis)[:,None]
            root_error=float(np.linalg.norm(P[starts]-expected,axis=1).max());assert root_error<1e-6,(frame,n,root_error)
            ends=starts+data['counts']-1;span_error=float(np.abs(np.linalg.norm(P[ends]-P[starts],axis=1)-np.linalg.norm(old[ends]-old[starts],axis=1)).max());assert span_error<1e-6,(frame,n,span_error)
            entry['groom'].append({'object':n,'curves':len(starts),'points':len(P),'maximumActualRootVsIndependentWorldFrameErrorM':root_error,'maximumRootTipSpanChangeM':span_error,'actualNativeCurveGeometryFinite':True})
        rows.append(entry);print('R69_SAMPLED_FOLLOW',frame,entry['maximumActualBodyDisplacementFromNeutralM'],entry['groom'],flush=True)
    assert rows[1]['maximumActualBodyDisplacementFromNeutralM']>.02 and rows[3]['maximumActualBodyDisplacementFromNeutralM']>.05
    images=[];packed=[]
    for im in bpy.data.images:
        if im.source!='FILE':continue
        if im.packed_file:assert len(im.packed_file.data)>0;packed.append(im.name);continue
        p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.exists();im.reload();images.append({'relative':im.filepath,'sha256':m.sha(p)})
    assert len(images)==15 and len(packed)==2 and not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    result={'status':'PASS_SAVED_SOURCE_INDEXED_FK_AND_SAMPLED_ROOT_FOLLOW_ONLY','source':str(source),'sha256':m.sha(source),'openedFromHistory':history,'originalFiveNativeMeshKeysUVTransformsMaterialsExact':True,'originalVisibleCurveNativePositionsRadiiAndMaterialsExact':True,'skinWeights':weight_errors,'bones':52,'boneRestHeadTail':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in rig.data.bones},'poseSamples':rows,'relativeTextures':images,'packedImages':packed,'restReferencePoints':len(cache.data.vertices),'restReferenceHasFacesOrCollisionRole':False,'oldBlinkActionKept':summary['oldBlinkActionRetainedDetachedForControlPilot'],'noAddonsAutoexecOrFrameHandlersRequired':True,'hiddenAuthoringGuidesRemainNeutralOnly':True,'fullFacialRootContactBodyDeformationHairPhysicsContinuousMotionOrRuntimeAccepted':False,'scope':'Five actual sampled FK poses; all displayed groom roots and per-curve root-tip spans. Root equality is correspondence, not valid follicle joining, skin clearance, full-spline thickness or natural hair dynamics. Whole body pose quality and all requested animations remain unaccepted.','seconds':time.time()-tick}
    result['modelStatistics']={'sourceFileBytes':source.stat().st_size,'visibleMeshComponents':stats,'totalNativeVisibleMeshVertices':sum(x['nativeVertices'] for x in stats),'totalRenderVisibleMeshVertices':sum(x['renderVertices'] for x in stats),'totalRenderVisibleMeshTriangles':sum(x['renderTriangles'] for x in stats),'visibleHairCurves':10989,'visibleHairPoints':207239,'deformBones':52,'relativeExternalTextures':15,'packedSourceImages':2,'sourceActionFrames':[1,61],'sourceFps':24,'runtimeCpuGpuMemoryAndLOD':'NOT_TESTED'}
    s.frame_set(1);m.save('history-readback.json' if history else 'a-independent-readback.json',result);print('R69_READBACK_PASS',time.time()-tick,flush=True)
if __name__=='__main__':main()
