"""Candidate B: trace neutral visible optical geometry rather than fixed depth."""
import bpy,math,json,importlib.util
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('pin',Path(__file__).with_name('build-female-next-r0020-pinned-blink.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def trace(tree,centre,sign):
    side='L' if sign>0 else 'R';optics=[b.solid.data(o)[2] for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN6_'+side+'_')];points=[]
    def ray(x,z):return tree.ray_cast(Vector((x,-.3,z)),Vector((0,1,0)),.45)
    def exposed(x,z):
        origin=Vector((x,-.3,z));direction=Vector((0,1,0));dists=[r[3] for optical in optics if (r:=optical.ray_cast(origin,direction,.45))[0] is not None]
        if not dists:return False
        hit,n,face,dist=ray(x,z)
        return hit is None or dist>min(dists)+.000001
    for absoluteX in np.linspace(.009,.050,411):
        x=sign*absoluteX;openZ=[float(z) for z in np.linspace(centre[2]-.014,centre[2]+.014,281) if exposed(x,float(z))]
        if not openZ:continue
        one={'x':x,'absX':float(absoluteX)}
        for label,gap,skin in (('lower',min(openZ),min(openZ)-.00020),('upper',max(openZ),max(openZ)+.00020)):
            # Bracket actual body occlusion; broaden only the bracket if needed.
            direction=1 if label=='upper' else -1
            while exposed(x,skin) and abs(skin-gap)<.002:skin+=direction*.00020
            assert not exposed(x,skin),(side,x,label)
            for _ in range(16):
                z=(gap+skin)/2
                if exposed(x,z):gap=z
                else:skin=z
            z=skin+(.00012 if label=='upper' else -.00012);hit,n,face,dist=ray(x,z)
            if hit is None:break
            one[label]=list(hit);one[label+'Angle']=math.atan2(hit.z-centre[2],-(hit.y-centre[1]))
        if 'upper' in one and 'lower' in one and one['upperAngle']>one['lowerAngle']+.002:points.append(one)
    assert len(points)>80
    b.save('b-visible-rim-'+side+'.json',{'points':points,'scope':'Neutral front orthographic body/opaque-optical-union ray visibility at 0.1mm grid, 16 bisections and 0.12mm skin margin. Not all-view closure or continuous contact proof.'})
    return points

def main():
    b.PREFIX='b';b.DST=b.S/'aevrynd-female-next-r0020-b-visible-rim-blink-study.blend';b.c.trace=trace;original=b.save
    def save(name,obj):
        name='b-'+name[2:] if name.startswith('a-') else 'b-iteration-contract.json' if name=='iteration-contract.json' else name
        if name=='b-iteration-contract.json':
            obj['hypothesis']='Keep candidate A exact brow support pinning, replace fixed-depth rim detection with actual body-versus-optical-union visible boundary. Cover small canthus gaps omitted by the earlier depth threshold.';obj['knownSeparateIssue']='Closure is pending actual mask and multiangle renders; this is not proof of complete closure.'
        if name=='b-build-verification.json':obj['rimDetection']='Actual neutral optical-union front visibility; 0.1mm grid, refined boundaries.'
        original(name,obj)
    b.save=save;b.main()
if __name__=='__main__':main()
