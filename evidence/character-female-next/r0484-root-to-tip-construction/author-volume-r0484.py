"""Build volumetric lock cross sections, preserving every actual follicle."""
from pathlib import Path
from runpy import run_path
from hashlib import file_digest,sha256
import json
import numpy as np
import bpy
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'female-next-r0484-volume-locks-UNACCEPTED.blend'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1.e-12)
def smooth(x):
    x=np.clip(x,0.,1.);return x*x*(3.-2.*x)

def main():
    proof=read(ROOT/'authored-source-receipt.json');assert sha(Path(proof['source']['path']))==proof['source']['sha256']
    assert not DEST.exists()
    bpy.ops.wm.open_mainfile(filepath=proof['source']['path'],load_ui=False,use_scripts=False)
    control=bpy.data.objects['R484 complete hair | control'];data=control.data
    base=np.empty((24831,80,3),dtype='f4');data.position_data.foreach_get('vector',base.ravel())
    source=np.load(ROOT/'original-strip-guides.npz',allow_pickle=False)
    mapped=np.load(ROOT/'spatial-lock-A.npz',allow_pickle=False)
    source_ids=source['component'];columns=source['column'];guides=source['position']
    components=mapped['sourceComponent'];start=mapped['guideEntryIndex'];phase=np.linspace(0.,1.,80,dtype='f4')[None,:]
    q=np.empty_like(base);populations=[]
    for component in np.unique(components):
        members=np.flatnonzero(components==component);populations.append(len(members))
        ids=[np.flatnonzero((source_ids==component)&(columns==column))[0] for column in (0,1,2)]
        lines=[]
        for line in guides[ids]:
            arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(line,axis=0),axis=1))]
            lines.append(np.stack([np.interp(np.linspace(0.,arc[-1],80),arc,line[:,k]) for k in range(3)],axis=1))
        lines=np.asarray(lines,dtype='f4')
        s=start[members,None]+(79-start[members,None])*phase
        lo=np.minimum(s.astype('i4'),78);f=(s-lo)[:,:,None]
        left=lines[0,lo]*(1.-f)+lines[0,lo+1]*f
        middle=lines[1,lo]*(1.-f)+lines[1,lo+1]*f
        right=lines[2,lo]*(1.-f)+lines[2,lo+1]*f
        tangent=unit(np.gradient(middle,axis=1));across=right-left
        u=unit(across-tangent*(across*tangent).sum(2)[:,:,None]);v=unit(np.cross(tangent,u))
        radius=np.linalg.norm(across,axis=2)*(.5/.7)
        roots=base[members,0];center=roots.mean(0);scatter=roots-center
        if len(members)==1:
            xy=np.zeros((1,2),dtype='f4')
        else:
            _,_,axes=np.linalg.svd(scatter,full_matrices=False)
            xy=scatter@axes[:2].T;xy/=np.maximum(xy.std(0),.00005)
        polar=np.linalg.norm(xy,axis=1);rank=np.empty(len(members),dtype='i4');rank[np.argsort(polar,kind='stable')]=np.arange(len(members))
        r=np.sqrt((rank+.5)/len(members)) if len(members)>1 else np.zeros(1)
        angle=np.arctan2(xy[:,1],xy[:,0])
        taper=1.-.75*smooth((phase-.68)/.32)
        offset=u*(np.cos(angle)*r)[:,None,None]*radius[:,:,None]*taper[:,:,None]
        offset+=v*(np.sin(angle)*r)[:,None,None]*radius[:,:,None]*.7*taper[:,:,None]
        line=middle+offset
        delta=roots-line[:,0]
        line+=delta[:,None,:]*(1.-smooth(phase/.30))[:,:,None]
        q[members]=line
    fixture=bpy.data.objects['R482 archived complete neutral skin'].data
    skin=np.empty((len(fixture.vertices),3),dtype='f4');fixture.vertices.foreach_get('co',skin.ravel())
    faces=np.empty(24831,dtype='i4');data.attributes['AFN409_SKIN_TRIANGLE_ID'].data.foreach_get('value',faces)
    tri=np.asarray([p.vertices[:] for p in fixture.polygons],dtype='i4');p=skin[tri[faces]]
    normal=unit(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]))
    end=11;length=np.linalg.norm(np.diff(q[:,:end+1],axis=1),axis=2).sum(1)
    direction=unit(q[:,3]-q[:,0]);tangent=unit(direction-normal*(normal*direction).sum(1)[:,None])
    m0=unit(tangent+.25*normal)*length[:,None];m1=unit(q[:,end+2]-q[:,end-2])*length[:,None]
    t=np.linspace(0.,1.,end+1,dtype='f4')[None,:,None]
    q[:,:end+1]=(2*t**3-3*t**2+1)*base[:,0,None]+(t**3-2*t**2+t)*m0[:,None]+(-2*t**3+3*t**2)*q[:,end,None]+(t**3-t**2)*m1[:,None]
    q=q.astype('f4');q[:,0]=base[:,0];assert np.isfinite(q).all()
    obj=control.copy();obj.data=data.copy();obj.name='R484 complete hair | B';obj.data.name='R484 volume locks | B'
    bpy.context.scene.collection.objects.link(obj);obj.data.position_data.foreach_set('vector',q.ravel());obj.data.update_tag();obj.update_tag()
    bpy.data.objects['R484 complete hair | A'].hide_render=True;bpy.data.objects['R484 complete hair | A'].hide_set(True)
    obj.hide_render=False;obj.hide_set(False)
    np.savez_compressed(ROOT/'volume-lock-B.npz',position=q,sourceComponent=components)
    # Localize linked material/image dependencies and retain all inherited notices.
    before_linked=[dict(name=i.name,type=i.bl_rna.identifier) for i in bpy.data.user_map() if i.library]
    bpy.ops.object.make_local(type='ALL')
    bpy.ops.file.pack_all()
    bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
    assert not [i for i in bpy.data.user_map() if i.library]
    assert not [i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file]
    text=bpy.data.texts.new('Aevrynd_R484_Volumetric_Lock_Note')
    text.write('Unaccepted B replaces planar strip-following offsets with complete elliptical volume cross sections. All 24,831 original follicles, identities and radii are retained. The same original artist strip paths define guide centers and physical widths. Original mesh stays hidden reference. No contact, dynamics, engine or user acceptance is claimed. Linked material/image dependencies localized and packed; original full working source remains untouched.\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    bpy.ops.wm.open_mainfile(filepath=str(DEST),load_ui=False,use_scripts=False)
    actual=np.empty((24831,80,3),dtype='f4');bpy.data.objects['R484 complete hair | B'].data.position_data.foreach_get('vector',actual.ravel())
    assert np.array_equal(actual,q)
    record=dict(source=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=sha(DEST)),parent=proof['source'],
        positionHashes=proof['positionHashes']|dict(B=sha256(q.tobytes()).hexdigest()),rootsBitIdentical=True,
        rootGroups=len(populations),groupPopulationP0P50P95P100=np.quantile(populations,[0,.5,.95,1]).tolist(),
        changedStrands=int(np.any(q!=base,axis=(1,2)).sum()),localizedDependencies=before_linked,
        externalLibraries=[i.filepath for i in bpy.data.libraries],externalImages=[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file],
        collisionStatus='NOT_EVALUATED',motionStatus='NOT_EVALUATED',websiteChanged=False)
    (ROOT/'volume-source-receipt.json').write_bytes(json.dumps(record,indent=2).encode('utf8'))
    print(json.dumps({k:v for k,v in record.items() if k!='localizedDependencies'},indent=2),flush=True)

if __name__=='__main__':main()
