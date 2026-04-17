import math

import numpy as np

from .suncalc import get_position, get_times, getMoonPosition


def get_position_degrees(date, lng, lat):
    """
    Sun position in radians and degrees.
    bearing_deg uses classic compass convention:
    0 = north, 90 = east, 180 = south, 270 = west
    """
    pos = get_position(date, lng, lat)

    suncalc_azimuth_deg = np.degrees(pos["azimuth"])
    altitude_deg = np.degrees(pos["altitude"])
    bearing_deg = (suncalc_azimuth_deg + 180) % 360

    return {
        "azimuth_rad": pos["azimuth"],
        "altitude_rad": pos["altitude"],
        "suncalc_azimuth_deg": suncalc_azimuth_deg,
        "altitude_deg": altitude_deg,
        "bearing_deg": bearing_deg,
    }


def get_shadow_direction(date, lng, lat):
    pos = get_position_degrees(date, lng, lat)

    sun_bearing_deg = pos["bearing_deg"]
    shadow_bearing_deg = (sun_bearing_deg + 180) % 360

    return {
        "sun_bearing_deg": sun_bearing_deg,
        "shadow_bearing_deg": shadow_bearing_deg,
        "altitude_deg": pos["altitude_deg"],
        "sun_above_horizon": pos["altitude_deg"] > 0,
    }


def get_shadow_length(date, lng, lat, object_height):
    pos = get_position_degrees(date, lng, lat)
    altitude_deg = pos["altitude_deg"]

    if altitude_deg <= 0:
        return np.inf

    return object_height / np.tan(np.radians(altitude_deg))


def get_sun_vector(date, lng, lat):
    """
    Returns unit vector from point toward the sun.
    Coordinate system:
    x -> east
    y -> north
    z -> up
    """
    pos = get_position_degrees(date, lng, lat)
    bearing_deg = pos["bearing_deg"]
    altitude_deg = pos["altitude_deg"]

    b = math.radians(bearing_deg)
    a = math.radians(altitude_deg)

    x = math.cos(a) * math.sin(b)
    y = math.cos(a) * math.cos(b)
    z = math.sin(a)

    vec = np.array([x, y, z], dtype=float)
    norm = np.linalg.norm(vec)
    if norm == 0:
        return np.array([0.0, 0.0, 1.0])

    return vec / norm


def get_moon_position_degrees(date, lng, lat):
    moon = getMoonPosition(date, lat, lng)

    suncalc_azimuth_deg = np.degrees(moon["azimuth"])
    altitude_deg = np.degrees(moon["altitude"])
    bearing_deg = (suncalc_azimuth_deg + 180) % 360

    return {
        "azimuth_rad": moon["azimuth"],
        "altitude_rad": moon["altitude"],
        "distance_km": moon["distance"],
        "parallactic_angle_rad": moon["parallacticAngle"],
        "suncalc_azimuth_deg": suncalc_azimuth_deg,
        "altitude_deg": altitude_deg,
        "bearing_deg": bearing_deg,
        "above_horizon": altitude_deg > 0,
    }


def get_day_summary(date, lng, lat):
    times = get_times(date, lng, lat)

    return {
        "sunrise": times["sunrise"],
        "sunset": times["sunset"],
        "solar_noon": times["solar_noon"],
        "nadir": times["nadir"],
        "dawn": times.get("dawn"),
        "dusk": times.get("dusk"),
    }
