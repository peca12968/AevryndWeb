"""Reconcile the already saved model after a JSON scalar serialization error.

Never rebuild or overwrite the .blend; recover measurements from real data.
"""
from pathlib import Path
import bpy,numpy as np,time,importlib.util
s=importlib.util.spec_from_file_location('guide68recoverbuild',Path(__file__).with_name('build-female-next-r0068-guide-surface.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def main():
    tick=time.time();path=m.OUT;originalSHA=m.m.sha(path);assert path.exists() and not (m.E/'a-build-summary.json').exists();bpy.ops.wm.open_mainfile(filepath=str(path));g=bpy.data.objects['AFN68_TWO_ISLAND_GROWTH_SURFACE'];A=np.array(g.matrix_world);G0=m.array3(g.data.attributes['AFN68_OriginalGrowthPosition'].data,'vector').astype('f8');G1=m.array3(g.data.vertices,'co').astype('f8');g.data.calc_loop_triangles();GT=np.array([t.vertices[:] for t in g.data.loop_triangles],dtype='i4');p0=G0@A[:3,:3].T+A[:3,3];p1=G1@A[:3,:3].T+A[:3,3];registration=np.linalg.norm(p1-p0,axis=1)
    native=[];raw=np.load(m.E/'a-render-curve-data.npz')
    for i,name in enumerate(('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES')):
        o=bpy.data.objects[name];P=m.array3(o.data.position_data,'vector');counts=np.array([c.points_length for c in o.data.curves],dtype='i4');rr=np.empty(len(P),dtype='f4');o.data.attributes['radius'].data.foreach_get('value',rr);assert np.array_equal(P,raw[str(i)+'positions']) and np.array_equal(counts,raw[str(i)+'counts']) and np.array_equal(rr,raw[str(i)+'radii']);native.append({'object':name,'curves':len(counts),'points':len(P),'curvePointCounts':sorted(set(counts.tolist())),'localRadiusRangeM':[float(rr.min()),float(rr.max())]})
    radius=max(x['localRadiusRangeM'][1] for x in native);standOff=radius*np.linalg.norm(A[:3,:3],ord=2);sourceChanges=[]
    for name in ('AFN68_EDITABLE_MAIN_GUIDES','AFN68_EDITABLE_FLYAWAY_GUIDES'):
        o=bpy.data.objects[name]
        for md in o.modifiers:
            if md.type=='NODES' and md.node_group:
                for node in md.node_group.nodes:
                    if node.bl_idname=='GeometryNodeGroup' and node.node_tree and node.node_tree.name.startswith('Shrinkwrap Hair Curves'):
                        target=next(i.default_value for i in node.inputs if i.name=='Surface' and i.type=='OBJECT');sourceChanges.append({'object':name,'node':node.name,'surface':target.name,'offsetAndActivationLocal':node.inputs['Offset Distance'].default_value,'basis':'Actual source radius; no collision tolerance sweep.'})
    # Read original guide roots, not a reconstructed guess, for source-bind gaps.
    with bpy.data.libraries.load(str(m.m.SRC),link=False) as (src,dst):dst.objects=['long hair main','long hair strands']
    bindings=[]
    for original,name in zip(dst.objects,('AFN68_EDITABLE_MAIN_GUIDES','AFN68_EDITABLE_FLYAWAY_GUIDES')):
        o=bpy.data.objects[name];counts=np.array([c.points_length for c in o.data.curves],dtype='i4');starts=np.r_[0,np.cumsum(counts)[:-1]];P=m.array3(original.data.position_data,'vector');face=np.empty(len(counts),dtype='i4');o.data.attributes['AFN68_SourceGrowthTriangle'].data.foreach_get('value',face);weights=m.array3(o.data.attributes['AFN68_SourceGrowthBarycentric'].data,'vector');near=np.einsum('ij,ijk->ik',weights,G0[GT[face]]);gap=np.linalg.norm(P[starts]-near,axis=1);bindings.append({'object':name,'nativeGuides':len(counts),'nativePoints':len(P),'maximumOriginalRootGrowthDistanceLocal':float(gap.max()),'binding':'Stored source growth triangle/barycentric rest-frame correspondence; recovered from immutable source roots.'})
    body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']
    for md in body.modifiers:
        if md.type=='SUBSURF':md.levels=md.render_levels
    bpy.context.view_layer.update();V=m.k.mesh(body)['V'];collider=bpy.data.objects['AFN68_RENDER_BODY_CONTACT_REFERENCE'];cv=m.array3(collider.data.vertices,'co').astype('f8')@A[:3,:3].T+A[:3,3];error=float(np.linalg.norm(V-cv,axis=1).max());assert error<1e-6
    for md in body.modifiers:
        if md.type=='SUBSURF':md.levels=1
    assert m.m.sha(path)==originalSHA
    m.m.save('a-build-summary.json',{'source':str(m.SRC),'sourceSha256':m.SOURCE_SHA,'publisherSource':str(m.m.SRC),'publisherSourceSha256':m.m.SHA,'sourceCredit':bpy.context.scene['AFN68_source_credit'],'output':str(path),'outputSha256':originalSHA,'metadataRecoveredWithoutRecreatingOrResavingModel':True,'recoveryReason':'Model/curve data were saved before JSON could serialize a numpyfloat32 scalar. Read saved model and original source; never overwrite the model.','anatomicalAlignmentMatrix':A.tolist(),'alignmentBasis':'Eye separation/centre and head top; single fit.','growthVertices':len(G0),'growthTriangles':len(GT),'maximumGrowthRegistrationWorldM':float(registration.max()),'growthRegistrationMethod':'First exits from verified head-interior origin onto actual render tissue, preserving topology/UV/islands/parting.','growthVertexStandOffWorldM':float(standOff),'guideBindings':bindings,'sourceNodeChanges':sourceChanges,'visibleComponents':native,'bodyRenderCollisionReferenceMaximumReconstructionErrorM':error,'bodySkinEyesStageUnchanged':True,'sourceSurfaceDeformModifiersDisabledAfterExplicitBind':True,'newHairDynamicsOrEngineAcceptance':False,'sourceRights':'CC BY-SA notice retained as source declares; exact version not specified. Body has separate CC0 provenance. No engine code licensing change.','recoverySecondsBeforePreview':time.time()-tick});m.m.save('a-preview-control.json',m.preview());print('R68_SAVED_STUDY_RECOVERED',originalSHA,native,time.time()-tick,flush=True)
if __name__=='__main__':main()
