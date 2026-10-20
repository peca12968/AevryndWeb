"""Cheap actual displayed triangle crossing falsification, never a clearance proof."""
from pathlib import Path
import bpy,numpy as np,json,time
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0074-oral-controls'
def arrays(o,bounds=None):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;p=np.empty((len(d.vertices),3),'f4');d.vertices.foreach_get('co',p.ravel());a=np.array(o.matrix_world);p=p.astype('f8')@a[:3,:3].T+a[:3,3];d.calc_loop_triangles();t=np.empty((len(d.loop_triangles),3),'i4');d.loop_triangles.foreach_get('vertices',t.ravel())
    if bounds is not None:
        tri=p[t];mask=np.all(tri.max(1)>=bounds[0],axis=1)&np.all(tri.min(1)<=bounds[1],axis=1);t=t[mask]
    ids=np.unique(t);inv=np.full(len(p),-1,'i4');inv[ids]=np.arange(len(ids));return p[ids],inv[t]
def proper_cross(a,b):
    # Strict segment/triangle interiors: robust strong witnesses only.
    for first,second in ((a,b),(b,a)):
        e1=second[1]-second[0];e2=second[2]-second[0]
        for j in range(3):
            start=first[j];direction=first[(j+1)%3]-start;cross=np.cross(direction,e2);det=np.dot(e1,cross)
            if abs(det)<1e-18:continue
            offset=start-second[0];u=np.dot(offset,cross)/det;cross2=np.cross(offset,e1);v=np.dot(direction,cross2)/det;t=np.dot(e2,cross2)/det
            if min(u,v,1-u-v)>1e-6 and 1e-6<t<1-1e-6:
                point=start+t*direction
                # Avoid classifying numerical grazing as a strong crossing.
                if min(t,1-t)*np.linalg.norm(direction)>1e-7:return point.tolist()
    return None
def main():
    tick=time.time();ref=json.loads((E/'c-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;rows=[];failed=False
    names={'upper':'AFN74_UPPER_TEETH_RIGID','lower':'AFN74_LOWER_TEETH_RIGID','skin':'AFN74_SKIN_AND_EXISTING_OCULAR_LINING','tongue':'AFN74_TONGUE_REGION'}
    for frame in (1,7,13,31,37):
        s.frame_set(frame);bpy.context.view_layer.update();data={k:arrays(bpy.data.objects[names[k]]) for k in ('upper','lower','tongue')};allteeth=np.r_[data['upper'][0],data['lower'][0]];bounds=(allteeth.min(0)-.002,allteeth.max(0)+.002);data['skin']=arrays(bpy.data.objects[names['skin']],bounds)
        trees={k:BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True,epsilon=0.) for k,(v,t) in data.items()};pairs=[]
        for a,b in (('upper','lower'),('upper','skin'),('lower','skin'),('upper','tongue'),('lower','tongue')):
            overlap=trees[a].overlap(trees[b]);witness=None
            for ia,ib in overlap:
                point=proper_cross(data[a][0][data[a][1][ia]],data[b][0][data[b][1][ib]])
                if point is not None:witness={'triangleA':int(ia),'triangleB':int(ib),'worldPointM':point,'triangleWorldA':data[a][0][data[a][1][ia]].tolist(),'triangleWorldB':data[b][0][data[b][1][ib]].tolist()};failed=True;break
            row={'pair':[a,b],'broadCandidatePairs':len(overlap),'firstStrongProperSurfaceCrossing':witness,'noWitnessIsNotClearanceProof':True};pairs.append(row);print('R74_CONTACT_SCREEN',frame,a,b,len(overlap),bool(witness),flush=True)
        rows.append({'frame':frame,'jawOpen':bpy.data.objects['AFN74_ORAL_CONTROLS']['jaw_open'],'dentalBoundsWith2mmMarginM':[x.tolist() for x in bounds],'pairs':pairs})
        if failed:break
    result={'status':'FALSIFIED_ACTUAL_ORAL_SURFACE_CROSSING' if failed else 'NO_STRONG_CROSSING_FOUND_SCOPE_STILL_UNACCEPTED','source':ref['output'],'sourceSha256':ref['outputSha256'],'rows':rows,'worldWitnessEdgeInteriorMarginM':1e-7,'method':'Actual evaluated displayed triangles; BVH candidates followed by strict noncoplanar segment-triangle interior crossing.','limitations':['A positive witness falsifies the tested surface-pair claim. No witness does not prove clearance.','Coplanar contacts, closed solid containment, true global signed minimum and continuous time are unverified.','Teeth/gum anatomical root joining, body self contact, hair and cloth are not certified.','Skin broad-phase subset conservatively overlaps the complete dental AABB plus2mm.'],'globalSignedMinimumM':None,'seconds':time.time()-tick}
    (E/'c-oral-contact-screen.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('R74_ORAL_SCREEN_DONE',result['status'],time.time()-tick,flush=True)
if __name__=='__main__':main()
