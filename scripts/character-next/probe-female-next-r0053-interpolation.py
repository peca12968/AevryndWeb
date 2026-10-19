"""Inspect native density/Poisson controls only after master qualification.

No dense evaluation, source save, bundled graph redistribution, or promotion.
The installed production tool's units must be understood before allocating
children. Node data stays ephemeral in this Blender process.
"""
from pathlib import Path
import bpy,importlib.util,json
sp=importlib.util.spec_from_file_location('interp53guard',Path(__file__).with_name('build-female-next-r0053-scalp-foundation.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
E=k.E;b=k.b

def main():
    proof=json.loads((E/'grown-fixed-saved-static-verification.json').read_text())
    assert proof['surfaceUVBindingMatchesActualFoot']
    assert proof['actualFiniteBodyCapsules']['unqualifiedSegments']==0
    assert not proof['actualFiniteBodyCapsules']['rootFailures']
    assert proof['actualFiniteMasterSelfCapsules']['overlapsBeyondNumericalAllowance']==0
    assert proof['otherOpticalWetLashMeshesAndBrows']['status']=='PASS_TESTED_STATIC_EXTERNAL_SCOPE'
    assert len(proof['authoredAndContactTestedCurveIndices'])==64
    assert b.sha(Path(proof['source']))==proof['sourceSha256']
    library=k.k.LIB
    with bpy.data.libraries.load(str(library),link=False) as (source,target):
        target.node_groups=['Interpolate Hair Curves']
    group=target.node_groups[0]
    facts={'installedBlender':bpy.app.version_string,'librarySha256':b.sha(library),
           'masterSourceSha256':proof['sourceSha256'],'interfaces':[],
           'distributionControls':[],'densityRelatedMath':[],
           'scope':'Ephemeral production-tool interface inspection only; no graphs copied or source saved.'}
    for socket in group.interface.items_tree:
        if socket.item_type=='SOCKET':
            facts['interfaces'].append({'name':socket.name,'identifier':socket.identifier,
                'type':socket.socket_type,'description':socket.description})
    for node in group.nodes:
        if node.bl_idname=='GeometryNodeDistributePointsOnFaces':
            facts['distributionControls'].append({'mode':node.distribute_method,
                'inputs':[{'name':s.name,'value':s.default_value if isinstance(getattr(s,'default_value',None),(int,float,str,bool)) else None} for s in node.inputs]})
        if node.bl_idname=='GeometryNodeMenuSwitch':
            facts['distributionControls'].append({'menuItems':[item.name for item in node.enum_items]})
        if node.bl_idname in ('ShaderNodeMath','ShaderNodeMathOperation'):
            linked=any(l.from_node.bl_idname=='NodeGroupInput' and l.from_socket.name=='Density' and l.to_node==node for l in group.links)
            if linked:facts['densityRelatedMath'].append({'operation':node.operation,'constants':[s.default_value for s in node.inputs if not s.is_linked and isinstance(getattr(s,'default_value',None),(int,float))]})
    k.save('interpolation-interface-facts.json',facts)
    print(json.dumps(facts,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
