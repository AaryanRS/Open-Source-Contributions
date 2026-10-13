"""
FURY Brain Visualization
Stage 5.1 - Scientific Cortex + Point Nodes

Current visualization:
    - Real fsaverage5 cortical surface
    - Destrieux anatomical parcellation
    - 500-600 cortex-aware points
    - True FURY point primitives (not spheres)
    - Restrained scientific color palette
    - Dark scientific background
    - Slow continuous rotation
    - Interactive mouse rotation / zoom
    - PNG snapshot
    - Smoke test

NOT YET INCLUDED:
    - Neural connections
    - Animated neural activity
    - Region clicking / selection
    - MP4 recording

Those will be added only after this visual foundation is approved.

Scientific note:
    fsaverage5 is a standardized human cortical template.
    It is not an individual person's MRI.

    The points are visualization nodes sampled from the cortical
    surface. They are NOT individual biological neurons.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import nibabel as nib
import numpy as np
from nilearn import datasets

from fury import actor, window


# ============================================================================
# 1. CONFIGURATION
# ============================================================================

WINDOW_SIZE = (1280, 800)

DEFAULT_NODE_COUNT = 600
SMOKE_TEST_NODE_COUNT = 120

RANDOM_SEED = 42

OUTPUT_DIR = Path("brain_output")

SNAPSHOT_PATH = (
    OUTPUT_DIR / "brain_scientific_points.png"
)

SMOKE_SNAPSHOT_PATH = (
    OUTPUT_DIR / "brain_scientific_points_smoke.png"
)

# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------

BACKGROUND = (
    0.004,
    0.015,
    0.024,
    1.0,
)

# ---------------------------------------------------------------------------
# Brain surface
# ---------------------------------------------------------------------------

SURFACE_OPACITY = 0.10

# ---------------------------------------------------------------------------
# Neural points
# ---------------------------------------------------------------------------

POINT_SIZE = 4.0
POINT_OPACITY = 0.96

# ---------------------------------------------------------------------------
# Automatic rotation
# ---------------------------------------------------------------------------

ROTATION_INTERVAL = 0.033
ROTATION_DEGREES = 0.14

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

CAMERA_POSITION = (
    2.35,
    -1.65,
    0.55,
)

CAMERA_TARGET = (
    0.0,
    0.0,
    0.0,
)


# ============================================================================
# 2. VALIDATION
# ============================================================================


def validate_node_count(node_count: int) -> None:
    """Validate the requested number of visualization nodes."""
    if not isinstance(node_count, int):
        raise TypeError(
            "node_count must be an integer."
        )

    if not 100 <= node_count <= 2000:
        raise ValueError(
            "node_count must be between 100 and 2000."
        )


def verify_environment() -> None:
    """Print the versions used by the project."""
    import fury
    import nilearn

    print()
    print("Environment")
    print("-----------")
    print(f"FURY:    {fury.__version__}")
    print(f"NumPy:   {np.__version__}")
    print(f"Nilearn: {nilearn.__version__}")
    print(f"NiBabel: {nib.__version__}")
    print()


# ============================================================================
# 3. GIFTI SURFACE LOADING
# ============================================================================


def load_gifti_surface(
    path: str | Path,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Load a GIFTI cortical surface.

    Returns
    -------
    vertices:
        Array with shape (N, 3).

    faces:
        Triangle array with shape (M, 3).
    """
    image = nib.load(path)

    vertices = np.asarray(
        image.agg_data("pointset"),
        dtype=np.float32,
    )

    faces = np.asarray(
        image.agg_data("triangle"),
        dtype=np.int32,
    )

    if vertices.ndim != 2 or vertices.shape[1] != 3:
        raise RuntimeError(
            f"Invalid vertex array shape: {vertices.shape}"
        )

    if faces.ndim != 2 or faces.shape[1] != 3:
        raise RuntimeError(
            f"Invalid face array shape: {faces.shape}"
        )

    return vertices, faces


# ============================================================================
# 4. COMMON BRAIN COORDINATE SYSTEM
# ============================================================================


def normalize_brain(
    left_vertices: np.ndarray,
    right_vertices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Put both hemispheres into one shared normalized coordinate system.

    The hemispheres are centered and scaled together so their relative
    anatomical relationship is preserved.
    """
    combined = np.vstack(
        [
            left_vertices,
            right_vertices,
        ]
    )

    center = combined.mean(
        axis=0
    )

    left = (
        left_vertices
        - center
    )

    right = (
        right_vertices
        - center
    )

    scale = np.max(
        np.linalg.norm(
            np.vstack(
                [
                    left,
                    right,
                ]
            ),
            axis=1,
        )
    )

    if not np.isfinite(scale) or scale <= 0:
        raise RuntimeError(
            "Unable to calculate a valid brain scale."
        )

    left /= scale
    right /= scale

    return (
        left.astype(np.float32),
        right.astype(np.float32),
    )


# ============================================================================
# 5. SCIENTIFIC COLOR SYSTEM
# ============================================================================


def create_scientific_palette(
    region_count: int,
) -> np.ndarray:
    """
    Create a restrained scientific palette.

    We deliberately avoid a rainbow spectrum.

    The surface uses dark/muted colors while the neural points use
    a separate pale cyan/white color so the network will later stand
    out from the anatomy.
    """

    scientific_colors = np.array(
        [
            # Deep cyan
            [0.075, 0.28, 0.34],

            # Scientific blue
            [0.085, 0.23, 0.38],

            # Teal
            [0.095, 0.34, 0.34],

            # Blue-teal
            [0.10, 0.29, 0.42],

            # Slate blue
            [0.14, 0.26, 0.36],

            # Desaturated cyan
            [0.13, 0.34, 0.40],
        ],
        dtype=np.float32,
    )

    palette = np.empty(
        (region_count, 3),
        dtype=np.float32,
    )

    for index in range(region_count):
        palette[index] = scientific_colors[
            index % len(scientific_colors)
        ]

    return palette


# ============================================================================
# 6. NODE ALLOCATION
# ============================================================================


def allocate_nodes_to_regions(
    region_map: np.ndarray,
    node_count: int,
) -> dict[int, int]:
    """
    Allocate nodes proportionally across anatomical regions.

    Every valid region receives at least one node when possible.
    Remaining nodes are distributed according to cortical area.
    """

    valid_regions = np.unique(
        region_map[
            region_map > 0
        ]
    )

    if len(valid_regions) == 0:
        raise RuntimeError(
            "No valid anatomical regions were found."
        )

    if node_count < len(valid_regions):
        raise ValueError(
            "Node count is smaller than the number of "
            "valid anatomical regions."
        )

    region_vertex_counts = np.array(
        [
            np.count_nonzero(
                region_map == region_id
            )
            for region_id in valid_regions
        ],
        dtype=np.float64,
    )

    allocation = np.ones(
        len(valid_regions),
        dtype=np.int32,
    )

    remaining = (
        node_count
        - len(valid_regions)
    )

    weights = (
        region_vertex_counts
        / region_vertex_counts.sum()
    )

    proportional = (
        weights
        * remaining
    )

    extra = np.floor(
        proportional
    ).astype(np.int32)

    allocation += extra

    leftover = (
        node_count
        - int(allocation.sum())
    )

    if leftover > 0:
        fractional = (
            proportional
            - extra
        )

        order = np.argsort(
            fractional
        )[::-1]

        for index in order[:leftover]:
            allocation[index] += 1

    return {
        int(region_id): int(count)
        for region_id, count in zip(
            valid_regions,
            allocation,
            strict=True,
        )
    }


# ============================================================================
# 7. SPATIALLY DISTRIBUTED SAMPLING
# ============================================================================


def farthest_point_sample(
    points: np.ndarray,
    count: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Select spatially distributed points.

    A pure random sample can produce ugly clusters.
    Farthest-point sampling spreads the nodes across the actual
    cortical geometry.
    """

    point_count = len(points)

    if count <= 0:
        return np.empty(
            0,
            dtype=np.int32,
        )

    if count >= point_count:
        return np.arange(
            point_count,
            dtype=np.int32,
        )

    first = int(
        rng.integers(
            0,
            point_count,
        )
    )

    selected = np.empty(
        count,
        dtype=np.int32,
    )

    selected[0] = first

    minimum_distance = np.sum(
        (
            points
            - points[first]
        )
        ** 2,
        axis=1,
    )

    minimum_distance[first] = -1.0

    for index in range(
        1,
        count,
    ):
        next_index = int(
            np.argmax(
                minimum_distance
            )
        )

        selected[index] = next_index

        new_distance = np.sum(
            (
                points
                - points[next_index]
            )
            ** 2,
            axis=1,
        )

        minimum_distance = np.minimum(
            minimum_distance,
            new_distance,
        )

        minimum_distance[
            next_index
        ] = -1.0

    return selected


# ============================================================================
# 8. CORTICAL NODE GENERATION
# ============================================================================


def sample_cortical_nodes(
    vertices: np.ndarray,
    regions: np.ndarray,
    node_count: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Sample actual cortical vertices as visualization nodes.

    Every returned node position is therefore attached directly to
    the real cortical surface geometry.
    """

    region_allocations = (
        allocate_nodes_to_regions(
            region_map=regions,
            node_count=node_count,
        )
    )

    positions = []
    region_ids = []

    for region_id, region_count in (
        region_allocations.items()
    ):
        candidates = np.flatnonzero(
            regions == region_id
        )

        if len(candidates) == 0:
            continue

        candidate_positions = (
            vertices[candidates]
        )

        local_indices = (
            farthest_point_sample(
                points=candidate_positions,
                count=region_count,
                rng=rng,
            )
        )

        global_indices = (
            candidates[
                local_indices
            ]
        )

        positions.append(
            vertices[
                global_indices
            ]
        )

        region_ids.extend(
            [region_id] * region_count
        )

    node_positions = np.vstack(
        positions
    ).astype(np.float32)

    node_regions = np.asarray(
        region_ids,
        dtype=np.int32,
    )

    if len(node_positions) != node_count:
        raise RuntimeError(
            f"Expected {node_count} nodes, "
            f"generated {len(node_positions)}."
        )

    permutation = rng.permutation(
        node_count
    )

    return (
        node_positions[
            permutation
        ],
        node_regions[
            permutation
        ],
    )


def build_brain_nodes(
    left_vertices: np.ndarray,
    right_vertices: np.ndarray,
    left_regions: np.ndarray,
    right_regions: np.ndarray,
    node_count: int,
    rng: np.random.Generator,
):
    """
    Build equally balanced left/right cortical node populations.
    """

    left_count = (
        node_count // 2
    )

    right_count = (
        node_count
        - left_count
    )

    (
        left_positions,
        left_region_ids,
    ) = sample_cortical_nodes(
        vertices=left_vertices,
        regions=left_regions,
        node_count=left_count,
        rng=rng,
    )

    (
        right_positions,
        right_region_ids,
    ) = sample_cortical_nodes(
        vertices=right_vertices,
        regions=right_regions,
        node_count=right_count,
        rng=rng,
    )

    node_positions = np.vstack(
        [
            left_positions,
            right_positions,
        ]
    ).astype(np.float32)

    node_regions = np.concatenate(
        [
            left_region_ids,
            right_region_ids,
        ]
    ).astype(np.int32)

    node_hemispheres = np.concatenate(
        [
            np.zeros(
                left_count,
                dtype=np.int8,
            ),
            np.ones(
                right_count,
                dtype=np.int8,
            ),
        ]
    )

    return (
        node_positions,
        node_regions,
        node_hemispheres,
    )


# ============================================================================
# 9. MAIN VISUALIZATION CLASS
# ============================================================================


class BrainVisualization:
    """
    Scientific brain visualization consisting of:

        anatomical cortical surface
        +
        600 cortex-aware point nodes
    """

    def __init__(
        self,
        node_count: int = DEFAULT_NODE_COUNT,
        seed: int = RANDOM_SEED,
        window_size: tuple[int, int] = WINDOW_SIZE,
    ) -> None:

        validate_node_count(
            node_count
        )

        self.node_count = node_count

        self.rng = np.random.default_rng(
            seed
        )

        self.window_size = window_size

        self.scene = None
        self.show_manager = None
        self.brain_group = None
        self.point_actor = None

        self.node_positions = None
        self.node_regions = None
        self.node_hemispheres = None

        self.paused = False

        self.build()

    # ------------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------------

    def load_anatomy(self):
        """Download/load the standardized cortical anatomy and atlas."""

        print(
            "Fetching fsaverage5 cortical surface..."
        )

        fsaverage = (
            datasets.fetch_surf_fsaverage(
                mesh="fsaverage5"
            )
        )

        print(
            "Fetching Destrieux cortical atlas..."
        )

        destrieux = (
            datasets.fetch_atlas_surf_destrieux()
        )

        print(
            "Loading left hemisphere..."
        )

        left_vertices, left_faces = (
            load_gifti_surface(
                fsaverage["pial_left"]
            )
        )

        print(
            "Loading right hemisphere..."
        )

        right_vertices, right_faces = (
            load_gifti_surface(
                fsaverage["pial_right"]
            )
        )

        left_regions = np.asarray(
            destrieux["map_left"],
            dtype=np.int32,
        )

        right_regions = np.asarray(
            destrieux["map_right"],
            dtype=np.int32,
        )

        left_vertices, right_vertices = (
            normalize_brain(
                left_vertices,
                right_vertices,
            )
        )

        labels = [
            label.decode("utf-8")
            if isinstance(label, bytes)
            else str(label)
            for label in destrieux["labels"]
        ]

        return {
            "left_vertices": left_vertices,
            "left_faces": left_faces,
            "left_regions": left_regions,
            "right_vertices": right_vertices,
            "right_faces": right_faces,
            "right_regions": right_regions,
            "labels": labels,
        }

    # ------------------------------------------------------------------------
    # SURFACE
    # ------------------------------------------------------------------------

    def create_surface_actor(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
        regions: np.ndarray,
        palette: np.ndarray,
    ):
        """Create a subtle scientific anatomical surface."""

        colors = palette[
            np.mod(
                regions,
                len(palette),
            )
        ]

        colors = np.asarray(
            colors,
            dtype=np.float32,
        )

        return actor.surface(
            vertices=vertices,
            faces=faces,
            material="phong",
            colors=colors,
            opacity=SURFACE_OPACITY,
        )

    # ------------------------------------------------------------------------
    # POINTS
    # ------------------------------------------------------------------------

    def create_point_actor(
        self,
        positions: np.ndarray,
    ):
        """
        Create the neural nodes as true FURY points.

        These are point primitives with a logical-pixel size rather
        than spheres or mesh glyphs.
        """

        point_color = (
            0.72,
            0.93,
            0.98,
            1.0,
        )

        return actor.point(
            centers=positions,
            size=POINT_SIZE,
            colors=point_color,
            material="basic",
            aa=True,
            opacity=POINT_OPACITY,
            enable_picking=False,
        )

    # ------------------------------------------------------------------------
    # BUILD
    # ------------------------------------------------------------------------

    def build(self):
        """Construct the complete scientific brain scene."""

        anatomy = self.load_anatomy()

        left_vertices = anatomy[
            "left_vertices"
        ]

        left_faces = anatomy[
            "left_faces"
        ]

        left_regions = anatomy[
            "left_regions"
        ]

        right_vertices = anatomy[
            "right_vertices"
        ]

        right_faces = anatomy[
            "right_faces"
        ]

        right_regions = anatomy[
            "right_regions"
        ]

        labels = anatomy[
            "labels"
        ]

        # --------------------------------------------------------------
        # Scientific surface palette.
        # --------------------------------------------------------------

        palette = (
            create_scientific_palette(
                region_count=len(labels)
            )
        )

        # --------------------------------------------------------------
        # Generate cortex-aware nodes.
        # --------------------------------------------------------------

        (
            self.node_positions,
            self.node_regions,
            self.node_hemispheres,
        ) = build_brain_nodes(
            left_vertices=left_vertices,
            right_vertices=right_vertices,
            left_regions=left_regions,
            right_regions=right_regions,
            node_count=self.node_count,
            rng=self.rng,
        )

        print()
        print(
            f"Generated {self.node_count} "
            "cortex-aware points."
        )

        print(
            "Left hemisphere:",
            np.count_nonzero(
                self.node_hemispheres == 0
            ),
        )

        print(
            "Right hemisphere:",
            np.count_nonzero(
                self.node_hemispheres == 1
            ),
        )

        # --------------------------------------------------------------
        # Scene.
        # --------------------------------------------------------------

        self.scene = window.Scene(
            background=BACKGROUND
        )

        # All brain content belongs to one group.
        self.brain_group = actor.Group(
            name="BrainVisualization"
        )

        self.scene.add(
            self.brain_group
        )

        # --------------------------------------------------------------
        # Anatomical surfaces.
        # --------------------------------------------------------------

        left_surface = (
            self.create_surface_actor(
                vertices=left_vertices,
                faces=left_faces,
                regions=left_regions,
                palette=palette,
            )
        )

        right_surface = (
            self.create_surface_actor(
                vertices=right_vertices,
                faces=right_faces,
                regions=right_regions,
                palette=palette,
            )
        )

        self.brain_group.add(
            left_surface,
            right_surface,
        )

        # --------------------------------------------------------------
        # Neural point nodes.
        # --------------------------------------------------------------

        self.point_actor = (
            self.create_point_actor(
                positions=self.node_positions
            )
        )

        self.brain_group.add(
            self.point_actor
        )

        # --------------------------------------------------------------
        # Show manager.
        # --------------------------------------------------------------

        self.show_manager = (
            window.ShowManager(
                scene=self.scene,
                size=self.window_size,
                title=(
                    "FURY Brain Visualization "
                    "- Scientific Point Network"
                ),
                enable_events=True,
                show_fps=True,
                max_fps=60,
            )
        )

        # --------------------------------------------------------------
        # Camera.
        # --------------------------------------------------------------

        camera = (
            self.show_manager
            .screens[0]
            .camera
        )

        camera.local.position = (
            *CAMERA_POSITION,
        )

        camera.look_at(
            CAMERA_TARGET
        )

        # --------------------------------------------------------------
        # Continuous rotation.
        # --------------------------------------------------------------

        self.show_manager.register_callback(
            self.animate,
            ROTATION_INTERVAL,
            True,
            "brain_auto_rotation",
        )

    # ------------------------------------------------------------------------
    # ANIMATION
    # ------------------------------------------------------------------------

    def animate(self):
        """
        Rotate anatomy and points together.

        The points and anatomical surface share the same parent Group,
        therefore their relative spatial positions never change.
        """

        if self.paused:
            return

        self.brain_group.rotate(
            (
                0.0,
                ROTATION_DEGREES,
                0.0,
            )
        )

    # ------------------------------------------------------------------------
    # SNAPSHOT
    # ------------------------------------------------------------------------

    def save_snapshot(
        self,
        filename: Path,
    ):
        """Save a rendered PNG using FURY's current offscreen snapshot API."""

        filename.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        window.snapshot(
            scene=self.scene,
            fname=str(filename),
        )

        print()
        print(
            "Snapshot saved:"
        )
        print(
            filename.resolve()
        )

    # ------------------------------------------------------------------------
    # RUN
    # ------------------------------------------------------------------------

    def run(self):
        """Start the interactive window."""

        print()
        print("Controls")
        print("--------")
        print("Mouse drag  : rotate")
        print("Mouse wheel : zoom")
        print("Window close: exit")
        print()
        print(
            "Automatic rotation is enabled."
        )

        self.show_manager.start()


# ============================================================================
# 10. SMOKE TEST
# ============================================================================


def smoke_test():
    """
    Build a smaller scene and render one frame.

    This validates:
        - package imports
        - anatomical dataset loading
        - GIFTI parsing
        - atlas loading
        - cortex-aware node sampling
        - FURY surface rendering
        - FURY point rendering
        - offscreen snapshot creation
    """

    print()
    print(
        "Running scientific point-node smoke test..."
    )

    visualization = BrainVisualization(
        node_count=SMOKE_TEST_NODE_COUNT,
        seed=7,
        window_size=(900, 650),
    )

    visualization.save_snapshot(
        SMOKE_SNAPSHOT_PATH
    )

    visualization.show_manager.close()

    if not SMOKE_SNAPSHOT_PATH.exists():
        raise RuntimeError(
            "Smoke test failed: "
            "PNG snapshot was not created."
        )

    print()
    print(
        "SMOKE TEST PASSED"
    )
    print(
        SMOKE_SNAPSHOT_PATH.resolve()
    )


# ============================================================================
# 11. COMMAND LINE
# ============================================================================


def parse_arguments():
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description=(
            "Scientific FURY brain visualization "
            "with cortex-aware point nodes."
        )
    )

    parser.add_argument(
        "--nodes",
        type=int,
        default=DEFAULT_NODE_COUNT,
        help=(
            "Number of cortex-aware points "
            "(default: 600)."
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help=(
            "Random seed used by the spatial sampler."
        ),
    )

    parser.add_argument(
        "--snapshot",
        action="store_true",
        help=(
            "Save a PNG before opening "
            "the interactive window."
        ),
    )

    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help=(
            "Run a small offscreen rendering test."
        ),
    )

    return parser.parse_args()


# ============================================================================
# 12. MAIN
# ============================================================================


def main():
    """Program entry point."""

    verify_environment()

    arguments = parse_arguments()

    if arguments.smoke_test:
        smoke_test()
        return

    visualization = BrainVisualization(
        node_count=arguments.nodes,
        seed=arguments.seed,
        window_size=WINDOW_SIZE,
    )

    if arguments.snapshot:
        visualization.save_snapshot(
            SNAPSHOT_PATH
        )

    visualization.run()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()