# Native KiCad project directory

This directory is reserved for the native schematic and PCB files. At the time of this commit, it intentionally contains no fabricated placeholder CAD.

Expected project deliverables once the circuit is engineered and verified:

- A native KiCad project and schematic.
- A native PCB layout with footprints and routing.
- Any required local symbol/footprint libraries and 3D model references.
- ERC and DRC reports with unresolved findings documented.
- CAD-derived assembled and exploded 3D views.
- Gerber copper/mask/silkscreen/outline layers and drill files.
- Assembly drawing and pick-and-place data when the design is released for assembly.

Do not treat a PDF drawing, draft connection table, illustrative render or this directory as a manufacturing package. The exact modem, power source, sensor interface and installation requirements must be confirmed before the schematic and layout can be frozen.

The GitHub Actions workflow in the repository will detect native KiCad files and attempt CLI exports when they are added. A successful workflow is only a software-file check; it does not replace electrical review, bench testing, RF validation, safety assessment or regulatory approval.
