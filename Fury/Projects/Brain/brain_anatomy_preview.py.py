from pathlib import Path

import nibabel as nib
import numpy as np
from nilearn import datasets

from fury import actor, window


OUTPUT = Path("brain_output")
OUTPUT.mkdir(exist_ok=True)

WINDOW_SIZE = (1280, 800)


def load_gifti_surface(path):
    """Load vertices and triangular faces from a GIFTI surface."""
    image = nib.load(path)

    vertices = np.asarray(
        image.agg_data("pointset"),
        dtype=np.float32,
    )

    faces = np.asarray(
        image.agg_data("triangle"),
        dtype=np.int32,
    )

    return vertices, faces


def normalize_brain(left_vertices, right_vertices):
    """Put both hemispheres into one shared coordinate system."""
    all_vertices = np.vstack(
        [left_vertices, right_vertices]
    )

    center = all_vertices.mean(axis=0)

    left = left_vertices - center
    right = right_vertices - center

    scale = np.max(
        np.linalg.norm(
            np.vstack([left, right]),
            axis=1,
        )
    )

    if not np.isfinite(scale) or scale <= 0:
        raise RuntimeError(
            "Invalid anatomical surface scale."
        )

    left /= scale
    right /= scale

    return (
        left.astype(np.float32),
        right.astype(np.float32),
    )


def main():
    print("Fetching fsaverage5 anatomical surface...")

    fsaverage = datasets.fetch_surf_fsaverage(
        mesh="fsaverage5"
    )

    print("Loading left hemisphere...")
    left_vertices, left_faces = load_gifti_surface(
        fsaverage["pial_left"]
    )

    print("Loading right hemisphere...")
    right_vertices, right_faces = load_gifti_surface(
        fsaverage["pial_right"]
    )

    left_vertices, right_vertices = normalize_brain(
        left_vertices,
        right_vertices,
    )

    print(
        "Left:",
        left_vertices.shape,
        left_faces.shape,
    )

    print(
        "Right:",
        right_vertices.shape,
        right_faces.shape,
    )

    # Left cortical hemisphere.
    left_brain = actor.surface(
        vertices=left_vertices,
        faces=left_faces,
        material="phong",
        colors=(0.04, 0.55, 0.65),
        opacity=0.92,
    )

    # Right cortical hemisphere.
    right_brain = actor.surface(
        vertices=right_vertices,
        faces=right_faces,
        material="phong",
        colors=(0.10, 0.75, 0.72),
        opacity=0.92,
    )

    scene = window.Scene(
        background=(0.005, 0.018, 0.028, 1.0)
    )

    scene.add(
        left_brain,
        right_brain,
    )

    show_manager = window.ShowManager(
        scene=scene,
        size=WINDOW_SIZE,
        title="FURY Brain Anatomy Preview",
        show_fps=True,
        max_fps=60,
    )

    camera = show_manager.screens[0].camera

    camera.local.position = (
        0.0,
        -0.15,
        2.8,
    )

    camera.look_at(
        (0.0, 0.0, 0.0)
    )

    # Let FURY update the camera/view using the actual scene bounds.
    window.update_camera(
        camera,
        WINDOW_SIZE,
        scene,
    )

    # Save one offscreen PNG before opening the interactive window.
    snapshot_path = OUTPUT / "anatomical_brain.png"

    window.snapshot(
        scene=scene,
        fname=str(snapshot_path),
    )

    print(
        f"\nSnapshot saved to:\n{snapshot_path.resolve()}"
    )

    print(
        "\nOpening interactive FURY window..."
    )

    show_manager.start()


if __name__ == "__main__":
    main()