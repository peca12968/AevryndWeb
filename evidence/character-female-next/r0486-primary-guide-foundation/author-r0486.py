"""New scalp-region primary-guide foundation; no inherited free lengths."""
from pathlib import Path
from hashlib import file_digest,sha256
import bpy,numpy as np,json
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent
P=R.parent/'r0485-native-root-to-tip'
DEST=R/'female-next-r0486-primary-guides-UNACCEPTED.blend'
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def unit(x):return x/max(np.linalg.norm(x),1e-10)
def main():
    source=P/'female-next-r0485-native-groom-portable-UNACCEPTED.blend'
    assert sha(source)=='13ae0a9c5a01dd401913ba3c93005dc17e692617a4443ea9a2b5cde6568dd023' and not DEST.exists()
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    control=bpy.data.objects['R485 complete hair | B'];d=control.data
    base=np.empty((24831,80,3),dtype='f4');d.position_data.foreach_get('vector',base.ravel());roots=base[:,0]
    ids=np.empty(24831,dtype='i4');d.attributes['AFN409_CURVE_ID'].data.foreach_get('value',ids)
    rad=np.empty((24831,80),dtype='f4');d.attributes['radius'].data.foreach_get('value',rad.ravel())
    body=bpy.data.objects['R482 archived complete neutral skin'];mesh=body.data
    vertices=np.empty((len(mesh.vertices),3),dtype='f4');mesh.vertices.foreach_get('co',vertices.ravel())
    faces=np.array([p.vertices[:] for p in mesh.polygons],dtype='i4')
    bvh=BVHTree.FromPolygons(vertices.tolist(),faces.tolist(),all_triangles=True)
    # Six explicit ownership domains: left/right x frontal, crown, occipital.
    side=(roots[:,0]>=.004).astype('i4');zone=np.where(roots[:,1]<-.055,0,np.where(roots[:,1]>.015,2,1))
    region=side*3+zone;selected=[];region_rows={}
    for reg in range(6):
        members=np.flatnonzero(region==reg);v=roots[members]
        chosen=[int(np.argmin(np.linalg.norm(v-v.mean(0),axis=1)))];dist=np.full(len(v),np.inf)
        for k in range(20):
            dist=np.minimum(dist,((v-v[chosen[-1]])**2).sum(1))
            nxt=int(dist.argmax())
            if nxt in chosen:break
            chosen.append(nxt)
        indexes=members[chosen];region_rows[str(reg)]=indexes.tolist();selected.extend(indexes.tolist())
    selected=np.asarray(selected,dtype='i4');guides=[];guide_notes=[]
    for index in selected:
        root=roots[index].astype('f8');s=1. if root[0]>=.004 else -1.
        # Parted crown follows the actual neutral scalp before a free gravity fall.
        pos=root.copy();path=[root.copy()];depart=False;velocity=None
        total=.185+.045*np.clip((root[2]-1.49)/.08,0,1)
        back=float(np.clip((root[1]-.005)/.045,0,1))
        for step in range(1,151):
            if not depart:
                hit,normal,face,distance=bvh.find_nearest(Vector(pos))
                n=np.array(normal);surface=np.array(hit)
                direction=np.array([s*(.62*(1-back)+.12),.18+.22*back,-1.])
                tangent=unit(direction-n*np.dot(direction,n))
                if pos[2]<1.495 or (abs(pos[0])>.071 and n[2]<.25) or (pos[1]>.052 and n[2]<.35):
                    depart=True;velocity=tangent
                else:
                    proposal=surface+tangent*(total/150)
                    h,nn,_,_=bvh.find_nearest(Vector(proposal))
                    pos=np.array(h)+np.array(nn)*.0045
            if depart:
                velocity=unit(.91*velocity+.09*np.array([s*.03,.04,-1.]))
                pos=pos+velocity*(total/150)
            path.append(pos.copy())
        path=np.asarray(path);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
        q=np.stack([np.interp(np.linspace(0,arc[-1],80),arc,path[:,k]) for k in range(3)],axis=1)
        q[0]=root;guides.append(q);guide_notes.append(dict(sourceCurveID=int(ids[index]),region=int(region[index]),length=float(arc[-1]),departed=depart))
    guides=np.asarray(guides,dtype='f4');groot=guides[:,0];gregion=region[selected]
    # Four guide displacement fields blend only inside the same scalp domain.
    q=np.empty_like(base);owner=np.empty((len(roots),4),dtype='i4');weights=np.empty((len(roots),4),dtype='f4')
    for reg in range(6):
        members=np.flatnonzero(region==reg);bank=np.flatnonzero(gregion==reg)
        distance=((roots[members,None]-groot[bank][None])**2).sum(2)
        near=np.argsort(distance,axis=1)[:,:4];chosen=bank[near]
        w=1/np.maximum(np.take_along_axis(distance,near,axis=1),1e-9)**1.5;w/=w.sum(1,keepdims=True)
        movement=guides[chosen]-groot[chosen][:,:,None,:]
        q[members]=roots[members,None]+np.sum(movement*w[:,:,None,None],axis=1)
        owner[members]=chosen;weights[members]=w
    q[:,0]=roots;assert np.isfinite(q).all() and np.array_equal(q[:,0],roots)
    candidate=control.copy();candidate.data=d.copy();candidate.name='R486 complete hair | primary guide foundation';candidate.data.name='R486 guide-interpolated full strands'
    bpy.context.scene.collection.objects.link(candidate);candidate.data.position_data.foreach_set('vector',q.ravel())
    for name,typ,values in [('AEVRYND_SCALP_REGION','INT',region),('AEVRYND_PRIMARY_GUIDE','INT',owner[:,0])]:
        a=candidate.data.attributes.new(name,typ,'CURVE');a.data.foreach_set('value',values)
    for o in bpy.data.objects:
        if o.type=='CURVES' and o!=candidate:o.hide_render=True;o.hide_set(True)
    candidate.hide_render=False;candidate.hide_set(False);candidate.data.update_tag();candidate.update_tag()
    # Primary guides remain separately editable native curves with persistent IDs.
    gd=bpy.data.hair_curves.new('R486 Primary guide topology');gd.add_curves([80]*len(guides));gd.position_data.foreach_set('vector',guides.ravel())
    radius=gd.attributes.get('radius') or gd.attributes.new('radius','FLOAT','POINT')
    radius.data.foreach_set('value',np.full(guides.shape[:2],.00015,dtype='f4').ravel())
    for name,values in [('AEVRYND_PRIMARY_GUIDE_ID',np.arange(len(guides),dtype='i4')),('AEVRYND_SOURCE_CURVE_ID',ids[selected]),('AEVRYND_SCALP_REGION',gregion)]:
        a=gd.attributes.new(name,'INT','CURVE');a.data.foreach_set('value',values)
    go=bpy.data.objects.new('R486 Editable primary guides | NOT render fibres',gd);bpy.context.scene.collection.objects.link(go);go.hide_render=True;go.hide_set(True)
    for m in d.materials:gd.materials.append(m)
    np.savez_compressed(R/'primary-guide-construction.npz',guides=guides,sourceCurveIndex=selected,sourceCurveIDs=ids[selected],region=region,ownerGuide=owner,ownerWeight=weights,position=q)
    shot=json.loads((R.parent/'r0470-independent-posterior-locks/shot-A-face.json').read_text(encoding='utf-8-sig'))['shot']
    scene=bpy.context.scene;scene.camera.matrix_world=Matrix(shot['camera']);scene.camera.data.type=shot['cameraType'];scene.camera.data.lens=shot['lens'];scene.render.threads_mode='FIXED';scene.render.threads=4
    bpy.ops.object.select_all(action='DESELECT');candidate.select_set(True);bpy.context.view_layer.objects.active=candidate
    note=bpy.data.texts.new('Aevrynd_R486_Primary_Guide_Foundation');note.write('Independent unaccepted construction. Six scalp domains, 126 or fewer actual-root primary guides, scalp-tangent travel then gravity fall. All child roots, IDs, binding and radii retained. No inherited failed free lengths. Owner interpolation is stored in the sidecar NPZ. No finite collision, dynamics or engine acceptance is implied. Retain inherited reference attribution; no exclusive ownership claim.\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    record=dict(source=dict(path=str(DEST),sha256=sha(DEST),bytes=DEST.stat().st_size),parent=dict(path=str(source),sha256=sha(source)),candidateObject=candidate.name,controlObject=control.name,primaryGuideObject=go.name,guideCount=len(guides),domains=region_rows,guideNotes=guide_notes,rootsBitIdentical=True,positionHash=sha256(q.tobytes()).hexdigest(),rootHash=sha256(roots.copy().tobytes()).hexdigest(),radiusQuantiles=np.quantile(rad,[0,.5,.95,1]).tolist(),collision='NOT_VERIFIED',motion='NOT_VERIFIED',appearance='PENDING_COMPLETE_REVIEW')
    (R/'construction-receipt.json').write_text(json.dumps(record,indent=2),encoding='utf8');print('R486_SOURCE',record['source'],len(guides),flush=True)
if __name__=='__main__':main()
