from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from app.render_3d import (
    _attach_picker,
    _cloud_fraction,
    _estimate_longwave_down,
    _point_surface_temperature_estimate,
    _rain_points,
    _rain_strength_label,
    _safe_time_to_local_str,
    _snapshot,
    _snapshot_value,
    build_point_analysis,
    draw_cloud_overlay,
    draw_moon_minecraft_style,
    draw_night_map,
    draw_rain_overlay,
    draw_status,
    draw_sun,
    render_scene,
    setup_axes,
)
from app.simulation import build_frame_state
from app.state import AppState


@dataclass
class Snap:
    value: float | None
    unit: str | None = None


def make_bundle():
    return {
        "clouds": Snap(0.5, "fraction [0,1]"),
        "rain": Snap(1.2, "mm/h"),
        "temperature": Snap(12.0, "°C"),
        "air_temperature_k": Snap(285.15, "K"),
        "relative_humidity": Snap(0.65, "ułamek [0,1]"),
        "wind_speed_m_per_s": Snap(2.3, "m/s"),
        "precipitation_m_per_s": Snap(1.2 / 3600000.0, "m/s"),
        "air_pressure_pa": Snap(100500.0, "Pa"),
        "shortwave_down_w_per_m2": Snap(300.0, "W/m²"),
        "longwave_down_w_per_m2": Snap(None, "W/m²"),
    }


def test_safe_time_to_local_str_handles_naive_datetime():
    dt = datetime(2026, 4, 19, 12, 0)
    assert _safe_time_to_local_str(dt, timezone.utc) == "12:00"


def test_snapshot_helpers_work():
    bundle = make_bundle()
    assert _snapshot(bundle, "temperature").value == 12.0
    assert _snapshot_value(bundle, "temperature") == 12.0
    assert _snapshot_value(bundle, "missing") is None


def test_cloud_fraction_supports_fraction_unit():
    bundle = make_bundle()
    assert np.isclose(_cloud_fraction(bundle), 0.5 / 8.0)


def test_point_surface_temperature_estimate_returns_value():
    value = _point_surface_temperature_estimate(12.0, 0.7, False, 1.0)
    assert value > 12.0


def test_estimate_longwave_down_returns_positive_value():
    value = _estimate_longwave_down(285.15, 0.6, 0.5)
    assert value > 0


def test_attach_picker_stores_payload():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    scatter = ax.scatter([0], [0], [0])
    _attach_picker(scatter, [{"x": 0, "y": 0}])
    assert hasattr(scatter, "_point_payload")
    plt.close(fig)


def test_setup_axes_sets_ranges():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    setup_axes(ax, zoom_factor=2.0)
    x0, x1 = ax.get_xlim()
    assert x1 > x0
    plt.close(fig)


def test_draw_helpers_add_artists():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    frame_state = build_frame_state(datetime(2026, 4, 19).date(), 12.0)
    draw_night_map(ax)
    draw_sun(ax, frame_state["sun_vector"])
    draw_moon_minecraft_style(ax, frame_state["sun_vector"])
    draw_status(ax, frame_state, weather_bundle=make_bundle())
    draw_cloud_overlay(ax, 50.0)
    draw_rain_overlay(ax, 1.0, include_infield=True)
    assert len(ax.collections) > 0
    plt.close(fig)


def test_rain_strength_label_categories():
    assert _rain_strength_label(None) == "brak"
    assert _rain_strength_label(0.05) == "śladowy"
    assert _rain_strength_label(0.2) == "słaby"
    assert _rain_strength_label(1.0) == "umiarkowany"
    assert _rain_strength_label(2.0) == "mocny"
    assert _rain_strength_label(5.0) == "bardzo mocny"


def test_rain_points_non_empty():
    assert len(_rain_points(include_infield=True)) > 0


def test_build_point_analysis_and_render_scene_return_analysis():
    frame_state = build_frame_state(datetime(2026, 4, 19).date(), 12.0)
    app_state = AppState(selected_date=frame_state["dt_local"].date(), hour=12.0)
    bundle = make_bundle()

    analysis = build_point_analysis(frame_state, app_state, weather_bundle=bundle)
    assert analysis["all"]
    assert "longwave_down_w_per_m2" in analysis["all"][0]

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    rendered = render_scene(ax, frame_state, app_state, weather_bundle=bundle)
    assert rendered["all"]
    plt.close(fig)
