"""Read saved complete C, source-bound growth data and unchanged anatomy.

This is data/neutral geometry verification, never a full hair-contact pass.
"""
from pathlib import Path
import bpy,numpy as np,time,sys,importlib.util
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('guide68verifybuild','build-female-next-r0068-guide-surface.py');v=module('guide68verifynative','verify-female-next-r0061-complete-groom.py');k=m.k
def components(d):
    parent=list(range(len(d.vertices)))
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    for poly in d.polygons:
        vs=list(poly.vertices)
        for x in vs[1:]:parent[find(x)]=find(vs[0])
    return len({find(i) for i in range(len(parent))})
def main():
    tick=time.time();ref=m.read(m.E/'c-build-summary.json');path=Path(ref['output']);history='--history' in sys.argv
    if history:path=m.R/'sites-engine-journey/assets-source/aevrynd-character/female-next'/path.name
    assert m.m.sha(path)==ref['outputSha256'] and m.m.sha(m.SRC)==m.SOURCE_SHA;names=list(m.read(m.E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values());bpy.ops.wm.open_mainfile(filepath=str(m.SRC));bpy.context.scene.frame_set(1)
    native={n:v.mesh_signature(bpy.data.objects[n]) for n in names};mats={mat.name:k.f.v.v32.material_signature(mat) for mat in bpy.data.materials if mat.use_nodes};curves={o.name:k.v59.native_curves(o) for o in bpy.data.objects if o.type=='CURVES'};visibility={o.name:[o.type,o.hide_render,o.hide_get()] for o in bpy.context.scene.objects if o.type in ('MESH','CURVES')};stage=k.f.v.stage()
    bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);assert native=={n:v.mesh_signature(bpy.data.objects[n]) for n in names};assert mats=={n:k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats};assert curves=={n:k.v59.native_curves(bpy.data.objects[n]) for n in curves}
    for name,vis in visibility.items():
        o=bpy.data.objects[name];expect=[vis[0],True,True] if name=='AFN57_CANONICAL_BOB_GUIDES' else vis;assert [o.type,o.hide_render,o.hide_get()]==expect
    assert k.f.v.stage()==stage and not bpy.data.objects.get('AFN68_RENDER_BODY_CONTACT_REFERENCE');raw=np.load(m.E/'c-render-curve-data.npz');actual=[]
    for i,r in enumerate(ref['visibleComponents']):
        o=bpy.data.objects[r['object']];d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=m.array3(d.position_data,'vector');counts=np.array([c.points_length for c in d.curves],dtype='i4');rr=np.empty(len(P),dtype='f4');d.attributes['radius'].data.foreach_get('value',rr);assert np.array_equal(P,raw[str(i)+'positions']) and np.array_equal(counts,raw[str(i)+'counts']) and np.array_equal(rr,raw[str(i)+'radii']) and np.array_equal(np.array(o.matrix_world),raw['matrix']);assert np.isfinite(P).all() and np.isfinite(rr).all() and (rr>=0).all() and not o.hide_render and len(o.modifiers)==0;actual.append({'object':o.name,'curves':len(counts),'points':len(P),'actualGeometryRadiiAndMatrixExact':True})
    body=bpy.data.objects[names[4]];assert all(md.levels==md.render_levels for md in body.modifiers if md.type=='SUBSURF');v.raise_subdivision();G={};bodyRow=None
    for name in names:
        row=k.mesh(bpy.data.objects[name]);G[name]={field:v.digest(row[field]) for field in ('V','T','mi','nativeTriangleFace')}
        if name==names[4]:bodyRow=row
    prior=m.read(m.E.parent/'r0065-eye-shading/a-functional-contact-transfer.json');assert prior['sha256']==m.SOURCE_SHA and G==prior['allSevenActualRenderGeometryHashesExact']['neutral']
    growth=bpy.data.objects['AFN68_TWO_ISLAND_GROWTH_SURFACE'];d=growth.data;islands=components(d);assert islands==2 and 'parting' in growth.vertex_groups and len(d.uv_layers)>0;ids=np.empty(len(d.vertices),dtype='i4');d.attributes['AFN68_RestBodyTriangle'].data.foreach_get('value',ids);weights=m.array3(d.attributes['AFN68_RestBodyBarycentric'].data,'vector').astype('f8');assert np.max(np.abs(weights.sum(1)-1))<1e-6;tri=bodyRow['V'][bodyRow['T'][ids]];anchor=np.einsum('ij,ijk->ik',weights,tri);normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None];A=np.array(growth.matrix_world);world=m.array3(d.vertices,'co').astype('f8')@A[:3,:3].T+A[:3,3];offset=m.read(m.E/'a-build-summary.json')['growthVertexStandOffWorldM'];error=float(np.linalg.norm(world-(anchor+normal*offset),axis=1).max());assert error<1e-6
    images=[];packed=[]
    for im in bpy.data.images:
        if im.source=='FILE':
            if im.packed_file:
                import hashlib
                payload=bytes(im.packed_file.data);assert len(payload)>0 and im.size[0]>0 and im.size[1]>0;packed.append({'name':im.name,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'resolution':list(im.size),'portablePackedData':True});continue
            p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.exists();im.reload();images.append({'relative':im.filepath,'sha256':m.m.sha(p),'colorSpace':im.colorspace_settings.name})
    assert len(images)==15 and not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    result={'status':'PASS_COMPLETE_STUDY_DATA_SCOPE_PHYSICS_UNACCEPTED','source':str(path),'sha256':m.m.sha(path),'openedFromHistory':history,'baselineSourceSha256':m.SOURCE_SHA,'allOriginalFiveMeshesKeysUVMatricesMaterialsExact':True,'originalCurvesExactOnlySparseBobHidden':True,'originalSkinEyeGainLightingExposureExact':True,'actualNeutralRenderGeometryExact':G,'visibleNativeCurves':actual,'growthMeshIslands':islands,'partingAndUVDataPresent':True,'growthVertexActualRestBodyCorrespondenceMaximumErrorM':error,'growthBindingIsRestPoseOnlyNotDeformingFollicleModel':True,'liveBodyContactDependencyAndRenderLevelViewport':True,'duplicateStaticBodyReferenceRemoved':True,'relativeTextures':images,'fullRootJoinCurvedTubeSelfContinuousDynamicsOrEngineAccepted':False,'sourceNotice':bpy.context.scene['AFN68_source_credit'],'seconds':time.time()-tick}
    result['packedSourceImages']=packed
    # Ground the next broader dependency choice in actual original CC0 data.
    char=m.R/'Reference/character/charmorph-vitruvian-cc0/char.blend'
    with bpy.data.libraries.load(str(char),link=False) as (src,dst):dst.objects=src.objects
    result['nextBodyRigDataInventory']={'source':str(char),'sha256':m.m.sha(char),'rawNotLinkedOrExecuted':True,'armatures':[{'name':o.name,'bones':len(o.data.bones)} for o in dst.objects if o.type=='ARMATURE'],'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'vertexGroups':len(o.vertex_groups),'mode':o.mode,'armatureTargets':[md.object.name if md.object else None for md in o.modifiers if md.type=='ARMATURE']} for o in dst.objects if o.type=='MESH'],'doesNotProveRigCanOperate':True}
    m.m.save('history-readback.json' if history else 'c-native-readback.json',result);print('R68_COMPLETE_STUDY_READBACK',actual,error,result['nextBodyRigDataInventory'],time.time()-tick,flush=True)
if __name__=='__main__':main()
