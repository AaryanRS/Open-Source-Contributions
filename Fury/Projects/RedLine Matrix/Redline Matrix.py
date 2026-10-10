"""
FURY Organic Neural / Vascular Network Visualization
=====================================================

Target:
    A dense, organic, branching 3D structure inspired by the supplied
    reference image.

Rendering:
    FURY 2.0.x / PyGfx / wgpu

Design:
    - 3D streamtubes for primary branches
    - FURY streamlines for secondary branches
    - Dense organic central core
    - Bright red on black
    - Continuous slow rotation
    - Interactive camera
    - GPU streamtube generation with CPU fallback

Profiles:
    preview  -> 120 branches
    balanced -> 240 branches
    high     -> 300 branches

Usage:
    python fury_organic_network.py
    python fury_organic_network.py --profile preview
    python fury_organic_network.py --profile balanced
    python fury_organic_network.py --profile high
    python fury_organic_network.py --smoke-test
"""

from __future__ import annotations

# ============================================================
# 1. HEADER AND IMPORTS
# ============================================================

import argparse
import math
import platform
import sys
from dataclasses import dataclass

import numpy as np

from fury import actor
from fury import window


# ============================================================
# 2. ENVIRONMENT / VERSION CONFIGURATION
# ============================================================

EXPECTED_FURY_VERSION = "2.0.0"


@dataclass(frozen=True)
class Config:
    """
    Configuration describing the complexity of the generated network.
    """

    primary_branches: int
    children_per_primary: int
    primary_points: int
    child_points: int
    seed: int
    rotation_deg_per_tick: float


# Three configurations using the same procedural system.
#
# Preview:
#     24 primary + 96 secondary = 120 total
#
# Balanced:
#     48 primary + 192 secondary = 240 total
#
# High:
#     60 primary + 240 secondary = 300 total
PROFILES = {
    "preview": Config(
        primary_branches=24,
        children_per_primary=4,
        primary_points=38,
        child_points=24,
        seed=42,
        rotation_deg_per_tick=0.12,
    ),
    "balanced": Config(
        primary_branches=48,
        children_per_primary=4,
        primary_points=52,
        child_points=30,
        seed=42,
        rotation_deg_per_tick=0.10,
    ),
    "high": Config(
        primary_branches=60,
        children_per_primary=4,
        primary_points=58,
        child_points=34,
        seed=42,
        rotation_deg_per_tick=0.08,
    ),
}


def check_environment() -> None:
    """
    Validate the runtime environment before creating the scene.
    """

    fury_version = getattr(
        __import__("fury"),
        "__version__",
        "unknown",
    )

    print("=" * 62)
    print("FURY Organic Network")
    print("=" * 62)

    print(f"[INFO] Python      : {platform.python_version()}")
    print(f"[INFO] Platform    : {platform.platform()}")
    print(f"[INFO] FURY        : {fury_version}")
    print(f"[INFO] NumPy       : {np.__version__}")

    if fury_version != EXPECTED_FURY_VERSION:
        print(
            "[WARN] This script was validated against "
            f"FURY {EXPECTED_FURY_VERSION}."
        )
        print(
            "[WARN] Your installed version is "
            f"{fury_version}. The APIs may differ."
        )

    # FURY 2.0.0 requires Python >= 3.10.
    if sys.version_info < (3, 10):
        raise RuntimeError(
            "Python 3.10 or newer is required by FURY 2.0.0."
        )


# ============================================================
# 3. CONFIGURATION VALIDATION
# ============================================================

def validate_config(config: Config) -> None:
    """
    Validate procedural generation parameters.
    """

    if not 1 <= config.primary_branches <= 100:
        raise ValueError(
            "primary_branches must be between 1 and 100."
        )

    if not 1 <= config.children_per_primary <= 6:
        raise ValueError(
            "children_per_primary must be between 1 and 6."
        )

    if config.primary_points < 8:
        raise ValueError(
            "primary_points must be at least 8."
        )

    if config.child_points < 8:
        raise ValueError(
            "child_points must be at least 8."
        )

    if (
        not math.isfinite(config.rotation_deg_per_tick)
        or config.rotation_deg_per_tick < 0
    ):
        raise ValueError(
            "rotation_deg_per_tick must be a finite non-negative number."
        )


# ============================================================
# 4. PROCEDURAL GEOMETRY HELPERS
# ============================================================

def normalize(vector: np.ndarray) -> np.ndarray:
    """
    Return a normalized 3D vector.

    A fallback vector prevents division by zero when random
    vectors happen to be extremely close to zero.
    """

    norm = float(np.linalg.norm(vector))

    if norm < 1e-8:
        return np.array(
            [1.0, 0.0, 0.0],
            dtype=np.float64,
        )

    return vector / norm


def random_direction(
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Generate an organic 3D direction.

    Z is slightly compressed so the final structure has a
    broad, spreading appearance similar to the reference.
    """

    direction = rng.normal(
        size=3,
    )

    direction[2] *= 0.78

    return normalize(direction)


# ============================================================
# 5. PRIMARY BRANCH GENERATION
# ============================================================

def build_primary_branches(
    rng: np.random.Generator,
    config: Config,
) -> list[np.ndarray]:
    """
    Generate the major branches.

    Every primary branch begins close to the origin and then
    grows outward using a continuously changing tangent.

    This creates the dense central core naturally.
    """

    lines: list[np.ndarray] = []

    print(
        f"[INFO] Generating "
        f"{config.primary_branches} primary branches..."
    )

    for _ in range(config.primary_branches):

        # Initial direction.
        direction = random_direction(rng)

        # Start very close to the origin.
        #
        # The small random displacement prevents every branch
        # from occupying exactly the same first point.
        position = rng.normal(
            loc=0.0,
            scale=0.18,
            size=3,
        )

        points = [
            position.copy()
        ]

        tangent = direction.copy()

        for i in range(
            1,
            config.primary_points,
        ):

            progress = (
                i / (config.primary_points - 1)
            )

            # Stronger randomness near the core.
            #
            # This produces irregular organic curvature while
            # allowing the branch to stabilize as it grows.
            bend = rng.normal(
                loc=0.0,
                scale=0.10 * (
                    1.0 - 0.65 * progress
                ),
                size=3,
            )

            tangent = normalize(
                0.91 * tangent
                + 0.09 * direction
                + bend
            )

            # Slightly longer steps produce outward growth.
            step = (
                0.17
                + 0.055 * (1.0 - progress)
            )

            position = (
                position
                + tangent * step
            )

            # Tiny positional noise prevents mathematically
            # perfect curves.
            position += rng.normal(
                loc=0.0,
                scale=0.012 * (
                    1.0 - progress
                ),
                size=3,
            )

            points.append(
                position.copy()
            )

        lines.append(
            np.asarray(
                points,
                dtype=np.float32,
            )
        )

    return lines


# ============================================================
# 6. SECONDARY BRANCH GENERATION
# ============================================================

def build_secondary_branches(
    rng: np.random.Generator,
    primary_lines: list[np.ndarray],
    config: Config,
) -> list[np.ndarray]:
    """
    Generate secondary branches from the primary branches.

    Each secondary branch begins somewhere along an existing
    primary branch instead of beginning at the origin.

    This is the key feature that makes the structure look like
    an actual branching system rather than a collection of
    independent radial curves.
    """

    children: list[np.ndarray] = []

    print(
        "[INFO] Generating secondary branches..."
    )

    for parent in primary_lines:

        for _ in range(
            config.children_per_primary
        ):

            # Choose a point somewhere after the core
            # but before the end of the parent.
            start_idx = int(
                rng.integers(
                    max(
                        3,
                        config.primary_points // 5,
                    ),
                    max(
                        4,
                        int(
                            config.primary_points
                            * 0.70
                        ),
                    ),
                )
            )

            start = parent[
                start_idx
            ].astype(np.float64)

            # Estimate the local direction of the
            # primary branch.
            tangent = normalize(
                parent[
                    min(
                        start_idx + 1,
                        len(parent) - 1,
                    )
                ].astype(np.float64)
                -
                parent[
                    max(
                        start_idx - 1,
                        0,
                    )
                ].astype(np.float64)
            )

            # Push the child generally away from the center.
            radial = normalize(
                start
                + rng.normal(
                    0.0,
                    0.2,
                    size=3,
                )
            )

            # Combine:
            #   parent direction
            #   random organic direction
            #   outward radial direction
            child_direction = normalize(
                0.62 * tangent
                + 0.52 * random_direction(rng)
                + 0.42 * radial
            )

            position = start.copy()

            points = [
                position.copy()
            ]

            for i in range(
                1,
                config.child_points,
            ):

                progress = (
                    i / (
                        config.child_points - 1
                    )
                )

                bend = rng.normal(
                    loc=0.0,
                    scale=0.13 * (
                        1.0 - 0.55 * progress
                    ),
                    size=3,
                )

                child_direction = normalize(
                    0.88 * child_direction
                    + 0.12 * tangent
                    + bend
                )

                step = (
                    0.13
                    + 0.045 * (
                        1.0 - progress
                    )
                )

                position = (
                    position
                    + child_direction * step
                )

                position += rng.normal(
                    loc=0.0,
                    scale=0.014 * (
                        1.0 - progress
                    ),
                    size=3,
                )

                points.append(
                    position.copy()
                )

            children.append(
                np.asarray(
                    points,
                    dtype=np.float32,
                )
            )

    return children


# ============================================================
# 7. GEOMETRY VALIDATION
# ============================================================

def validate_lines(
    lines: list[np.ndarray],
    name: str,
) -> None:
    """
    Validate generated FURY line data before passing it to
    the rendering pipeline.
    """

    if not isinstance(lines, list):
        raise TypeError(
            f"{name} must be a list of NumPy arrays."
        )

    if not lines:
        raise ValueError(
            f"{name} cannot be empty."
        )

    for index, line in enumerate(lines):

        array = np.asarray(line)

        if array.ndim != 2:
            raise ValueError(
                f"{name}[{index}] must be 2-dimensional."
            )

        if array.shape[1] != 3:
            raise ValueError(
                f"{name}[{index}] must have shape (P, 3)."
            )

        if array.shape[0] < 2:
            raise ValueError(
                f"{name}[{index}] needs at least 2 points."
            )

        if not np.all(
            np.isfinite(array)
        ):
            raise ValueError(
                f"{name}[{index}] contains NaN "
                "or infinite values."
            )


# ============================================================
# 8. RED COLOR PALETTES
# ============================================================

def create_primary_colors(
    rng: np.random.Generator,
    count: int,
) -> np.ndarray:
    """
    Create subtle red variations for primary branches.
    """

    return np.column_stack(
        [
            np.ones(count),
            rng.uniform(
                0.0,
                0.055,
                count,
            ),
            rng.uniform(
                0.0,
                0.025,
                count,
            ),
        ]
    ).astype(np.float32)


def create_secondary_colors(
    rng: np.random.Generator,
    count: int,
) -> np.ndarray:
    """
    Create slightly darker red variations for fine branches.
    """

    return np.column_stack(
        [
            np.ones(count),
            rng.uniform(
                0.0,
                0.035,
                count,
            ),
            rng.uniform(
                0.0,
                0.015,
                count,
            ),
        ]
    ).astype(np.float32)


# ============================================================
# 9. FURY SCENE CONSTRUCTION
# ============================================================

def create_scene(
    profile: str = "balanced",
):
    """
    Construct the complete FURY scene.

    Returns:
        scene
        primary_actor
        secondary_actor
        primary_lines
        secondary_lines
    """

    if profile not in PROFILES:
        raise ValueError(
            f"Unknown profile '{profile}'. "
            f"Choose from {list(PROFILES)}."
        )

    config = PROFILES[profile]

    validate_config(config)

    rng = np.random.default_rng(
        config.seed
    )

    print(
        f"[INFO] Selected profile: {profile}"
    )

    # --------------------------------------------------------
    # Generate geometry
    # --------------------------------------------------------

    primary_lines = build_primary_branches(
        rng,
        config,
    )

    secondary_lines = build_secondary_branches(
        rng,
        primary_lines,
        config,
    )

    validate_lines(
        primary_lines,
        "primary_lines",
    )

    validate_lines(
        secondary_lines,
        "secondary_lines",
    )

    print(
        f"[INFO] Primary branches   : "
        f"{len(primary_lines)}"
    )

    print(
        f"[INFO] Secondary branches : "
        f"{len(secondary_lines)}"
    )

    print(
        f"[INFO] Total branches     : "
        f"{len(primary_lines) + len(secondary_lines)}"
    )

    # --------------------------------------------------------
    # Generate colors
    # --------------------------------------------------------

    primary_colors = create_primary_colors(
        rng,
        len(primary_lines),
    )

    secondary_colors = create_secondary_colors(
        rng,
        len(secondary_lines),
    )

    # --------------------------------------------------------
    # Main branches
    #
    # FURY 2.0 streamtube creates actual 3D tubular geometry.
    # GPU backend is used first because your RTX 5060 is ideal
    # for this workload.
    # --------------------------------------------------------

    print(
        "[INFO] Building primary 3D streamtubes..."
    )

    try:

        primary_actor = actor.streamtube(
            primary_lines,
            colors=primary_colors,
            opacity=0.98,
            radius=0.045,
            segments=6,
            end_caps=True,
            flat_shading=False,
            material="basic",
            enable_picking=False,
            backend="gpu",
        )

    except Exception as gpu_error:

        print(
            "[WARN] GPU streamtube generation failed."
        )

        print(
            f"[WARN] Reason: {gpu_error}"
        )

        print(
            "[WARN] Falling back to CPU streamtube generation."
        )

        primary_actor = actor.streamtube(
            primary_lines,
            colors=primary_colors,
            opacity=0.98,
            radius=0.045,
            segments=6,
            end_caps=True,
            flat_shading=False,
            material="basic",
            enable_picking=False,
            backend="cpu",
        )

    # --------------------------------------------------------
    # Secondary branches
    #
    # These remain thin to reproduce the fine branching seen
    # in the reference image while keeping GPU cost reasonable.
    # --------------------------------------------------------

    print(
        "[INFO] Building secondary streamlines..."
    )

    secondary_actor = actor.streamlines(
        secondary_lines,
        colors=secondary_colors,
        thickness=1.8,
        opacity=0.96,
        outline_thickness=0.0,
        enable_picking=False,
    )

    # --------------------------------------------------------
    # Scene
    # --------------------------------------------------------

    scene = window.Scene(
        background=(
            0.0,
            0.0,
            0.0,
            1.0,
        )
    )

    # Both actors share the exact same world origin.
    # This makes the center naturally dense.
    scene.add(
        primary_actor,
        secondary_actor,
    )

    return (
        scene,
        primary_actor,
        secondary_actor,
        primary_lines,
        secondary_lines,
    )


# ============================================================
# 10. CAMERA / INTERACTION SETUP
# ============================================================

def create_show_manager(
    scene,
) -> window.ShowManager:
    """
    Create the interactive FURY window.

    FURY 2 automatically supplies a camera controller when
    no custom controller is provided, giving interactive
    mouse-based scene navigation.
    """

    show_manager = window.ShowManager(
        scene=scene,
        title="FURY — Organic Neural Network",
        size=(900, 900),
        camera_light=False,
        enable_events=True,
        show_fps=False,
        max_fps=60,
    )

    camera = (
        show_manager
        .screens[0]
        .camera
    )

    # Camera starts far enough away to contain the complete
    # procedural structure.
    camera.local.position = (
        0.0,
        -1.5,
        28.0,
    )

    camera.look_at(
        (
            0.0,
            0.0,
            0.0,
        )
    )

    return show_manager


# ============================================================
# 11. CONTINUOUS ROTATION
# ============================================================

def add_rotation_animation(
    show_manager: window.ShowManager,
    primary_actor,
    secondary_actor,
    degrees_per_tick: float,
) -> None:
    """
    Add continuous slow rotation.

    The two actors are rotated together around the common
    origin so the network behaves as one visualization.
    """

    def rotate_scene() -> None:

        primary_actor.rotate(
            (
                0.0,
                0.0,
                degrees_per_tick,
            )
        )

        secondary_actor.rotate(
            (
                0.0,
                0.0,
                degrees_per_tick,
            )
        )

    show_manager.register_callback(
        rotate_scene,
        0.016,
        True,
        "organic_network_rotation",
    )


# ============================================================
# 12. MAIN APPLICATION
# ============================================================

def run_visualization(
    profile: str = "balanced",
) -> None:

    check_environment()

    (
        scene,
        primary_actor,
        secondary_actor,
        primary_lines,
        secondary_lines,
    ) = create_scene(profile)

    config = PROFILES[profile]

    print(
        "[INFO] Creating interactive FURY window..."
    )

    show_manager = create_show_manager(
        scene
    )

    add_rotation_animation(
        show_manager,
        primary_actor,
        secondary_actor,
        config.rotation_deg_per_tick,
    )

    print("=" * 62)
    print("Visualization ready.")
    print("Use the mouse to orbit / zoom the scene.")
    print("Close the window to exit.")
    print("=" * 62)

    # Start the FURY rendering/event loop.
    show_manager.start()


# ============================================================
# 13. OFFSCREEN SMOKE TEST
# ============================================================

def smoke_test(
    profile: str = "preview",
) -> None:
    """
    Create and render one frame without opening a normal
    interactive window.

    This validates:
        - procedural geometry
        - FURY actor construction
        - scene construction
        - camera setup
        - actual rendering
    """

    check_environment()

    (
        scene,
        _primary_actor,
        _secondary_actor,
        primary_lines,
        secondary_lines,
    ) = create_scene(profile)

    show_manager = window.ShowManager(
        scene=scene,
        title="FURY Smoke Test",
        size=(512, 512),
        window_type="offscreen",
        camera_light=False,
        enable_events=False,
        max_fps=30,
    )

    camera = (
        show_manager
        .screens[0]
        .camera
    )

    camera.local.position = (
        0.0,
        -1.5,
        28.0,
    )

    camera.look_at(
        (
            0.0,
            0.0,
            0.0,
        )
    )

    # Request a render.
    show_manager.render()

    # Capture the rendered frame in memory.
    # fname=None guarantees that no file is written.
    frame = show_manager.snapshot(
        fname=None
    )

    if frame is None:
        raise RuntimeError(
            "FURY returned no rendered frame."
        )

    if frame.ndim != 3:
        raise RuntimeError(
            f"Unexpected frame dimensions: {frame.shape}"
        )

    if frame.shape[2] not in (3, 4):
        raise RuntimeError(
            f"Unexpected channel count: {frame.shape}"
        )

    show_manager.close()

    print("=" * 62)
    print("[PASS] FURY smoke test succeeded.")
    print(
        f"[PASS] Rendered frame: "
        f"{frame.shape[1]} x {frame.shape[0]}"
    )
    print(
        f"[PASS] Primary branches: "
        f"{len(primary_lines)}"
    )
    print(
        f"[PASS] Secondary branches: "
        f"{len(secondary_lines)}"
    )
    print(
        f"[PASS] Total branches: "
        f"{len(primary_lines) + len(secondary_lines)}"
    )
    print("=" * 62)


# ============================================================
# 14. COMMAND-LINE ENTRY POINT
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Procedural organic branching visualization "
            "built with FURY 2.0."
        )
    )

    parser.add_argument(
        "--profile",
        choices=tuple(PROFILES.keys()),
        default="balanced",
        help="Visualization complexity profile.",
    )

    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Render one offscreen frame and exit.",
    )

    args = parser.parse_args()

    if args.smoke_test:
        smoke_test(
            profile=args.profile
        )
    else:
        run_visualization(
            profile=args.profile
        )


if __name__ == "__main__":
    main()