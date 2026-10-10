# FURY Polyatomic Molecular Dynamics Visualization

A generic 3D visualization project built with **FURY** and **NumPy** to display multiple polyatomic molecules as rigid bodies moving through a 3D volume.

The project is designed around a **molecular-dynamics-style visualization** rather than a full molecular-dynamics physics engine. Molecules have a calculated center of mass (CM), a CM-centered local coordinate system, deterministic translational motion, and rigid-body 3D rotation. Molecular interactions, forces, energies, and collisions are intentionally out of scope for the first version.

The default demonstration uses **NH₄⁺ (ammonium)** with five atoms because it matches the original reference image and satisfies the 5+ atom requirement discussed for the project. The code is **generic**: the molecule can be replaced by changing the atom coordinates, atomic properties, and bond list in one configuration object.

Requirement:

fury==2.0.0
vtk==9.7.0
numpy==2.5.2

---

## Table of Contents

1. [Project goals](#project-goals)
2. [Current capabilities](#current-capabilities)
3. [Technology stack](#technology-stack)
4. [Environment](#environment)
5. [Project files](#project-files)
6. [Installation](#installation)
7. [Quick start](#quick-start)
8. [Command-line options](#command-line-options)
9. [Keyboard and UI controls](#keyboard-and-ui-controls)
10. [How the coordinate system works](#how-the-coordinate-system-works)
11. [Center-of-mass calculation](#center-of-mass-calculation)
12. [Rigid-body motion model](#rigid-body-motion-model)
13. [Molecule placement](#molecule-placement)
14. [Default NH₄⁺ model](#default-nh₄-model)
15. [Creating a custom molecule](#creating-a-custom-molecule)
16. [Atomic masses, radii, and colors](#atomic-masses-radii-and-colors)
17. [Changing visualization settings](#changing-visualization-settings)
18. [Changing the number of molecules](#changing-the-number-of-molecules)
19. [Output and screenshots](#output-and-screenshots)
20. [Smoke test](#smoke-test)
21. [Performance](#performance)
22. [Troubleshooting](#troubleshooting)
23. [Known limitations](#known-limitations)
24. [Scientific interpretation](#scientific-interpretation)
25. [Project architecture](#project-architecture)
26. [How to extend the project](#how-to-extend-the-project)
27. [Suggested future roadmap](#suggested-future-roadmap)
28. [Development and maintenance](#development-and-maintenance)
29. [Changelog](#changelog)
30. [License](#license)

---

## Project goals

The project has four main goals:

1. Visualize a **polyatomic molecule containing five or more atoms** in a clear 3D space-filling style.
2. Define the molecule in its own **local coordinate system**, with the **center of mass at `(0, 0, 0)`**.
3. Generate many copies of the molecule and move each copy with **translation + 3D rotation** while preserving its internal geometry.
4. Provide an interactive FURY scene that is easy to extend later toward a more complete molecular-dynamics simulation.

A major design requirement is that the molecular coordinate system must not depend on the order in which FURY actors or grouped objects are created.

---

## Current capabilities

The current implementation provides:

- Generic atom-based molecule definition.
- Arbitrary 3D atom coordinates.
- Atom masses used for center-of-mass calculation.
- Automatic centering of the molecule on its CM.
- Validation of positions, masses, radii, and bonds.
- Space-filling-style atom spheres.
- Optional cylindrical bonds.
- Automatic element-based colors.
- 3D randomized lattice placement for many molecule copies.
- Minimum-distance validation between initial molecule centers.
- 80 molecules by default for the high-fidelity scene.
- 12 molecules in preview mode.
- Deterministic trajectories using a random seed.
- Circular translational motion of molecule CMs.
- Rigid-body 3D rotation of each molecule.
- Independent phase/orientation/rotation parameters per molecule.
- Toggleable bond visibility.
- Toggleable center-of-mass markers.
- Pause/resume control.
- Reset control.
- Simulation speed control.
- PNG snapshot support.
- A one-frame offscreen smoke test.
- FURY scene and camera setup.
- On-screen FPS display through the FURY show manager.

---

## Technology stack

### Required

- **Python** 3.14.7 (current project environment)
- **FURY** 2.0.0
- **VTK** 9.7.0
- **NumPy** 2.5.2
- A working OpenGL-capable graphics environment

### Hardware used during project setup

- OS: Windows 11
- GPU: NVIDIA RTX 5060

### External libraries

The current project intentionally keeps the dependency set small. It uses:

- FURY for 3D rendering, actors, scene management, interaction, UI, and snapshots.
- NumPy for numeric arrays, vector calculations, center-of-mass calculations, and rigid transforms.
- Python standard-library modules for command-line parsing, file paths, data classes, mathematics, warnings, and environment information.

No SciPy, Matplotlib, PyQt, Tkinter, or separate graphics engine is required by the current implementation.

---

## Environment

The known working development environment is:

```text
Windows 11
Python 3.14.7
FURY 2.0.0
VTK 9.7.0
NumPy 2.5.2
NVIDIA RTX 5060
```

Before running the project on a different machine, verify the installed versions.

```powershell
python -c "import fury, vtk, numpy; print('FURY:', fury.__version__); print('VTK:', vtk.vtkVersion.GetVTKVersion()); print('NumPy:', numpy.__version__)"
python -c "import sys; print(sys.version)"
```

If your environment differs, especially the FURY version, test the smoke test before making changes to the visualization.

---

## Project files

A minimal project directory can look like this:

```text
polyatomic-project/
├── polyatomic_visualization.py
├── README.md
├── requirements.txt        # optional but recommended for reproducibility
└── output/
    └── polyatomic_snapshot.png   # created after taking a snapshot
```

### Main file

`polyatomic_visualization.py`

Contains the complete implementation: configuration, molecule definition, geometry validation, center-of-mass calculation, FURY actors, molecule placement, trajectory generation, animation, interaction, snapshots, and smoke testing.

### README

`README.md`

This document.

### requirements.txt

Recommended pinned dependency list:

```text
fury==2.0.0
vtk==9.7.0
numpy==2.5.2
```

The `output` folder is created automatically only when a snapshot is requested.

---

## Installation

If FURY is already installed and imports correctly, no additional package installation is required for the current project.

For a reproducible setup, use:

```powershell
python -m pip install "fury==2.0.0" "vtk==9.7.0" "numpy==2.5.2"
```

Or, using a requirements file:

```powershell
python -m pip install -r requirements.txt
```

Then verify:

```powershell
python -c "import fury, vtk, numpy; print('FURY:', fury.__version__); print('VTK:', vtk.vtkVersion.GetVTKVersion()); print('NumPy:', numpy.__version__)"
```

---

## Quick start

### 1. Run the smoke test first

```powershell
python polyatomic_visualization.py --smoke-test
```

The test builds a single molecule and attempts to render one offscreen frame. A successful run confirms that the core geometry and rendering path are functioning.

### 2. Run the low-complexity preview

```powershell
python polyatomic_visualization.py --preview
```

Preview mode uses:

- 12 molecules.
- Lower sphere tessellation.
- Lower bond tessellation.

This is the recommended first interactive run.

### 3. Run the standard high-fidelity scene

```powershell
python polyatomic_visualization.py
```

The default high-fidelity configuration contains **80 molecules**.

### 4. Try a custom molecule count

```powershell
python polyatomic_visualization.py --count 50
python polyatomic_visualization.py --count 100
```

The current script validates the requested count and accepts values from 1 through 200.

---

## Command-line options

The program supports the following arguments:

```text
--preview
    Use the 12-molecule preview configuration and lower geometry complexity.

--smoke-test
    Build and render one molecule offscreen, then exit.

--count N
    Override the number of molecule copies. Current valid range: 1-200.

--seed N
    Set the deterministic random seed for placement and trajectory parameters.
```

Examples:

```powershell
python polyatomic_visualization.py --preview
python polyatomic_visualization.py --count 50
python polyatomic_visualization.py --count 100 --seed 12345
python polyatomic_visualization.py --smoke-test
```

The default seed is `20261003`.

---

## Keyboard and UI controls

The interactive window provides both on-screen FURY controls and keyboard shortcuts.

| Input | Action |
|---|---|
| Mouse | FURY camera interaction, orbit, zoom, and scene inspection |
| `B` | Toggle bonds ON/OFF |
| `M` | Toggle center-of-mass markers ON/OFF |
| `P` | Pause/resume |
| `Space` | Pause/resume |
| `R` | Reset time, pause state, and simulation speed |
| `+` or `=` | Increase simulation speed |
| `-` or `_` | Decrease simulation speed |
| `S` | Save the current scene as a PNG snapshot |

The on-screen controls include:

- `Bonds: OFF/ON`
- `CM: OFF/ON`
- `Pause: OFF/ON`
- `Reset`

Bonds and CM markers start **OFF** to keep the default view close to the reference image.

---

## How the coordinate system works

The project uses a strict separation between **molecular local coordinates** and **world coordinates**.

The molecule is defined first in raw coordinates:

```text
Raw atom coordinates
        |
        v
Calculate mass-weighted center of mass
        |
        v
Subtract CM from every atom coordinate
        |
        v
Local coordinates with CM = (0, 0, 0)
        |
        v
Apply rigid-body rotation
        |
        v
Apply CM translation
        |
        v
World-space coordinates / transform
        |
        v
FURY scene
```

This is intentional. The FURY scene is the rendering layer; it is not the authoritative source of molecular coordinates.

### Why this matters

The project was motivated by a coordinate-system problem observed when grouping multiple objects in another tool: the coordinate system could be effectively reinterpreted or shifted based on the last object added to a group.

This implementation avoids that dependency by calculating and storing the molecular coordinates explicitly before the FURY group is created.

The molecule therefore has a stable local coordinate frame regardless of atom insertion order.

---

## Center-of-mass calculation

For atoms with masses `m_i` and position vectors `r_i`, the center of mass is:

```text
CM = sum(m_i * r_i) / sum(m_i)
```

In vector form:

```text
r_CM = [ Σ m_i r_i ] / [ Σ m_i ]
```

The program calculates the CM from the configured atomic masses and then centers every atom:

```text
local_position_i = raw_position_i - r_CM
```

The code then checks that the recalculated CM is numerically close to zero.

This gives the key invariant:

```text
molecule local CM ≈ (0, 0, 0)
```

The CM marker shown by the `M` control is placed at this local origin and therefore moves with the molecule as it translates and rotates.

---

## Rigid-body motion model

The molecule is treated as a **rigid body** in the first version.

That means internal distances and angles remain constant.

For a local atom position `r_local`, the world position conceptually follows:

```text
r_world(t) = R(t) * r_local + T(t)
```

where:

- `R(t)` is the 3D rotation matrix.
- `T(t)` is the position of the molecule CM in world space.

The current implementation applies this as a single 4×4 transform to the molecule group.

### Why the attached atoms do not independently orbit

A physically consistent rigid molecule cannot have each bonded atom independently orbiting its central atom like a planet while simultaneously keeping the same bond geometry.

Instead, the **whole molecule rotates**. This produces the requested moving/tumbling appearance while preserving:

- Bond lengths.
- Bond angles.
- Relative atomic positions.
- Overall molecular shape.

A later version can add vibrational motion or other internal degrees of freedom if required.

---

## Translational motion

The current molecule CM follows a circular trajectory in the XY plane.

The basic form is:

```text
x(t) = x0 + r * cos(phase + omega * t)
y(t) = y0 + r * sin(phase + omega * t)
z(t) = z0
```

Each molecule has its own:

- Orbit center.
- Orbit radius.
- Initial phase.
- Orbit angular velocity.

Because these values differ between molecules, the entire system does not move as one synchronized block.

The trajectories are deterministic for a given random seed.

---

## 3D rotation

Each molecule also receives:

- A random normalized 3D rotation axis.
- A rotation period.
- A random starting orientation.

The implementation uses an axis-angle rotation matrix generated from Rodrigues' rotation formula.

This allows different molecules to tumble around different 3D axes while retaining their internal shape.

---

## Molecule placement

The initial molecular CMs are generated from a compact 3D lattice.

The lattice is then randomized with controlled jitter.

Conceptually:

```text
Regular lattice
     |
     v
Shuffle positions
     |
     v
Add controlled random jitter
     |
     v
Check minimum pairwise distance
     |
     v
Accept positions
```

The current implementation does **not** use physical collision dynamics.

The minimum-distance check is a placement safeguard so the initial molecular cloud does not start in an obviously overlapping state.

The long-term trajectories are predetermined. Molecule-molecule interaction forces are intentionally not simulated.

---

## Default NH₄⁺ model

The default molecule has five atoms:

```text
1 × N
4 × H
```

with four N-H bonds.

The hydrogen coordinates are arranged in a tetrahedral pattern around the nitrogen.

The program calculates the CM from the atomic masses rather than assuming the nitrogen atom is the molecular origin.

That distinction matters because the nitrogen and hydrogen atoms do not have equal masses.

---

## Creating a custom molecule

The most important editable object is:

```python
MOLECULE_DEFINITION
```

The configuration uses a simple dictionary structure:

```python
MOLECULE_DEFINITION = {
    "name": "MyMolecule",
    "charge": 0,
    "atoms": [
        {
            "element": "C",
            "position": [0.0, 0.0, 0.0],
        },
        {
            "element": "H",
            "position": [1.0, 0.0, 0.0],
        },
        # Add more atoms...
    ],
    "bonds": [
        (0, 1),
        # Add more atom-index pairs...
    ],
}
```

### Atom indexing

Atoms are zero-indexed.

For example:

```text
Atom 0 = first atom in atoms[]
Atom 1 = second atom in atoms[]
Atom 2 = third atom in atoms[]
```

A bond:

```python
(0, 1)
```

means that atom 0 and atom 1 are connected.

### Required atom information

Each atom should provide:

- `element`
- `position`

For supported elements, the program can use the built-in mass, radius, and color tables.

Example:

```python
{
    "element": "O",
    "position": [1.10, 0.0, 0.0],
}
```

### Custom per-atom properties

You can also specify:

```python
{
    "element": "C",
    "position": [0.0, 0.0, 0.0],
    "mass": 12.011,
    "radius": 1.70,
    "color": "#202020",
}
```

`color` can be given as either:

- RGB floats in `[0, 1]`.
- RGB integers in `[0, 255]`.
- A `#RRGGBB` hex color string.

Example:

```python
"color": (0.2, 0.8, 0.3)
```

or:

```python
"color": "#33CC55"
```

---

## Atomic masses, radii, and colors

The file contains built-in dictionaries for common elements.

### Atomic masses

```python
ATOMIC_MASSES
```

### Approximate van-der-Waals radii

```python
ATOMIC_VDW_RADII
```

### Visual element colors

```python
ELEMENT_COLORS
```

The current style is intentionally close to the reference image: smooth spheres, strong shading, and a clean white background.

For an element already in the tables, color is selected automatically from `ELEMENT_COLORS`.

For an element not in the built-in tables, add its mass/radius/color to the corresponding dictionaries (or provide a custom visual mapping in the code before building the geometry).

---

## Changing visualization settings

The main visual parameters are near the top of `polyatomic_visualization.py`.

### Background

```python
BACKGROUND = (1.0, 1.0, 1.0, 1.0)
```

The current value is white to match the reference.

### Atom size

```python
ATOM_RADIUS_SCALE = 0.55
```

This scales the built-in atomic radii for the space-filling appearance.

Examples:

```text
0.45  -> less overlap / smaller visual atoms
0.55  -> current reference-inspired setting
0.65  -> more overlap / larger visual atoms
```

### Bond radius

```python
BOND_RADIUS = 0.075
```

Larger values produce thicker bonds.

### Sphere quality

High-fidelity mode:

```python
HIGH_PHI = 40
HIGH_THETA = 40
```

Preview mode:

```python
PREVIEW_PHI = 20
PREVIEW_THETA = 20
```

Higher tessellation usually means smoother spheres but more rendering work.

### Bond quality

High-fidelity mode uses:

```python
HIGH_BOND_SECTORS = 24
```

Preview uses:

```python
PREVIEW_BOND_SECTORS = 12
```

### Window size

```python
WINDOW_SIZE = (1200, 800)
```

Adjust as needed for your display or presentation.

---

## Changing the number of molecules

Default values:

```python
HIGH_MOLECULE_COUNT = 80
PREVIEW_MOLECULE_COUNT = 12
```

The runtime count can also be specified from the command line:

```powershell
python polyatomic_visualization.py --count 50
python polyatomic_visualization.py --count 100
```

The script currently accepts 1–200 molecules.

For a presentation, start with 12 or 50 and increase to 80/100 after confirming stable performance.

---

## Changing the motion

### Translation speed

The main periods are:

```python
ORBIT_PERIODS = (14.0, 16.0, 18.0, 20.0)
```

Smaller numbers mean faster circular motion.

### Rotation speed

```python
SPIN_PERIODS = (9.0, 11.0, 13.0, 16.0)
```

Again, smaller values mean faster rigid-body rotation.

### Orbit radius

```python
ORBIT_RADIUS_MIN = 0.22
ORBIT_RADIUS_MAX = 0.48
```

These control how much the CM moves around its orbit center.

### Random seed

```python
DEFAULT_SEED = 20261003
```

Changing the seed changes:

- Initial lattice randomization.
- Orbit phases.
- Rotation axes.
- Starting orientations.
- Orbit/spin period selection.

Keeping the same seed is useful when comparing two code changes because the starting configuration remains reproducible.

---

## Output and screenshots

The application is designed primarily as an **interactive visualization**.

The current workflow uses manual snapshots rather than automatically rendering a long animation sequence.

Press:

```text
S
```

The current scene is saved to:

```text
output/polyatomic_snapshot.png
```

The `output` directory is created automatically when the snapshot is requested.

No output file is written during normal startup unless the snapshot function is invoked.

### Saving a presentation image

A simple workflow is:

1. Start the application.
2. Orbit/zoom the camera to the desired view.
3. Turn bonds/CM markers on or off as required.
4. Pause at the desired moment if necessary.
5. Press `S`.
6. Use the generated PNG from the `output` directory.

---

## Smoke test

The project contains a built-in smoke test:

```powershell
python polyatomic_visualization.py --smoke-test
```

The test verifies three important things:

1. The molecule definition can be validated and converted into CM-centered local coordinates.
2. The FURY scene can be constructed.
3. A single offscreen frame can be rendered as a NumPy image array.

A successful result prints the environment versions and the rendered image shape.

### Minimal standalone smoke test

If you want a very small external test after installation, run:

```python
import numpy as np
from fury import window, actor

scene = window.Scene()
scene.background((1.0, 1.0, 1.0))
scene.add(
    actor.sphere(
        centers=np.array([[0.0, 0.0, 0.0]]),
        colors=np.array([[0.0, 0.6, 0.2]]),
        radii=np.array([1.0]),
        phi=12,
        theta=12,
        material="phong",
        enable_picking=False,
        smooth=True,
        wireframe=False,
        impostor=False,
    )
)

image = window.snapshot(
    scene=scene,
    fname=None,
    return_array=True,
)

assert isinstance(image, np.ndarray)
assert image.ndim == 3
assert image.shape[-1] in (3, 4)
print("Basic FURY rendering smoke test passed:", image.shape)
```

If the standalone test fails, troubleshoot the FURY/VTK rendering environment before debugging the molecular simulation logic.

---

## Performance

The target scene is 50–100 polyatomic molecule copies, with 80 as the current default high-fidelity count.

### Performance strategy used in the current version

- All atoms of a molecule are grouped into one sphere actor rather than one independent actor per atom.
- All bonds of a molecule are represented by one cylinder actor.
- One rigid transform is applied to the molecular group.
- Preview mode uses lower sphere and bond tessellation.
- Placement validation is an O(N²) distance check, which is acceptable for the current 1–200 molecule limit.

### Recommended testing order

```powershell
python polyatomic_visualization.py --smoke-test
python polyatomic_visualization.py --preview
python polyatomic_visualization.py --count 50
python polyatomic_visualization.py --count 80
python polyatomic_visualization.py --count 100
```

### If performance is lower than expected

Reduce complexity in this order:

1. Lower sphere tessellation.
2. Lower bond sector count.
3. Reduce the number of molecules.
4. Consider a later optimization using FURY sphere impostors for very large atom counts.

The current release favors visual quality and a clear demonstration over extremely large particle counts.

---

## Troubleshooting

### FURY cannot be imported

Error:

```text
ModuleNotFoundError: No module named 'fury'
```

Install the pinned version:

```powershell
python -m pip install "fury==2.0.0"
```

Make sure the `python` command you use to run the script is the same Python environment where FURY was installed.

---

### FURY version mismatch

The script checks that the installed FURY version is the expected one.

Check it with:

```powershell
python -c "import fury; print(fury.__version__)"
```

If it differs, either install the pinned version or intentionally update the code after checking the relevant FURY API changes.

---

### VTK import or rendering failure

Check:

```powershell
python -c "import vtk; print(vtk.vtkVersion.GetVTKVersion())"
```

For the project environment, the expected VTK version is:

```text
9.7.0
```

---

### The window is black or the rendering is corrupted

Possible causes include:

- NVIDIA driver problems.
- A graphics backend problem.
- An incompatible remote-desktop/session environment.
- Broken or mismatched VTK/FURY installation.

Start with:

```powershell
python polyatomic_visualization.py --smoke-test
```

Then verify the NVIDIA driver and rerun the test.

---

### Preview works but 80–100 molecules are slow

This is usually a geometry/scene complexity issue rather than a coordinate-system issue.

Try:

```powershell
python polyatomic_visualization.py --count 50
```

and reduce the high-fidelity tessellation if necessary.

---

### Bonds do not appear

Press:

```text
B
```

or click the `Bonds` toggle.

Bonds intentionally start disabled.

---

### CM markers do not appear

Press:

```text
M
```

or click the `CM` toggle.

The CM marker is intentionally hidden at startup.

---

### A custom molecule fails validation

Check:

- Every atom has a valid `element`.
- Every `position` has exactly three finite numbers.
- Every mass is positive.
- Every radius is positive.
- Every bond has exactly two integer indices.
- Bond indices are inside the atom list range.
- An atom is not bonded to itself.
- Duplicate bonds are removed.

Example valid bond list:

```python
"bonds": [
    (0, 1),
    (0, 2),
    (1, 3),
]
```

---

### A custom element is not recognized

The current built-in lookup tables contain a selected set of common elements.

Add the required element to:

```python
ATOMIC_MASSES
ATOMIC_VDW_RADII
ELEMENT_COLORS
```

before using it with the default lookup behavior.

---

### The visual molecule is too large or too small

Adjust:

```python
ATOM_RADIUS_SCALE
```

or an individual atom's `radius` value.

Remember that the reference-inspired look intentionally uses visible sphere overlap.

---

### Molecules appear too close together

The initial placement uses a conservative minimum-distance test. If you change the molecule size, atom radii, or orbit radius significantly, also revisit the spacing logic in `generate_initial_centers()`.

---

## Known limitations

The current version is a **kinematic visualization**, not a physical molecular-dynamics engine.

It does not currently implement:

- Intermolecular force fields.
- Lennard-Jones potentials.
- Coulomb/electrostatic forces.
- Bond stretching forces.
- Angle bending potentials.
- Torsional potentials.
- Energy calculation.
- Temperature/thermostat control.
- Pressure/volume control.
- Momentum-conserving particle collisions.
- Real molecular integration such as Velocity Verlet.
- Periodic boundary conditions.
- Physical collision response.
- Molecular vibration.
- Internal flexible-body motion.
- Automatic generation of molecular structures from chemical formulas.
- External molecular file parsing such as PDB/XYZ/SDF in the current script.
- Automated MP4 generation in the current interactive workflow.

These are deliberate boundaries for the first project stage.

---

## Scientific interpretation

The visualization has two different levels of correctness that should be kept separate.

### Correct and physically meaningful parts

- A mass-weighted center of mass is used.
- The molecular coordinate frame can be explicitly defined around the CM.
- A rigid-body transformation preserves internal geometry.
- Translation and rotation are mathematically represented with standard rigid transformations.
- The same local molecule can be instantiated many times without changing its internal coordinates.

### Deliberately simplified parts

- The circular trajectories are prescribed, not derived from forces.
- Rotation rates are prescribed, not calculated from torques or inertia tensors.
- Molecules do not physically interact.
- The initial spacing is a visualization-oriented clearance constraint, not a collision/force model.
- The atomic visual radii are chosen for a reference-inspired space-filling rendering and should not be treated as an exact molecular surface calculation.

Therefore, the correct description of the current project is:

> **A generic rigid-body, molecular-dynamics-style visualization implemented with FURY and NumPy.**

It should not be described as a full molecular-dynamics simulation until force integration and physical interaction models are added.

---

## Project architecture

The main implementation is split conceptually into the following layers.

```text
1. Environment verification
        |
        v
2. User molecule definition
        |
        v
3. Molecule validation
        |
        v
4. Center-of-mass calculation
        |
        v
5. CM-centered local coordinates
        |
        v
6. FURY molecule geometry
   - atom spheres
   - bond cylinders
   - CM marker
        |
        v
7. Molecule instance generation
   - initial CM positions
   - orbit parameters
   - spin parameters
        |
        v
8. Rigid transformation
   R(t) + T(t)
        |
        v
9. FURY scene / camera / UI
        |
        v
10. Animation callback
        |
        v
11. Interactive rendering
```

### Main functions/classes

#### `validate_molecule_definition()`

Checks input data before rendering.

#### `build_geometry()`

Calculates the molecular CM and converts raw coordinates into a CM-centered local representation.

#### `make_bond_geometry()`

Converts atom-pair connections into cylinder centers, lengths, and directions.

#### `make_molecule_group()`

Creates the FURY representation of one molecule.

#### `generate_initial_centers()`

Creates the 3D starting positions and checks minimum distance.

#### `build_states()`

Creates independent trajectory/rotation state for every molecular copy.

#### `rigid_transform()`

Builds the transformation applied to each molecule.

#### `MolecularSimulation`

Owns the FURY scene, camera, UI, animation, controls, and snapshot behavior.

#### `smoke_test()`

Builds and renders one frame offscreen for environment verification.

---

## How to extend the project

The safest way to add features is to preserve the existing separation between **molecule-local data**, **molecule state**, and **world rendering**.

### Add labels

A future label system could show:

- Molecule ID.
- Element symbols.
- Current CM coordinates.
- Velocity.
- Rotation axis.

Labels that belong to the molecule should live in the molecule's coordinate system.

### Add CM trajectory trails

A trail can store previous world-space CM positions:

```text
CM(t0)
  |
CM(t1)
  |
CM(t2)
  |
CM(t3)
```

This would make circular motion visually obvious.

### Add coordinate axes

A selected molecule could display a local XYZ frame whose orientation follows the rigid-body rotation.

This would provide a very clear demonstration that:

```text
local molecule coordinates
        +
rigid-body rotation
        =
world orientation
```

### Add molecule selection

FURY picking could later allow the user to select one molecule and display its:

- CM.
- Velocity.
- Angular velocity.
- Local axes.
- Identifier.

### Add true molecular dynamics later

The next major step would be to replace prescribed motion with a state containing physical values such as:

```text
position
velocity
orientation
angular velocity
mass
moment of inertia
```

and integrate those states over time.

That would be a substantial change and should be developed separately from the current rendering layer.

---

## Suggested future roadmap

### Phase 1 — Current

- Generic polyatomic molecule.
- CM-centered coordinate system.
- Rigid translation.
- Rigid rotation.
- Multiple molecules.
- Interactive visualization.

### Phase 2 — Visualization improvements

- Molecule labels.
- Velocity vectors.
- CM trajectory trails.
- Local coordinate axes.
- Selected-molecule inspection.
- Better UI panels.
- Mixture of grid + controlled randomness.

### Phase 3 — Physical motion

- Velocity Verlet or another integrator.
- Intermolecular collisions.
- Simplified repulsive/attractive potentials.
- Configurable time step.
- Velocity and angular velocity state.
- Basic conservation checks.

### Phase 4 — Molecular simulation features

- Lennard-Jones interactions.
- Coulomb interactions where appropriate.
- Temperature control.
- Periodic boundaries.
- Energy visualization.
- Simulation statistics.

### Phase 5 — Advanced molecular data

- XYZ/PDB/SDF loading.
- Molecular structure import.
- Multiple molecule species.
- Real simulation-result playback.
- Frame/trajectory import.

---

## Development and maintenance

### Recommended workflow

Before changing the visualization:

```powershell
python polyatomic_visualization.py --smoke-test
```

After making a small change:

```powershell
python polyatomic_visualization.py --preview
```

Only then move back to:

```powershell
python polyatomic_visualization.py
```

### Keep the random seed stable during development

A fixed seed makes it easier to tell whether a code change affected the simulation or whether the scene simply received a different random configuration.

### Keep the local coordinate system authoritative

When adding new features, do not redefine the molecular origin from FURY actor insertion order. Compute all molecule-local coordinates from the molecule data first.

### Keep geometry and motion separate

The geometry layer should define:

```text
atoms
masses
radii
colors
bonds
local coordinates
```

The motion layer should define:

```text
CM trajectory
rotation
velocity
angular velocity
```

The rendering layer should convert those values into FURY state.

This separation will make future physics additions much easier.

---

## Reproducibility

The current project is deterministic for a fixed:

- Molecule definition.
- Molecule count.
- Random seed.
- FURY/VTK/NumPy environment.

For reproducible demonstrations, keep the following fixed:

```text
FURY version
VTK version
NumPy version
Python version
seed
molecule definition
visual parameters
```

---

## Changelog

### 0.1.0 — Initial project

- Generic polyatomic molecule definition.
- Five-atom NH₄⁺ reference demonstration.
- Automatic mass-weighted CM calculation.
- CM-centered local coordinates.
- Rigid-body 3D rotation.
- Circular translational motion.
- Multiple molecule instancing.
- Jittered 3D lattice placement.
- Minimum-distance validation.
- Space-filling atom spheres.
- Optional cylindrical bonds.
- Automatic element colors.
- CM visualization toggle.
- Bond visualization toggle.
- Pause/resume control.
- Reset control.
- Simulation speed control.
- PNG snapshots.
- Offscreen smoke test.
- FURY scene/camera/UI integration.

### Changelog template for future releases

```text
## X.Y.Z — YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...

### Performance
- ...

### Compatibility
- Python: ...
- FURY: ...
- VTK: ...
- NumPy: ...
```

When upgrading FURY, VTK, or NumPy, run the smoke test first and document the new versions here.

---

## License

No license has been assigned in the current project.

If this project is going to be shared publicly, choose an appropriate license and add the corresponding license text and copyright information.

---

## Project summary

This project is a **generic, CM-centered, rigid-body polyatomic molecular visualization** built with FURY.

The core concept is:

```text
Molecule definition
      ↓
Atomic masses + coordinates
      ↓
Center of mass
      ↓
Local CM = (0,0,0)
      ↓
Rigid-body rotation
      ↓
Circular CM translation
      ↓
Many independent molecule instances
      ↓
FURY interactive 3D visualization
```

The architecture is intentionally designed so the molecular coordinate system remains stable and independent of object/group insertion order. That provides a clean foundation for later additions such as trajectory trails, molecule selection, multiple species, collision handling, and eventually full molecular-dynamics physics.
