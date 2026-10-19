"""Correct volume ownership for actual free-fibre containment anchors.

An aggregate of a closed body, closed eye shells AND open iris surfaces is not
a closed solid. Keep the valid aggregate surface capsule results; independently
classify against the actual closed body, and exclude optical containment only
with actual component bounds. No tolerance or geometry changes.
"""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('owners61',Path(__file__).with_name('build-female-next-r0061-surface-flow-groom.py'));g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)

def main():
    tick=time.time();ref=json.loads((g.E/'b-fibres-build-summary.json').read_text());assert g.sha(Path(ref['output']))==ref['outputSha256'];old=json.loads((g.E/'b-actual-fibre-contact-verification.json').read_text());assert old['unqualifiedSegments']==0
    cache=np.load(g.E/'actual-body-render-surface.npz');P=cache['P'];T=cache['T'];tri=P[T];tree=BVHTree.FromPolygons(P.tolist(),T.tolist(),all_triangles=True);raw=np.load(g.E/'b-fibres-authoring.npz');roots=raw['positions'][:,1];bad=[]
    for ci,p in enumerate(roots):
        state=g.k.f.flowcheck.cap.solid.classify(tree,tri,Vector(p))
        if state!='outside':bad.append({'curve':ci,'state':state,'firstFreePoint':p.tolist()})
    bpy.ops.wm.open_mainfile(filepath=ref['output']);owners=[]
    names=json.loads((g.E.parent/'r0060-ocular-assembly/b-build-summary.json').read_text())['visibleComponents']
    for ci in range(4):
        o=bpy.data.objects[names[str(ci)]]
        for md in o.modifiers:
            if md.type=='SUBSURF':md.levels=md.render_levels
        row=g.k.mesh(o);lo=row['V'].min(0);hi=row['V'].max(0);inside=np.all((roots>=lo)&(roots<=hi),axis=1)
        assert not inside.any(),('Need closed-shell classification, bounding exclusion insufficient',ci,int(inside.sum()))
        owners.append({'component':o.name,'bounds':[lo.tolist(),hi.tolist()],'anchorsWithinBounds':0})
    result={'source':ref['output'],'sha256':ref['outputSha256'],'status':'PASS_NEUTRAL_FREE_SHAFT_VS_BODY_OPTICS_SCOPE' if not bad else 'FAIL_OR_UNRESOLVED','allActualFreeCapsuleSegments':old['segments'],'unqualifiedCapsuleSegments':old['unqualifiedSegments'],'minimumConservativeSeparationLowerBoundM':old['minimumCertifiedClearanceLowerBoundM'],'exactGlobalSignedMinimumM':None,'actualClosedBodyAnchors':len(roots),'bodyAnchorFailures':bad,'opticalBoundsExclusion':owners,'previousAggregateRootUnresolved':len(old['rootFailures']),'testCorrection':'Open iris surfaces invalidate aggregate parity/winding as a solid test. Actual closed body volume tested separately; all optical containment excluded by disjoint actual component bounds. Capsule separation still tests all actual body/optical surfaces. No physical or numeric tolerance changed.','anatomicalRootJoinsAndSelfMotion':'First follicle segment, hair/hair, hair/tie and all dynamics unaccepted. Tie-shaft self failure remains real and unexcused.','seconds':time.time()-tick}
    g.save('b-corrected-volume-owner-verification.json',result);print('R61_VOLUME_OWNERS',result['status'],len(bad),time.time()-tick,flush=True)
if __name__=='__main__':main()
