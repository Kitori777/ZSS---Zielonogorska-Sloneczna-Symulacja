from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


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


WEATHER_VARIABLES = {
    "temperature": {
        "label": "Temperatura powietrza",
        "unit": "°C",
        "station": "temperatura_C",
        "model": "2m_temperature",
    },
    "dewpoint": {
        "label": "Punkt rosy",
        "unit": "°C",
        "station": "punkt_rosy_C",
        "model": "2m_dewpoint_temperature",
    },
    "pressure": {
        "label": "Ciśnienie",
        "unit": "hPa",
        "station": "cisnienie_hPa",
        "model": "surface_pressure",
    },
    "wind_speed": {
        "label": "Prędkość wiatru",
        "unit": "m/s",
        "station": "predkosc_wiatru",
        "model": "__wind_speed__",
    },
    "precipitation": {
        "label": "Opad",
        "unit": "mm/h",
        "station": "opad_mm_6h",
        "model": "total_precipitation_hourly",
        "extra": "prcp",
    },
    "snow_depth": {
        "label": "Pokrywa śnieżna",
        "unit": "cm",
        "station": "snieg_cm",
        "model": "snow_depth",
    },
    "cloud_cover": {
        "label": "Zachmurzenie",
        "unit": "oktanty",
        "station": "zachmurzenie_oktanty",
        "model": None,
    },
}


class WeatherRepository:
    def __init__(
        self,
        station_csv: str | Path | None = None,
        model_csv: str | Path | None = None,
        extra_rain_csv: str | Path | None = None,
    ):
        self.station_df = self._load_station(station_csv) if station_csv else None
        self.model_df = self._load_model(model_csv) if model_csv else None
        self.extra_rain_df = self._load_extra_rain(extra_rain_csv) if extra_rain_csv else None

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
            dt = dt.dt.tz_convert("Europe/Warsaw").dt.tz_localize(None)
        except Exception:
            dt = dt.dt.tz_localize(None)

        df["time"] = dt
        df["prcp"] = pd.to_numeric(df["prcp"], errors="coerce")

        return df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)

    def _nearest_value(self, df: pd.DataFrame | None, time_value: pd.Timestamp, column: str | None) -> Optional[float]:
        if df is None or df.empty or column is None or column not in df.columns:
            return None

        diffs = (df["time"] - time_value).abs()
        idx = diffs.idxmin()

        max_delta = pd.Timedelta(hours=1)
        if diffs.loc[idx] > max_delta:
            return None

        val = df.loc[idx, column]
        return None if pd.isna(val) else float(val)

    def get_snapshot(self, time_value, variable_key: str, source: str = "best") -> WeatherSnapshot:
        ts = pd.Timestamp(time_value)
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)

        cfg = WEATHER_VARIABLES[variable_key]

        station_value = self._nearest_value(self.station_df, ts, cfg.get("station"))
        model_value = self._nearest_value(self.model_df, ts, cfg.get("model"))
        extra_value = self._nearest_value(self.extra_rain_df, ts, cfg.get("extra"))

        if source == "station":
            value = station_value
        elif source == "model":
            value = model_value
        elif source == "extra":
            value = extra_value
        else:
            if variable_key == "precipitation":
                value = extra_value if extra_value is not None else model_value if model_value is not None else station_value
            else:
                value = station_value if station_value is not None else model_value

        return WeatherSnapshot(
            time=ts,
            source=source,
            variable_key=variable_key,
            label=cfg["label"],
            unit=cfg["unit"],
            value=value,
            station_value=station_value,
            model_value=model_value,
            extra_value=extra_value,
        )

    def get_weather_bundle(self, time_value, source: str = "best") -> dict:
        return {
            "clouds": self.get_snapshot(time_value, "cloud_cover", source="station"),
            "rain": self.get_snapshot(time_value, "precipitation", source=source),
            "temperature": self.get_snapshot(time_value, "temperature", source=source),
        }
