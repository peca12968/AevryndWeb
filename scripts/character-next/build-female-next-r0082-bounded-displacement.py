"""Third and final construction: bounded whole-style scalp displacement.
Unlike B's transported frame offsets, this extends the exact paired vertex
displacement by nearest source-surface barycentrics. Its world displacement
is a convex combination of source/target vertex differences, so cannot exceed
their maximum norm (plus a declared finite-precision allowance).
"""
from pathlib import Path
import bpy,json,importlib.util
sp=importlib.util.spec_from_file_location('bounded82',Path(__file__).with_name('build-female-next-r0082-surface-wrap.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b)
E=b.E;OUT=b.S/'aevrynd-female-next-r0082-c-bounded-scalp-displacement.blend';capBound=None
def node(o,source,scale,shift):
 ng=bpy.data.node_groups.new('AFN82_BOUNDED_VERTEX_DISPLACEMENT_EXTENSION','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');n=ng.nodes;l=ng.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');pos=n.new('GeometryNodeInputPosition');info=n.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=source;info.inputs['As Instance'].default_value=False
 def sample(value):
  s=n.new('GeometryNodeSampleNearestSurface');s.data_type='FLOAT_VECTOR';l.new(info.outputs['Geometry'],s.inputs['Mesh']);l.new(value,s.inputs['Value']);l.new(pos.outputs['Position'],s.inputs['Sample Position']);return s.outputs['Value']
 foot=sample(pos.outputs['Position']);attr=n.new('GeometryNodeInputNamedAttribute');attr.data_type='FLOAT_VECTOR';attr.inputs['Name'].default_value='AFN82_TargetPositionLocal';target=sample(attr.outputs['Attribute']);delta=n.new('ShaderNodeVectorMath');delta.operation='SUBTRACT';l.new(target,delta.inputs[0]);l.new(foot,delta.inputs[1]);add=n.new('ShaderNodeVectorMath');add.operation='ADD';l.new(pos.outputs['Position'],add.inputs[0]);l.new(delta.outputs['Vector'],add.inputs[1]);sp=n.new('GeometryNodeSetPosition');l.new(inp.outputs['Geometry'],sp.inputs['Geometry']);l.new(add.outputs['Vector'],sp.inputs['Position']);l.new(sp.outputs['Geometry'],out.inputs['Geometry']);md=o.modifiers.new('AFN82_BOUNDED_SCALP_DISPLACEMENT','NODES');md.node_group=ng;o['AFN82_displacement_operator']='After original curl generation: P + barycentric(target scalp - source scalp) at nearest source point. All points, no guide-root-only fitting or frame-offset rotation. World motion bounded by maximum paired vertex displacement plus2micrometres. Not a continuous/injective/contact certificate.'
def save(name,value):
 global capBound
 name='c-'+name[2:] if name.startswith('b-') else name
 if name=='c-surface-construction-guard.json':capBound=value['maximumActualCapDisplacementM'];value['operator']='Barycentric extension of paired vertex displacement, no transported rotation';value['worldDisplacementUpperBoundM']=capBound
 if name=='c-generated-field-guard.json':
  value['convexCombinationWorldDisplacementBoundM']=capBound;value['finitePrecisionAllowanceM']=2e-6;value['withinDerivedBound']=value['maximumGeneratedDisplacementM']<=capBound+2e-6;(E/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');assert value['withinDerivedBound'],'The declared barycentric bound failed; no tolerance relaxation'
 if name=='c-build-summary.json':value.update(lineageFile='c-wrap-and-render-lineage.npz',construction='BOUNDED_PAIRED_SCALP_DISPLACEMENT_AFTER_SOURCE_CURL',worldVertexDisplacementBoundM=capBound,normalFrameRotationApplied=False,priorRadialCageAndRotatedWrapRejected=True)
 (E/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def main():
 originalRender=b.a.render;b.OUT=OUT;b.LINEAGE=E/'c-wrap-and-render-lineage.npz';b.node=node;b.save=save;b.a.render=lambda tag,view:originalRender('c-displacement',view);b.main();print('R82_FINAL_BOUNDED_DISPLACEMENT_SOURCE',str(OUT),flush=True)
if __name__=='__main__':main()
