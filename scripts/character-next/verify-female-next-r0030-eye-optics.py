"""Saved layered-optics contact, actual limbus join and exterior-union proof."""
import bpy,importlib.util,json,time,gc
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('build30',Path(__file__).with_name('build-female-next-r0030-eye-optics.py'));a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
spec=importlib.util.spec_from_file_location('verify29',Path(__file__).with_name('verify-female-next-r0029-native-eye-interface.py'));v29=importlib.util.module_from_spec(spec);spec.loader.exec_module(v29)
b=a.b;E=a.E
def tree(v,t):return BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True,epsilon=0.0)
def edges(t):
    e=np.sort(np.concatenate((t[:,[0,1]],t[:,[1,2]],t[:,[2,0]])),axis=1);u,c=np.unique(e,axis=0,return_counts=True);return u,c
def boundary(v,t):
    u,c=edges(t);return {tuple(sorted((tuple(v[i]),tuple(v[j])))) for i,j in u[c==1]}
def component_count(n,ed):
    parent=list(range(n))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,j in ed:parent[find(int(i))]=find(int(j))
    return len({find(i) for i in range(n)})
def winding_classification(V,T,point):
    total=0.
    for start in range(0,len(T),65536):
        tri=V[T[start:start+65536]]-point;a,b,c=tri[:,0],tri[:,1],tri[:,2];na=np.linalg.norm(a,axis=1);nb=np.linalg.norm(b,axis=1);nc=np.linalg.norm(c,axis=1);num=np.einsum('ij,ij->i',a,np.cross(b,c));den=na*nb*nc+np.einsum('ij,ij->i',a,b)*nc+np.einsum('ij,ij->i',b,c)*na+np.einsum('ij,ij->i',c,a)*nb;total+=float(np.sum(2*np.arctan2(num,den)))
    w=total/(4*np.pi);return {'classification':'outside' if abs(w)<1e-6 else ('inside' if abs(abs(w)-1)<1e-6 else 'unresolved'),'signedWinding':w,'method':'Complete body triangle solid-angle winding in float64,65536-triangle chunks. Used when five rays disagree; no majority vote or exclusion.'}
def main():
    start=time.time();report=a.read('build-verification.json');assert b.sha(a.OUT)==report['outputSha256'];assert b.sha(a.SRC)==report['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=str(a.OUT));body=bpy.data.objects[b.BODY];assert a.q.signature(body)==report['bodyOriginalSignature'];assert not bpy.data.libraries and not bpy.data.texts
    # Hidden original references do not have evaluated world transforms after
    # load. Temporarily enable viewport evaluation only (never rendering or
    # saving), then compare them with the pinned source signatures.
    bpy.data.collections['AFN30_HIDDEN_ORIGINAL_GLOBES'].hide_viewport=False
    for g in report['geometry'].values():bpy.data.objects[g['originalObject']].hide_set(False)
    bpy.context.view_layer.update()
    V,T=b.evaluated(body,True);bt=tree(V,T);parts={};structure={};body_contact={}
    for side,g in report['geometry'].items():
        for component,name in g['parts'].items():
            o=bpy.data.objects[name];p,pt=b.evaluated(o,True);ot=tree(p,pt);parts[name]=(p,pt,ot);ed,count=edges(pt);area=np.linalg.norm(np.cross(p[pt[:,1]]-p[pt[:,0]],p[pt[:,2]]-p[pt[:,0]]),axis=1)*.5;selfpairs=[(int(i),int(j)) for i,j in ot.overlap(ot) if i<j and set(pt[i]).isdisjoint(pt[j])];cross=bt.overlap(ot);sample=float(min(bt.find_nearest(Vector(x.tolist()))[3] for x in p));anchor=v29.parity(bt,p[0])
            if anchor['classification']=='unresolved':
                fallback=winding_classification(V,T,p[0]);anchor={'classification':fallback['classification'],'fiveRayResult':anchor,'windingFallback':fallback}
            structure[name]={'vertices':len(p),'triangles':len(pt),'connectedComponents':component_count(len(p),ed),'boundaryEdges':int((count==1).sum()),'nonManifoldEdges':int((count>2).sum()),'nonFiniteCoordinates':int((~np.isfinite(p)).sum()),'minimumTriangleAreaM2':float(area.min()),'nonAdjacentSelfPairs':len(selfpairs),'selfExamples':selfpairs[:8],'openSurfaceMeaning':'Cornea/sclera share the proven source limbus. Pupil is an explicit recessed interior backing surface, not an anatomical tissue solid.' if component!='Iris' else 'Closed iris annulus with front/back/inner/outer thickness surfaces.'};body_contact[name]={'bodyTrianglePairs':len(cross),'pairExamples':[[int(i),int(j)] for i,j in cross[:8]],'anchorBodyContainment':anchor,'vertexSampleUnsignedMinimumGapM':sample,'gapDefinition':'All optical vertices sampled against the actual full body triangles; not an exact complete-surface signed minimum.'}
    del bt;gc.collect();pair_rows=[];seams={};outer={}
    for side,g in report['geometry'].items():
        sclera=g['parts']['Sclera'];cornea=g['parts']['Cornea'];sv,st,_=parts[sclera];cv,ct,_=parts[cornea];sb=boundary(sv,st);cb=boundary(cv,ct);s_y=sv[:,1];c_y=cv[:,1];plane=float(np.median(cv[list({i for edge in edges(ct)[0][edges(ct)[1]==1] for i in edge}),1]));assert sb==cb and len(sb)>0
        # Their complete geometry occupies opposite closed halfspaces and the
        # same edge loop. Therefore contact can only be the actual source seam,
        # not overlapping tissue volume. Raw pairs are retained below.
        separation={'sharedBoundaryEdges':len(sb),'boundaryEdgesExact':True,'planeYM':plane,'scleraMinimumYMinusPlaneM':float(s_y.min()-plane),'corneaMaximumYMinusPlaneM':float(c_y.max()-plane)};assert separation['scleraMinimumYMinusPlaneM']>=-1e-10 and separation['corneaMaximumYMinusPlaneM']<=1e-10;seams[side]=separation
        original=bpy.data.objects[g['originalObject']];actual=a.q.signature(original)
        a.save('original-reference-inspection-'+side+'.json',{'expected':g['originalSignature'],'actual':actual,'basis':b.matrix(original.matrix_basis),'parentInverse':b.matrix(original.matrix_parent_inverse),'parentWorld':b.matrix(original.parent.matrix_world)})
        assert actual==g['originalSignature'];ev,et=b.evaluated(original,True);orig=tree(ev,et);samples=np.concatenate((sv,cv,sv[st].mean(1),cv[ct].mean(1)));maximum=max(orig.find_nearest(Vector(x.tolist()))[3] for x in samples);original_area=float((np.linalg.norm(np.cross(ev[et[:,1]]-ev[et[:,0]],ev[et[:,2]]-ev[et[:,0]]),axis=1)*.5).sum());split_area=float(sum((np.linalg.norm(np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]]),axis=1)*.5).sum() for p,t in ((sv,st),(cv,ct))));assert maximum<5e-7 and abs(original_area-split_area)<1e-9
        outer[side]={'originalReferenceHidden':original.hide_render,'originalRawSignatureExact':True,'maximumSplitVertexAndTriangleCentroidSourceSurfaceResidualM':float(maximum),'originalSurfaceAreaM2':original_area,'partitionSurfaceAreaM2':split_area,'absoluteAreaDifferenceM2':abs(original_area-split_area),'method':'Every new exterior vertex/triangle centroid sampled on original surface plus exact opposite-halfspace split, matching shared edge loop and total surface area. No exterior radius/position fit or eye shrink.'}
    names=sorted(parts)
    for i,n in enumerate(names):
        for m in names[i+1:]:
            cross=parts[n][2].overlap(parts[m][2]);legal=any({n,m}=={g['parts']['Sclera'],g['parts']['Cornea']} for g in report['geometry'].values());pair_rows.append({'pair':[n,m],'rawTriangleContactPairs':len(cross),'structurallyProvenLimbusContact':legal,'nonJoinTrianglePairs':0 if legal else len(cross),'classification':'Only the exact shared source limbus plane/edge loop can meet; complete halfspace proof above.' if legal else 'No exclusion.'})
    clean=all(v['bodyTrianglePairs']==0 and v['anchorBodyContainment']['classification']=='outside' for v in body_contact.values()) and all(v['connectedComponents']==1 and v['nonAdjacentSelfPairs']==v['nonManifoldEdges']==v['nonFiniteCoordinates']==0 for v in structure.values()) and all(v['nonJoinTrianglePairs']==0 for v in pair_rows)
    result={'source':str(a.OUT),'sourceSha256':b.sha(a.OUT),'savedFileOpened':True,'bodyGeometryUVTransformExact':True,'structure':structure,'bodyContacts':body_contact,'opticalPairs':pair_rows,'sourceLimbusJoinProof':seams,'exteriorPartition':outer,'images':[{'name':im.name,'packed':bool(im.packed_file),'colorSpace':im.colorspace_settings.name} for im in bpy.data.images],'status':'PASS_NEUTRAL_OPTICAL_SURFACES_AND_PROVEN_LIMBUS_JOIN' if clean else 'FAIL_OPTICAL_CONTACT_OR_STRUCTURE','seconds':time.time()-start,'limits':['Neutral static only; gaze/blink/continuous motion not tested.','Source cornea contour and single-interface EEVEE refraction are approximate, not calibrated ocular optics.','Wetline/lacrimal tissue and full skin/hair/rig/oral/clothes/runtime still missing.','Pupil backing is a dark interior proxy behind a real iris aperture, not a retinal/lens simulation.','No body self-contact expansion; body geometry is exactly r29 and its existing scoped static evidence remains applicable.','Sampled unsigned gaps/residuals are not exact full-surface signed minima.']};a.save('saved-optical-verification.json',result);print('R0030_VERIFY_DONE',json.dumps({'status':result['status'],'bodyPairs':{n:c['bodyTrianglePairs'] for n,c in body_contact.items()},'nonJoinPairs':sum(v['nonJoinTrianglePairs'] for v in pair_rows),'structureSelf':{n:v['nonAdjacentSelfPairs'] for n,v in structure.items()},'seams':seams,'seconds':result['seconds']}),flush=True)
if __name__=='__main__':main()
