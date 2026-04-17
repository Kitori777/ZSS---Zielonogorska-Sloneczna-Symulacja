from __future__ import annotations

import math

import numpy as np

from app.scene import (
    CX,
    CY,
    GRID_STEP,
    MOON_DISTANCE,
    MOON_MARKER_SIZE,
    SCENE_H,
    SCENE_W,
    SUN_DISTANCE,
    SUN_MARKER_SIZE,
    compute_light_map,
    draw_obstacles,
    draw_speedway,
    point_in_infield,
    point_on_speedway_track,
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
        value = value.to_pydatetime(warn=False)

    if not hasattr(value, "strftime"):
        return str(value)

    if getattr(value, "tzinfo", None) is None:
        return value.strftime("%H:%M")

    return value.astimezone(target_tzinfo).strftime("%H:%M")


def _snapshot(bundle, key):
    if not bundle:
        return None
    return bundle.get(key)


def _snapshot_value(bundle, key):
    snap = _snapshot(bundle, key)
    if snap is None:
        return None
    return getattr(snap, "value", None)


def _cloud_fraction(bundle):
    snap = _snapshot(bundle, "clouds")
    if snap is None or snap.value is None:
        return 0.0
    value = float(snap.value)
    if getattr(snap, "unit", None) == "oktanty" or value <= 8.0:
        return max(0.0, min(value / 8.0, 1.0))
    return max(0.0, min(value / 100.0, 1.0))


def _point_surface_temperature_estimate(air_temp, solar_factor, is_shaded, rain_mm_h):
    if air_temp is None:
        return None
    rain_mm_h = 0.0 if rain_mm_h is None else float(rain_mm_h)
    value = float(air_temp) + 8.0 * solar_factor - min(3.5, rain_mm_h * 0.9)
    if is_shaded:
        value -= 1.5
    return value


def _estimate_longwave_down(air_temp_k, relative_humidity, cloud_fraction):
    if air_temp_k is None:
        return None

    air_temp_k = float(air_temp_k)
    air_temp_c = air_temp_k - 273.15
    rh = 0.6 if relative_humidity is None else max(0.0, min(float(relative_humidity), 1.0))
    cloud_fraction = max(0.0, min(float(cloud_fraction), 1.0))

    saturation_hpa = 6.112 * math.exp((17.67 * air_temp_c) / (air_temp_c + 243.5))
    vapor_hpa = max(0.05, rh * saturation_hpa)

    eps_clear = 1.24 * (vapor_hpa / air_temp_k) ** (1.0 / 7.0)
    eps_all_sky = min(1.0, eps_clear * (1.0 + 0.22 * cloud_fraction * cloud_fraction))
    sigma = 5.670374419e-8
    return eps_all_sky * sigma * air_temp_k**4


def build_point_analysis(frame_state, app_state, weather_bundle=None):
    sun_info = frame_state["sun_info"]
    sun_vector = frame_state["sun_vector"]

    lit_x, lit_y, shade_x, shade_y = compute_light_map(
        sun_vector,
        include_infield=app_state.include_infield,
    )

    lit_points = {(float(x), float(y)) for x, y in zip(lit_x, lit_y, strict=True)}
    shade_points = {(float(x), float(y)) for x, y in zip(shade_x, shade_y, strict=True)}
    all_points = sorted(lit_points | shade_points)

    rain_snap = _snapshot(weather_bundle, "rain")
    temp_snap = _snapshot(weather_bundle, "temperature")
    temp_k_snap = _snapshot(weather_bundle, "air_temperature_k")
    cloud_snap = _snapshot(weather_bundle, "clouds")
    rh_snap = _snapshot(weather_bundle, "relative_humidity")
    wind_snap = _snapshot(weather_bundle, "wind_speed_m_per_s")
    precip_ms_snap = _snapshot(weather_bundle, "precipitation_m_per_s")
    pressure_snap = _snapshot(weather_bundle, "air_pressure_pa")
    shortwave_snap = _snapshot(weather_bundle, "shortwave_down_w_per_m2")
    longwave_snap = _snapshot(weather_bundle, "longwave_down_w_per_m2")

    rain_mm_h = None if rain_snap is None else rain_snap.value
    air_temp_c = None if temp_snap is None else temp_snap.value
    air_temp_k = None if temp_k_snap is None else temp_k_snap.value
    cloud_value = None if cloud_snap is None else cloud_snap.value
    cloud_unit = None if cloud_snap is None else cloud_snap.unit
    relative_humidity = None if rh_snap is None else rh_snap.value
    wind_speed = None if wind_snap is None else wind_snap.value
    precipitation_m_per_s = None if precip_ms_snap is None else precip_ms_snap.value
    air_pressure_pa = None if pressure_snap is None else pressure_snap.value
    shortwave = None if shortwave_snap is None else shortwave_snap.value
    longwave = None if longwave_snap is None else longwave_snap.value

    cloud_fraction = _cloud_fraction(weather_bundle)
    sun_altitude_deg = float(sun_info.get("altitude_deg", 0.0))
    base_solar = max(0.0, math.sin(math.radians(sun_altitude_deg)))
    rain_factor = 0.0 if rain_mm_h is None else max(0.0, min(float(rain_mm_h) / 4.0, 1.0))

    details = []
    lit_details = []
    shade_details = []

    for x, y in all_points:
        is_shaded = (x, y) in shade_points
        on_track = point_on_speedway_track(x, y)
        point_type = "tor" if on_track else "środek toru"

        shade_factor = 0.0 if is_shaded else 1.0
        solar_factor = (
            base_solar * shade_factor * (1.0 - 0.75 * cloud_fraction) * (1.0 - 0.35 * rain_factor)
        )
        solar_factor = max(0.0, min(solar_factor, 1.0))
        exposure_pct = solar_factor * 100.0
        estimated_temp = _point_surface_temperature_estimate(
            air_temp_c, solar_factor, is_shaded, rain_mm_h
        )

        cloud_fraction_value = cloud_fraction
        longwave_value = (
            longwave
            if longwave is not None
            else _estimate_longwave_down(air_temp_k, relative_humidity, cloud_fraction_value)
        )
        longwave_source = "source" if longwave is not None else "estimated"

        item = {
            "x": x,
            "y": y,
            "point_type": point_type,
            "is_shaded": is_shaded,
            "solar_exposure_pct": exposure_pct,
            "air_temperature_c": air_temp_c,
            "air_temperature_k": air_temp_k,
            "estimated_point_temperature_c": estimated_temp,
            "rain_mm_h": rain_mm_h if rain_mm_h is not None else 0.0,
            "precipitation_m_per_s": precipitation_m_per_s,
            "cloud_cover": cloud_fraction_value,
            "cloud_unit": "fraction [0,1]",
            "cloud_cover_raw": cloud_value,
            "cloud_unit_raw": cloud_unit,
            "relative_humidity": relative_humidity,
            "wind_speed_m_per_s": wind_speed,
            "air_pressure_pa": air_pressure_pa,
            "shortwave_down_w_per_m2": shortwave,
            "longwave_down_w_per_m2": longwave_value,
            "longwave_source": longwave_source,
            "local_time": frame_state["dt_local"],
        }
        details.append(item)
        if is_shaded:
            shade_details.append(item)
        else:
            lit_details.append(item)

    return {
        "all": details,
        "lit": lit_details,
        "shade": shade_details,
    }


def _attach_picker(collection, payload):
    try:
        collection.set_picker(8)
        collection._point_payload = payload
    except Exception:
        pass


def setup_axes(ax, zoom_factor=1.0, view_elev=28, view_azim=-58):
    zoom_factor = max(1.0, float(zoom_factor))
    half_w = (SCENE_W / 2.0) / zoom_factor
    half_h = (SCENE_H / 2.0) / zoom_factor
    half_z = 20.0 / zoom_factor

    ax.set_xlim(CX - half_w, CX + half_w)
    ax.set_ylim(CY - half_h, CY + half_h)
    ax.set_zlim(0, max(8.0, half_z * 2.0))

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Live / Symulacja 3D - słońce, księżyc, cień")

    ax.view_init(elev=view_elev, azim=view_azim)
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
        [sun_x],
        [sun_y],
        [sun_z],
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
        [moon_x],
        [moon_y],
        [moon_z],
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

    cloud_snap = _snapshot(weather_bundle, "clouds")
    rain_snap = _snapshot(weather_bundle, "rain")
    temp_snap = _snapshot(weather_bundle, "temperature")
    cloud_val = None if cloud_snap is None else cloud_snap.value
    rain_val = None if rain_snap is None else rain_snap.value
    temp_val = None if temp_snap is None else temp_snap.value

    weather_text = ""
    if weather_bundle:
        cloud_unit = "" if cloud_snap is None or cloud_snap.unit is None else f" {cloud_snap.unit}"
        rain_unit = "" if rain_snap is None or rain_snap.unit is None else f" {rain_snap.unit}"
        temp_unit = "" if temp_snap is None or temp_snap.unit is None else f" {temp_snap.unit}"
        clouds_txt = "brak" if cloud_val is None else f"{cloud_val:.1f}{cloud_unit}"
        rain_txt = "brak" if rain_val is None else f"{rain_val:.2f}{rain_unit}"
        temp_txt = "brak" if temp_val is None else f"{temp_val:.1f}{temp_unit}"
        weather_text = f"\nChmury: {clouds_txt}\nOpad: {rain_txt}\nTemperatura: {temp_txt}"

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


def draw_cloud_overlay(ax, cloud_cover_value):
    if cloud_cover_value is None:
        return

    cloud_cover_value = float(cloud_cover_value)
    if cloud_cover_value <= 8.0:
        intensity = max(0.0, min(cloud_cover_value / 8.0, 1.0))
    else:
        intensity = max(0.0, min(cloud_cover_value / 100.0, 1.0))
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
        ax.scatter([cx], [cy], [cz], s=size_base, c=CLOUD_COLOR, alpha=alpha, edgecolors="none")

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


def draw_rain_overlay(ax, rain_mm_h, include_infield=True, point_payload=None):
    if rain_mm_h is None:
        return

    rain_mm_h = float(rain_mm_h)
    if rain_mm_h <= 0.01:
        return

    points = _rain_points(include_infield=include_infield)
    if not points:
        return

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

    for x, y in selected_points:
        ax.plot(
            [x, x],
            [y, y],
            [z_top, z_bottom],
            color=RAIN_LINE_COLOR,
            alpha=line_alpha,
            linewidth=line_width,
        )

    px = [p[0] for p in points]
    py = [p[1] for p in points]
    pz = np.full(len(points), 0.18)

    size = 14 + min(45, rain_mm_h * 14)
    color_strength = min(1.0, 0.20 + rain_mm_h / 4.0)

    rain_scatter = ax.scatter(
        px,
        py,
        pz,
        s=size,
        c=RAIN_POINT_COLOR,
        alpha=0.15 + 0.35 * color_strength,
        marker="o",
        label=f"deszcz: {rain_mm_h:.2f} mm/h",
    )
    if point_payload:
        payload_map = {(item["x"], item["y"]): item for item in point_payload}
        ordered = [payload_map.get((float(x), float(y))) for x, y in points]
        ordered = [item for item in ordered if item is not None]
        if len(ordered) == len(points):
            _attach_picker(rain_scatter, ordered)

    ax.text2D(
        0.02,
        0.73,
        f"Deszcz na punktach toru: {_rain_strength_label(rain_mm_h)} ({rain_mm_h:.2f} mm/h)",
        transform=ax.transAxes,
        color="#93C5FD",
        fontsize=10,
        verticalalignment="top",
    )


def render_scene(
    ax, frame_state, app_state, weather_bundle=None, zoom_factor=1.0, view_elev=28, view_azim=-58
):
    ax.clear()
    setup_axes(ax, zoom_factor=zoom_factor, view_elev=view_elev, view_azim=view_azim)

    draw_speedway(ax)
    draw_obstacles(ax)
    draw_status(ax, frame_state, weather_bundle=weather_bundle)

    sun_info = frame_state["sun_info"]
    sun_vector = frame_state["sun_vector"]

    cloud_cover = (
        _snapshot_value(weather_bundle, "clouds")
        if app_state.show_weather and app_state.show_clouds
        else None
    )
    rain_mm_h = (
        _snapshot_value(weather_bundle, "rain")
        if app_state.show_weather and app_state.show_rain
        else None
    )

    analysis = build_point_analysis(frame_state, app_state, weather_bundle=weather_bundle)
    lit_details = analysis["lit"]
    shade_details = analysis["shade"]

    if cloud_cover is not None:
        draw_cloud_overlay(ax, cloud_cover)

    if app_state.show_sun and sun_info["altitude_deg"] > 0:
        draw_sun(ax, sun_vector)

    if app_state.show_moon:
        draw_moon_minecraft_style(ax, sun_vector)

    if sun_info["altitude_deg"] <= 0:
        draw_night_map(ax)
        if rain_mm_h is not None:
            draw_rain_overlay(
                ax,
                rain_mm_h,
                include_infield=app_state.include_infield,
                point_payload=analysis["all"],
            )
        legend = ax.legend(loc="upper right")
        if legend:
            legend.get_frame().set_facecolor("#FFFFFF")
            legend.get_frame().set_edgecolor("#D8DEE8")
        ax.set_position([0.03, 0.04, 0.94, 0.90])
        return analysis

    if app_state.show_light_map and lit_details:
        lit_x = [item["x"] for item in lit_details]
        lit_y = [item["y"] for item in lit_details]
        lit_scatter = ax.scatter(
            lit_x,
            lit_y,
            np.zeros(len(lit_x)),
            s=12,
            marker="s",
            c=TRACK_LIGHT_COLOR,
            alpha=0.75,
            label="oświetlone",
        )
        _attach_picker(lit_scatter, lit_details)

    if app_state.show_shadows and shade_details:
        shade_x = [item["x"] for item in shade_details]
        shade_y = [item["y"] for item in shade_details]
        shade_scatter = ax.scatter(
            shade_x,
            shade_y,
            np.zeros(len(shade_x)),
            s=12,
            marker="s",
            c=TRACK_SHADOW_COLOR,
            alpha=0.45,
            label="cień",
        )
        _attach_picker(shade_scatter, shade_details)

    if rain_mm_h is not None:
        draw_rain_overlay(
            ax, rain_mm_h, include_infield=app_state.include_infield, point_payload=analysis["all"]
        )

    legend = ax.legend(loc="upper right")
    if legend:
        legend.get_frame().set_facecolor("#FFFFFF")
        legend.get_frame().set_edgecolor("#D8DEE8")

    ax.set_position([0.03, 0.04, 0.94, 0.90])
    return analysis
