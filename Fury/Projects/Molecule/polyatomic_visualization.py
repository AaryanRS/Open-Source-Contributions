from __future__ import annotations

"""Generic polyatomic molecular-dynamics-style visualization using FURY 2.0.0.

Default demo: NH4+ (5 atoms) rendered in a space-filling style close to the
reference image. 80 rigid molecules are placed on a jittered 3-D lattice.
Each molecule's CM follows a deterministic circular trajectory while the
whole molecule rotates as one rigid body.

Run:
    python polyatomic_visualization.py --preview
    python polyatomic_visualization.py
    python polyatomic_visualization.py --smoke-test
    python polyatomic_visualization.py --count 50

Keyboard:
    B = bonds ON/OFF
    M = center-of-mass markers ON/OFF
    P or SPACE = pause/resume
    R = reset time/speed
    + / - = change simulation speed
    S = save a PNG snapshot to ./output/polyatomic_snapshot.png

Important: this is a kinematic, molecular-dynamics-style visualization. It is
NOT a force/energy molecular-dynamics solver; molecular interaction physics is
intentionally left out for this first version.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path
import math
import sys
import warnings

import numpy as np

try:
    import fury
    from fury import actor, window
    from fury.lib import EventType
    from fury.ui import TextButton2D
except ImportError as exc:
    raise SystemExit(
        "FURY import failed. Install the pinned version with:\n"
        '  python -m pip install "fury==2.0.0"\n'
        f"Original error: {exc}"
    ) from exc


# =============================================================================
# 1. Configuration / visual style
# =============================================================================

FURY_REQUIRED = "2.0.0"
WINDOW_SIZE = (1200, 800)
BACKGROUND = (1.0, 1.0, 1.0, 1.0)  # white reference-style background
MAX_FPS = 60
UPDATE_INTERVAL = 1.0 / 60.0

# Radii are derived from approximate van-der-Waals radii and scaled so the
# spheres overlap visibly, matching the reference's space-filling look.
ATOM_RADIUS_SCALE = 0.55
BOND_RADIUS = 0.075

# High fidelity = smooth polygon spheres; preview reduces tessellation.
HIGH_PHI, HIGH_THETA, HIGH_BOND_SECTORS = 40, 40, 24
PREVIEW_PHI, PREVIEW_THETA, PREVIEW_BOND_SECTORS = 20, 20, 12

DEFAULT_SEED = 20261003
HIGH_MOLECULE_COUNT = 80
PREVIEW_MOLECULE_COUNT = 12

# Circular CM trajectories. Periods are long enough to make motion readable.
ORBIT_RADIUS_MIN, ORBIT_RADIUS_MAX = 0.22, 0.48
ORBIT_PERIODS = (14.0, 16.0, 18.0, 20.0)
SPIN_PERIODS = (9.0, 11.0, 13.0, 16.0)
BASE_ROTATION_MAX_DEG = 180.0

ATOMIC_MASSES = {
    "H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999,
    "F": 18.998, "P": 30.974, "S": 32.06, "Cl": 35.45,
    "Br": 79.904, "I": 126.904, "Na": 22.990, "Mg": 24.305,
    "K": 39.098, "Ca": 40.078,
}
ATOMIC_VDW_RADII = {
    "H": 1.20, "C": 1.70, "N": 1.55, "O": 1.52,
    "F": 1.47, "P": 1.80, "S": 1.80, "Cl": 1.75,
    "Br": 1.85, "I": 1.98, "Na": 2.27, "Mg": 1.73,
    "K": 2.75, "Ca": 2.31,
}
# Reference-inspired colors. Values are RGB floats in [0, 1].
ELEMENT_COLORS = {
    "H": (0.92, 0.92, 0.92),
    "C": (0.18, 0.18, 0.18),
    "N": (0.05, 0.55, 0.18),
    "O": (0.85, 0.10, 0.08),
    "F": (0.55, 0.85, 0.35),
    "P": (1.00, 0.55, 0.10),
    "S": (0.92, 0.78, 0.10),
    "Cl": (0.15, 0.70, 0.20),
    "Br": (0.55, 0.15, 0.08),
    "I": (0.35, 0.15, 0.65),
    "Na": (0.10, 0.35, 0.95),
    "Mg": (0.30, 0.75, 0.85),
    "K": (0.55, 0.10, 0.75),
    "Ca": (0.25, 0.80, 0.85),
}


# =============================================================================
# 2. User-editable generic molecule definition
# =============================================================================


def make_nh4_demo() -> dict:
    """Create a 5-atom tetrahedral NH4+ example.

    Positions are arbitrary local coordinates. The program will calculate the
    mass-weighted CM and translate all positions so CM becomes [0, 0, 0].
    """
    tetra = np.array(
        [[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]],
        dtype=np.float64,
    )
    tetra /= np.linalg.norm(tetra[0])
    bond_length = 1.04
    p = np.vstack(([0.0, 0.0, 0.0], bond_length * tetra))
    return {
        "name": "NH4+",
        "charge": +1,
        "atoms": [
            {"element": "N", "position": p[0].tolist()},
            {"element": "H", "position": p[1].tolist()},
            {"element": "H", "position": p[2].tolist()},
            {"element": "H", "position": p[3].tolist()},
            {"element": "H", "position": p[4].tolist()},
        ],
        "bonds": [(0, 1), (0, 2), (0, 3), (0, 4)],
    }


# Change only this object to use another polyatomic molecule.
MOLECULE_DEFINITION = make_nh4_demo()


@dataclass(frozen=True)
class MoleculeGeometry:
    name: str
    local_positions: np.ndarray
    masses: np.ndarray
    radii: np.ndarray
    colors: np.ndarray
    bonds: tuple[tuple[int, int], ...]
    raw_center_of_mass: np.ndarray
    bound_radius: float


@dataclass
class MoleculeState:
    group: object
    bond_actor: object
    cm_actor: object
    orbit_center: np.ndarray
    orbit_radius: float
    orbit_phase: float
    orbit_omega: float
    spin_axis: np.ndarray
    spin_omega: float
    base_rotation: np.ndarray


def normalize(v: np.ndarray) -> np.ndarray:
    """Normalize a vector and fail clearly for a zero vector."""
    norm = float(np.linalg.norm(v))
    if norm <= 1e-12:
        raise ValueError("Cannot normalize a near-zero vector.")
    return v / norm


def axis_angle_matrix(axis: np.ndarray, angle: float) -> np.ndarray:
    """Return a 3x3 Rodrigues rotation matrix."""
    x, y, z = normalize(np.asarray(axis, dtype=np.float64))
    c, s = math.cos(angle), math.sin(angle)
    k = 1.0 - c
    return np.array([
        [c + x*x*k, x*y*k - z*s, x*z*k + y*s],
        [y*x*k + z*s, c + y*y*k, y*z*k - x*s],
        [z*x*k - y*s, z*y*k + x*s, c + z*z*k],
    ], dtype=np.float64)


def random_rotation(rng: np.random.Generator, max_angle_deg: float) -> np.ndarray:
    axis = normalize(rng.normal(size=3))
    angle = math.radians(float(rng.uniform(-max_angle_deg, max_angle_deg)))
    return axis_angle_matrix(axis, angle)


def color_to_rgb(value, element: str) -> tuple[float, float, float]:
    """Resolve a custom RGB tuple or '#RRGGBB' string into FURY RGB floats."""
    if isinstance(value, str):
        if len(value) != 7 or not value.startswith("#"):
            raise ValueError(f"Invalid color {value!r} for element {element}; use #RRGGBB.")
        try:
            return tuple(int(value[i:i+2], 16) / 255.0 for i in (1, 3, 5))
        except ValueError as exc:
            raise ValueError(f"Invalid hex color {value!r} for element {element}.") from exc

    arr = np.asarray(value, dtype=np.float64)
    if arr.shape != (3,) or not np.all(np.isfinite(arr)):
        raise ValueError(f"Color for {element} must contain exactly 3 finite values.")
    if np.max(arr) > 1.0:
        arr = arr / 255.0
    if np.any(arr < 0.0) or np.any(arr > 1.0):
        raise ValueError(f"Color for {element} must be RGB in [0,1] or [0,255].")
    return tuple(float(x) for x in arr)


# =============================================================================
# 3. Geometry validation + CM calculation
# =============================================================================


def validate_molecule_definition(definition: dict) -> None:
    if not isinstance(definition, dict):
        raise TypeError("MOLECULE_DEFINITION must be a dictionary.")
    atoms = definition.get("atoms")
    bonds = definition.get("bonds", [])
    if not isinstance(atoms, list) or not atoms:
        raise ValueError("MOLECULE_DEFINITION['atoms'] must be a non-empty list.")
    if len(atoms) < 5:
        warnings.warn("The mentor target is a 5+ atom polyatomic molecule.")
    if not isinstance(bonds, list):
        raise TypeError("MOLECULE_DEFINITION['bonds'] must be a list of (i, j) pairs.")

    n = len(atoms)
    seen_bonds = set()
    for i, a in enumerate(atoms):
        if not isinstance(a, dict):
            raise TypeError(f"Atom {i} must be a dictionary.")
        element = a.get("element")
        if not isinstance(element, str) or not element.strip():
            raise ValueError(f"Atom {i} needs a non-empty 'element'.")
        pos = np.asarray(a.get("position"), dtype=np.float64)
        if pos.shape != (3,) or not np.all(np.isfinite(pos)):
            raise ValueError(f"Atom {i} position must be a finite 3-vector.")
        mass = float(a.get("mass", ATOMIC_MASSES.get(element, 0.0)))
        radius = float(a.get("radius", ATOMIC_VDW_RADII.get(element, 0.0)))
        if mass <= 0:
            raise ValueError(f"Atom {i} ({element}) has no positive mass; supply 'mass'.")
        if radius <= 0:
            raise ValueError(f"Atom {i} ({element}) has no positive radius; supply 'radius'.")
        color_to_rgb(a.get("color", ELEMENT_COLORS.get(element, (0.6, 0.6, 0.6))), element)

    for pair in bonds:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError(f"Invalid bond {pair!r}; use (i, j).")
        i, j = pair
        if not isinstance(i, int) or not isinstance(j, int):
            raise TypeError(f"Bond {pair!r} indices must be integers.")
        if not (0 <= i < n and 0 <= j < n):
            raise IndexError(f"Bond {pair!r} is outside atom range 0..{n-1}.")
        if i == j:
            raise ValueError(f"Bond {pair!r} connects an atom to itself.")
        key = tuple(sorted((i, j)))
        if key in seen_bonds:
            raise ValueError(f"Duplicate bond detected: {pair!r}.")
        seen_bonds.add(key)


def build_geometry(definition: dict) -> MoleculeGeometry:
    """Resolve defaults, calculate CM, and create CM-centered local coordinates."""
    validate_molecule_definition(definition)
    atoms = definition["atoms"]
    raw_positions = np.asarray([a["position"] for a in atoms], dtype=np.float64)
    masses = np.asarray([
        float(a.get("mass", ATOMIC_MASSES[a["element"]])) for a in atoms
    ], dtype=np.float64)
    radii = np.asarray([
        float(a.get("radius", ATOMIC_VDW_RADII[a["element"]])) * ATOM_RADIUS_SCALE
        for a in atoms
    ], dtype=np.float64)
    colors = np.asarray([
        color_to_rgb(a.get("color", ELEMENT_COLORS.get(a["element"], (0.6, 0.6, 0.6))), a["element"])
        for a in atoms
    ], dtype=np.float32)

    total_mass = float(masses.sum())
    raw_cm = (raw_positions * masses[:, None]).sum(axis=0) / total_mass
    local_positions = raw_positions - raw_cm

    # This is the critical coordinate-system invariant for the project.
    centered_cm = (local_positions * masses[:, None]).sum(axis=0) / total_mass
    if not np.allclose(centered_cm, 0.0, atol=1e-10):
        raise RuntimeError(f"CM centering failed: computed local CM={centered_cm}.")

    # Conservative spherical bound used to keep molecule centers separated.
    bound_radius = float(np.max(np.linalg.norm(local_positions, axis=1) + radii))
    bonds = tuple((int(i), int(j)) for i, j in definition.get("bonds", []))
    return MoleculeGeometry(
        name=str(definition.get("name", "Polyatomic molecule")),
        local_positions=local_positions,
        masses=masses,
        radii=radii,
        colors=colors,
        bonds=bonds,
        raw_center_of_mass=raw_cm,
        bound_radius=bound_radius,
    )


# =============================================================================
# 4. Molecule placement + FURY actors
# =============================================================================


def lattice_dimensions(n: int) -> tuple[int, int, int]:
    nx = int(math.ceil(n ** (1.0 / 3.0)))
    ny = int(math.ceil(math.sqrt(n / nx)))
    nz = int(math.ceil(n / (nx * ny)))
    return nx, ny, nz


def generate_initial_centers(count: int, bound_radius: float, seed: int):
    """Create a jittered 3-D lattice and explicitly verify center separation."""
    if count < 1:
        raise ValueError("Molecule count must be at least 1.")

    # Bound + orbit radius + safety margin prevents obvious visual overlap.
    safety = 0.65
    min_distance = 2.0 * bound_radius + 2.0 * ORBIT_RADIUS_MAX + safety
    jitter = 0.45
    spacing = max(4.6, min_distance + 2.0 * jitter + 0.10)

    nx, ny, nz = lattice_dimensions(count)
    xs = (np.arange(nx) - (nx - 1) / 2.0) * spacing
    ys = (np.arange(ny) - (ny - 1) / 2.0) * spacing
    zs = (np.arange(nz) - (nz - 1) / 2.0) * spacing
    grid = np.array([(x, y, z) for z in zs for y in ys for x in xs], dtype=np.float64)

    rng = np.random.default_rng(seed)
    rng.shuffle(grid)
    centers = grid[:count].copy()
    centers += rng.uniform(-jitter, jitter, size=centers.shape)

    min_found = math.inf
    for i in range(count):
        d = np.linalg.norm(centers[i + 1:] - centers[i], axis=1)
        if d.size:
            min_found = min(min_found, float(d.min()))
    if count > 1 and min_found < min_distance:
        raise RuntimeError(
            f"Initial centers violate minimum distance: required {min_distance:.3f}, "
            f"found {min_found:.3f}. Increase lattice spacing or reduce jitter."
        )
    return centers, min_distance


def make_bond_geometry(
    positions: np.ndarray, bonds: tuple[tuple[int, int], ...]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    centers, heights, directions = [], [], []
    for i, j in bonds:
        a, b = positions[i], positions[j]
        v = b - a
        length = float(np.linalg.norm(v))
        if length <= 1e-12:
            raise ValueError(f"Bond ({i}, {j}) has zero length.")
        centers.append((a + b) / 2.0)
        heights.append(length)
        directions.append(v / length)
    if not centers:
        return np.empty((0, 3)), np.empty((0,)), np.empty((0, 3))
    return np.asarray(centers), np.asarray(heights), np.asarray(directions)


def make_molecule_group(geometry: MoleculeGeometry, phi: int, theta: int, sectors: int):
    """Create one rigid FURY group: spheres + bonds + optional CM marker."""
    group = actor.Group(name="PolyatomicMolecule")

    # One sphere actor contains all atoms in this molecule. Phong + smooth keeps
    # the reference's shaded, rounded appearance without per-atom actor spam.
    spheres = actor.sphere(
        centers=geometry.local_positions,
        colors=geometry.colors,
        radii=geometry.radii,
        phi=phi,
        theta=theta,
        material="phong",
        enable_picking=False,
        smooth=True,
        wireframe=False,
        impostor=False,
    )
    group.add(spheres)

    bond_centers, bond_heights, bond_dirs = make_bond_geometry(
        geometry.local_positions, geometry.bonds
    )
    if len(bond_centers):
        bonds = actor.cylinder(
            centers=bond_centers,
            colors=(0.22, 0.22, 0.22),
            height=bond_heights,
            sectors=sectors,
            radii=BOND_RADIUS,
            directions=bond_dirs,
            capped=True,
            material="phong",
            enable_picking=False,
            wireframe=False,
        )
    else:
        bonds = actor.Group(name="NoBonds")
    bonds.visible = False
    group.add(bonds)

    # Marker is intentionally just outside the largest sphere so CM remains
    # visible in the overlapping space-filling representation.
    cm_radius = max(float(geometry.radii.max()) * 1.20, 0.35)
    cm = actor.sphere(
        centers=np.zeros((1, 3)),
        colors=(1.0, 0.72, 0.0),
        radii=cm_radius,
        phi=max(20, phi // 2),
        theta=max(20, theta // 2),
        material="phong",
        enable_picking=False,
        smooth=True,
        wireframe=True,
        wireframe_thickness=2.0,
        impostor=False,
    )
    cm.visible = False
    group.add(cm)
    return group, bonds, cm


def build_states(geometry: MoleculeGeometry, count: int, seed: int, preview: bool):
    centers, min_distance = generate_initial_centers(count, geometry.bound_radius, seed)
    phi = PREVIEW_PHI if preview else HIGH_PHI
    theta = PREVIEW_THETA if preview else HIGH_THETA
    sectors = PREVIEW_BOND_SECTORS if preview else HIGH_BOND_SECTORS

    rng = np.random.default_rng(seed + 101)
    states = []
    for idx in range(count):
        group, bonds, cm = make_molecule_group(geometry, phi, theta, sectors)
        orbit_radius = float(rng.uniform(ORBIT_RADIUS_MIN, ORBIT_RADIUS_MAX))
        phase = float(rng.uniform(0.0, 2.0 * math.pi))
        orbit_period = float(rng.choice(ORBIT_PERIODS))
        spin_period = float(rng.choice(SPIN_PERIODS))
        spin_axis = normalize(rng.normal(size=3))
        base_rotation = random_rotation(rng, BASE_ROTATION_MAX_DEG)

        # Choose orbit_center so the requested initial center is exactly the CM.
        initial_offset = orbit_radius * np.array(
            [math.cos(phase), math.sin(phase), 0.0], dtype=np.float64
        )
        orbit_center = centers[idx] - initial_offset

        states.append(MoleculeState(
            group=group,
            bond_actor=bonds,
            cm_actor=cm,
            orbit_center=orbit_center,
            orbit_radius=orbit_radius,
            orbit_phase=phase,
            orbit_omega=2.0 * math.pi / orbit_period,
            spin_axis=spin_axis,
            spin_omega=2.0 * math.pi / spin_period,
            base_rotation=base_rotation,
        ))
    return states, centers, min_distance


def rigid_transform(state: MoleculeState, time_s: float) -> np.ndarray:
    """Return the world transform T(t) and R(t) for one rigid molecule."""
    phase = state.orbit_phase + state.orbit_omega * time_s
    translation = state.orbit_center + state.orbit_radius * np.array(
        [math.cos(phase), math.sin(phase), 0.0], dtype=np.float64
    )
    dynamic_rotation = axis_angle_matrix(state.spin_axis, state.spin_omega * time_s)
    rotation = dynamic_rotation @ state.base_rotation

    transform = np.eye(4, dtype=np.float32)
    transform[:3, :3] = rotation.astype(np.float32)
    transform[:3, 3] = translation.astype(np.float32)
    return transform


# =============================================================================
# 5. Interactive FURY simulation
# =============================================================================


class MolecularSimulation:
    def __init__(self, definition: dict, count: int, seed: int, preview: bool):
        self.geometry = build_geometry(definition)
        self.count, self.seed, self.preview = count, seed, preview
        self.time_s = 0.0
        self.time_scale = 1.0
        self.paused = False
        self.bonds_visible = False
        self.cm_visible = False

        self.states, self.initial_centers, self.min_distance = build_states(
            self.geometry, count, seed, preview
        )

        # All children are defined in molecule-local CM coordinates. FURY sees
        # the explicit rigid transform below; it never becomes the coordinate
        # authority for the molecule geometry.
        self.scene = window.Scene(background=BACKGROUND)
        for state in self.states:
            self.scene.add(state.group)

        self.show_manager = window.ShowManager(
            scene=self.scene,
            size=WINDOW_SIZE,
            title="FURY Polyatomic Molecular Dynamics",
            window_type="default",
            camera_light=True,
            enable_events=True,
            show_fps=True,
            max_fps=MAX_FPS,
        )
        self._configure_camera()
        self._build_ui()
        self._register_events()
        self._apply_visibility()
        self._update_transforms(0.0)

    def _configure_camera(self):
        screen = self.show_manager.screens[0]
        camera = screen.camera
        extent = float(np.max(np.abs(self.initial_centers)))
        extent += self.geometry.bound_radius + ORBIT_RADIUS_MAX
        scale = max(extent, 2.5)
        camera.local.position = (0.0, -2.10 * scale, 1.60 * scale)
        camera.look_at((0.0, 0.0, 0.0))
        self.show_manager.show_axes_gizmo(size=50, position=(70, 70))

    def _button_states(self, off_text: str, on_text: str):
        return {
            "default": {"text": off_text, "color": (0.92, 0.92, 0.92)},
            "hover": {"text": off_text, "color": (0.80, 0.90, 0.80)},
            "pressed": {"text": on_text, "color": (0.62, 0.82, 0.62)},
        }

    def _build_ui(self):
        self.bonds_button = TextButton2D(
            "Bonds: OFF", states=self._button_states("Bonds: OFF", "Bonds: ON"),
            position=(20, 20), size=(135, 42), font_size=18, is_toggle=True,
        )
        self.cm_button = TextButton2D(
            "CM: OFF", states=self._button_states("CM: OFF", "CM: ON"),
            position=(165, 20), size=(115, 42), font_size=18, is_toggle=True,
        )
        self.pause_button = TextButton2D(
            "Pause: OFF",
            states={
                "default": {"text": "Pause: OFF", "color": (0.92, 0.92, 0.92)},
                "hover": {"text": "Pause: OFF", "color": (0.92, 0.86, 0.70)},
                "pressed": {"text": "Pause: ON", "color": (0.95, 0.75, 0.45)},
            },
            position=(290, 20), size=(125, 42), font_size=18, is_toggle=True,
        )
        self.reset_button = TextButton2D(
            "Reset",
            states={
                "default": {"text": "Reset", "color": (0.92, 0.92, 0.92)},
                "hover": {"text": "Reset", "color": (0.80, 0.80, 0.90)},
                "pressed": {"text": "Reset", "color": (0.70, 0.70, 0.85)},
            },
            position=(425, 20), size=(95, 42), font_size=18, is_toggle=False,
        )
        self.scene.add(self.bonds_button, self.cm_button, self.pause_button, self.reset_button)
        self.bonds_button.on_clicked = self._on_bonds_clicked
        self.cm_button.on_clicked = self._on_cm_clicked
        self.pause_button.on_clicked = self._on_pause_clicked
        self.reset_button.on_clicked = self._on_reset_clicked

    def _register_events(self):
        self.show_manager.renderer.add_event_handler(self._on_key_down, EventType.KEY_DOWN)
        self.show_manager.register_callback(
            self._tick, UPDATE_INTERVAL, True, "PolyatomicSimulationLoop"
        )

    def _on_bonds_clicked(self, button):
        self.bonds_visible = bool(button.toggled)
        self._apply_visibility()

    def _on_cm_clicked(self, button):
        self.cm_visible = bool(button.toggled)
        self._apply_visibility()

    def _on_pause_clicked(self, button):
        self.paused = bool(button.toggled)

    def _on_reset_clicked(self, _button):
        self.reset()

    def _on_key_down(self, event):
        key = str(getattr(event, "key", "")).strip().lower()
        if key in {"space", "p"}:
            self.paused = not self.paused
            self.pause_button.toggled = self.paused
        elif key == "b":
            self.bonds_visible = not self.bonds_visible
            self.bonds_button.toggled = self.bonds_visible
        elif key == "m":
            self.cm_visible = not self.cm_visible
            self.cm_button.toggled = self.cm_visible
        elif key == "r":
            self.reset()
        elif key in {"+", "=", "add"}:
            self.time_scale = min(4.0, self.time_scale * 1.25)
        elif key in {"-", "_", "subtract"}:
            self.time_scale = max(0.10, self.time_scale / 1.25)
        elif key == "s":
            self.save_snapshot()
        self._apply_visibility()

    def _apply_visibility(self):
        for state in self.states:
            state.bond_actor.visible = self.bonds_visible
            state.cm_actor.visible = self.cm_visible

    def _update_transforms(self, time_s: float):
        for state in self.states:
            # One rigid 4x4 transform is applied to the molecule Group. This
            # preserves every atom/bond's relative coordinates exactly.
            state.group.transform(rigid_transform(state, time_s))

    def _tick(self):
        if not self.paused:
            self.time_s += UPDATE_INTERVAL * self.time_scale
        self._update_transforms(self.time_s)

    def reset(self):
        self.time_s = 0.0
        self.time_scale = 1.0
        self.paused = False
        self.pause_button.toggled = False
        self._update_transforms(0.0)
        self._apply_visibility()

    def save_snapshot(self):
        # Disk output happens only after the user explicitly presses S.
        out_dir = Path("output")
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "polyatomic_snapshot.png"
        self.show_manager.snapshot(fname=str(path))
        print(f"Snapshot saved to: {path.resolve()}")

    def start(self):
        charge = self.geometry.name
        if "charge" in MOLECULE_DEFINITION:
            charge = f"{charge}, charge={MOLECULE_DEFINITION['charge']:+g}"
        print("\nFURY polyatomic visualization started.")
        print(f"Molecule: {charge}")
        print(f"Atoms per molecule: {len(self.geometry.local_positions)}")
        print(f"Molecules: {self.count}")
        print(f"Raw CM: {self.geometry.raw_center_of_mass}")
        print("Local CM after centering: [0.0, 0.0, 0.0]")
        print(f"Initial CM minimum-distance threshold: {self.min_distance:.3f}")
        print("\nMouse: FURY camera controls / orbit / zoom")
        print("B bonds | M CM | P/Space pause | R reset | +/- speed | S snapshot")
        self.show_manager.start()


# =============================================================================
# 6. Smoke test + environment verification
# =============================================================================


def verify_environment():
    actual = getattr(fury, "__version__", "unknown")
    if actual != FURY_REQUIRED:
        raise RuntimeError(
            f"This script targets FURY {FURY_REQUIRED}, but found {actual}. "
            "Install the pinned version or adjust the code after checking FURY docs."
        )
    try:
        import vtk
    except ImportError as exc:
        raise RuntimeError("VTK import failed even though FURY imported successfully.") from exc
    print(
        f"Environment: Python {sys.version.split()[0]} | FURY {actual} | "
        f"VTK {vtk.vtkVersion.GetVTKVersion()} | NumPy {np.__version__}"
    )


def smoke_test():
    """Build one small molecule and render exactly one offscreen frame."""
    geometry = build_geometry(MOLECULE_DEFINITION)
    scene = window.Scene(background=BACKGROUND)
    group, _, _ = make_molecule_group(geometry, phi=12, theta=12, sectors=8)
    scene.add(group)
    group.transform(np.eye(4, dtype=np.float32))
    image = window.snapshot(scene=scene, fname=None, return_array=True)
    if not isinstance(image, np.ndarray) or image.ndim != 3 or image.shape[-1] not in (3, 4):
        raise RuntimeError(
            f"Smoke test returned unexpected frame: type={type(image)}, "
            f"shape={getattr(image, 'shape', None)}"
        )
    print(f"Smoke test passed. Rendered frame shape: {image.shape}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FURY polyatomic molecular visualization")
    parser.add_argument("--preview", action="store_true", help="Use 12 molecules and lower tessellation.")
    parser.add_argument("--smoke-test", action="store_true", help="Render one offscreen frame and exit.")
    parser.add_argument("--count", type=int, default=None, help="Override molecule count (1-200).")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic placement/trajectory seed.")
    return parser.parse_args()


def main():
    args = parse_args()
    verify_environment()
    if args.smoke_test:
        smoke_test()
        return

    preview = bool(args.preview)
    count = args.count if args.count is not None else (
        PREVIEW_MOLECULE_COUNT if preview else HIGH_MOLECULE_COUNT
    )
    if not (1 <= count <= 200):
        raise ValueError("--count must be between 1 and 200.")

    sim = MolecularSimulation(MOLECULE_DEFINITION, count, args.seed, preview)
    sim.start()


if __name__ == "__main__":
    main()
