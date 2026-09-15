# v249 r1042 full perioral patch review

r1042 removes the complete r1039 mouth region in one operation: 232 skin faces, 480 vermilion faces and 120 inner-rim faces. It replaces them with a single 62-by-9 quad annulus whose outer seam remains welded to the body and whose inner edge exposes the owned oral layers.

- The final deterministic build adds 558 vertices and 558 quad faces. All 35 shape keys remain index-compatible, every new vertex carries at least four normalized deform groups, and the active female morph stack is inverse-baked into Basis so it does not distort the authored neutral target a second time.
- Frames 1/20/33/61 plus mouth-open and smile pass with zero non-adjacent body self-collision and zero overlap against the six oral layers.
- Broad 74-edge and tight 56/62-edge boundary studies prove that shrinking the replacement region removes nose and chin pinching. They also prove that a radial annulus cannot create production lip flow: its lower half converges into visible radial creases and a dark overhanging curtain.
- Strict mouth quality is 18/100, below r1041 at 31/100 and retained r1033 at 39/100. r1042 is retained only as topology, shape-key and collision evidence; website promotion is forbidden.
- Fixed-crop drift from r1039 is +0.007563% left cheek, +0.015895% right cheek and 0.0% forehead. The plus-or-minus 1% tone gate passes with no global darkening.

The next implementation must use separate upper and lower horizontal grids. Each grid needs loops that follow the orbicularis direction and an explicit closed pole at each commissure; the current annular route is closed.
