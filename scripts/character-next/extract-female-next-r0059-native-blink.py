"""Same-topology native eyelid morph and native facial-hair pose data."""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0';E=R/'Evidence/character-female-next/r0059-authored-blink';PREV=E.parent/'r0057-coherent-foundation'
def main():
    tick=time.time();lib=json.loads((PREV/'canonical-library.json').read_text());path=Path(lib['output']);assert hashlib.sha256(path.read_bytes()).hexdigest()==lib['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['cm_vitruvian'];P=np.load(D/'Default.npy');keys={};array={};roles={}
    for side in ('Left','Right'):
        raw=np.load(E/('source-Eyes_Closed_'+side+'.npz'));Q=P.copy();Q[raw['idx']]+=raw['delta'];key=o.shape_key_add(name='AFN59_Source_Blink_'+side);key.data.foreach_set('co',Q.astype('f4').ravel());keys[side]=key;array['key'+side]=Q.astype('f4');array['indices'+side]=raw['idx'];array['delta'+side]=raw['delta']
        touched=set(raw['idx'].tolist());roles[side]={str(mi):sum(1 for p in o.data.polygons if p.material_index==mi and any(v in touched for v in p.vertices)) for mi in range(8)}
    for ps in o.particle_systems:ps.settings.child_type='NONE'
    for md in o.modifiers:
        if md.type=='PARTICLE_SYSTEM':md.show_viewport=True
    o.data.shape_keys.key_blocks['AFN57_Supplied_Female_Morph'].value=1
    poses=[('neutral',0.,0.)]+[(f'{side.lower()}_{int(t*100):03d}',t if side=='Left' else 0.,t if side=='Right' else 0.) for side in ('Left','Right') for t in (.25,.5,.75,1.)]+[(f'both_{int(t*100):03d}',t,t) for t in (.25,.5,.75,1.)]
    body={};bounds={}
    for name,left,right in poses:
        keys['Left'].value=left;keys['Right'].value=right;bpy.context.scene.frame_set(1);bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();body[name]=np.array([v.co[:] for v in me.vertices],dtype='f4');ev.to_mesh_clear()
        for system,label in ((0,'lashes'),(1,'brows')):
            ps=ev.particle_systems[system];mod=next(m for m in ev.modifiers if m.type=='PARTICLE_SYSTEM' and m.particle_system==ps);counts=np.array([len(p.hair_keys) for p in ps.particles],dtype='i4');points=np.array([key.co_object(ev,mod,particle)[:] for particle in ps.particles for key in particle.hair_keys],dtype='f4');assert np.isfinite(points).all() and points[:,2].min()>1.5
            if name=='neutral':
                old=np.load(PREV/('female-object-space-'+label+'.npz'));assert np.array_equal(points,old['positions']) and np.array_equal(counts,old['counts']),('Neutral regression',label)
                array[label+'Counts']=counts;array[label+'Radii']=np.full(len(points),ps.settings.root_radius*ps.settings.radius_scale,dtype='f4')
            else:assert np.array_equal(counts,array[label+'Counts'])
            array[label+'_'+name]=points;bounds[label+'_'+name]=[points.min(0).tolist(),points.max(0).tolist()]
        print('R59_NATIVE_POSE',name,left,right,flush=True)
    errors={}
    for label in ('lashes','brows'):
        for t in (25,50,75,100):
            predicted=array[f'{label}_left_{t:03d}']+array[f'{label}_right_{t:03d}']-array[label+'_neutral'];errors[f'{label}_{t}']=float(np.linalg.norm(predicted-array[f'{label}_both_{t:03d}'],axis=1).max())
    assert max(errors.values())<1e-6,('Independent controls not additive enough',errors)
    np.savez_compressed(E/'native-blink-pose-data.npz',**array,**{'body_'+name:pts for name,pts in body.items()})
    row={'canonicalLibrarySha256':lib['sha256'],'sourceNativeParticleEvaluation':True,'importedToolCode':False,'poses':[{'name':n,'left':l,'right':r} for n,l,r in poses],'canonicalBodyVertices':len(P),'affectedMaterialPolygonCounts':roles,'neutralFacialHairExactlyMatchesR57D':True,'nativeLeftRightAdditivityMaximumErrorM':errors,'nativeFacialHairBoundsM':bounds,'pointShapeInterpolation':'Five exact samples per eye including neutral; later between-sample linear approximation must be measured, not called exact or continuously collision safe.','seconds':time.time()-tick}
    (E/'native-blink-extraction.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8');print('R59_NATIVE_BLINK_EXTRACTED',len(poses),max(errors.values()),time.time()-tick,flush=True)
if __name__=='__main__':main()
