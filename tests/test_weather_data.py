from pathlib import Path

import pandas as pd

from app.weather_data import WeatherRepository


def create_station_csv(path: Path):
    df = pd.DataFrame(
        [
            {
                "data_czas": "2026-04-19 12:00:00",
                "temperatura_C": 10.0,
                "punkt_rosy_C": 5.0,
                "cisnienie_hPa": 1000.0,
                "predkosc_wiatru": 2.5,
                "opad_mm_6h": 1.2,
                "snieg_cm": 0.0,
                "zachmurzenie_oktanty": 6.0,
                "wilgotnosc_proc": 55.0,
            }
        ]
    )
    df.to_csv(path, index=False)


def create_model_csv(path: Path):
    df = pd.DataFrame(
        [
            {
                "time": "2026-04-19 12:00:00",
                "2m_temperature": 11.0,
                "2m_dewpoint_temperature": 4.0,
                "surface_pressure": 100500.0,
                "10m_u_component_of_wind": 3.0,
                "10m_v_component_of_wind": 4.0,
                "total_precipitation": 0.001,
                "snow_depth": 0.0,
                "surface_solar_radiation_downwards": 420.0,
                "surface_thermal_radiation_downwards": 310.0,
            }
        ]
    )
    df.to_csv(path, index=False)


def create_extra_csv(path: Path):
    df = pd.DataFrame([{"time": "2026-04-19T12:00:00Z", "prcp": 0.4}])
    df.to_csv(path, index=False)


def test_weather_repository_load_and_snapshot(tmp_path):
    station = tmp_path / "station.csv"
    model = tmp_path / "model.csv"
    extra = tmp_path / "extra.csv"
    create_station_csv(station)
    create_model_csv(model)
    create_extra_csv(extra)

    repo = WeatherRepository(station_csv=station, model_csv=model, extra_rain_csv=extra)
    snap = repo.get_snapshot(pd.Timestamp("2026-04-19 12:00:00"), "temperature", source="station")
    assert snap.value == 10.0


def test_weather_repository_transforms_and_bundle(tmp_path):
    station = tmp_path / "station.csv"
    model = tmp_path / "model.csv"
    extra = tmp_path / "extra.csv"
    create_station_csv(station)
    create_model_csv(model)
    create_extra_csv(extra)

    repo = WeatherRepository(station_csv=station, model_csv=model, extra_rain_csv=extra)
    bundle = repo.get_weather_bundle(pd.Timestamp("2026-04-19 12:00:00"), source="station")
    assert bundle["temperature"].value == 10.0
    assert bundle["air_temperature_k"].value == 283.15
    assert bundle["air_pressure_pa"].value == 100000.0
    assert bundle["relative_humidity"].value == 0.55
    assert bundle["precipitation_m_per_s"].value > 0


def test_weather_repository_best_uses_openmeteo_when_available(tmp_path):
    station = tmp_path / "station.csv"
    model = tmp_path / "model.csv"
    extra = tmp_path / "extra.csv"
    create_station_csv(station)
    create_model_csv(model)
    create_extra_csv(extra)

    repo = WeatherRepository(station_csv=station, model_csv=model, extra_rain_csv=extra)
    repo.openmeteo_df = pd.DataFrame(
        [
            {
                "time": pd.Timestamp("2026-04-19 12:00:00"),
                "temperature_2m": 13.0,
                "dew_point_2m": 6.0,
                "surface_pressure": 1008.0,
                "cloud_cover": 75.0,
                "precipitation": 0.7,
                "wind_speed_10m_ms": 5.0,
                "relative_humidity_2m": 67.0,
                "shortwave_radiation": 510.0,
                "snow_depth_cm": 0.0,
            }
        ]
    )
    repo._openmeteo_last_refresh = pd.Timestamp.now().to_pydatetime()
    repo._openmeteo_window = (pd.Timestamp("2026-04-12"), pd.Timestamp("2026-05-05"))

    bundle = repo.get_weather_bundle(pd.Timestamp("2026-04-19 12:00:00"), source="best")
    assert bundle["temperature"].value == 13.0
    assert bundle["shortwave_down_w_per_m2"].value == 510.0
    assert bundle["relative_humidity"].value == 0.67


def test_weather_repository_estimates_missing_columns_as_none(tmp_path):
    station = tmp_path / "station.csv"
    create_station_csv(station)
    repo = WeatherRepository(station_csv=station)
    snap = repo.get_snapshot(
        pd.Timestamp("2026-04-19 12:00:00"), "longwave_down_w_per_m2", source="station"
    )
    assert snap.value is None
