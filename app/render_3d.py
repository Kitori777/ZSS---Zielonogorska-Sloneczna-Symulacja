import math
import numpy as np

from app.scene import (
    SCENE_W,
    SCENE_H,
    SUN_DISTANCE,
    SUN_MARKER_SIZE,
    MOON_DISTANCE,
    MOON_MARKER_SIZE,
    CX,
    CY,
    GRID_STEP,
    point_on_speedway_track,
    point_in_infield,
    compute_light_map,
    draw_speedway,
    draw_obstacles,
)
from app.simulation import bearing_to_text


SUN_COLOR = "#FDB813"
SUN_RAY_COLOR = "#F6C453"
MOON_COLOR = "#8FB8FF"
TRACK_LIGHT_COLOR = "#E8E1D3"
TRACK_SHADOW_COLOR = "#B9B2A4"
NIGHT_COLOR = "#D7E3F4"


def _safe_time_to_local_str(value, target_tzinfo):
    if value is None:
        return "--:--"

    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()

    if not hasattr(value, "strftime"):
        return str(value)

    if getattr(value, "tzinfo", None) is None:
        return value.strftime("%H:%M")

    return value.astimezone(target_tzinfo).strftime("%H:%M")


def setup_axes(ax):
    ax.set_xlim(0, SCENE_W)
    ax.set_ylim(0, SCENE_H)
    ax.set_zlim(0, 40)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Live / Symulacja 3D - słońce, księżyc, cień")

    ax.view_init(elev=28, azim=-58)
    ax.grid(True, alpha=0.25)


def draw_night_map(ax):
    xs = np.arange(0, SCENE_W + GRID_STEP, GRID_STEP)
    ys = np.arange(0, SCENE_H + GRID_STEP, GRID_STEP)
    night_x, night_y = [], []

    for x in xs:
        for y in ys:
            if point_on_speedway_track(x, y) or point_in_infield(x, y):
                night_x.append(x)
                night_y.append(y)

    if night_x:
        ax.scatter(
            night_x,
            night_y,
            np.zeros(len(night_x)),
            s=12,
            marker="s",
            c=NIGHT_COLOR,
            alpha=0.45,
            label="noc",
        )


def draw_sun(ax, sun_vector):
    sun_x = CX + sun_vector[0] * SUN_DISTANCE
    sun_y = CY + sun_vector[1] * SUN_DISTANCE
    sun_z = 8 + sun_vector[2] * SUN_DISTANCE * 0.7

    ax.scatter(
        [sun_x], [sun_y], [sun_z],
        s=SUN_MARKER_SIZE,
        marker="o",
        c=SUN_COLOR,
        edgecolors="#C88D00",
        linewidths=1.2,
    )
    ax.text(sun_x, sun_y, sun_z + 2, "SŁOŃCE", fontsize=10, ha="center", color="#7A4E00")

    for tx, ty in [(20, 50), (45, 30), (70, 50), (95, 68), (60, 50)]:
        ax.plot(
            [sun_x, tx],
            [sun_y, ty],
            [sun_z, 0],
            alpha=0.45,
            color=SUN_RAY_COLOR,
            linewidth=1.3,
        )


def draw_moon_minecraft_style(ax, sun_vector):
    """
    Księżyc stylizowany: zawsze po przeciwnej stronie słońca.
    Daje efekt jak w grach/symulacjach, a nie realny ruch astronomiczny.
    """
    moon_vector = -sun_vector

    moon_x = CX + moon_vector[0] * MOON_DISTANCE
    moon_y = CY + moon_vector[1] * MOON_DISTANCE
    moon_z = 8 + moon_vector[2] * MOON_DISTANCE * 0.7

    # rysuj tylko jeśli jest nad horyzontem
    if moon_z <= 0:
        return

    ax.scatter(
        [moon_x], [moon_y], [moon_z],
        s=MOON_MARKER_SIZE,
        marker="o",
        c=MOON_COLOR,
        edgecolors="#4F7FD9",
        linewidths=1.0,
    )
    ax.text(moon_x, moon_y, moon_z + 2, "KSIĘŻYC", fontsize=9, ha="center", color="#365D9D")


def draw_status(ax, frame_state):
    dt_local = frame_state["dt_local"]
    sun_info = frame_state["sun_info"]
    shadow_info = frame_state["shadow_info"]
    day_info = frame_state["day_info"]

    sunrise = _safe_time_to_local_str(day_info.get("sunrise"), dt_local.tzinfo)
    sunset = _safe_time_to_local_str(day_info.get("sunset"), dt_local.tzinfo)

    status = (
        f"Data lokalna: {dt_local.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Słońce: {shadow_info['sun_bearing_deg']:.1f}° ({bearing_to_text(shadow_info['sun_bearing_deg'])})\n"
        f"Wysokość słońca: {sun_info['altitude_deg']:.1f}°\n"
        f"Cień: {bearing_to_text(shadow_info['shadow_bearing_deg'])}\n"
        f"Wschód: {sunrise} | Zachód: {sunset}"
    )

    ax.text2D(0.02, 0.95, status, transform=ax.transAxes)


def render_scene(ax, frame_state, app_state):
    ax.clear()
    setup_axes(ax)

    draw_speedway(ax)
    draw_obstacles(ax)
    draw_status(ax, frame_state)

    sun_info = frame_state["sun_info"]
    sun_vector = frame_state["sun_vector"]

    # Słońce w dzień
    if app_state.show_sun and sun_info["altitude_deg"] > 0:
        draw_sun(ax, sun_vector)

    # Księżyc stylizowany jak w Minecraft — po przeciwnej stronie słońca
    if app_state.show_moon:
        draw_moon_minecraft_style(ax, sun_vector)

    # Noc: bez napisu, tylko wizualizacja nocna
    if sun_info["altitude_deg"] <= 0:
        draw_night_map(ax)

        legend = ax.legend(loc="upper right")
        if legend:
            legend.get_frame().set_facecolor("#FFFFFF")
            legend.get_frame().set_edgecolor("#D8DEE8")
        return

    # Dzień
    if app_state.show_light_map or app_state.show_shadows:
        lit_x, lit_y, shade_x, shade_y = compute_light_map(
            sun_vector,
            include_infield=app_state.include_infield,
        )

        if app_state.show_light_map and lit_x:
            ax.scatter(
                lit_x,
                lit_y,
                np.zeros(len(lit_x)),
                s=12,
                marker="s",
                c=TRACK_LIGHT_COLOR,
                alpha=0.75,
                label="oświetlone",
            )

        if app_state.show_shadows and shade_x:
            ax.scatter(
                shade_x,
                shade_y,
                np.zeros(len(shade_x)),
                s=12,
                marker="s",
                c=TRACK_SHADOW_COLOR,
                alpha=0.45,
                label="cień",
            )

    legend = ax.legend(loc="upper right")
    if legend:
        legend.get_frame().set_facecolor("#FFFFFF")
        legend.get_frame().set_edgecolor("#D8DEE8")
