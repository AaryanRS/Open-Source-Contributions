from pathlib import Path

import nibabel as nib
import numpy as np
from nilearn import datasets

from fury import actor, window


OUTPUT = Path("brain_output")
OUTPUT.mkdir(exist_ok=True)

WINDOW_SIZE = (1280, 800)


def load_surface(path):
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


def normalize_brain(left, right):
    combined = np.vstack((left, right))

    center = combined.mean(axis=0)

    left = left - center
    right = right - center

    scale = np.max(
        np.linalg.norm(
            np.vstack((left, right)),
            axis=1,
        )
    )

    if not np.isfinite(scale) or scale <= 0:
        raise RuntimeError("Invalid brain scale.")

    return (
        (left / scale).astype(np.float32),
        (right / scale).astype(np.float32),
    )


def create_palette(count):
    """
    Generate distinct neon/scientific colors.

    We intentionally keep the colors fairly bright because later
    the neural network will be rendered over this anatomical layer.
    """
    colors = np.empty(
        (count, 3),
        dtype=np.float32,
    )

    golden_ratio = 0.61803398875

    for index in range(count):
        hue = (index * golden_ratio) % 1.0

        # HSV -> RGB
        h = hue * 6.0
        i = int(h)
        f = h - i

        s = 0.82
        v = 0.95

        p = v * (1.0 - s)
        q = v * (1.0 - f * s)
        t = v * (1.0 - (1.0 - f) * s)

        i %= 6

        if i == 0:
            rgb = (v, t, p)
        elif i == 1:
            rgb = (q, v, p)
        elif i == 2:
            rgb = (p, v, t)
        elif i == 3:
            rgb = (p, q, v)
        elif i == 4:
            rgb = (t, p, v)
        else:
            rgb = (v, p, q)

        colors[index] = rgb

    return colors


def region_vertex_colors(region_map, palette):
    """
    Convert the atlas region ID at every vertex into an RGB color.
    """
    colors = np.zeros(
        (len(region_map), 3),
        dtype=np.float32,
    )

    valid = (
        (region_map >= 0)
        & (region_map < len(palette))
    )

    colors[valid] = palette[
        region_map[valid]
    ]

    # Atlas ID 0 is the Unknown region.
    colors[~valid] = np.array(
        [0.025, 0.07, 0.08],
        dtype=np.float32,
    )

    return colors


def main():
    print("Fetching anatomical datasets...")

    fsaverage = datasets.fetch_surf_fsaverage(
        mesh="fsaverage5"
    )

    destrieux = datasets.fetch_atlas_surf_destrieux()

    print("Loading cortical surfaces...")

    left_vertices, left_faces = load_surface(
        fsaverage["pial_left"]
    )

    right_vertices, right_faces = load_surface(
        fsaverage["pial_right"]
    )

    left_vertices, right_vertices = normalize_brain(
        left_vertices,
        right_vertices,
    )

    left_regions = np.asarray(
        destrieux["map_left"],
        dtype=np.int32,
    )

    right_regions = np.asarray(
        destrieux["map_right"],
        dtype=np.int32,
    )

    labels = [
        label.decode("utf-8")
        if isinstance(label, bytes)
        else str(label)
        for label in destrieux["labels"]
    ]

    print(
        f"Atlas contains {len(labels)} labels."
    )

    # ------------------------------------------------------------------
    # COLOR THE ATLAS
    # ------------------------------------------------------------------

    palette = create_palette(
        len(labels)
    )

    left_colors = region_vertex_colors(
        left_regions,
        palette,
    )

    right_colors = region_vertex_colors(
        right_regions,
        palette,
    )

    # ------------------------------------------------------------------
    # BRAIN SURFACES
    # ------------------------------------------------------------------

    left_brain = actor.surface(
        vertices=left_vertices,
        faces=left_faces,
        colors=left_colors,
        material="phong",
        opacity=0.88,
    )

    right_brain = actor.surface(
        vertices=right_vertices,
        faces=right_faces,
        colors=right_colors,
        material="phong",
        opacity=0.88,
    )

    # ------------------------------------------------------------------
    # SCENE
    # ------------------------------------------------------------------

    scene = window.Scene(
        background=(0.004, 0.015, 0.025, 1.0)
    )

    scene.add(
        left_brain,
        right_brain,
    )

    show_manager = window.ShowManager(
        scene=scene,
        size=WINDOW_SIZE,
        title="FURY Brain Anatomical Regions",
        show_fps=True,
        max_fps=60,
    )

    # ------------------------------------------------------------------
    # CAMERA
    # ------------------------------------------------------------------

    camera = show_manager.screens[0].camera

    camera.local.position = (
        0.0,
        -0.10,
        2.65,
    )

    camera.look_at(
        (0.0, 0.0, 0.0)
    )

    window.update_camera(
        camera,
        WINDOW_SIZE,
        scene,
    )

    # ------------------------------------------------------------------
    # SNAPSHOT
    # ------------------------------------------------------------------

    output = (
        OUTPUT
        / "brain_anatomical_regions.png"
    )

    window.snapshot(
        scene=scene,
        fname=str(output),
    )

    print(
        "\nSaved:"
        f"\n{output.resolve()}"
    )

    print(
        "\nOpen the FURY window and inspect the "
        "anatomical color separation."
    )

    show_manager.start()


if __name__ == "__main__":
    main()