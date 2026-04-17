from datetime import datetime, timezone

import numpy as np
import pandas as pd

from suncalc import get_position, get_times

date = datetime(2013, 3, 5, tzinfo=timezone.utc)
lat = 50.5
lng = 30.5
height = 2000

testTimes = {
    "solar_noon": "2013-03-05T10:10:57Z",
    "nadir": "2013-03-04T22:10:57Z",
    "sunrise": "2013-03-05T04:34:56Z",
    "sunset": "2013-03-05T15:46:57Z",
    "sunrise_end": "2013-03-05T04:38:19Z",
    "sunset_start": "2013-03-05T15:43:34Z",
    "dawn": "2013-03-05T04:02:17Z",
    "dusk": "2013-03-05T16:19:36Z",
    "nautical_dawn": "2013-03-05T03:24:31Z",
    "nautical_dusk": "2013-03-05T16:57:22Z",
    "night_end": "2013-03-05T02:46:17Z",
    "night": "2013-03-05T17:35:36Z",
    "golden_hour_end": "2013-03-05T05:19:01Z",
    "golden_hour": "2013-03-05T15:02:52Z",
}

heightTestTimes = {
    "solar_noon": "2013-03-05T10:10:57Z",
    "nadir": "2013-03-04T22:10:57Z",
    "sunrise": "2013-03-05T04:25:07Z",
    "sunset": "2013-03-05T15:56:46Z",
}


def test_get_position():
    pos = get_position(date, lng, lat)
    assert np.isclose(pos["azimuth"], -2.5003175907168385)
    assert np.isclose(pos["altitude"], -0.7000406838781611)


def test_get_times():
    times = get_times(date, lng, lat)
    for key, value in testTimes.items():
        assert times[key].strftime("%Y-%m-%dT%H:%M:%SZ") == value


def test_get_times_height():
    times = get_times(date, lng, lat, height)
    for key, value in heightTestTimes.items():
        assert times[key].strftime("%Y-%m-%dT%H:%M:%SZ") == value


def test_get_position_pandas_single_timestamp():
    ts_date = pd.Timestamp(date)

    pos = get_position(ts_date, lng, lat)
    assert np.isclose(pos["azimuth"], -2.5003175907168385)
    assert np.isclose(pos["altitude"], -0.7000406838781611)


def test_get_position_pandas_datetime_series():
    df = pd.DataFrame({"date": [date] * 3, "lat": [lat] * 3, "lng": [lng] * 3})

    results = [get_position(row.date, row.lng, row.lat) for row in df.itertuples(index=False)]

    assert len(results) == 3
    assert np.isclose(results[0]["azimuth"], -2.5003175907168385)
    assert np.isclose(results[0]["altitude"], -0.7000406838781611)


def test_get_times_pandas_single():
    times = get_times(date, lng, lat)
    assert isinstance(times["solar_noon"], pd.Timestamp)


def test_get_times_datetime_single():
    times = get_times(date, lng, lat)

    # pd.Timestamp jest instancją datetime.datetime
    assert isinstance(times["solar_noon"], datetime)


def test_get_times_arrays():
    df = pd.DataFrame({"date": [date] * 3, "lat": [lat] * 3, "lng": [lng] * 3})

    results = [get_times(row.date, row.lng, row.lat) for row in df.itertuples(index=False)]

    assert len(results) == 3
    assert results[0]["solar_noon"].strftime("%Y-%m-%dT%H:%M:%SZ") == testTimes["solar_noon"]
    assert results[0]["sunrise"].strftime("%Y-%m-%dT%H:%M:%SZ") == testTimes["sunrise"]


def test_get_times_for_high_latitudes():
    date = datetime(2020, 5, 26, 0, 0, 0)
    lng = -114.0719
    lat = 51.0447

    # ważne tylko, żeby nie rzuciło wyjątku
    get_times(date, lng, lat)
