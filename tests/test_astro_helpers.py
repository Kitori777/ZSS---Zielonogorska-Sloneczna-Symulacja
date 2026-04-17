from datetime import datetime, timezone

import numpy as np

from suncalc import (
    get_day_summary,
    get_moon_position_degrees,
    get_position_degrees,
    get_shadow_direction,
    get_shadow_length,
    get_sun_vector,
)

date = datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc)
lat = 51.9290278
lng = 15.5293056


def test_get_position_degrees_returns_expected_keys():
    pos = get_position_degrees(date, lng, lat)
    assert set(pos) == {
        "azimuth_rad",
        "altitude_rad",
        "suncalc_azimuth_deg",
        "altitude_deg",
        "bearing_deg",
    }
    assert -180 <= pos["suncalc_azimuth_deg"] <= 180
    assert 0 <= pos["bearing_deg"] <= 360


def test_get_shadow_direction_is_opposite_to_sun_bearing():
    data = get_shadow_direction(date, lng, lat)
    expected = (data["sun_bearing_deg"] + 180) % 360
    assert np.isclose(data["shadow_bearing_deg"], expected)


def test_get_shadow_length_positive_when_sun_above_horizon():
    length = get_shadow_length(date, lng, lat, 10.0)
    assert np.isfinite(length)
    assert length > 0


def test_get_shadow_length_inf_when_sun_below_horizon():
    night = datetime(2026, 4, 19, 0, 0, tzinfo=timezone.utc)
    length = get_shadow_length(night, lng, lat, 10.0)
    assert np.isinf(length)


def test_get_sun_vector_is_normalized():
    vec = get_sun_vector(date, lng, lat)
    assert vec.shape == (3,)
    assert np.isclose(np.linalg.norm(vec), 1.0)


def test_get_moon_position_degrees_returns_keys():
    moon = get_moon_position_degrees(date, lng, lat)
    assert {"distance_km", "bearing_deg", "altitude_deg", "above_horizon"} <= set(moon)


def test_get_day_summary_contains_sunrise_and_sunset():
    day = get_day_summary(date, lng, lat)
    assert {"sunrise", "sunset", "solar_noon", "nadir", "dawn", "dusk"} <= set(day)
