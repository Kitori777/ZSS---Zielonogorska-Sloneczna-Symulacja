from datetime import date

from app.simulation import (
    bearing_to_text,
    build_frame_state,
    build_live_state,
    decimal_hour_to_hm,
    decimal_hour_to_hms,
    local_datetime_to_utc,
    local_timezone,
)


def test_local_timezone_exists():
    assert local_timezone() is not None


def test_decimal_hour_to_hms_rounds_and_clamps():
    assert decimal_hour_to_hms(10.5) == (10, 30, 0)
    assert decimal_hour_to_hms(-1) == (0, 0, 0)
    assert decimal_hour_to_hms(30) == (23, 59, 59)


def test_decimal_hour_to_hm():
    assert decimal_hour_to_hm(8.25) == (8, 15)


def test_local_datetime_to_utc_returns_two_datetimes():
    dt_utc, dt_local = local_datetime_to_utc(date(2026, 4, 19), 12.5)
    assert dt_utc.tzinfo is not None
    assert dt_local.tzinfo is not None


def test_bearing_to_text_wraps_compass_directions():
    assert bearing_to_text(0) == "północ"
    assert bearing_to_text(90) == "wschód"
    assert bearing_to_text(225) == "południowy-zachód"


def test_build_frame_state_contains_all_expected_keys():
    state = build_frame_state(date(2026, 4, 19), 12.0)
    assert {
        "dt_utc",
        "dt_local",
        "sun_info",
        "shadow_info",
        "moon_info",
        "day_info",
        "sun_vector",
    } <= set(state)


def test_build_live_state_contains_expected_keys():
    state = build_live_state()
    assert {
        "dt_utc",
        "dt_local",
        "sun_info",
        "shadow_info",
        "moon_info",
        "day_info",
        "sun_vector",
    } <= set(state)
