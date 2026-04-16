from __future__ import annotations

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

RAIN_LINE_COLOR = "#4A90E2"
RAIN_POINT_COLOR = "#2F80ED"
CLOUD_COLOR = "#C7CED9"
STATUS_COLOR = "#F3F4F6"


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


def _snapshot_value(bundle, key):
    if not bundle:
        return None
    snap = bundle.get(key)
    if snap is None:
        return None
    return getattr(snap, "value", None)


def setup_axes(ax):
    ax.set_xlim(0, SCENE_W)
    ax.set_ylim(0, SCENE_H)
    ax.set_zlim(0, 40)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Live / Symulacja 3D - słońce, księżyc, cień")

    ax.view_init(elev=28, azim=-58)
    ax.set_box_aspect((SCENE_W, SCENE_H, 32))
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
    ax.text(sun_x, sun_y, sun_z + 2, "SŁOŃCE", fontsize=10, ha="center", color="#FDE68A")

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
    moon_vector = -sun_vector

    moon_x = CX + moon_vector[0] * MOON_DISTANCE
    moon_y = CY + moon_vector[1] * MOON_DISTANCE
    moon_z = 8 + moon_vector[2] * MOON_DISTANCE * 0.7

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
    ax.text(moon_x, moon_y, moon_z + 2, "KSIĘŻYC", fontsize=9, ha="center", color="#DBEAFE")


def draw_status(ax, frame_state, weather_bundle=None):
    dt_local = frame_state["dt_local"]
    sun_info = frame_state["sun_info"]
    shadow_info = frame_state["shadow_info"]
    day_info = frame_state["day_info"]

    sunrise = _safe_time_to_local_str(day_info.get("sunrise"), dt_local.tzinfo)
    sunset = _safe_time_to_local_str(day_info.get("sunset"), dt_local.tzinfo)

    cloud_val = _snapshot_value(weather_bundle, "clouds")
    rain_val = _snapshot_value(weather_bundle, "rain")
    temp_val = _snapshot_value(weather_bundle, "temperature")

    weather_text = ""
    if weather_bundle:
        clouds_txt = "brak" if cloud_val is None else f"{cloud_val:.1f} okt"
        rain_txt = "brak" if rain_val is None else f"{rain_val:.2f} mm/h"
        temp_txt = "brak" if temp_val is None else f"{temp_val:.1f} °C"
        weather_text = (
            f"\nChmury: {clouds_txt}"
            f"\nOpad: {rain_txt}"
            f"\nTemperatura: {temp_txt}"
        )

    status = (
        f"Data lokalna: {dt_local.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Słońce: {shadow_info['sun_bearing_deg']:.1f}° ({bearing_to_text(shadow_info['sun_bearing_deg'])})\n"
        f"Wysokość słońca: {sun_info['altitude_deg']:.1f}°\n"
        f"Cień: {bearing_to_text(shadow_info['shadow_bearing_deg'])}\n"
        f"Wschód: {sunrise} | Zachód: {sunset}"
        f"{weather_text}"
    )

    ax.text2D(
        0.02,
        0.96,
        status,
        transform=ax.transAxes,
        color=STATUS_COLOR,
        fontsize=11,
        verticalalignment="top",
    )


def _rain_strength_label(rain_mm_h: float | None) -> str:
    if rain_mm_h is None or rain_mm_h <= 0.01:
        return "brak"
    if rain_mm_h < 0.10:
        return "śladowy"
    if rain_mm_h < 0.50:
        return "słaby"
    if rain_mm_h < 1.50:
        return "umiarkowany"
    if rain_mm_h < 4.00:
        return "mocny"
    return "bardzo mocny"


def draw_cloud_overlay(ax, cloud_cover_okta):
    if cloud_cover_okta is None:
        return

    intensity = max(0.0, min(float(cloud_cover_okta) / 8.0, 1.0))
    if intensity <= 0.05:
        return

    cloud_count = max(2, int(round(2 + intensity * 7)))
    alpha = 0.18 + 0.32 * intensity
    size_base = 1800 + 2600 * intensity

    centers = [
        (18, 26, 33),
        (35, 68, 31),
        (55, 38, 34),
        (72, 74, 32),
        (92, 30, 35),
        (112, 64, 33),
        (126, 42, 31),
        (82, 50, 36),
        (48, 20, 30),
    ]

    for i in range(min(cloud_count, len(centers))):
        cx, cy, cz = centers[i]

        # rdzeń chmury
        ax.scatter(
            [cx],
            [cy],
            [cz],
            s=size_base,
            c=CLOUD_COLOR,
            alpha=alpha,
            edgecolors="none",
        )

        # boczne „puchy”
        offsets = [(-5, 0, -1), (5, 0, 0), (-2, 4, 1), (3, -4, 0)]
        for dx, dy, dz in offsets:
            ax.scatter(
                [cx + dx],
                [cy + dy],
                [cz + dz],
                s=size_base * 0.55,
                c=CLOUD_COLOR,
                alpha=alpha * 0.95,
                edgecolors="none",
            )


def _rain_points(include_infield=True):
    xs = np.arange(0, SCENE_W + GRID_STEP, GRID_STEP)
    ys = np.arange(0, SCENE_H + GRID_STEP, GRID_STEP)

    points = []
    for x in xs:
        for y in ys:
            on_track = point_on_speedway_track(x, y)
            on_field = point_in_infield(x, y) if include_infield else False
            if on_track or on_field:
                points.append((x, y))
    return points


def draw_rain_overlay(ax, rain_mm_h, include_infield=True):
    if rain_mm_h is None:
        return

    rain_mm_h = float(rain_mm_h)
    if rain_mm_h <= 0.01:
        return

    points = _rain_points(include_infield=include_infield)
    if not points:
        return

    # im większy opad, tym większa gęstość i widoczność
    density_step = 6
    if rain_mm_h >= 0.1:
        density_step = 4
    if rain_mm_h >= 0.5:
        density_step = 3
    if rain_mm_h >= 1.5:
        density_step = 2

    selected_points = points[::density_step]

    line_alpha = min(0.85, 0.20 + rain_mm_h * 0.18)
    line_width = 0.8 if rain_mm_h < 0.5 else 1.2
    z_top = 18.0 + min(10.0, rain_mm_h * 2.0)
    z_bottom = 3.0

    # pionowe smugi deszczu
    for x, y in selected_points:
        ax.plot(
            [x, x],
            [y, y],
            [z_top, z_bottom],
            color=RAIN_LINE_COLOR,
            alpha=line_alpha,
            linewidth=line_width,
        )

    # punkty na torze / infieldzie pokazujące gdzie „spadł” deszcz
    px = [p[0] for p in points]
    py = [p[1] for p in points]
    pz = np.full(len(points), 0.18)

    size = 14 + min(45, rain_mm_h * 14)
    color_strength = min(1.0, 0.20 + rain_mm_h / 4.0)

    ax.scatter(
        px,
        py,
        pz,
        s=size,
        c=RAIN_POINT_COLOR,
        alpha=0.15 + 0.35 * color_strength,
        marker="o",
        label=f"deszcz: {rain_mm_h:.2f} mm/h",
    )

    # podpis intensywności
    ax.text2D(
        0.02,
        0.73,
        f"Deszcz na punktach toru: {_rain_strength_label(rain_mm_h)} ({rain_mm_h:.2f} mm/h)",
        transform=ax.transAxes,
        color="#93C5FD",
        fontsize=10,
        verticalalignment="top",
    )


def render_scene(ax, frame_state, app_state, weather_bundle=None):
    ax.clear()
    setup_axes(ax)

    draw_speedway(ax)
    draw_obstacles(ax)
    draw_status(ax, frame_state, weather_bundle=weather_bundle)

    sun_info = frame_state["sun_info"]
    sun_vector = frame_state["sun_vector"]

    cloud_cover = _snapshot_value(weather_bundle, "clouds") if app_state.show_weather and app_state.show_clouds else None
    rain_mm_h = _snapshot_value(weather_bundle, "rain") if app_state.show_weather and app_state.show_rain else None

    # CHMURY nad obecną sceną
    if cloud_cover is not None:
        draw_cloud_overlay(ax, cloud_cover)

    # Słońce
    if app_state.show_sun and sun_info["altitude_deg"] > 0:
        draw_sun(ax, sun_vector)

    # Księżyc
    if app_state.show_moon:
        draw_moon_minecraft_style(ax, sun_vector)

    # Noc
    if sun_info["altitude_deg"] <= 0:
        draw_night_map(ax)

        if rain_mm_h is not None:
            draw_rain_overlay(ax, rain_mm_h, include_infield=app_state.include_infield)

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

    # DESZCZ na tej samej scenie
    if rain_mm_h is not None:
        draw_rain_overlay(ax, rain_mm_h, include_infield=app_state.include_infield)

    legend = ax.legend(loc="upper right")
    if legend:
        legend.get_frame().set_facecolor("#FFFFFF")
        legend.get_frame().set_edgecolor("#D8DEE8")

    ax.set_position([0.03, 0.04, 0.94, 0.90])
