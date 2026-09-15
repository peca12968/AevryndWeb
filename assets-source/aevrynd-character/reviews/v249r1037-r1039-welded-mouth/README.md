# v249 r1037-r1039 welded-mouth review

This fixed-light review follows the r1036 detached-overlay rejection and keeps all new mouth surfaces welded to the body mesh.

- r1037 proves the existing three 120-vertex body rings can be reshaped safely up to strength 0.30. Strength 0.45 creates neutral and smile self-intersection. The safe result remains too open and angular for visual acceptance.
- r1038 adds three gradual 120-vertex inset support rings. All 360 new vertices preserve the 35 shape keys and receive at least four deform-weight groups. The selected b-natural-slit bound passes frames 1/20/33/61, mouth-open and smile with zero body self-collision and zero overlap against all six oral layers.
- r1039 keeps r1038 geometry byte-identical and splits 480 visible vermilion faces from the deepest 120-face oral rim. The b-natural-vermilion material removes the near-black whole-lip assignment, but the outer serration, planar lower surface, weak commissures and flat dental presentation remain unacceptable.
- Fixed-crop skin luminance drift is 0.001586% left cheek, 0.000649% right cheek and 0.0% forehead, well inside the plus-or-minus 1% gate. No global darkening is introduced.
- Strict mouth scores: r1037 27/100, r1038 30/100, r1039 34/100. These are research gains over the r1035 aperture proof, but r1033 remains the retained visual/technical face candidate at about 39/100 mouth quality.
- Website promotion remains forbidden. Website v83 remains unchanged and still carries the documented 5.56% embedded skin-base-color deficit.

The next pass must regularize the outer welded boundary without expanding across the face, rebuild upper and lower lip volume as separate curvature fields, close both commissures and replace the flat dental shapes before another promotion decision.
