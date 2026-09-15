# v249 r1041 parametric lip retopology review

r1041 replaces inherited irregular angular spacing across the six welded 120-vertex mouth rings with one monotonic closed-loop parameterization. The outer facial seam stays locked and every corresponding ring vertex shares the same angular sample, preventing the local order reversals found during the first diagnostic run.

- The retained 0.35 technical bound passes frames 1/20/33/61, mouth-open and smile with zero non-adjacent body self-collision and zero overlap against all six oral layers.
- The 0.50 bound self-intersects in every tested state and is rejected. It is excluded from the final deterministic rerun because Blender crashed during its last redundant comparison render after completing the collision audit.
- Even spacing smooths a small part of the inherited serration, but the upper lip still reads as a hard attached strip, the lower lip has a broad white highlight band, the commissures end in spikes, and the oral cavity and teeth remain planar.
- Strict mouth quality is 31/100, below both r1040 at 36/100 and the retained r1033 candidate at 39/100. r1041 is a technical study and is forbidden from website promotion.
- Fixed-crop drift from r1039 is -0.000024% left cheek, +0.000552% right cheek and 0.0% forehead. The plus-or-minus 1% skin-tone gate passes with no global darkening.

The next pass must replace the complete perioral patch, including the philtral transition, vermilion, wetline and closed mouth-corner poles. Further deformation of these six rings cannot reach a human mouth shape.
