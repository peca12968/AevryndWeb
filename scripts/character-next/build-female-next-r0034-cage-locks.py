"""B: independent cubic control cages, not interpolated shoulder knots.

A's explicit interpolating points create horizontal outrigger shelves. Treat
the authored free points as independent cubic B-spline control cages; preserve
the start tangent and smooth the whole free length without visiting corners.
"""
import bpy,importlib.util,json,sys
from pathlib import Path
import numpy as np
from mathutils import Matrix
spec=importlib.util.spec_from_file_location('a34',Path(__file__).with_name('build-female-next-r0034-master-locks.py'));a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
g=a.g

def free_controls(P,tangent,m):
    K=np.vstack((P[-1],P[-1]+tangent*.022,np.array(m[6],dtype='f8')))
    return K,np.zeros_like(K)

def spline_point(K,knots,t,degree=3):
    n=len(K)-1;k=n if t>=1 else int(np.searchsorted(knots,t,side='right')-1);d=[K[j].copy() for j in range(k-degree,k+1)]
    for r in range(1,degree+1):
        for j in range(degree,r-1,-1):
            left=knots[j+k-degree];right=knots[j+1+k-r];weight=(t-left)/(right-left) if right>left else 0.;d[j]=(1-weight)*d[j-1]+weight*d[j]
    return d[degree]

def free_samples(K,T,count=161):
    degree=3;n=len(K)-1;knots=np.r_[np.zeros(4),np.linspace(0,1,n-degree+2)[1:-1],np.ones(4)]
    return a.resample(np.array([spline_point(K,knots,float(t)) for t in np.linspace(0,1,193)]),count)

def editable_controls(name,K,T,body):
    d=bpy.data.curves.new('CTRL34_B_'+name,'CURVE');d.dimensions='3D';sp=d.splines.new('NURBS');sp.points.add(len(K)-1);sp.points.foreach_set('co',np.column_stack((K,np.ones(len(K)))).astype('f4').ravel());sp.order_u=4;sp.use_endpoint_u=True
    o=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(o);o.parent=body;o.matrix_world=Matrix.Identity(4);o.hide_render=True;o.hide_set(True);o['aevrynd_layer']='EDITABLE_INDEPENDENT_FREE_LOCK_CAGE';o['basis']='Clamped cubic B-spline, own explicit controls; cache rebuild required';return o

def configure():
    a.free_controls=free_controls;a.free_samples=free_samples;a.editable_controls=editable_controls
    base_camera=g.b.camera
    def whole_hair_camera(view):
        base_camera(view)
        if not view.startswith('body'):bpy.context.scene.camera.data.lens=85
    g.b.camera=whole_hair_camera

def main():
    configure();a.OUT=a.S/'aevrynd-female-next-r0034-b-independent-cage-locks.blend'
    bpy.ops.wm.open_mainfile(filepath=str(a.SRC));g.b.E=a.E;g.b.setup(bpy.context.scene,g.b.config(bpy.context.scene));g.q.render('before-wide')
    original_save=a.save
    a.save=lambda n,x:original_save(('b-'+n[2:]) if n.startswith('a-') else ('b-'+n if n in ('round-contract.json','baseline-state.json') else n),x)
    original_render=g.q.render;g.q.render=lambda label:original_render('b-guides' if label=='a-guides' else label)
    original_legacy=a.legacy_paths
    def legacy(name,*args,**kwargs):return original_legacy(name.replace('AFN34_A_','AFN34_B_'),*args,**kwargs)
    a.legacy_paths=legacy
    original_np_save=np.savez_compressed
    def cache(path,*args,**kwargs):
        path=Path(path)
        if path.name=='aevrynd-female-next-r0034-a-master-guides.npz':path=path.with_name('aevrynd-female-next-r0034-b-master-guides.npz')
        return original_np_save(path,*args,**kwargs)
    np.savez_compressed=cache;a.main()
    p=a.E/'b-round-contract.json';contract=json.loads(p.read_text());contract.update({'candidate':'B','candidateCount':2,'reason':'Actual A pilot has outrigger-like interpolated shoulders and excessive edge spread; do not expand fibres from it','methodDifference':'Each own free path is a clamped cubic control cage, not an interpolating Hermite chain or a shared analytic angle/ring','camera':'New85mm complete-hair front/oblique/profile with fresh matched before-wide source renders; unchanged light/exposure/materials. Wider framing exposes all boundaries, not an appearance improvement by itself.'});p.write_text(json.dumps(contract,indent=2)+'\n')

if __name__=='__main__':main()
