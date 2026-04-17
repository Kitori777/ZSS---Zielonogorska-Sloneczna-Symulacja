from dataclasses import dataclass
from datetime import datetime


@dataclass
class AppState:
    selected_date: object
    hour: float
    playing: bool = False
    frame_hour: float = 0.0

    mode: str = "live"  # "live" or "simulation"
    show_sun: bool = True
    show_moon: bool = True
    show_shadows: bool = True
    show_light_map: bool = True

    time_step_hours: float = 1.0
    include_infield: bool = True

    show_weather: bool = True
    show_clouds: bool = True
    show_rain: bool = True
    weather_source: str = "best"

    def reset_to_now(self):
        now = datetime.now()
        self.selected_date = now.date()
        self.hour = now.hour + now.minute / 60.0
        self.playing = False
        self.frame_hour = 0.0
