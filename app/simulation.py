from datetime import datetime, timezone

from app.scene import LAT, LNG
from suncalc import (
    get_day_summary,
    get_moon_position_degrees,
    get_position_degrees,
    get_shadow_direction,
    get_sun_vector,
)


def local_timezone():
    return datetime.now().astimezone().tzinfo


def decimal_hour_to_hms(hour_value: float):
    total_seconds = int(round(hour_value * 3600))
    total_seconds = max(0, min(total_seconds, 23 * 3600 + 59 * 60 + 59))

    hour = total_seconds // 3600
    minute = (total_seconds % 3600) // 60
    second = total_seconds % 60

    return hour, minute, second


def decimal_hour_to_hm(hour_value: float):
    hour, minute, _ = decimal_hour_to_hms(hour_value)
    return hour, minute


def local_datetime_to_utc(date_obj, hour_value):
    tz = local_timezone()

    hour, minute, second = decimal_hour_to_hms(float(hour_value))

    local_dt = datetime(
        year=date_obj.year,
        month=date_obj.month,
        day=date_obj.day,
        hour=hour,
        minute=minute,
        second=second,
        tzinfo=tz,
    )
    return local_dt.astimezone(timezone.utc), local_dt


def bearing_to_text(deg: float) -> str:
    directions = [
        "północ",
        "północny-wschód",
        "wschód",
        "południowy-wschód",
        "południe",
        "południowy-zachód",
        "zachód",
        "północny-zachód",
    ]
    idx = round(deg / 45) % 8
    return directions[idx]


def build_frame_state(date_obj, hour_value):
    dt_utc, dt_local = local_datetime_to_utc(date_obj, hour_value)

    sun_info = get_position_degrees(dt_utc, LNG, LAT)
    shadow_info = get_shadow_direction(dt_utc, LNG, LAT)
    moon_info = get_moon_position_degrees(dt_utc, LNG, LAT)
    day_info = get_day_summary(dt_utc, LNG, LAT)
    sun_vector = get_sun_vector(dt_utc, LNG, LAT)

    return {
        "dt_utc": dt_utc,
        "dt_local": dt_local,
        "sun_info": sun_info,
        "shadow_info": shadow_info,
        "moon_info": moon_info,
        "day_info": day_info,
        "sun_vector": sun_vector,
    }


def build_live_state():
    now = datetime.now()
    current_decimal_hour = (
        now.hour + now.minute / 60.0 + now.second / 3600.0 + now.microsecond / 3_600_000_000.0
    )
    return build_frame_state(now.date(), current_decimal_hour)
