import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# =========================================================
# SCENA
# =========================================================

LAT = 51.9290278
LNG = 15.5293056

SCENE_W = 140
SCENE_H = 100
GRID_STEP = 2.0

SUN_DISTANCE = 170.0
SUN_MARKER_SIZE = 200
MOON_DISTANCE = 185.0
MOON_MARKER_SIZE = 120

CX = 70
CY = 50

# Tor żużlowy jako eliptyczny ring
OUTER_A = 52
OUTER_B = 26

INNER_A = 38
INNER_B = 14

FIELD_A = 34
FIELD_B = 11

OBSTACLES = [
    {
        "name": "trybuna_zach",
        "height": 14.0,
        "footprint": (8, 35, 20, 65),
    },
    {
        "name": "budynek_pit",
        "height": 8.0,
        "footprint": (108, 18, 126, 28),
    },
    {
        "name": "drzewa_polnoc",
        "height": 12.0,
        "footprint": (52, 82, 88, 92),
    },
]


def point_in_ellipse(x, y, cx, cy, a, b):
    return ((x - cx) ** 2) / (a ** 2) + ((y - cy) ** 2) / (b ** 2) <= 1.0


def point_on_speedway_track(x, y):
    inside_outer = point_in_ellipse(x, y, CX, CY, OUTER_A, OUTER_B)
    inside_inner = point_in_ellipse(x, y, CX, CY, INNER_A, INNER_B)
    return inside_outer and not inside_inner


def point_in_infield(x, y):
    return point_in_ellipse(x, y, CX, CY, FIELD_A, FIELD_B)


def ellipse_points(cx, cy, a, b, n=240):
    t = np.linspace(0, 2 * np.pi, n)
    x = cx + a * np.cos(t)
    y = cy + b * np.sin(t)
    return x, y


def ray_intersects_box(ray_origin, ray_dir, box_min, box_max):
    tmin = -np.inf
    tmax = np.inf

    for i in range(3):
        if abs(ray_dir[i]) < 1e-12:
            if ray_origin[i] < box_min[i] or ray_origin[i] > box_max[i]:
                return False
        else:
            t1 = (box_min[i] - ray_origin[i]) / ray_dir[i]
            t2 = (box_max[i] - ray_origin[i]) / ray_dir[i]

            t_near = min(t1, t2)
            t_far = max(t1, t2)

            tmin = max(tmin, t_near)
            tmax = min(tmax, t_far)

            if tmin > tmax:
                return False

    if tmax < 0:
        return False

    return True


def build_box_faces(x1, y1, x2, y2, h):
    p000 = [x1, y1, 0]
    p100 = [x2, y1, 0]
    p110 = [x2, y2, 0]
    p010 = [x1, y2, 0]

    p001 = [x1, y1, h]
    p101 = [x2, y1, h]
    p111 = [x2, y2, h]
    p011 = [x1, y2, h]

    return [
        [p000, p100, p110, p010],
        [p001, p101, p111, p011],
        [p000, p100, p101, p001],
        [p100, p110, p111, p101],
        [p110, p010, p011, p111],
        [p010, p000, p001, p011],
    ]


def compute_light_map(sun_dir, include_infield=True):
    xs = np.arange(0, SCENE_W + GRID_STEP, GRID_STEP)
    ys = np.arange(0, SCENE_H + GRID_STEP, GRID_STEP)

    lit_x, lit_y = [], []
    shade_x, shade_y = [], []

    for x in xs:
        for y in ys:
            on_track = point_on_speedway_track(x, y)
            on_field = point_in_infield(x, y) if include_infield else False

            if not (on_track or on_field):
                continue

            origin = np.array([x, y, 0.05], dtype=float)
            blocked = False

            for obs in OBSTACLES:
                x1, y1, x2, y2 = obs["footprint"]
                h = obs["height"]

                box_min = np.array([min(x1, x2), min(y1, y2), 0.0], dtype=float)
                box_max = np.array([max(x1, x2), max(y1, y2), h], dtype=float)

                if ray_intersects_box(origin, sun_dir, box_min, box_max):
                    blocked = True
                    break

            if blocked:
                shade_x.append(x)
                shade_y.append(y)
            else:
                lit_x.append(x)
                lit_y.append(y)

    return lit_x, lit_y, shade_x, shade_y


def draw_speedway(ax):
    xo, yo = ellipse_points(CX, CY, OUTER_A, OUTER_B)
    xi, yi = ellipse_points(CX, CY, INNER_A, INNER_B)
    xf, yf = ellipse_points(CX, CY, FIELD_A, FIELD_B)

    ax.plot(xo, yo, np.zeros_like(xo), linewidth=2)
    ax.plot(xi, yi, np.zeros_like(xi), linewidth=2)
    ax.plot(xf, yf, np.zeros_like(xf), linewidth=1, alpha=0.7)

    ax.text(CX, CY, 0.5, "ŚRODEK TORU", ha="center")


def draw_obstacles(ax):
    for obs in OBSTACLES:
        x1, y1, x2, y2 = obs["footprint"]
        h = obs["height"]

        faces = build_box_faces(x1, y1, x2, y2, h)
        box = Poly3DCollection(faces, alpha=0.35)
        ax.add_collection3d(box)

        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        ax.text(cx, cy, h + 1, f"{obs['name']}\n{h} m", fontsize=8, ha="center")
