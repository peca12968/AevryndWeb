"""Close the observed rear slot and add an explicit inner crown design layer.

This is layered volume blocking, not a scalp-cap strand generator or final
renderable hair. Actual scalp geometry is reused, not re-researched or moved.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time
sp=importlib.util.spec_from_file_location('edit54layers',Path(__file__).with_name('sculpt-female-next-r0054-volume-coverage.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E;SRC=k.OUT;OUT=b.S/'aevrynd-female-next-r0054-c-layered-volume-blockout.blend'

def main():
    tick=time.time();sourceProof=json.loads((E/'b-build-summary.json').read_text());assert b.sha(SRC)==sourceProof['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state();edited=[]
    for side,sign in [('L',1.),('R',-1.)]:
        ob=bpy.data.objects['AFN54_'+side+'_rear_centre'];X=np.array([list(v.co) for v in ob.data.vertices],dtype='f8');old=X.copy()
        lo,hi=X[:,0].min(),X[:,0].max()
        inner=np.clip((X[:,0]-lo)/(hi-lo),0,1) if side=='L' else np.clip((hi-X[:,0])/(hi-lo),0,1)
        height=np.clip((1.515-X[:,2])/.045,0,1);height=height*height*(3-2*height)
        X[:,0]+=sign*.010*inner*height
        for vertex,point in zip(ob.data.vertices,X):vertex.co=point
        ob.data.update();edited.append({'object':ob.name,'editedVertices':int((np.linalg.norm(X-old,axis=1)>1e-8).sum()),'maximumMoveM':float(np.linalg.norm(X-old,axis=1).max())})
    scalp=bpy.data.objects['AFN53_ANATOMICAL_SCALP'];V,T=b.evaluated(scalp,True)
    centre=V[T].mean(1);selected=(centre[:,2]>1.505)
    part=(np.abs(centre[:,0])<.001)&(centre[:,1]<.020)&(centre[:,2]>1.530)
    selected&=~part;chosen=T[selected];ids,inv=np.unique(chosen,return_inverse=True)
    normals=np.array([list(v.normal) for v in scalp.data.vertices],dtype='f8')
    assert len(normals)==len(V)
    P=V[ids]+normals[ids]*.0045
    mesh=bpy.data.meshes.new('AFN54_INNER_CROWN_VOLUME_PROXY');mesh.from_pydata(P.tolist(),[],inv.reshape(-1,3).tolist());mesh.update()
    for face in mesh.polygons:face.use_smooth=True
    ob=bpy.data.objects.new(mesh.name,mesh);bpy.data.collections['AFN54_AUTHORING_VOLUME_PROXIES'].objects.link(ob)
    ob.data.materials.append(bpy.data.materials['AFN54_IDENTICAL_CLAY_PROXY'])
    solid=ob.modifiers.new('AFN54_InnerMassThickness','SOLIDIFY');solid.thickness=.006;solid.offset=0
    faceSet=mesh.attributes.new('.sculpt_face_set','INT','FACE');faceSet.data.foreach_set('value',[13]*len(mesh.polygons))
    ob['aevrynd_layer']='AUTHORING_INNER_VOLUME_PROXY_NOT_HAIR'
    ob['scope']='Inner crown mass/part footprint from retained skin, used only to assess complete volume. Not physical strands, scalp replacement, contact proxy or accepted final hairstyle.'
    bpy.context.view_layer.update();after=f.state()
    altered={'AFN54_L_rear_centre','AFN54_R_rear_centre'}
    assert all(after['meshes'][name]==row for name,row in before['meshes'].items() if name not in altered)
    assert all(after['materials'][name]==row for name,row in before['materials'].items())
    assert all(after[key]==before[key] for key in ('skinFields','curves','stage'))
    b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    k.k.save('c-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),
        'rearCoverageEdits':edited,'innerCrownSource':'Retained actual skin domain, upper region only','innerCrownFaces':len(chosen),
        'partFootprint':'Narrow upper/front centre part only; no long rear bald slot.',
        'existingCharacterUnchanged':True,'scope':'Layered design volume only, no final hair/contact/dynamic/runtime claim.',
        'status':'LAYERED_VOLUME_PENDING_COMPLETE_FORM_REVIEW','seconds':time.time()-tick})
    f.E=E;f.render('c-proxy',('face','oblique','profile'));k.k.k.k.k.a.i.ch.review.extras('c-proxy',E);k.k.orthographic('c-proxy')
    print('R54_LAYERED_VOLUME',len(chosen),time.time()-tick,flush=True)

if __name__=='__main__':main()
