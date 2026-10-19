"""Reopen isolated foundation; verify preserved sculpt and actual neutral contacts."""
import bpy, importlib.util, json, time, hashlib
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
spec=importlib.util.spec_from_file_location('foundation28',Path(__file__).with_name('build-female-next-r0028-cc0-foundation.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def geomstats(v,t):
    edge=np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]),axis=1);_,counts=np.unique(edge,axis=0,return_counts=True);areas=np.linalg.norm(np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]),axis=1)*.5
    return {'vertices':len(v),'triangles':len(t),'nonFiniteCoordinates':int((~np.isfinite(v)).sum()),'boundaryEdges':int((counts==1).sum()),'nonManifoldEdges':int((counts>2).sum()),'minimumTriangleAreaM2':float(areas.min()),'trianglesBelow1e-14M2':int((areas<1e-14).sum()),'evaluatedWorldGeometrySha256':hashlib.sha256(v.tobytes()+t.tobytes()).hexdigest()}
def main():
    report=b.read('build-verification.json');assert b.sha(b.OUT)==report['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(b.OUT));s=bpy.context.scene;rows={};arrays={};start=time.time()
    assert len(bpy.data.objects)==7 and len([o for o in s.objects if o.type=='MESH'])==3
    assert not bpy.data.libraries and not bpy.data.texts and not bpy.data.armatures and not bpy.data.actions and not bpy.data.images
    for name,original in report['originalObjects'].items():
        o=bpy.data.objects[name];assert b.mesh_signature(o.data)==original['mesh'];assert o.get('AFN28_license')=='CC0';assert o.get('AFN28_author')=='Dan Ulrich';assert o.animation_data is None or not o.animation_data.drivers
        v,t=b.evaluated(o,True);arrays[name]=(v,t);rows[name]={'baseSignatureMatchesOriginal':True,'base':b.mesh_signature(o.data),'evaluated':geomstats(v,t),'parent':o.parent.name if o.parent else None,'modifiers':[{'type':m.type,'levels':getattr(m,'levels',None),'renderLevels':getattr(m,'render_levels',None),'totalLevels':getattr(m,'total_levels',None),'externalMultires':getattr(m,'is_external',None),'externalFilename':getattr(m,'filepath',None)} for m in o.modifiers]}
        assert rows[name]['evaluated']['nonFiniteCoordinates']==0
        # Quantitatively compare the reopened evaluated surface with a fresh
        # selected asset append below, including authored Multires displacement.
        print('R28_STRUCTURE',name,json.dumps(rows[name]['evaluated']),flush=True)
    v,t=arrays[b.BODY];tree=BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True,epsilon=0.0);eyes={}
    for name,(p,pt) in arrays.items():
        if name==b.BODY:continue
        eye=BVHTree.FromPolygons(p.tolist(),pt.tolist(),all_triangles=True,epsilon=0.0);pairs=tree.overlap(eye)
        nearest=np.array([tree.find_nearest(Vector(x))[3] for x in p])
        indices=np.unique([a for a,c in pairs]);locations=v[t[indices]].reshape(-1,3)
        eyes[name]={'bodyEyeTrianglePairs':len(pairs),'uniqueBodyTriangles':len(indices),'crossingBodyTriangleVertexBoundsM':{'min':locations.min(0).tolist(),'max':locations.max(0).tolist()} if len(locations) else None,'vertexSampleUnsignedMinimumGapM':float(nearest.min()),'trianglePairExamples':[[int(a),int(c)] for a,c in pairs[:16]],'definition':'Complete evaluated body/eye triangle surface intersection; distance is eye-vertex sampling, not full all-surface minimum. No containment exclusion or animation.'}
    names=[n for n in arrays if n!=b.BODY];p,pt=arrays[names[0]];q,qt=arrays[names[1]];eye_pair=len(BVHTree.FromPolygons(p.tolist(),pt.tolist(),all_triangles=True).overlap(BVHTree.FromPolygons(q.tolist(),qt.tolist(),all_triangles=True)))
    # Fresh append and evaluate proves saved Multires sculpt details, not only
    # the coarse base mesh and modifier level metadata, survived independently.
    with bpy.data.libraries.load(str(b.REF),link=False) as (a,c):c.collections=[b.COLLECTION]
    col=c.collections[0];s.collection.children.link(col);common=np.array(report['sharedNormalizationMatrix'],dtype='f8').reshape(4,4);preserved={}
    fresh_objects=list(col.all_objects)
    b.save('fresh-append-inspection.json',{'collection':col.name,'objects':[(o.name,o.type) for o in fresh_objects]})
    for o in fresh_objects:
        key=o.name.split('.001')[0] if o.name.endswith('.001') else o.name
        # Blender can choose a different numeric suffix; original mesh hash
        # identifies the three data objects without relying on suffixes.
        signature=b.mesh_signature(o.data);matches=[n for n,r in report['originalObjects'].items() if r['mesh']==signature];assert len(matches)==1;key=matches[0]
        for m in o.modifiers:m.levels=m.render_levels=3
        o.hide_viewport=False;o.hide_set(False)
        bpy.context.view_layer.update();v0,t0=b.evaluated(o,True);expected=v0@common[:3,:3].T+common[:3,3];actual,ta=arrays[key];assert np.array_equal(t0,ta)
        error=float(np.linalg.norm(actual-expected,axis=1).max());assert error<.0000003
        preserved[key]={'freshReferenceEvaluatedVertices':len(v0),'topologyExact':True,'maximumWorldPositionErrorM':error,'toleranceM':.0000003,'comparison':'Saved independent source vs fresh official selected CC0 collection under the same shared float32 transform. All evaluated vertices, not samples.'}
    out={'source':str(b.OUT),'sourceSha256':b.sha(b.OUT),'savedFileOpened':True,'allBaseMeshUVSignaturesMatch':True,'sculptPreservation':preserved,'structure':rows,'neutralContacts':eyes,'eyeEyeTrianglePairs':eye_pair,'externalLibrariesInSavedSource':0,'textProgramsInSavedSource':0,'rigs':0,'morphs':0,'seconds':time.time()-start,'contactStatus':'NEUTRAL_SURFACE_INTERSECTION_FAIL' if any(e['bodyEyeTrianglePairs'] for e in eyes.values()) else 'NO_NEUTRAL_BODY_EYE_TRIANGLE_CROSSINGS_ONLY','limits':['No body self-intersection sweep performed.','No containment, continuous motion, expression, hair, cloth or engine test.','Unrigged scan source, not full character acceptance.','Separate cornea/iris/pupil and wetline not authored on this foundation.']};b.save('saved-foundation-verification.json',out);print('R0028_VERIFY_DONE',json.dumps({'contactStatus':out['contactStatus'],'eyes':{n:r['bodyEyeTrianglePairs'] for n,r in eyes.items()},'preserved':preserved}),flush=True)
if __name__=='__main__':main()
