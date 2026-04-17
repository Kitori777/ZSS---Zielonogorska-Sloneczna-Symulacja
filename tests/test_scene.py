import numpy as np
from matplotlib import pyplot as plt

from app.scene import (
    CX,
    CY,
    FIELD_A,
    FIELD_B,
    build_box_faces,
    compute_light_map,
    draw_obstacles,
    draw_speedway,
    ellipse_points,
    point_in_ellipse,
    point_in_infield,
    point_on_speedway_track,
    ray_intersects_box,
)


def test_point_in_ellipse_center_true():
    assert point_in_ellipse(CX, CY, CX, CY, FIELD_A, FIELD_B)


def test_point_on_speedway_track_true_for_ring_point():
    assert point_on_speedway_track(CX + 45, CY)


def test_point_in_infield_true_for_center():
    assert point_in_infield(CX, CY)


def test_ellipse_points_length_matches_n():
    x, y = ellipse_points(CX, CY, 10, 5, n=50)
    assert len(x) == 50
    assert len(y) == 50


def test_ray_intersects_box_true_and_false_cases():
    origin = np.array([0.0, 0.0, 0.0])
    ray_dir = np.array([1.0, 0.0, 0.0])
    box_min = np.array([1.0, -1.0, -1.0])
    box_max = np.array([2.0, 1.0, 1.0])
    assert ray_intersects_box(origin, ray_dir, box_min, box_max)

    miss_dir = np.array([0.0, 1.0, 0.0])
    assert not ray_intersects_box(origin, miss_dir, box_min, box_max)


def test_build_box_faces_returns_six_faces():
    faces = build_box_faces(0, 0, 1, 1, 2)
    assert len(faces) == 6
    assert all(len(face) == 4 for face in faces)


def test_compute_light_map_returns_points_on_surface():
    sun_dir = np.array([1.0, 0.0, 1.0]) / np.linalg.norm([1.0, 0.0, 1.0])
    lit_x, lit_y, shade_x, shade_y = compute_light_map(sun_dir, include_infield=True)
    assert len(lit_x) + len(shade_x) > 0
    assert len(lit_y) == len(lit_x)
    assert len(shade_y) == len(shade_x)


def test_draw_speedway_and_obstacles_add_artists():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    draw_speedway(ax)
    draw_obstacles(ax)
    assert len(ax.lines) >= 3
    assert len(ax.collections) >= 1
    plt.close(fig)
