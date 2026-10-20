"""Second structural method: actual scalp undercoat + free perimeter cards.

Rejects A's floating crown ribbons. Does not cover them: they are not reused.
Reauthors each perimeter root and builds a separate real-source scalp patch.
"""
import bpy,numpy as np,json,time,sys
from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location('ribbon64split',Path(__file__).with_name('build-female-next-r0064-guide-ribbons.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
g=m.g;k=g.k;E=m.E;S=m.S;OUT=S/'aevrynd-female-next-r0064-b-scalp-free-card-shape.blend'

def source_uv_patch(body):
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();local=np.empty(len(me.vertices)*3,'f4');me.vertices.foreach_get('co',local);local=local.reshape(-1,3).astype('f8');normal=np.empty(local.size,'f4');me.vertices.foreach_get('normal',normal);normal=normal.reshape(-1,3).astype('f8');M=np.array(body.matrix_world);P=local@M[:3,:3].T+M[:3,3];normal=normal@np.linalg.inv(M[:3,:3]);normal/=np.linalg.norm(normal,axis=1)[:,None]
    # Explicit anatomical growth boundary: forehead/temple, above pinna,
    # posterior scalp and nape. No failed-root deletion or test-driven mask.
    x,y,z=P.T;front=np.clip((-.030-y)/.085,0,1);line=1.417+.102*front-.32*np.abs(x)*front;growth=(z>line)&(z>1.414)&(np.abs(x)<.078)&(y>-.135)&(y<.065);growth&=~((np.abs(x)>.063)&(y>-.055)&(y<.020)&(z<1.481))
    tri=np.array([t.vertices[:] for t in me.loop_triangles],'i4');mats=np.array([t.material_index for t in me.loop_triangles]);mask=np.isin(mats,(4,5))&growth[tri].all(1);selected=tri[mask];used=np.unique(selected);remap=np.full(len(P),-1,'i4');remap[used]=np.arange(len(used));V=P[used]+normal[used]*.0008;T=remap[selected]
    mesh=bpy.data.meshes.new('AFN64_ACTUAL_SCALP_UNDERCOAT');mesh.from_pydata(V.tolist(),[],T.tolist());mesh.update();uv=mesh.uv_layers.new(name='AFN64_ScalpUV');C=np.array((0.,-.038,1.471));d=P[used]-C
    for poly in mesh.polygons:
        poly.use_smooth=True
        vals=[]
        for li in poly.loop_indices:
            v=mesh.loops[li].vertex_index;u=(np.arctan2(d[v,0],d[v,1])+np.pi)/(2*np.pi);vv=(P[used[v],2]-1.414)/.15;vals.append((li,u,vv))
        if max(r[1] for r in vals)-min(r[1] for r in vals)>.5:vals=[(li,u+1 if u<.5 else u,vv) for li,u,vv in vals]
        for li,u,vv in vals:uv.data[li].uv=(u,vv)
    for name,values,kind in [('AFN64_SourceRenderVertex',used,'INT')]:mesh.attributes.new(name,kind,'POINT').data.foreach_set('value',values)
    bodyids=np.empty(len(me.polygons),'i4');me.attributes['AFN60_NativeFaceID'].data.foreach_get('value',bodyids);faceids=bodyids[np.array([t.polygon_index for t in me.loop_triangles])[mask]];mesh.attributes.new('AFN64_NativeScalpFace','INT','FACE').data.foreach_set('value',faceids)
    ev.to_mesh_clear();return mesh,{'sourceVertices':len(P),'patchVertices':len(V),'patchTriangles':len(T),'outwardOffsetM':.0008,'growthBoundary':'Explicit front/temple/pinna/posterior/nape landmarks in source world metres; not based on failed contacts.'}

def main():
    tick=time.time();assert not OUT.exists();original=m.polygons
    def free():
        rows=[]
        for r in original():
            if r['region'] in ('front','crown'):r['points']=r['points'][2:]
            if r['region']=='fringe':r['points']=r['points'][1:]
            r['name']='free_'+r['name'];rows.append(r)
        return rows
    # Reuse authoring I/O and geometric sampling, not A's existing mesh/path.
    # This new root/free representation has its own immutable B source.
    m.polygons=free;m.OUT=OUT
    oldsave=m.save
    def save_b(n,x):
        if n=='round-contract.json':return
        oldsave(n.replace('a-','b-',1) if n.startswith('a-') else n,x)
    m.save=save_b
    m.build();body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];levels=[]
    for md in body.modifiers:
        if md.type=='SUBSURF':levels.append((md,md.levels));md.levels=md.render_levels
    bpy.context.view_layer.update();mesh,info=source_uv_patch(body);o=bpy.data.objects.new('AFN64_SCALP_UNDERCOAT',mesh);bpy.data.collections['AFN64_AUTHORED_HAIR'].objects.link(o);mesh.materials.append(next(mat for mat in bpy.data.materials if mat.name.startswith('AFN64_OPAQUE_SHAPE_REVIEW_ONLY')));o['scope']='Actual source scalp undercoat mesh, opaque shape preview only. 0.8mm outward source-normal offset, no contact proof.'
    for md,level in levels:md.levels=level
    k.b.camera('face');bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);ref=json.loads((E/'b-build-summary.json').read_text());ref.update(outputSha256=m.sha(OUT),scalp=info,method='Separate actual-skin undercoat + newly rooted free perimeter cards. Floating A crown cards not reused.');oldsave('b-build-summary.json',ref)
    oldsave('b-method-decision.json',{'rejectedA':'Opaque guide/card first preview has floating crown ribbons and large scalp holes. Do not build an atlas on it.','newB':'Actual source scalp undercoat owns crown coverage; free cards have new perimeter roots. This removes floating crown geometry, not an opacity mask hiding it.','notClaimed':'Final hair realism, full contact, guide control or motion. Opaque B first needs a readable complete shape.','secondsBeforeBPreview':time.time()-tick})
    m.shade.g.E=E;oldsave('b-first-view-controls.json',m.shade.render('b-shape',('face','profile','back')))
if __name__=='__main__':main()
