"""Bounded old/new facial geometry and existing CC0 pigment correspondence."""
import bpy,importlib.util,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('r31',Path(__file__).with_name('build-female-next-r0031-native-brows.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
b=c.b;R=b.R;S=b.S;E=R/'Evidence/character-female-next/r0032-registered-skin';E.mkdir(parents=True,exist_ok=True)
OLD=S/'aevrynd-female-next-r0023-b-neutral-review.blend';NEW=c.SRC;TEXTURE=S/'textures/makehuman-system-cc0/young_lightskinned_female_diffuse3.png'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def extract(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();v=np.empty(len(m.vertices)*3,dtype='f4');m.vertices.foreach_get('co',v);v=v.reshape(-1,3).astype('f8');mx=np.array(ev.matrix_world);v=v@mx[:3,:3].T+mx[:3,3];t=np.empty(len(m.loop_triangles)*3,dtype='i4');m.loop_triangles.foreach_get('vertices',t);t=t.reshape(-1,3);loops=np.empty(len(m.loop_triangles)*3,dtype='i4');m.loop_triangles.foreach_get('loops',loops);uv=np.empty(len(m.uv_layers.active.data)*2,dtype='f4');m.uv_layers.active.data.foreach_get('uv',uv);uv=uv.reshape(-1,2)[loops.reshape(-1,3)];ev.to_mesh_clear();return v,t,uv
def main():
    rows={}
    for label,path,name in [('old',OLD,'AFN_R0008_Body'),('new',NEW,b.BODY)]:
        bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects[name];v,t,uv=extract(o);bt=BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True);profiles=[]
        for x in (0.,.012,.022):
            for z in np.linspace(1.370,1.448,391):
                hit,n,ti,d=bt.ray_cast(Vector((x,-.4,float(z))),Vector((0,1,0)),.6)
                if hit is not None:profiles.append({'x':x,'z':float(z),'y':float(hit.y),'normal':list(n),'triangle':int(ti)})
        rows[label]={'path':str(path),'sha256':b.sha(path),'body':name,'baseVertices':len(o.data.vertices),'baseUV':b.mesh_signature(o.data)['uv'],'profiles':profiles,'skinImages':[{'name':n.image.name,'path':n.image.filepath,'packed':bool(n.image.packed_file),'colorSpace':n.image.colorspace_settings.name} for mat in o.data.materials if mat for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]}
        if label=='old':np.savez_compressed(E/'old-body-sampling.npz',vertices=v,triangles=t,triangleUV=uv)
    save('source-registration-inspection.json',{'old':rows['old'],'new':rows['new'],'texture':str(TEXTURE),'textureSha256':b.sha(TEXTURE),'calibration':json.loads((R/'Evidence/character-female-next/r0011-skin-brows/skin-albedo-calibration.json').read_text(encoding='utf8')),'scope':'Sources already local and CC0, no re-download. Different native UV hashes prove direct shader reuse is invalid. Actual cross-section data drives one bounded face registration.'});print('R32_INSPECT_DONE',json.dumps({k:{'vertices':r['baseVertices'],'UV':r['baseUV']} for k,r in rows.items()}),flush=True)
if __name__=='__main__':main()
