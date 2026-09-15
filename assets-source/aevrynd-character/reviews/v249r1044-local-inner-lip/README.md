# v249 r1044 local inner-lip review

r1044 returns to retained r1033 and limits the opening to a 20-by-0.8 mm inner-lip band. It preserves the outer face, adds three attached 36-vertex support rings and rebuilds six explicitly named Aevrynd-owned oral layers.

- The deterministic build removes 20 main faces, four residual candidate faces and 326 hidden faces; it adds 108 weighted vertices and 108 faces. All 35 shape keys remain compatible and every new vertex carries at least five deform groups.
- Frames 1/20/33/61 plus mouth-open and smile pass with zero non-adjacent body self-collision and zero body-to-oral-layer overlap.
- Strict mouth quality is 30/100, below retained r1033 at 39/100. The stable outer lip survives, but inherited folded faces from the main head component remain visible through the slit. Ray-guided deletion exposes deeper fragments and material reassignment creates hanging tabs, so both diagnostics are rejected.
- Fixed-crop drift from r1033 is -0.000398% left cheek, -0.000708% right cheek and +0.000000% forehead. The plus-or-minus 1% tone gate passes.
- Website promotion is forbidden. r1033 remains the retained mouth and face candidate.

The next mouth build must start from a clean contiguous oral vestibule with explicit upper and lower inner-lip paths, then transfer the retained r1033 outer facial surface onto it. Excavating or recoloring the inherited folded head is closed.
