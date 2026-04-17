from __future__ import annotations

import json
import ssl
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from app.scene import LAT, LNG

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None


def _identity(value):
    return value


def _percent_to_fraction(value):
    if value is None:
        return None
    return float(value) / 100.0


def _c_to_k(value):
    if value is None:
        return None
    return float(value) + 273.15


def _hpa_to_pa(value):
    if value is None:
        return None
    return float(value) * 100.0


def _mm_h_to_m_s(value):
    if value is None:
        return None
    return float(value) / 3_600_000.0


@dataclass
class WeatherSnapshot:
    time: pd.Timestamp
    source: str
    variable_key: str
    label: str
    unit: str
    value: float | None
    station_value: float | None = None
    model_value: float | None = None
    extra_value: float | None = None
    openmeteo_value: float | None = None


WEATHER_VARIABLES = {
    "temperature": {
        "label": "Temperatura powietrza",
        "unit": "°C",
        "station": "temperatura_C",
        "model": "2m_temperature",
        "openmeteo": "temperature_2m",
        "transform": _identity,
    },
    "air_temperature_k": {
        "label": "Temperatura powietrza",
        "unit": "K",
        "station": "temperatura_C",
        "model": "2m_temperature",
        "openmeteo": "temperature_2m",
        "transform": _c_to_k,
    },
    "dewpoint": {
        "label": "Punkt rosy",
        "unit": "°C",
        "station": "punkt_rosy_C",
        "model": "2m_dewpoint_temperature",
        "openmeteo": "dew_point_2m",
        "transform": _identity,
    },
    "pressure": {
        "label": "Ciśnienie",
        "unit": "hPa",
        "station": "cisnienie_hPa",
        "model": "surface_pressure",
        "openmeteo": "surface_pressure",
        "transform": _identity,
    },
    "air_pressure_pa": {
        "label": "Ciśnienie",
        "unit": "Pa",
        "station": "cisnienie_hPa",
        "model": "surface_pressure",
        "openmeteo": "surface_pressure",
        "transform": _hpa_to_pa,
    },
    "wind_speed": {
        "label": "Prędkość wiatru",
        "unit": "m/s",
        "station": "predkosc_wiatru",
        "model": "__wind_speed__",
        "openmeteo": "wind_speed_10m_ms",
        "transform": _identity,
    },
    "wind_speed_m_per_s": {
        "label": "Prędkość wiatru",
        "unit": "m/s",
        "station": "predkosc_wiatru",
        "model": "__wind_speed__",
        "openmeteo": "wind_speed_10m_ms",
        "transform": _identity,
    },
    "precipitation": {
        "label": "Opad",
        "unit": "mm/h",
        "station": "opad_mm_6h",
        "model": "total_precipitation_hourly",
        "extra": "prcp",
        "openmeteo": "precipitation",
        "transform": _identity,
    },
    "precipitation_m_per_s": {
        "label": "Opad",
        "unit": "m/s",
        "station": "opad_mm_6h",
        "model": "total_precipitation_hourly",
        "extra": "prcp",
        "openmeteo": "precipitation",
        "transform": _mm_h_to_m_s,
    },
    "snow_depth": {
        "label": "Pokrywa śnieżna",
        "unit": "cm",
        "station": "snieg_cm",
        "model": "snow_depth",
        "openmeteo": "snow_depth_cm",
        "transform": _identity,
    },
    "cloud_cover": {
        "label": "Zachmurzenie",
        "unit": "%",
        "station": "zachmurzenie_oktanty",
        "model": None,
        "openmeteo": "cloud_cover",
        "transform": _identity,
    },
    "relative_humidity": {
        "label": "Wilgotność względna",
        "unit": "ułamek [0,1]",
        "station": "wilgotnosc_proc",
        "model": None,
        "openmeteo": "relative_humidity_2m",
        "transform": _percent_to_fraction,
    },
    "shortwave_down_w_per_m2": {
        "label": "Promieniowanie krótkofalowe",
        "unit": "W/m²",
        "station": None,
        "model": "surface_solar_radiation_downwards",
        "openmeteo": "shortwave_radiation",
        "transform": _identity,
    },
    "longwave_down_w_per_m2": {
        "label": "Promieniowanie długofalowe",
        "unit": "W/m²",
        "station": None,
        "model": "surface_thermal_radiation_downwards",
        "openmeteo": None,
        "transform": _identity,
    },
}


class WeatherRepository:
    def __init__(
        self,
        station_csv: str | Path | None = None,
        model_csv: str | Path | None = None,
        extra_rain_csv: str | Path | None = None,
        latitude: float = LAT,
        longitude: float = LNG,
        timezone_name: str = "Europe/Warsaw",
    ):
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.timezone_name = timezone_name

        self.station_df = self._load_station(station_csv) if station_csv else None
        self.model_df = self._load_model(model_csv) if model_csv else None
        self.extra_rain_df = self._load_extra_rain(extra_rain_csv) if extra_rain_csv else None

        self.openmeteo_df: pd.DataFrame | None = None
        self._openmeteo_error: str | None = None
        self._openmeteo_last_refresh: datetime | None = None
        self._openmeteo_last_attempt: datetime | None = None
        self._openmeteo_window: tuple[pd.Timestamp, pd.Timestamp] | None = None

    def _load_station(self, path: str | Path) -> pd.DataFrame:
        path = Path(path)
        df = pd.read_csv(path)

        if "data_czas" in df.columns:
            df["time"] = pd.to_datetime(df["data_czas"], errors="coerce")
        else:
            required = ["rok", "miesiac", "dzien", "godzina"]
            if not all(col in df.columns for col in required):
                raise ValueError("Brak kolumn do złożenia czasu w pliku stacyjnym.")
            df["time"] = pd.to_datetime(
                dict(
                    year=df["rok"],
                    month=df["miesiac"],
                    day=df["dzien"],
                    hour=df["godzina"],
                ),
                errors="coerce",
            )

        numeric_cols = [
            "temperatura_C",
            "punkt_rosy_C",
            "cisnienie_hPa",
            "predkosc_wiatru",
            "opad_mm_6h",
            "snieg_cm",
            "zachmurzenie_oktanty",
            "wilgotnosc_proc",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)

    def _load_model(self, path: str | Path) -> pd.DataFrame:
        path = Path(path)
        df = pd.read_csv(path)

        if "time" not in df.columns:
            raise ValueError("Plik modelowy nie ma kolumny 'time'.")

        df["time"] = pd.to_datetime(df["time"], errors="coerce")
        df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)

        if "surface_pressure" in df.columns:
            df["surface_pressure"] = pd.to_numeric(df["surface_pressure"], errors="coerce") / 100.0

        if "snow_depth" in df.columns:
            df["snow_depth"] = pd.to_numeric(df["snow_depth"], errors="coerce") * 100.0

        for col in [
            "2m_temperature",
            "2m_dewpoint_temperature",
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
            "total_precipitation",
            "surface_solar_radiation_downwards",
            "surface_thermal_radiation_downwards",
        ]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "10m_u_component_of_wind" in df.columns and "10m_v_component_of_wind" in df.columns:
            df["__wind_speed__"] = np.sqrt(
                df["10m_u_component_of_wind"] ** 2 + df["10m_v_component_of_wind"] ** 2
            )

        if "total_precipitation" in df.columns:
            df["total_precipitation"] = df["total_precipitation"] * 1000.0
            tp_hourly = df["total_precipitation"].diff()
            if len(df) > 0:
                tp_hourly.iloc[0] = df["total_precipitation"].iloc[0]
            reset_mask = tp_hourly < 0
            tp_hourly.loc[reset_mask] = df.loc[reset_mask, "total_precipitation"]
            tp_hourly.loc[tp_hourly < 0] = 0
            df["total_precipitation_hourly"] = tp_hourly.fillna(0)

        return df

    def _load_extra_rain(self, path: str | Path) -> pd.DataFrame:
        path = Path(path)
        df = pd.read_csv(path)

        if "time" not in df.columns or "prcp" not in df.columns:
            raise ValueError("Dodatkowy plik opadów musi mieć kolumny: 'time', 'prcp'.")

        dt = pd.to_datetime(df["time"], errors="coerce", utc=True)
        try:
            dt = dt.dt.tz_convert(self.timezone_name).dt.tz_localize(None)
        except Exception:
            dt = dt.dt.tz_localize(None)

        df["time"] = dt
        df["prcp"] = pd.to_numeric(df["prcp"], errors="coerce")

        return df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)

    def _nearest_value(
        self, df: pd.DataFrame | None, time_value: pd.Timestamp, column: str | None
    ) -> Optional[float]:
        if df is None or df.empty or column is None or column not in df.columns:
            return None

        diffs = (df["time"] - time_value).abs()
        idx = diffs.idxmin()

        max_delta = pd.Timedelta(hours=1)
        if diffs.loc[idx] > max_delta:
            return None

        val = df.loc[idx, column]
        return None if pd.isna(val) else float(val)

    def _normalize_time(self, time_value) -> pd.Timestamp:
        ts = pd.Timestamp(time_value)
        if ts.tzinfo is not None:
            ts = ts.tz_convert(self.timezone_name).tz_localize(None)
        return ts

    def _format_source_name(self, source: str) -> str:
        mapping = {
            "best": "hybrydowe",
            "station": "stacja",
            "model": "model",
            "extra": "opad ekstra",
            "openmeteo": "Open-Meteo",
        }
        return mapping.get(source, source)

    def _openmeteo_needs_refresh(self, ts: pd.Timestamp) -> bool:
        if self.openmeteo_df is None or self.openmeteo_df.empty:
            return True

        now = datetime.now()
        if self._openmeteo_last_refresh is None:
            return True
        if now - self._openmeteo_last_refresh > timedelta(minutes=30):
            return True

        if self._openmeteo_window is None:
            return True

        start_ts, end_ts = self._openmeteo_window
        return ts < start_ts or ts > end_ts

    def _fetch_json(self, url: str) -> dict:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SunCalc3D/1.0"
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json",
        }

        if requests is not None:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()

        request = Request(url, headers=headers)
        ssl_context = ssl.create_default_context()
        with urlopen(request, timeout=15, context=ssl_context) as response:
            return json.loads(response.read().decode("utf-8"))

    def _load_openmeteo(self, ts: pd.Timestamp):
        if not self._openmeteo_needs_refresh(ts):
            return

        start_ts = ts.normalize() - pd.Timedelta(days=7)
        end_ts = ts.normalize() + pd.Timedelta(days=15) + pd.Timedelta(hours=23)

        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone_name,
            "hourly": ",".join(
                [
                    "temperature_2m",
                    "dew_point_2m",
                    "surface_pressure",
                    "cloud_cover",
                    "precipitation",
                    "wind_speed_10m",
                    "snow_depth",
                    "relative_humidity_2m",
                    "shortwave_radiation",
                ]
            ),
            "past_days": 7,
            "forecast_days": 16,
            "wind_speed_unit": "ms",
        }

        url = f"https://api.open-meteo.com/v1/forecast?{urlencode(params)}"
        self._openmeteo_last_attempt = datetime.now()

        try:
            payload = self._fetch_json(url)
            hourly = payload.get("hourly") or {}
            times = hourly.get("time") or []
            if not times:
                raise ValueError("Brak godzinowych danych w odpowiedzi Open-Meteo.")

            df = pd.DataFrame(hourly)
            df["time"] = pd.to_datetime(df["time"], errors="coerce")

            numeric_cols = [
                "temperature_2m",
                "dew_point_2m",
                "surface_pressure",
                "cloud_cover",
                "precipitation",
                "wind_speed_10m",
                "snow_depth",
                "relative_humidity_2m",
                "shortwave_radiation",
            ]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            if "snow_depth" in df.columns:
                df["snow_depth_cm"] = df["snow_depth"]
            if "wind_speed_10m" in df.columns:
                df["wind_speed_10m_ms"] = df["wind_speed_10m"]

            df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
            self.openmeteo_df = df
            self._openmeteo_last_refresh = datetime.now()
            self._openmeteo_window = (start_ts, end_ts)
            self._openmeteo_error = None
        except Exception as exc:
            self._openmeteo_error = f"{type(exc).__name__}: {exc}"
            if self.openmeteo_df is None:
                self.openmeteo_df = pd.DataFrame(columns=["time"])

    def get_openmeteo_status_text(self) -> str:
        if self._openmeteo_error:
            return f"Open-Meteo: błąd ({self._openmeteo_error})"
        if self._openmeteo_last_refresh is None:
            return "Open-Meteo: gotowe do pobrania"
        return f"Open-Meteo: OK {self._openmeteo_last_refresh.strftime('%H:%M:%S')}"

    def get_snapshot(self, time_value, variable_key: str, source: str = "best") -> WeatherSnapshot:
        ts = self._normalize_time(time_value)
        cfg = WEATHER_VARIABLES[variable_key]
        transform = cfg.get("transform", _identity)

        station_value = self._nearest_value(self.station_df, ts, cfg.get("station"))
        model_value = self._nearest_value(self.model_df, ts, cfg.get("model"))
        extra_value = self._nearest_value(self.extra_rain_df, ts, cfg.get("extra"))

        openmeteo_value = None
        if source in {"best", "openmeteo"}:
            self._load_openmeteo(ts)
            openmeteo_value = self._nearest_value(self.openmeteo_df, ts, cfg.get("openmeteo"))

        resolved_source = source
        if source == "station":
            value = station_value
        elif source == "model":
            value = model_value
        elif source == "extra":
            value = extra_value
        elif source == "openmeteo":
            value = openmeteo_value
            resolved_source = "openmeteo"
        else:
            if variable_key == "precipitation":
                if openmeteo_value is not None:
                    value = openmeteo_value
                    resolved_source = "openmeteo"
                elif extra_value is not None:
                    value = extra_value
                    resolved_source = "extra"
                elif model_value is not None:
                    value = model_value
                    resolved_source = "model"
                else:
                    value = station_value
                    resolved_source = "station"
            elif variable_key == "cloud_cover":
                if openmeteo_value is not None:
                    value = openmeteo_value
                    resolved_source = "openmeteo"
                else:
                    value = station_value
                    resolved_source = "station"
            else:
                if openmeteo_value is not None:
                    value = openmeteo_value
                    resolved_source = "openmeteo"
                elif station_value is not None:
                    value = station_value
                    resolved_source = "station"
                else:
                    value = model_value
                    resolved_source = "model"

        value = transform(value) if value is not None else None
        station_value = transform(station_value) if station_value is not None else None
        model_value = transform(model_value) if model_value is not None else None
        extra_value = transform(extra_value) if extra_value is not None else None
        openmeteo_value = transform(openmeteo_value) if openmeteo_value is not None else None

        display_unit = cfg["unit"]
        if variable_key == "cloud_cover":
            display_unit = "oktanty" if resolved_source == "station" else "%"

        return WeatherSnapshot(
            time=ts,
            source=resolved_source,
            variable_key=variable_key,
            label=cfg["label"],
            unit=display_unit,
            value=value,
            station_value=station_value,
            model_value=model_value,
            extra_value=extra_value,
            openmeteo_value=openmeteo_value,
        )

    def get_weather_bundle(self, time_value, source: str = "best") -> dict:
        clouds = self.get_snapshot(time_value, "cloud_cover", source=source)
        rain = self.get_snapshot(time_value, "precipitation", source=source)
        temperature = self.get_snapshot(time_value, "temperature", source=source)
        air_temperature_k = self.get_snapshot(time_value, "air_temperature_k", source=source)
        relative_humidity = self.get_snapshot(time_value, "relative_humidity", source=source)
        wind_speed = self.get_snapshot(time_value, "wind_speed_m_per_s", source=source)
        precipitation_m_per_s = self.get_snapshot(
            time_value, "precipitation_m_per_s", source=source
        )
        air_pressure_pa = self.get_snapshot(time_value, "air_pressure_pa", source=source)
        shortwave = self.get_snapshot(time_value, "shortwave_down_w_per_m2", source=source)
        longwave = self.get_snapshot(time_value, "longwave_down_w_per_m2", source=source)
        return {
            "clouds": clouds,
            "rain": rain,
            "temperature": temperature,
            "air_temperature_k": air_temperature_k,
            "relative_humidity": relative_humidity,
            "wind_speed_m_per_s": wind_speed,
            "precipitation_m_per_s": precipitation_m_per_s,
            "air_pressure_pa": air_pressure_pa,
            "shortwave_down_w_per_m2": shortwave,
            "longwave_down_w_per_m2": longwave,
            "meta": {
                "source": self._format_source_name(source),
                "openmeteo_status": self.get_openmeteo_status_text(),
                "openmeteo_error": self._openmeteo_error,
            },
        }
